from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models import Deal, Document
from schemas import DocumentResponse
from config import settings
import os

router = APIRouter()


@router.post("/deals/{deal_id}/documents")
async def upload_documents(
    deal_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(deal_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    created_docs = []
    for file in files:
        # Save file to disk
        file_path = os.path.join(upload_dir, file.filename)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Determine file type from extension
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "txt"
        
        doc = Document(
            deal_id=deal_id,
            filename=file.filename,
            file_path=file_path,
            file_type=ext,
            file_size=len(content),
            extracted_text=None,  # Parsed later during analysis
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        created_docs.append(DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            doc_type=doc.doc_type,
            doc_type_confidence=doc.doc_type_confidence,
            uploaded_at=doc.uploaded_at,
        ))
    
    return {"documents": created_docs}


@router.get("/deals/{deal_id}/documents")
def list_documents(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    docs = db.query(Document).filter(Document.deal_id == deal_id).all()
    return {
        "documents": [
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                file_type=doc.file_type,
                file_size=doc.file_size,
                doc_type=doc.doc_type,
                doc_type_confidence=doc.doc_type_confidence,
                uploaded_at=doc.uploaded_at,
            )
            for doc in docs
        ]
    }


from fastapi.responses import FileResponse

@router.get("/documents/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Document file not found")
    
    # Map common extensions to media types
    ext_map = {
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xls": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
        "txt": "text/plain",
    }
    media_type = ext_map.get(doc.file_type.lower(), "application/octet-stream")
    
    return FileResponse(
        doc.file_path,
        media_type=media_type,
        filename=doc.filename,
    )

@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file from disk
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    db.delete(doc)
    db.commit()
    return {"message": "deleted"}
