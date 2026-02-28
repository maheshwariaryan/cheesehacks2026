from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Deal, Document, Analysis, ChatMessage
from schemas import DealCreate, DealResponse, DealDetailResponse, DocumentResponse, AnalysisSummary
import os
import shutil

router = APIRouter()


@router.post("/deals", response_model=DealResponse)
def create_deal(deal: DealCreate, db: Session = Depends(get_db)):
    db_deal = Deal(
        name=deal.name,
        target_company=deal.target_company,
        industry=deal.industry,
        deal_size=deal.deal_size,
    )
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    return DealResponse(
        id=db_deal.id,
        name=db_deal.name,
        target_company=db_deal.target_company,
        industry=db_deal.industry,
        deal_size=db_deal.deal_size,
        status=db_deal.status,
        created_at=db_deal.created_at,
        document_count=0,
        analysis_count=0,
    )


@router.get("/deals")
def list_deals(db: Session = Depends(get_db)):
    deals = db.query(Deal).order_by(Deal.created_at.desc()).all()
    result = []
    for deal in deals:
        result.append(DealResponse(
            id=deal.id,
            name=deal.name,
            target_company=deal.target_company,
            industry=deal.industry,
            deal_size=deal.deal_size,
            status=deal.status,
            created_at=deal.created_at,
            document_count=len(deal.documents),
            analysis_count=len(deal.analyses),
        ))
    return {"deals": result}


@router.get("/deals/{deal_id}", response_model=DealDetailResponse)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    documents = [
        DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            doc_type=doc.doc_type,
            doc_type_confidence=doc.doc_type_confidence,
            uploaded_at=doc.uploaded_at,
        )
        for doc in deal.documents
    ]
    
    analyses = [
        AnalysisSummary(
            analysis_type=a.analysis_type,
            status=a.status,
            completed_at=a.completed_at,
        )
        for a in deal.analyses
    ]
    
    return DealDetailResponse(
        id=deal.id,
        name=deal.name,
        target_company=deal.target_company,
        industry=deal.industry,
        deal_size=deal.deal_size,
        status=deal.status,
        created_at=deal.created_at,
        documents=documents,
        analyses=analyses,
    )


@router.delete("/deals/{deal_id}")
def delete_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Delete uploaded files from disk
    upload_dir = os.path.join("./uploads", str(deal_id))
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    
    db.delete(deal)
    db.commit()
    return {"message": "deleted"}
