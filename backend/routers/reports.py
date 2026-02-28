import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import Deal, GeneratedReport, Analysis
from schemas import ReportResponse
from utils import parse_json_field

router = APIRouter()


@router.post("/deals/{deal_id}/reports/{report_type}")
def generate_report(
    deal_id: int,
    report_type: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Create report record
    reports_dir = os.path.abspath(os.path.join("./reports", str(deal_id)))
    os.makedirs(reports_dir, exist_ok=True)
    file_path = os.path.join(reports_dir, f"{report_type}_report.pdf")
    
    report = db.query(GeneratedReport).filter(
        GeneratedReport.deal_id == deal_id,
        GeneratedReport.report_type == report_type,
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
    
    # Kick off report generation in background
    background_tasks.add_task(run_report_generation, report.id, deal_id, report_type, file_path)
    
    return {"report_id": report.id, "status": "generating"}


@router.get("/deals/{deal_id}/reports")
def list_reports(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    reports = db.query(GeneratedReport).filter(GeneratedReport.deal_id == deal_id).all()
    return {
        "reports": [
            ReportResponse(
                id=r.id,
                report_type=r.report_type,
                generated_at=r.generated_at,
                download_url=f"/api/reports/{r.id}/download",
            )
            for r in reports
        ]
    }


@router.get("/reports/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(GeneratedReport).filter(GeneratedReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    file_path = os.path.abspath(report.file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    media_type = "text/html" if file_path.endswith(".html") else "application/pdf"
    filename = os.path.basename(file_path)
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": media_type,
            "X-Content-Type-Options": "nosniff"
        }
    )


@router.get("/deals/{deal_id}/reports/{report_type}/status")
def report_status(deal_id: int, report_type: str, db: Session = Depends(get_db)):
    report = db.query(GeneratedReport).filter(
        GeneratedReport.deal_id == deal_id,
        GeneratedReport.report_type == report_type,
    ).order_by(GeneratedReport.generated_at.desc()).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if os.path.exists(report.file_path):
        return {"status": "completed"}
    else:
        return {"status": "generating"}


def run_report_generation(report_id: int, deal_id: int, report_type: str, file_path: str):
    """Run report generation in background. Uses teammate's report_generator."""
    db = SessionLocal()
    try:
        # Gather analysis data
        analyses = db.query(Analysis).filter(Analysis.deal_id == deal_id).all()
        analysis_data = {}
        for a in analyses:
            analysis_data[a.analysis_type] = parse_json_field(a.results)

        deal = db.query(Deal).filter(Deal.id == deal_id).first()
        deal_dict = {
            "id": deal.id,
            "name": deal.name,
            "target_company": deal.target_company,
            "industry": deal.industry,
            "deal_size": deal.deal_size,
        }

        # Step 1: Try to generate AI narrative sections via Claude
        narrative = {}
        try:
            from services.claude_service import generate_report_content
            narrative = generate_report_content(report_type, {
                "deal": deal_dict,
                "analyses": analysis_data,
            })
        except ImportError:
            pass  # Claude not available — report will render without narrative
        except Exception as e:
            print(f"Narrative generation failed: {e}")

        # Step 2: Generate PDF via ReportGenerator
        try:
            from services.report_generator import ReportGenerator
            generator = ReportGenerator()
            actual_path = generator.generate(
                report_type=report_type,
                deal=deal_dict,
                analyses=analysis_data,
                narrative=narrative or {},
            )
            # Update the report record with the actual path
            report = db.query(GeneratedReport).filter(GeneratedReport.id == report_id).first()
            if report:
                report.file_path = actual_path
                db.commit()
        except ImportError:
            print(f"Report generator not available for deal {deal_id}.")
        except Exception as e:
            print(f"Report generation failed for deal {deal_id}: {e}")
    finally:
        db.close()
