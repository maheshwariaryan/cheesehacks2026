import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import Deal, Document, Analysis
from schemas import AnalysisResponse
from services.document_parser import parse_file
from services.financial_analyzer import (
    analyze_qoe, analyze_working_capital, calculate_ratios,
    calculate_dcf, detect_red_flags
)
from utils import parse_json_field

router = APIRouter()


@router.post("/deals/{deal_id}/analyze")
def trigger_analysis(deal_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    deal.status = "analyzing"
    db.commit()
    
    background_tasks.add_task(run_analysis_pipeline, deal_id)
    return {"status": "analyzing", "deal_id": deal_id}


@router.get("/deals/{deal_id}/analysis")
def list_analyses(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    analyses = db.query(Analysis).filter(Analysis.deal_id == deal_id).all()
    return {
        "analyses": [
            AnalysisResponse(
                id=a.id,
                analysis_type=a.analysis_type,
                status=a.status,
                results=parse_json_field(a.results),
                error_message=a.error_message,
                created_at=a.created_at,
                completed_at=a.completed_at,
            )
            for a in analyses
        ]
    }


@router.get("/deals/{deal_id}/analysis/{analysis_type}")
def get_analysis(deal_id: int, analysis_type: str, db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(
        Analysis.deal_id == deal_id,
        Analysis.analysis_type == analysis_type,
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return AnalysisResponse(
        id=analysis.id,
        analysis_type=analysis.analysis_type,
        status=analysis.status,
        results=parse_json_field(analysis.results),
        error_message=analysis.error_message,
        created_at=analysis.created_at,
        completed_at=analysis.completed_at,
    )


# ============================================================
# ANALYSIS PIPELINE (runs in BackgroundTasks)
# ============================================================

def run_analysis_pipeline(deal_id: int):
    """Runs in BackgroundTasks. Creates its OWN db session."""
    db = SessionLocal()
    try:
        deal = db.query(Deal).filter(Deal.id == deal_id).first()
        deal.status = "analyzing"
        db.commit()

        # --- STEP 1: Parse all documents ---
        for doc in deal.documents:
            if not doc.extracted_text:
                text = parse_file(doc.file_path, doc.file_type)
                doc.extracted_text = text
                db.commit()

        # --- STEP 2: ML classification (teammate's code) ---
        try:
            from services.ml_engine import DocumentClassifier
            classifier = DocumentClassifier()
            for doc in deal.documents:
                if doc.extracted_text:
                    doc_type, confidence = classifier.classify(doc.extracted_text, doc.filename)
                    doc.doc_type = doc_type
                    doc.doc_type_confidence = confidence
                    db.commit()
        except ImportError:
            pass  # ML service not yet available

        # --- STEP 3: AI extraction (teammate's code) ---
        all_financial_data = []
        try:
            from services.claude_service import extract_financial_data
            for doc in deal.documents:
                if doc.extracted_text:
                    try:
                        data = extract_financial_data(doc.extracted_text, doc.filename)
                    except Exception as e:
                        print(f"AI extraction failed for {doc.filename}: {e}. Falling back to local extractor.")
                        from services.local_extractor import extract_financial_data_local
                        data = extract_financial_data_local(doc.extracted_text, doc.filename)

                    if data:
                        doc.financial_data = json.dumps(data)
                        all_financial_data.append(data)
                        db.commit()
        except ImportError:
            pass  # Claude service not yet available

        # --- STEP 4: Merge financial data ---
        merged = merge_financial_data(all_financial_data)

        # If no AI extraction available, check for hardcoded seed data
        if not merged.get("income_statement"):
            # Try to load financial data from document records (seed data)
            for doc in deal.documents:
                if doc.financial_data:
                    data = parse_json_field(doc.financial_data)
                    if data:
                        all_financial_data.append(data)
            merged = merge_financial_data(all_financial_data)

        if not merged.get("income_statement"):
            # Fallback: pipeline can't run without financial data
            deal.status = "failed"
            db.commit()
            return

        # --- STEP 5: RAG ingestion (teammate's code) ---
        try:
            from services.rag_service import RAGService
            rag = RAGService()
            for doc in deal.documents:
                if doc.extracted_text:
                    rag.ingest_document(deal.id, doc.id, doc.extracted_text, doc.filename)
        except ImportError:
            pass

        # --- STEP 6: Run ALL financial calculations ---
        qoe = analyze_qoe(merged)
        save_analysis(db, deal_id, "qoe", qoe)

        wc = analyze_working_capital(merged)
        save_analysis(db, deal_id, "working_capital", wc)

        ratios = calculate_ratios(merged)
        save_analysis(db, deal_id, "ratios", ratios)

        dcf = calculate_dcf(merged)
        save_analysis(db, deal_id, "dcf", dcf)

        red_flags = detect_red_flags(merged, ratios, wc, qoe)
        save_analysis(db, deal_id, "red_flags", red_flags)

        # --- STEP 7: ML anomaly detection (teammate's code) ---
        try:
            from services.ml_engine import AnomalyDetector
            detector = AnomalyDetector()
            anomalies = detector.detect(merged, ratios)
            save_analysis(db, deal_id, "anomalies", anomalies)
        except ImportError:
            save_analysis(db, deal_id, "anomalies", [])

        # --- STEP 8: AI insights (with 90s timeout so a hung Claude call never stalls the pipeline) ---
        try:
            from services.claude_service import generate_insights
            import concurrent.futures
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(generate_insights, merged, ratios, red_flags, anomalies, qoe, dcf)
                    insights = future.result(timeout=90)
                save_analysis(db, deal_id, "ai_insights", insights)
            except concurrent.futures.TimeoutError:
                print(f"AI insights timed out after 90s — saving empty insights and continuing.")
                save_analysis(db, deal_id, "ai_insights", None)
            except Exception as e:
                print(f"AI insights generation failed: {e}")
                save_analysis(db, deal_id, "ai_insights", None)
        except ImportError:
            save_analysis(db, deal_id, "ai_insights", None)

        # --- Mark deal as completed BEFORE report generation ---
        # This ensures that even if report generation fails, the deal is accessible.
        deal.status = "completed"
        db.commit()

        # --- STEP 9: Auto-generate reports (non-blocking — failure won't affect deal status) ---
        try:
            from routers.reports import run_report_generation
            from models import GeneratedReport
            import os

            reports_dir = os.path.abspath(os.path.join("./reports", str(deal_id)))
            os.makedirs(reports_dir, exist_ok=True)

            for report_type in ["iar", "dcf", "red_flag", "qoe", "nwc", "executive_summary"]:
                try:
                    file_path = os.path.join(reports_dir, f"{report_type}_report.pdf")

                    report = db.query(GeneratedReport).filter(
                        GeneratedReport.deal_id == deal_id,
                        GeneratedReport.report_type == report_type
                    ).first()

                    if not report:
                        report = GeneratedReport(
                            deal_id=deal_id,
                            report_type=report_type,
                            file_path=file_path,
                        )
                        db.add(report)
                    else:
                        report.file_path = file_path

                    db.commit()
                    db.refresh(report)

                    print(f"Auto-generating {report_type} report for deal {deal_id}...")
                    run_report_generation(report.id, deal_id, report_type, file_path)
                except Exception as re:
                    print(f"Report {report_type} failed (non-fatal): {re}")

        except Exception as e:
            print(f"Auto-reporting block failed (non-fatal): {e}")

    except Exception as e:
        deal.status = "failed"
        db.commit()
        import traceback
        traceback.print_exc()
        print(f"Pipeline failed for deal {deal_id}: {e}")
    finally:
        db.close()


def save_analysis(db, deal_id, analysis_type, results):
    """Create or update an Analysis row."""
    existing = db.query(Analysis).filter(
        Analysis.deal_id == deal_id,
        Analysis.analysis_type == analysis_type
    ).first()
    if existing:
        existing.results = json.dumps(results) if results else None
        existing.status = "completed"
        existing.completed_at = datetime.utcnow()
    else:
        analysis = Analysis(
            deal_id=deal_id,
            analysis_type=analysis_type,
            results=json.dumps(results) if results else None,
            status="completed",
            completed_at=datetime.utcnow()
        )
        db.add(analysis)
    db.commit()


def merge_financial_data(data_list: list) -> dict:
    """
    Merge financial data from multiple documents.
    For each field: take the first non-zero value found.
    Adjustments: concatenate all lists.
    Notes: concatenate all lists.
    """
    if not data_list:
        return {}
    if len(data_list) == 1:
        return data_list[0]

    merged = {
        "company_name": "",
        "period": "",
        "currency": "USD",
        "income_statement": {},
        "balance_sheet": {},
        "cash_flow": {},
        "adjustments": [],
        "notes": [],
    }

    for data in data_list:
        if not merged["company_name"] and data.get("company_name"):
            merged["company_name"] = data["company_name"]
        if not merged["period"] and data.get("period"):
            merged["period"] = data["period"]

        for section in ["income_statement", "balance_sheet", "cash_flow"]:
            for key, value in data.get(section, {}).items():
                if value is not None and value != "" and not merged[section].get(key):
                    merged[section][key] = value

        merged["adjustments"].extend(data.get("adjustments", []))
        merged["notes"].extend(data.get("notes", []))

    return merged
