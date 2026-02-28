# TAM Hackathon — BACKEND AI/ML PROMPT (Person 2 of 3)

Copy everything below the line into Claude Code.

**You are building the AI/ML services.** Your teammate (Backend-Core person) has already built the FastAPI app, database, routes, document parser, all financial math, and seed data. You are adding 4 service files + HTML templates into their existing project. You must match their function signatures exactly so the pipeline calls your code correctly.

---

Build the AI/ML services for **TAM** (Transaction Analysis Machine). You are adding these files into an existing FastAPI backend project:

1. `services/claude_service.py` — Agentic AI extraction + insights + report narratives + Q&A
2. `services/rag_service.py` — Document chunking, embedding, retrieval via ChromaDB
3. `services/ml_engine.py` — Document classifier (keyword heuristic) + anomaly detector (statistical + rule-based)
4. `services/report_generator.py` — PDF report generation (3 types) via Jinja2 + WeasyPrint
5. `templates/*.html` — 3 professional PDF report templates

## Existing Project Context

Your teammate has already built these files (DO NOT recreate or modify them):
- `main.py` — FastAPI app (imports your services via try/except ImportError)
- `database.py` — SQLite + sync SQLAlchemy (`SessionLocal`, `get_db`)
- `models.py` — Deal, Document, Analysis, ChatMessage, GeneratedReport
- `schemas.py` — All Pydantic schemas
- `config.py` — `settings.ANTHROPIC_API_KEY`, `settings.OPENAI_API_KEY`
- `utils.py` — `safe_div(a, b)`, `parse_json_field(text)`
- `routers/*.py` — All API routes (they call YOUR functions)
- `services/document_parser.py` — Parses files → extracted text
- `services/financial_analyzer.py` — All math (QoE, NWC, ratios, DCF, red flags)
- `seed.py` — Demo data

**Your teammate's pipeline calls your code like this** (in `run_analysis_pipeline`):

```python
# Step 2: ML classification
from services.ml_engine import DocumentClassifier
classifier = DocumentClassifier()
doc_type, confidence = classifier.classify(text, filename)

# Step 3: AI extraction
from services.claude_service import extract_financial_data
data = extract_financial_data(document_text, filename)

# Step 5: RAG ingestion
from services.rag_service import RAGService
rag = RAGService()
rag.ingest_document(deal_id, doc_id, text, filename)

# Step 7: ML anomaly detection
from services.ml_engine import AnomalyDetector
detector = AnomalyDetector()
anomalies = detector.detect(financial_data, ratios)

# Step 8: AI insights
from services.claude_service import generate_insights
insights = generate_insights(merged_data, ratios, red_flags, anomalies, qoe, dcf)
```

**The chat router calls your code like this:**
```python
from services.rag_service import RAGService
from services.claude_service import ask_question

rag = RAGService()
chunks = rag.retrieve(deal_id=deal_id, query=message, top_k=5)
answer, sources = ask_question(question, deal_context)
```

**The reports router calls your code like this:**
```python
from services.claude_service import generate_report_content
from services.report_generator import ReportGenerator

narrative = generate_report_content(report_type, deal_data)
generator = ReportGenerator()
filepath = generator.generate(report_type, deal_dict, analyses_dict, narrative)
```

You MUST match these function signatures exactly.

## Tech Stack (your part)

- **AI:** Anthropic Claude (`claude-sonnet-4-20250514`) — sync `anthropic.Anthropic()` client
- **Embeddings:** OpenAI `text-embedding-3-small` — sync `openai.OpenAI()` client
- **Vector DB:** ChromaDB (local persistent, stored in `./chroma_db/`)
- **ML:** scikit-learn (IsolationForest, StandardScaler, numpy)
- **PDF:** WeasyPrint (HTML → PDF), Jinja2 (templates)

## File 1: `services/claude_service.py`

```python
import anthropic
import json
from config import settings

client = None  # Lazy init — only create when API key exists

def _get_client():
    global client
    if client is None:
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set")
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return client

MODEL = "claude-sonnet-4-20250514"

def _parse_json_response(text: str) -> dict | None:
    """Try to parse JSON from Claude's response. Handle markdown code blocks."""
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting from ```json ... ``` blocks
    import re
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Try finding first { ... } block
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return None


def extract_financial_data(document_text: str, filename: str = "") -> dict | None:
    """
    AGENTIC EXTRACTION — multi-step approach.

    Step 1: Initial extraction with detailed system prompt.

    System prompt:
    "You are a financial data extraction engine specialized in M&A due diligence.
    Extract ALL financial figures from the document into structured JSON.

    Rules:
    - Extract exact numbers. If shown in thousands (000s), multiply to full values.
    - If a field is not found in the document, use 0.
    - Identify non-recurring, unusual, or one-time items as adjustments.
    - Categorize adjustments as: non_recurring, related_party, accounting_policy,
      owner_compensation, discretionary, or normalization.
    - Flag data quality issues in the notes array.
    - Return ONLY valid JSON, no other text."

    User message: "Document: {filename}\n\n{document_text}"

    Target JSON shape:
    {
        "company_name": str,
        "period": str,
        "currency": "USD",
        "income_statement": {
            "revenue": float, "cogs": float, "gross_profit": float,
            "operating_expenses": float, "ebitda": float, "depreciation": float,
            "interest": float, "tax": float, "net_income": float
        },
        "balance_sheet": {
            "cash": float, "accounts_receivable": float, "inventory": float,
            "total_current_assets": float, "ppe": float, "total_assets": float,
            "accounts_payable": float, "short_term_debt": float,
            "total_current_liabilities": float, "long_term_debt": float,
            "total_liabilities": float, "total_equity": float
        },
        "cash_flow": {
            "operating_cf": float, "investing_cf": float, "financing_cf": float,
            "net_cf": float, "capex": float, "fcf": float
        },
        "adjustments": [{"description": str, "amount": float, "category": str}],
        "notes": [str]
    }

    Step 2 (agentic refinement): Check how many fields are 0 in the response.
    If more than 60% of income_statement + balance_sheet fields are 0, make a
    SECOND call:
    "The initial extraction found limited data. The document may use different
    terminology. Please re-examine more carefully, looking for: [list zero fields].
    Common alternate labels: 'Net sales' = revenue, 'Cost of revenue' = cogs,
    'Total stockholders equity' = total_equity, 'Property and equipment' = ppe.
    Return the complete JSON again."

    Merge Step 2 results into Step 1 (take non-zero values from Step 2).
    Return the merged result.
    """
    c = _get_client()

    target_shape = '''Return ONLY this JSON structure (use 0 for missing fields):
{
    "company_name": "",
    "period": "",
    "currency": "USD",
    "income_statement": {
        "revenue": 0, "cogs": 0, "gross_profit": 0,
        "operating_expenses": 0, "ebitda": 0, "depreciation": 0,
        "interest": 0, "tax": 0, "net_income": 0
    },
    "balance_sheet": {
        "cash": 0, "accounts_receivable": 0, "inventory": 0,
        "total_current_assets": 0, "ppe": 0, "total_assets": 0,
        "accounts_payable": 0, "short_term_debt": 0,
        "total_current_liabilities": 0, "long_term_debt": 0,
        "total_liabilities": 0, "total_equity": 0
    },
    "cash_flow": {
        "operating_cf": 0, "investing_cf": 0, "financing_cf": 0,
        "net_cf": 0, "capex": 0, "fcf": 0
    },
    "adjustments": [],
    "notes": []
}'''

    system_prompt = (
        "You are a financial data extraction engine specialized in M&A due diligence. "
        "Extract ALL financial figures from the document into structured JSON.\n\n"
        "Rules:\n"
        "- Extract exact numbers. If shown in thousands, multiply to full values.\n"
        "- If a field is not found, use 0.\n"
        "- Identify non-recurring/unusual items as adjustments.\n"
        "- Categorize adjustments as: non_recurring, related_party, accounting_policy, "
        "owner_compensation, discretionary, or normalization.\n"
        "- Return ONLY valid JSON.\n\n" + target_shape
    )

    # Step 1: Initial extraction
    response = c.messages.create(
        model=MODEL, max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Document: {filename}\n\n{document_text[:15000]}"}]
    )
    result = _parse_json_response(response.content[0].text)
    if not result:
        return None

    # Step 2: Agentic refinement — check how many fields are zero
    zero_fields = []
    for section in ["income_statement", "balance_sheet"]:
        for key, val in result.get(section, {}).items():
            if val == 0:
                zero_fields.append(f"{section}.{key}")

    total_fields = len(result.get("income_statement", {})) + len(result.get("balance_sheet", {}))
    if total_fields > 0 and len(zero_fields) / total_fields > 0.6:
        # Too many zeros — retry with guidance
        retry_prompt = (
            f"The initial extraction found limited data ({len(zero_fields)} of {total_fields} fields are 0). "
            f"Please re-examine the document more carefully.\n\n"
            f"Missing fields: {', '.join(zero_fields[:10])}\n\n"
            "Common alternate labels:\n"
            "- 'Net sales' or 'Total revenue' = revenue\n"
            "- 'Cost of revenue' or 'Cost of sales' = cogs\n"
            "- 'Total stockholders equity' = total_equity\n"
            "- 'Property and equipment, net' = ppe\n"
            "- 'Accounts receivable, net' = accounts_receivable\n\n"
            "Return the complete JSON again with as many values filled as possible."
        )
        retry_response = c.messages.create(
            model=MODEL, max_tokens=4096,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"Document: {filename}\n\n{document_text[:15000]}"},
                {"role": "assistant", "content": response.content[0].text},
                {"role": "user", "content": retry_prompt}
            ]
        )
        retry_result = _parse_json_response(retry_response.content[0].text)
        if retry_result:
            # Merge: take non-zero values from retry
            for section in ["income_statement", "balance_sheet", "cash_flow"]:
                for key, val in retry_result.get(section, {}).items():
                    if val and val != 0:
                        result.setdefault(section, {})[key] = val
            if retry_result.get("adjustments"):
                result["adjustments"] = retry_result["adjustments"]

    return result


def generate_insights(financial_data: dict, ratios: dict, red_flags: list,
                      anomalies: list, qoe: dict, dcf: dict) -> dict | None:
    """
    System prompt: "You are a senior M&A due diligence advisor. Given the complete
    financial analysis below, provide your expert assessment. Return ONLY valid JSON."

    User message: JSON dump of all analysis results.

    Target response:
    {
        "executive_summary": "3-5 sentence assessment",
        "key_findings": [{"finding": str, "impact": "high|medium|low", "recommendation": str}],
        "risk_assessment": {
            "overall_risk": "low|medium|high",
            "financial_risk": "one sentence",
            "operational_risk": "one sentence",
            "deal_recommendation": "proceed|proceed_with_caution|significant_concerns"
        },
        "valuation_opinion": "1-2 sentences on DCF and deal price",
        "questions_for_management": ["5-8 questions"]
    }
    """
    c = _get_client()

    context = json.dumps({
        "financial_data": financial_data,
        "ratios": ratios,
        "red_flags": red_flags,
        "anomalies": anomalies,
        "quality_of_earnings": qoe,
        "dcf_valuation": dcf,
    }, indent=2, default=str)

    response = c.messages.create(
        model=MODEL, max_tokens=4096,
        system=(
            "You are a senior M&A due diligence advisor at a top PE firm. "
            "Given the complete financial analysis, provide expert assessment. "
            "Return ONLY valid JSON with keys: executive_summary, key_findings, "
            "risk_assessment, valuation_opinion, questions_for_management."
        ),
        messages=[{"role": "user", "content": f"Full analysis:\n{context}"}]
    )
    return _parse_json_response(response.content[0].text)


def ask_question(question: str, deal_context: dict) -> tuple[str, list]:
    """
    RAG-powered Q&A. Called by chat router.

    deal_context contains:
    - financial_data, ratios, red_flags, qoe, working_capital, dcf, ai_insights
    - relevant_chunks: list of {chunk_text, filename, relevance_score} from RAG

    System prompt: "You are an FDD analyst assistant reviewing a deal. Answer using
    the financial data and document excerpts. Be specific with numbers. Cite which
    document facts come from."

    Returns: (answer_text, sources_list)
    """
    c = _get_client()

    chunks = deal_context.pop("relevant_chunks", [])
    chunk_text = "\n\n".join(
        f"[From {ch.get('filename', 'unknown')}]: {ch.get('chunk_text', '')}"
        for ch in chunks
    )

    context_str = json.dumps(deal_context, indent=2, default=str)[:8000]

    response = c.messages.create(
        model=MODEL, max_tokens=2048,
        system=(
            "You are an FDD analyst assistant. Answer using the financial analysis "
            "data and document excerpts below. Be specific with numbers. "
            "Cite documents when possible."
        ),
        messages=[{
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"--- Document Excerpts ---\n{chunk_text}\n\n"
                f"--- Analysis Data ---\n{context_str}"
            )
        }]
    )

    answer = response.content[0].text
    sources = [{"chunk_text": ch.get("chunk_text", "")[:200],
                "filename": ch.get("filename", ""),
                "relevance_score": ch.get("relevance_score", 0)}
               for ch in chunks]

    return answer, sources


def generate_report_content(report_type: str, deal_data: dict) -> dict | None:
    """
    Generate narrative sections for PDF reports.

    For "iar" (Independent Accountants' Report):
    Return: {scope, procedures_performed, findings, conclusion, limitations}

    For "dcf" (DCF Valuation Report):
    Return: {methodology_description, key_assumptions_narrative,
             sensitivity_discussion, conclusion}

    For "red_flag" (Red Flag Report):
    Return: {executive_summary, detailed_findings (expanded for each flag),
             risk_mitigation_recommendations, overall_assessment}
    """
    c = _get_client()

    prompts = {
        "iar": (
            "Generate the narrative sections of an Independent Accountants' Report "
            "for a financial due diligence engagement. Use formal, professional language. "
            "Return JSON with: scope, procedures_performed, findings, conclusion, limitations."
        ),
        "dcf": (
            "Generate narrative for a DCF Valuation Report. "
            "Return JSON with: methodology_description, key_assumptions_narrative, "
            "sensitivity_discussion, conclusion."
        ),
        "red_flag": (
            "Generate narrative for a Red Flag Assessment Report. "
            "Return JSON with: executive_summary, detailed_findings (expand each red flag), "
            "risk_mitigation_recommendations, overall_assessment."
        ),
    }

    context = json.dumps(deal_data, indent=2, default=str)[:10000]

    response = c.messages.create(
        model=MODEL, max_tokens=4096,
        system=prompts.get(report_type, prompts["iar"]),
        messages=[{"role": "user", "content": f"Deal data:\n{context}"}]
    )
    return _parse_json_response(response.content[0].text)
```

## File 2: `services/rag_service.py`

```python
import chromadb
import openai
import hashlib
import re
from typing import List
from config import settings

# Initialize clients
chroma_client = chromadb.PersistentClient(path="./chroma_db")
openai_client = None

def _get_openai():
    global openai_client
    if openai_client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")
        openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    return openai_client

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 3000       # characters (~750 tokens)
CHUNK_OVERLAP = 300     # characters

class RAGService:

    def ingest_document(self, deal_id: int, document_id: int,
                        text: str, filename: str) -> int:
        """
        1. Chunk the text (financial-aware splitting)
        2. Embed each chunk via OpenAI
        3. Store in ChromaDB collection "deal_{deal_id}"
        Returns number of chunks ingested.
        """
        chunks = self._chunk_text(text)
        if not chunks:
            return 0

        collection = chroma_client.get_or_create_collection(
            name=f"deal_{deal_id}",
            metadata={"hnsw:space": "cosine"}
        )

        # Generate embeddings
        embeddings = self._get_embeddings([c for c in chunks])

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(f"{document_id}_{i}_{chunk[:50]}".encode()).hexdigest()
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "document_id": document_id,
                "filename": filename,
                "chunk_index": i,
            })

        # Upsert into ChromaDB
        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return len(chunks)

    def retrieve(self, deal_id: int, query: str, top_k: int = 5) -> list:
        """
        1. Embed the query
        2. Search ChromaDB for top_k nearest chunks
        3. Return [{chunk_text, filename, relevance_score, chunk_index}]
        """
        try:
            collection = chroma_client.get_collection(f"deal_{deal_id}")
        except Exception:
            return []

        query_embedding = self._get_embeddings([query])[0]

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        chunks = []
        if results and results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 1.0
                # ChromaDB cosine distance: 0 = identical, 2 = opposite
                # Convert to relevance: 1 - (distance / 2)
                relevance = round(1 - (distance / 2), 3)
                chunks.append({
                    "chunk_text": doc,
                    "filename": meta.get("filename", "unknown"),
                    "relevance_score": relevance,
                    "chunk_index": meta.get("chunk_index", 0),
                })

        return chunks

    def delete_deal_collection(self, deal_id: int):
        """Delete the ChromaDB collection for a deal."""
        try:
            chroma_client.delete_collection(f"deal_{deal_id}")
        except Exception:
            pass

    def _chunk_text(self, text: str) -> list:
        """
        Financial-aware chunking:
        1. Split on section headers (lines that look like headers)
        2. For large sections, split on paragraph breaks
        3. For still-large chunks, split on sentences
        4. Apply overlap between adjacent chunks
        """
        if not text or len(text.strip()) == 0:
            return []

        # Step 1: Split on section headers
        header_pattern = r'\n(?=(?:---\s*PAGE|\=\=\=\s*SHEET|[A-Z][A-Z\s]{5,}:?\s*$|#{1,3}\s+))'
        sections = re.split(header_pattern, text)

        # Step 2: Split large sections into chunks
        chunks = []
        for section in sections:
            if len(section) <= CHUNK_SIZE:
                if section.strip():
                    chunks.append(section.strip())
            else:
                # Split on paragraph breaks
                paragraphs = section.split("\n\n")
                current_chunk = ""
                for para in paragraphs:
                    if len(current_chunk) + len(para) <= CHUNK_SIZE:
                        current_chunk += "\n\n" + para if current_chunk else para
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = para
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

        # Step 3: Add overlap
        overlapped = []
        for i, chunk in enumerate(chunks):
            if i > 0 and len(chunks[i-1]) > CHUNK_OVERLAP:
                overlap = chunks[i-1][-CHUNK_OVERLAP:]
                chunk = overlap + "\n" + chunk
            overlapped.append(chunk)

        return overlapped

    def _get_embeddings(self, texts: list) -> list:
        """Batch embed using OpenAI text-embedding-3-small."""
        client = _get_openai()
        # Clean empty strings
        texts = [t if t.strip() else "empty" for t in texts]

        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )
        return [item.embedding for item in response.data]
```

## File 3: `services/ml_engine.py`

```python
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

def safe_div(a, b):
    if not b:
        return 0.0
    try:
        return float(a) / float(b)
    except:
        return 0.0

# ============================================================
# DOCUMENT CLASSIFIER (keyword heuristic — no training needed)
# ============================================================
class DocumentClassifier:

    KEYWORD_MAP = {
        "income_statement": ["revenue", "sales", "cost of goods", "gross profit",
                             "operating income", "net income", "ebitda", "expenses",
                             "cost of revenue", "operating expenses"],
        "balance_sheet": ["assets", "liabilities", "equity", "current assets",
                          "accounts receivable", "accounts payable", "retained earnings",
                          "stockholders equity", "total assets"],
        "cash_flow_statement": ["cash flow", "operating activities", "investing activities",
                                 "financing activities", "net cash", "capital expenditure",
                                 "cash provided", "cash used"],
        "audit_report": ["audit", "auditor", "opinion", "material misstatement",
                         "reasonable assurance", "going concern", "independent auditor"],
        "tax_return": ["taxable income", "tax liability", "deduction", "form 1120",
                       "schedule", "irs", "tax return"],
        "bank_statement": ["beginning balance", "ending balance", "deposits",
                           "withdrawals", "transaction", "bank statement"],
        "accounts_receivable_aging": ["aging", "0-30 days", "31-60", "61-90",
                                      "90+", "receivable", "outstanding", "past due"],
        "accounts_payable_aging": ["payable aging", "vendor", "due date",
                                    "invoice", "payable", "supplier"],
        "debt_schedule": ["principal", "interest rate", "maturity", "loan",
                          "credit facility", "amortization", "debt schedule"],
        "management_report": ["management discussion", "md&a", "outlook",
                               "key performance", "kpi", "business review"],
    }

    def classify(self, text: str, filename: str = "") -> tuple:
        """
        Returns (doc_type, confidence) where confidence is 0.0-1.0.
        Uses keyword frequency scoring + filename bonus.
        """
        text_lower = text.lower()[:5000]  # Only scan first 5000 chars
        filename_lower = filename.lower()
        scores = {}

        for doc_type, keywords in self.KEYWORD_MAP.items():
            # Count keyword matches in text
            score = sum(2 for kw in keywords if kw in text_lower)
            # Filename bonus
            type_words = doc_type.replace("_", " ").split()
            if any(w in filename_lower for w in type_words):
                score += 8
            # Specific filename patterns
            if doc_type == "income_statement" and any(p in filename_lower for p in ["income", "p&l", "pnl", "profit"]):
                score += 5
            if doc_type == "balance_sheet" and "balance" in filename_lower:
                score += 5
            if doc_type == "cash_flow_statement" and "cash" in filename_lower:
                score += 5
            scores[doc_type] = score

        if not scores or max(scores.values()) == 0:
            return "other", 0.3

        best_type = max(scores, key=scores.get)
        total = sum(scores.values())
        confidence = min(0.95, round(safe_div(scores[best_type], total) + 0.1, 2))
        return best_type, confidence


# ============================================================
# ANOMALY DETECTOR (statistical + rule-based)
# ============================================================
class AnomalyDetector:

    # Industry benchmark ranges (approximate mid-market)
    BENCHMARKS = {
        "gross_margin": (20, 80),
        "net_margin": (-5, 25),
        "current_ratio": (0.8, 3.0),
        "debt_to_equity": (0.2, 3.5),
        "asset_turnover": (0.3, 2.5),
        "ocf_to_net_income": (0.5, 2.5),
        "interest_coverage": (1.5, 30),
        "ebitda_margin": (5, 40),
    }

    def detect(self, financial_data: dict, ratios: dict) -> list:
        """
        Three-layer anomaly detection:
        1. Statistical (Z-score against benchmarks)
        2. Isolation Forest (multivariate)
        3. Rule-based domain checks

        Returns list of anomaly dicts.
        """
        anomalies = []
        inc = financial_data.get("income_statement", {})
        bs = financial_data.get("balance_sheet", {})
        cf = financial_data.get("cash_flow", {})

        # Collect feature values
        features = {
            "gross_margin": ratios.get("profitability", {}).get("gross_margin", 0),
            "net_margin": ratios.get("profitability", {}).get("net_margin", 0),
            "ebitda_margin": ratios.get("profitability", {}).get("ebitda_margin", 0),
            "current_ratio": ratios.get("liquidity", {}).get("current_ratio", 0),
            "debt_to_equity": ratios.get("leverage", {}).get("debt_to_equity", 0),
            "asset_turnover": ratios.get("efficiency", {}).get("asset_turnover", 0),
            "ocf_to_net_income": ratios.get("cash_flow", {}).get("ocf_to_net_income", 0),
            "interest_coverage": ratios.get("leverage", {}).get("interest_coverage", 0),
        }

        # --- LAYER 1: Z-score / range analysis ---
        for metric, (low, high) in self.BENCHMARKS.items():
            value = features.get(metric, 0)
            midpoint = (low + high) / 2
            spread = (high - low) / 2
            if spread <= 0:
                continue

            z_score = abs(value - midpoint) / spread

            if value < low or value > high:
                severity = "critical" if z_score > 3 else "high" if z_score > 2 else "medium"
                direction = "below" if value < low else "above"
                anomalies.append({
                    "anomaly": f"Unusual {metric.replace('_', ' ').title()}",
                    "severity": severity,
                    "category": "statistical",
                    "description": (
                        f"{metric.replace('_', ' ').title()} of {value:.1f} is {direction} "
                        f"the typical range ({low}-{high}). Z-score: {z_score:.1f}."
                    ),
                    "metric": metric,
                    "value": round(value, 2),
                    "expected_range": f"{low} - {high}",
                })

        # --- LAYER 2: Isolation Forest ---
        try:
            feature_values = list(features.values())
            if all(v == 0 for v in feature_values):
                pass  # Skip if all zeros
            else:
                X = np.array([feature_values])
                # Create synthetic "normal" data around benchmarks for training
                np.random.seed(42)
                normal_samples = []
                for _ in range(100):
                    sample = []
                    for metric in features.keys():
                        if metric in self.BENCHMARKS:
                            low, high = self.BENCHMARKS[metric]
                            sample.append(np.random.uniform(low, high))
                        else:
                            sample.append(np.random.normal(0, 1))
                    normal_samples.append(sample)

                train_data = np.array(normal_samples)
                scaler = StandardScaler()
                train_scaled = scaler.fit_transform(train_data)
                X_scaled = scaler.transform(X)

                iso = IsolationForest(contamination=0.1, random_state=42)
                iso.fit(train_scaled)
                prediction = iso.predict(X_scaled)
                score = iso.decision_function(X_scaled)[0]

                if prediction[0] == -1:  # Anomaly detected
                    anomalies.append({
                        "anomaly": "Multivariate Financial Profile Anomaly",
                        "severity": "high" if score < -0.3 else "medium",
                        "category": "statistical",
                        "description": (
                            f"The combination of financial metrics is statistically unusual "
                            f"compared to typical mid-market companies (anomaly score: {score:.2f}). "
                            "This may indicate unique business characteristics or data quality issues."
                        ),
                        "metric": "multivariate_profile",
                        "value": round(score, 3),
                        "expected_range": "> 0 (normal)",
                    })
        except Exception:
            pass  # Isolation Forest is best-effort

        # --- LAYER 3: Rule-based domain checks ---

        # Gross margin > 95% is suspicious
        gm = features["gross_margin"]
        if gm > 95:
            anomalies.append({
                "anomaly": "Suspiciously High Gross Margin",
                "severity": "high", "category": "rule_based",
                "description": f"Gross margin of {gm:.1f}% is extremely unusual. Verify COGS classification.",
                "metric": "gross_margin", "value": gm, "expected_range": "20-80%"
            })

        # EBITDA > Revenue
        if inc.get("ebitda", 0) > inc.get("revenue", 0) and inc.get("revenue", 0) > 0:
            anomalies.append({
                "anomaly": "EBITDA Exceeds Revenue",
                "severity": "critical", "category": "rule_based",
                "description": "EBITDA greater than revenue is mathematically impossible. Data error likely.",
                "metric": "ebitda_vs_revenue",
                "value": inc["ebitda"], "expected_range": f"< {inc['revenue']}"
            })

        # Balance sheet doesn't balance (>1% discrepancy)
        total_assets = bs.get("total_assets", 0)
        total_le = bs.get("total_liabilities", 0) + bs.get("total_equity", 0)
        if total_assets > 0 and abs(total_assets - total_le) > total_assets * 0.01:
            anomalies.append({
                "anomaly": "Balance Sheet Imbalance",
                "severity": "high", "category": "rule_based",
                "description": (
                    f"Assets ({total_assets:,.0f}) ≠ Liabilities + Equity ({total_le:,.0f}). "
                    "Off by {:.0f}. Balance sheet does not balance.".format(abs(total_assets - total_le))
                ),
                "metric": "bs_balance",
                "value": round(total_assets - total_le, 0),
                "expected_range": "0 (balanced)"
            })

        # Low OCF/NI ratio — possible aggressive accounting
        ocf = cf.get("operating_cf", 0)
        ni = inc.get("net_income", 0)
        if ni > 0 and ocf > 0:
            ratio = safe_div(ocf, ni)
            if ratio < 0.3:
                anomalies.append({
                    "anomaly": "Low Cash Conversion",
                    "severity": "high", "category": "rule_based",
                    "description": (
                        f"OCF/Net Income of {ratio:.2f} — earnings not converting to cash. "
                        "Possible aggressive revenue recognition or accrual issues."
                    ),
                    "metric": "ocf_to_net_income",
                    "value": round(ratio, 2),
                    "expected_range": "0.8 - 1.5"
                })

        return anomalies
```

## File 4: `services/report_generator.py`

```python
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
import json
import os
from datetime import datetime

template_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "..", "templates"))
)

class ReportGenerator:

    def generate(self, report_type: str, deal: dict, analyses: dict,
                 narrative: dict) -> str:
        """
        1. Select template
        2. Build context
        3. Render HTML
        4. Convert to PDF via WeasyPrint
        5. Return file path
        """
        template_map = {
            "iar": "iar_report.html",
            "dcf": "dcf_report.html",
            "red_flag": "red_flag_report.html",
        }

        template = template_env.get_template(template_map[report_type])

        # Provide fallback empty dicts for all analyses
        context = {
            "deal": deal,
            "generated_date": datetime.utcnow().strftime("%B %d, %Y"),
            "narrative": narrative or {},
            "qoe": analyses.get("qoe", {}),
            "working_capital": analyses.get("working_capital", {}),
            "ratios": analyses.get("ratios", {}),
            "dcf": analyses.get("dcf", {}),
            "red_flags": analyses.get("red_flags", []),
            "anomalies": analyses.get("anomalies", []),
            "ai_insights": analyses.get("ai_insights", {}),
        }

        html_content = template.render(**context)

        output_dir = f"./reports/{deal.get('id', 0)}"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{report_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(output_dir, filename)

        HTML(string=html_content).write_pdf(filepath)
        return filepath
```

## File 5-7: HTML Templates

Create 3 Jinja2 HTML templates in the `templates/` directory. All templates share this base CSS:

```css
@page { size: A4; margin: 2cm; @bottom-center { content: "Page " counter(page) " of " counter(pages); font-size: 9pt; color: #718096; } }
body { font-family: 'Georgia', 'Times New Roman', serif; font-size: 11pt; line-height: 1.6; color: #1a1a1a; }
h1 { font-family: 'Helvetica Neue', 'Arial', sans-serif; color: #1e3a5f; font-size: 22pt; border-bottom: 3px solid #1e3a5f; padding-bottom: 8px; }
h2 { font-family: 'Helvetica Neue', 'Arial', sans-serif; color: #2c5282; font-size: 16pt; margin-top: 24px; }
h3 { font-family: 'Helvetica Neue', 'Arial', sans-serif; color: #2d3748; font-size: 13pt; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; }
th { background: #1e3a5f; color: white; padding: 10px 14px; text-align: left; font-family: 'Helvetica Neue', sans-serif; font-size: 10pt; }
td { padding: 8px 14px; border-bottom: 1px solid #e2e8f0; font-size: 10pt; }
tr:nth-child(even) { background: #f7fafc; }
.cover { text-align: center; padding: 120px 0 80px; page-break-after: always; }
.cover h1 { font-size: 28pt; border: none; }
.cover .subtitle { font-size: 16pt; color: #4a5568; margin-top: 12px; }
.cover .date { font-size: 12pt; color: #718096; margin-top: 24px; }
.cover .confidential { font-size: 10pt; color: #e53e3e; margin-top: 40px; text-transform: uppercase; letter-spacing: 2px; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 4px; font-size: 9pt; font-weight: bold; font-family: 'Helvetica Neue', sans-serif; }
.badge-high, .badge-critical { background: #e53e3e; color: white; }
.badge-medium { background: #dd6b20; color: white; }
.badge-low { background: #3182ce; color: white; }
.badge-green { background: #38a169; color: white; }
.metric-box { background: #edf2f7; padding: 14px; border-radius: 8px; text-align: center; display: inline-block; margin: 6px; min-width: 140px; }
.metric-value { font-size: 22pt; font-weight: bold; color: #1e3a5f; }
.metric-label { font-size: 9pt; color: #718096; text-transform: uppercase; }
.section { margin-bottom: 20px; }
.note { background: #ebf8ff; border-left: 4px solid #3182ce; padding: 12px 16px; margin: 12px 0; }
.warning { background: #fffbeb; border-left: 4px solid #dd6b20; padding: 12px 16px; margin: 12px 0; }
.danger { background: #fff5f5; border-left: 4px solid #e53e3e; padding: 12px 16px; margin: 12px 0; }
.tam-logo { font-family: 'Helvetica Neue', sans-serif; font-size: 12pt; color: #1e3a5f; font-weight: bold; }
.footer { font-size: 8pt; color: #a0aec0; text-align: center; margin-top: 40px; }
```

### `templates/iar_report.html` — Independent Accountants' Report

Build a complete HTML document with the shared CSS above. Sections:
1. **Cover page** (with `page-break-after`): "Independent Accountants' Report — Financial Due Diligence", target company name `{{ deal.target_company }}`, date, "CONFIDENTIAL" tag, TAM branding
2. **Table of Contents** (hardcoded numbered list of sections)
3. **Section 1: Scope & Engagement** — render `{{ narrative.scope }}` or a fallback paragraph
4. **Section 2: Procedures Performed** — render `{{ narrative.procedures_performed }}` or fallback
5. **Section 3: Quality of Earnings** — Metric boxes for Reported EBITDA, Adjusted EBITDA, Quality Score. Then adjustments table from `{{ qoe.adjustments }}` with columns: Description, Category, Amount, Impact.
6. **Section 4: Working Capital** — Metric boxes: NWC, DSO, DIO, DPO, CCC. Assessment text.
7. **Section 5: Financial Ratios** — 4 tables (Liquidity, Profitability, Leverage, Efficiency) from `{{ ratios }}`
8. **Section 6: Key Findings** — render `{{ narrative.findings }}` or AI key_findings
9. **Section 7: Conclusion** — render `{{ narrative.conclusion }}`
10. **Limitations** — render `{{ narrative.limitations }}`

Use Jinja2 `{% for %}` loops for tables and lists. Use `{{ "%.2f"|format(value) }}` or `{{ "{:,.0f}".format(value) }}` for number formatting. Use `{% if %}` blocks to handle missing data gracefully.

### `templates/dcf_report.html` — DCF Valuation Report

1. **Cover page**: "Discounted Cash Flow Valuation", target company, date
2. **Section 1: Methodology** — render `{{ narrative.methodology_description }}` or default DCF methodology text
3. **Section 2: Key Assumptions** — table from `{{ dcf.assumptions }}`: WACC, growth rate, terminal growth, tax rate, capex %
4. **Section 3: 5-Year Projections** — table from `{{ dcf.projected_years }}`: Year, Revenue, EBITDA, FCF, Discount Factor, PV FCF
5. **Section 4: Terminal Value** — show terminal value calculation
6. **Section 5: Valuation Summary** — metric boxes: Enterprise Value, Equity Value, EV/Revenue, EV/EBITDA. Then a "bridge" breakdown: Sum PV FCFs + PV Terminal = EV + Cash - Debt = Equity Value
7. **Section 6: Sensitivity Discussion** — render `{{ narrative.sensitivity_discussion }}`
8. **Conclusion** — render `{{ narrative.conclusion }}`

### `templates/red_flag_report.html` — Red Flag Report

1. **Cover page**: "Red Flag Assessment Report", target company, date, overall risk badge
2. **Section 1: Executive Summary** — render `{{ narrative.executive_summary }}` or `{{ ai_insights.executive_summary }}`
3. **Section 2: Risk Summary** — count of flags by severity in a summary table. Deal recommendation badge.
4. **Section 3: Detailed Red Flags** — for each flag in `{{ red_flags }}`: title + severity badge, description, metric vs threshold. If narrative has `detailed_findings`, include expanded text.
5. **Section 4: Anomaly Detection Results** — for each anomaly in `{{ anomalies }}`: anomaly name + category badge, description, value + expected range.
6. **Section 5: Risk Mitigation** — render `{{ narrative.risk_mitigation_recommendations }}`
7. **Overall Assessment** — render `{{ narrative.overall_assessment }}`

## Important Notes

1. **Function signatures must match exactly** — your teammate's pipeline calls your functions with specific argument names and expects specific return types. Follow the signatures shown above.
2. **Lazy client initialization** — don't crash on import if API keys aren't set. Only fail when a function is actually called.
3. **_parse_json_response is critical** — Claude doesn't always return clean JSON. The parser handles markdown blocks and partial JSON.
4. **ChromaDB collections** — one per deal, named `deal_{deal_id}`. Delete when deal is deleted.
5. **WeasyPrint** — may need system dependencies (`apt-get install libpango-1.0-0 libgdk-pixbuf2.0-0` on Linux, `brew install pango` on Mac). Document this in a comment.
6. **Template fallbacks** — every `{{ narrative.X }}` should have an `{% if %}` guard or `|default('')` filter, since Claude might return partial JSON.

Now build all 4 service files and 3 HTML templates. Place them in the correct directories within the existing project structure. Make sure every function signature matches what the pipeline expects.
