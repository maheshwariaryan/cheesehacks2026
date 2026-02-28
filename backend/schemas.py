from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

# --- Requests ---
class DealCreate(BaseModel):
    name: str
    target_company: str
    industry: Optional[str] = None
    deal_size: Optional[float] = None

class ChatRequest(BaseModel):
    message: str

# --- Responses ---
class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    doc_type: Optional[str] = None
    doc_type_confidence: Optional[float] = None
    uploaded_at: datetime

class AnalysisSummary(BaseModel):
    analysis_type: str
    status: str
    completed_at: Optional[datetime] = None

class DealResponse(BaseModel):
    id: int
    name: str
    target_company: str
    industry: Optional[str] = None
    deal_size: Optional[float] = None
    status: str
    created_at: datetime
    document_count: int
    analysis_count: int

class DealDetailResponse(BaseModel):
    id: int
    name: str
    target_company: str
    industry: Optional[str] = None
    deal_size: Optional[float] = None
    status: str
    created_at: datetime
    documents: List[DocumentResponse]
    analyses: List[AnalysisSummary]

class AnalysisResponse(BaseModel):
    id: int
    analysis_type: str
    status: str
    results: Optional[Any] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[List[Any]] = None
    created_at: datetime

class ReportResponse(BaseModel):
    id: int
    report_type: str
    generated_at: datetime
    download_url: str
