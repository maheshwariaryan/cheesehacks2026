# TAM Hackathon — BACKEND CORE PROMPT (Person 1 of 3)

Copy everything below the line into Claude Code.

**You are building the CORE backend.** Another teammate is building the AI/ML services (Claude, RAG, ML, reports) that plug into your code. A third teammate is building the frontend. You MUST follow the shared models, schemas, and API contract exactly.

---

Build the core backend for **TAM** (Transaction Analysis Machine) — an AI-powered Financial Due Diligence platform. You are responsible for: the FastAPI app skeleton, database, all API routes, document parsing, ALL financial math, the analysis pipeline orchestrator, and seed data.

Your teammate (Backend-AI person) will later add these files into your project:
- `services/claude_service.py` — AI extraction + insights
- `services/rag_service.py` — ChromaDB chatbot
- `services/ml_engine.py` — anomaly detection + document classifier
- `services/report_generator.py` — PDF generation
- `templates/*.html` — PDF report templates

You must leave clean integration points for them (function calls with known signatures).

## Tech Stack

- **Framework:** FastAPI
- **Database:** SQLite via SQLAlchemy (sync `Session`, NOT async)
- **Document parsing:** pdfplumber, python-docx, openpyxl, pandas, Pillow
- **No Docker, no Redis, no Celery, no Postgres**

## How to Run

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Project Structure (your files marked with ✅)

```
backend/
├── main.py                    ✅  # FastAPI app, CORS, startup seed, include all routers
├── config.py                  ✅  # Settings from .env
├── database.py                ✅  # SQLite + SQLAlchemy sync setup
├── models.py                  ✅  # ALL DB models (shared with teammate)
├── schemas.py                 ✅  # ALL Pydantic schemas (shared with teammate)
├── requirements.txt           ✅  # ALL deps (including teammate's)
├── seed.py                    ✅  # Demo data seeder
├── utils.py                   ✅  # safe_div, JSON helpers
├── uploads/                       # Uploaded files stored here
├── chroma_db/                     # ChromaDB storage (teammate creates)
├── reports/                       # Generated PDFs (teammate creates)
├── routers/
│   ├── deals.py               ✅  # Deal CRUD
│   ├── documents.py           ✅  # Upload + parse documents
│   ├── analysis.py            ✅  # Trigger analysis pipeline, get results
│   ├── chat.py                ✅  # RAG chatbot endpoints (calls teammate's rag_service)
│   └── reports.py             ✅  # Report generation endpoints (calls teammate's report_generator)
├── services/
│   ├── document_parser.py     ✅  # Universal file parser (any format)
│   ├── financial_analyzer.py  ✅  # ALL financial math (QoE, NWC, ratios, DCF, red flags)
│   ├── claude_service.py      🔗  # Teammate builds — you define the expected interface
│   ├── rag_service.py         🔗  # Teammate builds — you define the expected interface
│   ├── ml_engine.py           🔗  # Teammate builds — you define the expected interface
│   └── report_generator.py    🔗  # Teammate builds — you define the expected interface
└── templates/                 🔗  # Teammate builds
```

## Database Models (`models.py`) — SHARED, BUILD EXACTLY THIS

```python
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Deal(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    target_company = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    deal_size = Column(Float, nullable=True)
    status = Column(String(50), default="pending")         # pending | analyzing | completed | failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    documents = relationship("Document", back_populates="deal", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="deal", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="deal", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50), nullable=False)         # pdf, xlsx, csv, docx, txt, png, jpg, etc.
    file_size = Column(Integer, default=0)
    extracted_text = Column(Text, nullable=True)
    doc_type = Column(String(100), nullable=True)          # income_statement, balance_sheet, etc.
    doc_type_confidence = Column(Float, nullable=True)
    financial_data = Column(Text, nullable=True)           # JSON string
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    deal = relationship("Deal", back_populates="documents")

class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    analysis_type = Column(String(50), nullable=False)     # qoe | working_capital | ratios | dcf | red_flags | anomalies | ai_insights
    results = Column(Text, nullable=True)                  # JSON string
    status = Column(String(50), default="pending")         # pending | running | completed | failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    deal = relationship("Deal", back_populates="analyses")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    role = Column(String(20), nullable=False)              # user | assistant
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)                  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    deal = relationship("Deal", back_populates="chat_messages")

class GeneratedReport(Base):
    __tablename__ = "generated_reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    report_type = Column(String(50), nullable=False)       # iar | dcf | red_flag
    file_path = Column(String(1000), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
```

## Pydantic Schemas (`schemas.py`) — SHARED, BUILD EXACTLY THIS

```python
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
```

## API Routes — BUILD ALL OF THESE

### `routers/deals.py`
```
POST   /api/deals                              → DealResponse
GET    /api/deals                              → { deals: DealResponse[] }
GET    /api/deals/{id}                         → DealDetailResponse
DELETE /api/deals/{id}                         → { message: "deleted" }
```
- POST: create deal, return with document_count=0, analysis_count=0
- GET list: return all deals sorted by created_at desc, compute document_count and analysis_count from relationships
- GET detail: include full documents list and analyses summary list
- DELETE: cascade delete all related documents, analyses, chat messages. Also delete uploaded files from disk.

### `routers/documents.py`
```
POST   /api/deals/{deal_id}/documents          → { documents: DocumentResponse[] }
       Body: multipart/form-data, field name "files" (multiple files)
GET    /api/deals/{deal_id}/documents          → { documents: DocumentResponse[] }
DELETE /api/documents/{id}                     → { message: "deleted" }
```
- POST: accept multiple files. For each file:
  1. Save to `./uploads/{deal_id}/{filename}` (create dir if needed)
  2. Determine file_type from extension
  3. Create Document row (extracted_text=None for now, parsed later during analysis)
  4. Return list of created documents

### `routers/analysis.py`
```
POST   /api/deals/{deal_id}/analyze            → { status: "analyzing", deal_id: int }
GET    /api/deals/{deal_id}/analysis           → { analyses: AnalysisResponse[] }
GET    /api/deals/{deal_id}/analysis/{type}    → AnalysisResponse
```
- POST: set deal status to "analyzing", kick off `run_analysis_pipeline(deal_id)` via `BackgroundTasks`, return immediately
- GET all: return all analyses for the deal, parse results JSON into dict
- GET by type: return single analysis, parse results JSON

### `routers/chat.py`
```
POST   /api/deals/{deal_id}/chat               → ChatMessageResponse
GET    /api/deals/{deal_id}/chat               → { messages: ChatMessageResponse[] }
DELETE /api/deals/{deal_id}/chat               → { message: "chat history cleared" }
```
- POST: save user message, call teammate's `rag_service.retrieve()` → `claude_service.ask_question()`, save assistant message with sources, return assistant message
- GET: return all messages for the deal sorted by created_at
- DELETE: delete all chat messages for the deal

**Integration point for teammate:** In the POST handler, the code should look like:
```python
# Import teammate's services (they will create these files)
from services.rag_service import RAGService
from services.claude_service import ask_question

rag = RAGService()
# 1. Retrieve relevant chunks
chunks = rag.retrieve(deal_id=deal_id, query=request.message, top_k=5)
# 2. Build deal context from analyses
deal_context = build_deal_context(db, deal_id)  # helper you write: loads all analysis results
deal_context["relevant_chunks"] = chunks
# 3. Ask Claude
answer, sources = ask_question(request.message, deal_context)
```

If the import fails (teammate hasn't built it yet), catch `ImportError` and return a stub response: `"AI services not yet available. Your teammate needs to add claude_service.py and rag_service.py."`

### `routers/reports.py`
```
POST   /api/deals/{deal_id}/reports/{type}     → { report_id: int, status: "generating" }
GET    /api/deals/{deal_id}/reports            → { reports: ReportResponse[] }
GET    /api/reports/{id}/download              → FileResponse (application/pdf)
GET    /api/deals/{deal_id}/reports/{type}/status → { status: "generating" | "completed" | "failed" }
```
- POST: create GeneratedReport row with status logic, kick off report generation in BackgroundTasks
- GET list: return all reports for deal, with download_url = `/api/reports/{id}/download`
- GET download: use `FileResponse` to serve the PDF file
- GET status: check if the report file exists on disk

**Integration point:** Call teammate's `report_generator.generate()`. If import fails, return stub error.

## `main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, SessionLocal
from models import Base
from seed import seed_demo_data

app = FastAPI(title="TAM API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
from routers import deals, documents, analysis, chat, reports
app.include_router(deals.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from models import Deal
        if db.query(Deal).count() == 0:
            seed_demo_data(db)
    finally:
        db.close()

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
```

## `database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## `config.py`

```python
from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tam.db")
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

settings = Settings()
```

## `utils.py`

```python
import json

def safe_div(a, b):
    """Safe division — returns 0.0 if b is zero, None, or falsy."""
    if not b:
        return 0.0
    try:
        return float(a) / float(b)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0

def parse_json_field(text):
    """Parse a JSON text field from SQLite. Returns dict/list or None."""
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
```

## Service: Document Parser (`services/document_parser.py`)

Universal parser. Handle ANY file format. Return extracted text.

```python
import pdfplumber
from docx import Document as DocxDocument
import openpyxl
import pandas as pd
from PIL import Image
import os

def parse_file(file_path: str, file_type: str) -> str:
    """Route by file_type to the right extractor. Always returns a string."""
    parsers = {
        "pdf": parse_pdf,
        "xlsx": parse_excel, "xls": parse_excel,
        "csv": parse_csv,
        "docx": parse_docx, "doc": parse_docx,
        "txt": parse_text,
        "png": parse_image, "jpg": parse_image, "jpeg": parse_image,
    }
    parser = parsers.get(file_type.lower(), parse_text)
    try:
        return parser(file_path)
    except Exception as e:
        return f"[Error parsing {file_type} file: {str(e)}]"

def parse_pdf(file_path: str) -> str:
    """
    Use pdfplumber. For each page:
    1. Extract text with layout preservation
    2. Extract tables → convert each to a pipe-delimited table string
    Separate pages with "--- PAGE {n} ---"
    """
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            tables = page.extract_tables()
            table_text = ""
            for table in tables:
                rows = []
                for row in table:
                    rows.append(" | ".join(str(cell or "") for cell in row))
                table_text += "\n[TABLE]\n" + "\n".join(rows) + "\n[/TABLE]\n"
            pages.append(f"--- PAGE {i+1} ---\n{text}\n{table_text}")
    return "\n\n".join(pages)

def parse_excel(file_path: str) -> str:
    """
    Use openpyxl. For each sheet:
    1. Read all rows into a list of lists
    2. Detect type by keywords in first 5 rows
    3. Format as: "=== SHEET: {name} (Detected: {type}) ===\n" + rows as pipe-delimited
    """
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheets_text = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = []
        for row in ws.iter_rows(values_only=True):
            rows.append(" | ".join(str(cell if cell is not None else "") for cell in row))
        text = "\n".join(rows)
        # Detect sheet type
        sample = text[:500].lower()
        if any(kw in sample for kw in ["revenue", "sales", "net income", "gross profit"]):
            detected = "Income Statement"
        elif any(kw in sample for kw in ["assets", "liabilities", "equity"]):
            detected = "Balance Sheet"
        elif any(kw in sample for kw in ["cash flow", "operating", "investing"]):
            detected = "Cash Flow Statement"
        else:
            detected = "Financial Data"
        sheets_text.append(f"=== SHEET: {sheet_name} (Detected: {detected}) ===\n{text}")
    return "\n\n".join(sheets_text)

def parse_csv(file_path: str) -> str:
    """Read CSV with pandas, convert to pipe-delimited string."""
    df = pd.read_csv(file_path)
    header = " | ".join(str(c) for c in df.columns)
    rows = [" | ".join(str(v) for v in row) for _, row in df.iterrows()]
    return header + "\n" + "\n".join(rows)

def parse_docx(file_path: str) -> str:
    """Extract paragraphs and tables from Word documents."""
    doc = DocxDocument(file_path)
    parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)
    for table in doc.tables:
        rows = []
        for row in table.rows:
            rows.append(" | ".join(cell.text for cell in row.cells))
        parts.append("[TABLE]\n" + "\n".join(rows) + "\n[/TABLE]")
    return "\n\n".join(parts)

def parse_text(file_path: str) -> str:
    """Read as plain text, try UTF-8 then latin-1."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()

def parse_image(file_path: str) -> str:
    """Return placeholder — images handled by Claude vision during extraction."""
    img = Image.open(file_path)
    return f"[IMAGE: {os.path.basename(file_path)} — {img.width}x{img.height}px. Send to Claude Vision for extraction.]"
```

## Service: Financial Analyzer (`services/financial_analyzer.py`)

This is the math engine. ALL financial calculations live here. Every function uses real formulas.

```python
from utils import safe_div

# ============================================================
# 1. QUALITY OF EARNINGS
# ============================================================
def analyze_qoe(financial_data: dict) -> dict:
    inc = financial_data.get("income_statement", {})
    adjustments = list(financial_data.get("adjustments", []))  # copy to avoid mutation

    revenue = inc.get("revenue", 0)
    net_income = inc.get("net_income", 0)
    interest = inc.get("interest", 0)
    tax = inc.get("tax", 0)
    depreciation = inc.get("depreciation", 0)

    # Reported EBITDA = Net Income + Interest + Tax + Depreciation
    reported_ebitda = net_income + interest + tax + depreciation

    # Sum adjustments (positive = add-back, negative = deduction)
    total_adj = sum(a.get("amount", 0) for a in adjustments)
    adjusted_ebitda = reported_ebitda + total_adj

    # Tag each adjustment's direction
    for adj in adjustments:
        adj["impact"] = "add_back" if adj.get("amount", 0) > 0 else "deduction"

    # Quality Score (0-100)
    magnitude = safe_div(abs(total_adj), max(abs(reported_ebitda), 1))
    score = 80
    if magnitude > 0.25: score -= 30
    elif magnitude > 0.10: score -= 15
    elif magnitude > 0.05: score -= 5
    for adj in adjustments:
        cat = adj.get("category", "")
        if cat == "non_recurring": score -= 10
        elif cat == "related_party": score -= 8
        elif cat == "owner_compensation": score -= 5
    op_exp = inc.get("operating_expenses", 0)
    if revenue > 0 and revenue < op_exp: score -= 15
    score = max(0, min(100, score))

    sustainability = "high" if score >= 70 else ("medium" if score >= 40 else "low")

    return {
        "reported_ebitda": round(reported_ebitda, 2),
        "adjusted_ebitda": round(adjusted_ebitda, 2),
        "total_adjustments": round(total_adj, 2),
        "adjustments": adjustments,
        "quality_score": score,
        "earnings_sustainability": sustainability,
        "ebitda_margin": round(safe_div(reported_ebitda, revenue) * 100, 1),
        "adjusted_ebitda_margin": round(safe_div(adjusted_ebitda, revenue) * 100, 1),
    }

# ============================================================
# 2. WORKING CAPITAL ANALYSIS
# ============================================================
def analyze_working_capital(financial_data: dict) -> dict:
    bs = financial_data.get("balance_sheet", {})
    inc = financial_data.get("income_statement", {})

    ar = bs.get("accounts_receivable", 0)
    inventory = bs.get("inventory", 0)
    current_assets = bs.get("total_current_assets", 0)
    ap = bs.get("accounts_payable", 0)
    current_liab = bs.get("total_current_liabilities", 0)
    revenue = inc.get("revenue", 0)
    cogs = inc.get("cogs", 0)

    nwc = current_assets - current_liab
    dso = safe_div(ar, revenue) * 365           # Days Sales Outstanding
    dio = safe_div(inventory, cogs) * 365       # Days Inventory Outstanding
    dpo = safe_div(ap, cogs) * 365              # Days Payable Outstanding
    ccc = dso + dio - dpo                        # Cash Conversion Cycle
    nwc_pct = safe_div(nwc, revenue) * 100
    current_ratio = safe_div(current_assets, current_liab)

    if ccc < 30: assessment = "Excellent cash conversion — business collects fast and pays strategically."
    elif ccc < 60: assessment = "Healthy working capital cycle within normal operating range."
    elif ccc < 90: assessment = "Moderate efficiency — cash tied up for a notable period. Investigate AR aging."
    else: assessment = "Poor cash conversion — significant capital locked in working capital. Immediate attention needed."

    return {
        "current_assets": round(current_assets, 2),
        "current_liabilities": round(current_liab, 2),
        "net_working_capital": round(nwc, 2),
        "current_ratio": round(current_ratio, 2),
        "dso": round(dso, 1), "dio": round(dio, 1), "dpo": round(dpo, 1),
        "cash_conversion_cycle": round(ccc, 1),
        "nwc_as_pct_revenue": round(nwc_pct, 1),
        "assessment": assessment,
    }

# ============================================================
# 3. FINANCIAL RATIOS (18 ratios + health score)
# ============================================================
def calculate_ratios(financial_data: dict) -> dict:
    inc = financial_data.get("income_statement", {})
    bs = financial_data.get("balance_sheet", {})
    cf = financial_data.get("cash_flow", {})

    revenue = inc.get("revenue", 0)
    cogs = inc.get("cogs", 0)
    gross_profit = inc.get("gross_profit", 0) or (revenue - cogs)
    ebitda = inc.get("ebitda", 0)
    net_income = inc.get("net_income", 0)
    interest = inc.get("interest", 0)

    current_assets = bs.get("total_current_assets", 0)
    inventory = bs.get("inventory", 0)
    cash = bs.get("cash", 0)
    current_liab = bs.get("total_current_liabilities", 0)
    total_assets = bs.get("total_assets", 0)
    total_equity = bs.get("total_equity", 0)
    total_liab = bs.get("total_liabilities", 0)
    ar = bs.get("accounts_receivable", 0)
    long_term_debt = bs.get("long_term_debt", 0)
    short_term_debt = bs.get("short_term_debt", 0)
    total_debt = long_term_debt + short_term_debt
    ocf = cf.get("operating_cf", 0)
    fcf = cf.get("fcf", 0)

    ratios = {
        "liquidity": {
            "current_ratio": round(safe_div(current_assets, current_liab), 2),
            "quick_ratio": round(safe_div(current_assets - inventory, current_liab), 2),
            "cash_ratio": round(safe_div(cash, current_liab), 2),
        },
        "profitability": {
            "gross_margin": round(safe_div(gross_profit, revenue) * 100, 1),
            "ebitda_margin": round(safe_div(ebitda, revenue) * 100, 1),
            "operating_margin": round(safe_div(ebitda, revenue) * 100, 1),
            "net_margin": round(safe_div(net_income, revenue) * 100, 1),
            "roe": round(safe_div(net_income, total_equity) * 100, 1),
            "roa": round(safe_div(net_income, total_assets) * 100, 1),
        },
        "leverage": {
            "debt_to_equity": round(safe_div(total_liab, total_equity), 2),
            "debt_to_assets": round(safe_div(total_liab, total_assets), 2),
            "interest_coverage": round(safe_div(ebitda, interest), 2),
            "debt_to_ebitda": round(safe_div(total_debt, ebitda), 2),
        },
        "efficiency": {
            "asset_turnover": round(safe_div(revenue, total_assets), 2),
            "inventory_turnover": round(safe_div(cogs, inventory), 2),
            "receivables_turnover": round(safe_div(revenue, ar), 2),
        },
        "cash_flow": {
            "ocf_to_net_income": round(safe_div(ocf, net_income), 2),
            "fcf_margin": round(safe_div(fcf, revenue) * 100, 1),
        },
    }

    # Health score (0-100) — weighted composite
    liq = min(100, max(0, ratios["liquidity"]["current_ratio"] / 2.0 * 100))
    prof = min(100, max(0, ratios["profitability"]["net_margin"] / 20.0 * 100))
    lev = max(0, min(100, (4.0 - ratios["leverage"]["debt_to_equity"]) / 3.0 * 100))
    eff = min(100, ratios["efficiency"]["asset_turnover"] / 1.0 * 100)
    cf_s = min(100, max(0, ratios["cash_flow"]["ocf_to_net_income"] / 1.5 * 100))
    health = int(liq * 0.20 + prof * 0.25 + lev * 0.20 + eff * 0.15 + cf_s * 0.20)
    health = max(0, min(100, health))

    rating = "Excellent" if health >= 80 else "Good" if health >= 65 else "Fair" if health >= 45 else "Concerning" if health >= 25 else "Critical"
    ratios["overall_health_score"] = health
    ratios["health_rating"] = rating
    return ratios

# ============================================================
# 4. DCF VALUATION
# ============================================================
def calculate_dcf(financial_data: dict, assumptions: dict = None) -> dict:
    defaults = {
        "projection_years": 5,
        "revenue_growth_rate": 0.10,
        "growth_decline_per_year": 0.01,
        "capex_pct_revenue": 0.05,
        "tax_rate": 0.25,
        "wacc": 0.12,
        "terminal_growth_rate": 0.03,
    }
    a = {**defaults, **(assumptions or {})}

    inc = financial_data.get("income_statement", {})
    bs = financial_data.get("balance_sheet", {})

    base_revenue = inc.get("revenue", 0)
    ebitda = inc.get("ebitda", 0)
    current_ebitda_margin = safe_div(ebitda, base_revenue)
    cash_val = bs.get("cash", 0)
    total_debt = bs.get("long_term_debt", 0) + bs.get("short_term_debt", 0)

    projected_years = []
    revenue = base_revenue
    for year in range(1, a["projection_years"] + 1):
        growth = max(0.02, a["revenue_growth_rate"] - (year - 1) * a["growth_decline_per_year"])
        revenue = revenue * (1 + growth)
        year_ebitda = revenue * current_ebitda_margin
        tax = year_ebitda * a["tax_rate"]
        capex = revenue * a["capex_pct_revenue"]
        fcf = year_ebitda - tax - capex
        df = 1 / ((1 + a["wacc"]) ** year)
        projected_years.append({
            "year": year,
            "revenue": round(revenue, 0),
            "ebitda": round(year_ebitda, 0),
            "fcf": round(fcf, 0),
            "discount_factor": round(df, 4),
            "pv_fcf": round(fcf * df, 0),
            "growth_rate": round(growth * 100, 1),
        })

    final_fcf = projected_years[-1]["fcf"]
    terminal_value = final_fcf * (1 + a["terminal_growth_rate"]) / (a["wacc"] - a["terminal_growth_rate"])
    terminal_discount = 1 / ((1 + a["wacc"]) ** a["projection_years"])
    pv_terminal = terminal_value * terminal_discount

    sum_pv_fcf = sum(y["pv_fcf"] for y in projected_years)
    enterprise_value = sum_pv_fcf + pv_terminal
    equity_value = enterprise_value + cash_val - total_debt

    return {
        "assumptions": a,
        "projected_years": projected_years,
        "terminal_value": round(terminal_value, 0),
        "pv_terminal_value": round(pv_terminal, 0),
        "sum_pv_fcf": round(sum_pv_fcf, 0),
        "enterprise_value": round(enterprise_value, 0),
        "equity_value": round(equity_value, 0),
        "ev_to_revenue": round(safe_div(enterprise_value, base_revenue), 2),
        "ev_to_ebitda": round(safe_div(enterprise_value, ebitda), 2),
        "current_ebitda_margin": round(current_ebitda_margin * 100, 1),
    }

# ============================================================
# 5. RED FLAG DETECTION (12 checks)
# ============================================================
def detect_red_flags(financial_data: dict, ratios: dict, working_capital: dict, qoe: dict) -> list:
    flags = []
    inc = financial_data.get("income_statement", {})
    cf = financial_data.get("cash_flow", {})

    def flag(title, severity, desc, metric, value, threshold):
        flags.append({"flag": title, "severity": severity, "description": desc,
                       "metric": metric, "value": round(value, 2), "threshold": threshold})

    # HIGH
    cr = ratios.get("liquidity", {}).get("current_ratio", 99)
    if cr < 1.0:
        flag("Low Liquidity", "high", f"Current ratio of {cr} — liabilities exceed current assets.", "current_ratio", cr, 1.0)

    dte = ratios.get("leverage", {}).get("debt_to_equity", 0)
    if dte > 3.0:
        flag("Excessive Leverage", "high", f"Debt-to-equity of {dte} — heavily debt-financed.", "debt_to_equity", dte, 3.0)

    ic = ratios.get("leverage", {}).get("interest_coverage", 99)
    if 0 < ic < 1.5:
        flag("Cannot Cover Interest", "high", f"Interest coverage of {ic}x — earnings barely cover interest.", "interest_coverage", ic, 1.5)

    ocf = cf.get("operating_cf", 0)
    if ocf < 0:
        flag("Negative Operating Cash Flow", "high", "Core operations are cash-negative.", "operating_cf", ocf, 0)

    qs = qoe.get("quality_score", 100)
    if qs < 30:
        flag("Severe Earnings Quality Issues", "high", f"QoE score {qs}/100 — earnings are unreliable.", "quality_score", qs, 30)

    # MEDIUM
    dso = working_capital.get("dso", 0)
    if dso > 60:
        flag("Slow Collections", "medium", f"DSO of {dso:.0f} days — over 2 months to collect.", "dso", dso, 60)

    ccc = working_capital.get("cash_conversion_cycle", 0)
    if ccc > 90:
        flag("Long Cash Cycle", "medium", f"CCC of {ccc:.0f} days — significant WC drag.", "cash_conversion_cycle", ccc, 90)

    gm = ratios.get("profitability", {}).get("gross_margin", 100)
    if gm < 20:
        flag("Low Gross Margin", "medium", f"Gross margin of {gm}% — thin margins.", "gross_margin", gm, 20)

    nm = ratios.get("profitability", {}).get("net_margin", 0)
    if nm < 0:
        flag("Net Loss", "medium", f"Net margin of {nm}% — company is unprofitable.", "net_margin", nm, 0)

    if inc.get("revenue", 0) > 0 and ocf < 0:
        flag("Earnings Quality Concern", "medium", "Revenue positive but OCF negative — earnings not converting to cash.", "ocf_vs_revenue", ocf, 0)

    d2e = ratios.get("leverage", {}).get("debt_to_ebitda", 0)
    if d2e > 4.0:
        flag("High Debt Load", "medium", f"Debt/EBITDA of {d2e}x — would take {d2e:.1f} years to repay.", "debt_to_ebitda", d2e, 4.0)

    # LOW
    qr = ratios.get("liquidity", {}).get("quick_ratio", 99)
    if qr < 0.5:
        flag("Low Quick Ratio", "low", f"Quick ratio of {qr} — limited liquid assets.", "quick_ratio", qr, 0.5)

    return flags
```

## Analysis Pipeline Orchestrator

Put this in `routers/analysis.py` or a separate `services/pipeline.py`. This is the function that runs in `BackgroundTasks`:

```python
import json
from datetime import datetime
from database import SessionLocal
from models import Deal, Document, Analysis
from services.document_parser import parse_file
from services.financial_analyzer import (
    analyze_qoe, analyze_working_capital, calculate_ratios,
    calculate_dcf, detect_red_flags
)

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
                    data = extract_financial_data(doc.extracted_text, doc.filename)
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

        # --- STEP 8: AI insights (teammate's code) ---
        try:
            from services.claude_service import generate_insights
            insights = generate_insights(merged, ratios, red_flags, anomalies, qoe, dcf)
            save_analysis(db, deal_id, "ai_insights", insights)
        except ImportError:
            save_analysis(db, deal_id, "ai_insights", None)

        deal.status = "completed"
        db.commit()

    except Exception as e:
        deal.status = "failed"
        db.commit()
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
                if value and not merged[section].get(key):
                    merged[section][key] = value

        merged["adjustments"].extend(data.get("adjustments", []))
        merged["notes"].extend(data.get("notes", []))

    return merged
```

## Seed Data (`seed.py`)

```python
import json
from datetime import datetime
from models import Deal, Document, Analysis
from services.financial_analyzer import (
    analyze_qoe, analyze_working_capital, calculate_ratios,
    calculate_dcf, detect_red_flags
)

DEMO_FINANCIAL_DATA = {
    "company_name": "Apex Cloud Solutions",
    "period": "FY 2025",
    "currency": "USD",
    "income_statement": {
        "revenue": 22400000, "cogs": 6720000, "gross_profit": 15680000,
        "operating_expenses": 12320000, "ebitda": 3360000, "depreciation": 890000,
        "interest": 420000, "tax": 512000, "net_income": 1538000
    },
    "balance_sheet": {
        "cash": 3200000, "accounts_receivable": 4800000, "inventory": 280000,
        "total_current_assets": 8680000, "ppe": 2100000, "total_assets": 14200000,
        "accounts_payable": 1950000, "short_term_debt": 1200000,
        "total_current_liabilities": 4350000, "long_term_debt": 3800000,
        "total_liabilities": 8150000, "total_equity": 6050000
    },
    "cash_flow": {
        "operating_cf": 2850000, "investing_cf": -1400000, "financing_cf": -980000,
        "net_cf": 470000, "capex": -1200000, "fcf": 1650000
    },
    "adjustments": [
        {"description": "One-time litigation settlement", "amount": 750000, "category": "non_recurring"},
        {"description": "Former CEO consulting fees (above market)", "amount": 320000, "category": "owner_compensation"},
        {"description": "Related party lease above market rate", "amount": -180000, "category": "related_party"},
        {"description": "COVID-era PPP loan forgiveness", "amount": 200000, "category": "non_recurring"}
    ],
    "notes": [
        "Revenue grew 28% YoY from $17.5M",
        "Top customer represents ~18% of revenue",
        "Company transitioned from perpetual licenses to SaaS in 2023"
    ]
}

DEMO_INSIGHTS = {
    "executive_summary": "Apex Cloud Solutions demonstrates strong revenue growth (28% YoY) with healthy SaaS unit economics. Gross margins of 70% are typical for B2B SaaS. However, elevated DSO of 78 days and significant QoE adjustments ($1.09M, 32% of reported EBITDA) warrant attention. The business is fundamentally sound but requires careful examination of customer concentration and working capital management.",
    "key_findings": [
        {"finding": "EBITDA adjustments total $1.09M (32% of reported EBITDA)", "impact": "high", "recommendation": "Negotiate based on adjusted EBITDA of $4.45M. Verify each adjustment independently."},
        {"finding": "DSO of 78 days indicates slow collections", "impact": "medium", "recommendation": "Request AR aging schedule. Investigate enterprise payment terms vs collection issues."},
        {"finding": "Strong operating cash flow of $2.85M with positive FCF", "impact": "low", "recommendation": "Cash generation is healthy. FCF margin of 7.4% should expand as growth moderates."},
        {"finding": "Debt-to-equity of 1.35 is moderate", "impact": "low", "recommendation": "Leverage is manageable. Interest coverage of 8x provides comfortable headroom."},
        {"finding": "Related party lease arrangement flagged", "impact": "medium", "recommendation": "Obtain independent appraisal of lease terms vs market rates."}
    ],
    "risk_assessment": {
        "overall_risk": "medium",
        "financial_risk": "Moderate — strong growth and margins offset by elevated working capital and QoE adjustments.",
        "operational_risk": "Low to moderate — SaaS transition largely complete, but customer concentration (~18%) should be monitored.",
        "deal_recommendation": "proceed_with_caution"
    },
    "valuation_opinion": "DCF suggests enterprise value of ~$35-40M (EV/Revenue ~1.6-1.8x, EV/EBITDA ~10-12x adjusted). At $45M deal price, the buyer pays a modest premium justified by growth trajectory. Consider earnout structure.",
    "questions_for_management": [
        "Provide the AR aging schedule broken down by customer. What drives the 78-day DSO?",
        "What percentage of revenue is annual vs monthly contracts? What is net revenue retention?",
        "Detail the related party lease — who is the counterparty and what are comparable market rates?",
        "What is customer churn rate and logo retention over the past 3 years?",
        "Are there pending or threatened litigation matters beyond the settled case?",
        "What capex is maintenance vs discretionary?",
        "Walk us through the SaaS transition — what percentage of revenue is now recurring?"
    ]
}

def seed_demo_data(db):
    """Create one demo deal with all analyses pre-computed."""
    deal = Deal(
        name="Apex Cloud Solutions Acquisition",
        target_company="Apex Cloud Solutions",
        industry="SaaS",
        deal_size=45000000,
        status="completed",
    )
    db.add(deal)
    db.flush()  # get the deal.id

    # Add a fake document
    doc = Document(
        deal_id=deal.id,
        filename="apex_financials_fy2025.pdf",
        file_path="seed_data",
        file_type="pdf",
        file_size=2145000,
        extracted_text="[Seed data — financial statements for Apex Cloud Solutions FY2025]",
        doc_type="income_statement",
        doc_type_confidence=0.94,
        financial_data=json.dumps(DEMO_FINANCIAL_DATA),
    )
    db.add(doc)

    # Run all financial calculations on the seed data
    qoe = analyze_qoe(DEMO_FINANCIAL_DATA)
    wc = analyze_working_capital(DEMO_FINANCIAL_DATA)
    ratios = calculate_ratios(DEMO_FINANCIAL_DATA)
    dcf = calculate_dcf(DEMO_FINANCIAL_DATA)
    red_flags = detect_red_flags(DEMO_FINANCIAL_DATA, ratios, wc, qoe)

    analyses = [
        ("qoe", qoe),
        ("working_capital", wc),
        ("ratios", ratios),
        ("dcf", dcf),
        ("red_flags", red_flags),
        ("anomalies", []),  # Empty until teammate's ML engine is added
        ("ai_insights", DEMO_INSIGHTS),
    ]

    for a_type, results in analyses:
        analysis = Analysis(
            deal_id=deal.id,
            analysis_type=a_type,
            results=json.dumps(results),
            status="completed",
            completed_at=datetime.utcnow(),
        )
        db.add(analysis)

    db.commit()
    print(f"Seeded demo deal: '{deal.name}' (id={deal.id}) with {len(analyses)} analyses")
```

## `requirements.txt` (include EVERYTHING — both yours and teammate's deps)

```
fastapi
uvicorn[standard]
sqlalchemy
anthropic
openai
python-multipart
pdfplumber
PyPDF2
python-docx
openpyxl
pandas
Pillow
scikit-learn
numpy
chromadb
weasyprint
jinja2
python-dotenv
```

## `.env.example`

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DATABASE_URL=sqlite:///./tam.db
UPLOAD_DIR=./uploads
```

## Implementation Notes

1. **CORS:** Allow `["http://localhost:3000", "http://localhost:3001"]`
2. **Sync SQLAlchemy only.** `SessionLocal = sessionmaker(bind=engine)`.
3. **JSON in SQLite:** `Text` column + `json.dumps()`/`json.loads()`.
4. **BackgroundTasks:** Pipeline and report generation run in background. Always create OWN `SessionLocal()`.
5. **Graceful teammate integration:** Every call to teammate's services is wrapped in `try: ... except ImportError:`. The app runs and serves seed data even before teammate's code is added.
6. **File uploads:** Save to `./uploads/{deal_id}/{filename}`. Max 50MB.
7. **Seed on startup:** In `main.py` startup event, seed if no deals exist.
8. **No auth** — hackathon demo.

Build everything now. Start with database.py → models.py → schemas.py → utils.py → config.py → services/ → routers/ → seed.py → main.py. Make sure the app starts and serves the seed demo data on first run.
