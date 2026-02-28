# TAM — Transaction Analysis Machine
**The AI-Powered Operating System for Financial Due Diligence**

![TAM Architecture Overview](./docs/images/architecture.png)

TAM (Transaction Analysis Machine) is a full-stack, AI-driven platform built for Private Equity analysts and M&A professionals. It automates the gruelling, highly manual process of **Financial Due Diligence (FDD)**, transforming weeks of "grunt work" into seconds of automated insight.

---

## 🚀 Live Demo
**Frontend Workspace:** 

> **Deployment Note:** The Next.js frontend is production-ready on Vercel. However, the **TAM Neural Engine** (backend) requires high-compute environments for its ML models (`scikit-learn`, `chromadb`) and dynamic PDF generation (`playwright`). To experience the full end-to-end pipeline, the backend is best run in a Dockerized environment or locally.

---

## 🧠 Deep Dive: The AI & ML Engine

TAM doesn't just "read" documents; it interprets them through a multi-layered Intelligence Stack.

### 1. Document Classification (NLP)
Using a hybrid approach of **Hugging Face Transformers** (fine-tuned for financial terminology) and keyword-heuristics, TAM automatically identifies the document type (e.g., Trial Balance, P&L, AR Aging). This ensures that a Balance Sheet is never analyzed as an Income Statement.

### 2. Multivariate Anomaly Detection (Unsupervised ML)
We use a **Scikit-Learn Isolation Forest** model to detect outliers. Unlike simple rule-based systems, this unsupervised ML model looks at the *combination* of metrics (e.g., high revenue growth vs. low receivables turnover) to flag statistical anomalies that might indicate earnings manipulation or data quality issues.

### 3. Agentic Extraction Workflow
The extraction process is **self-correcting**. If the initial LLM pass (Claude 4.5 Sonnet) returns a "sparse" result (too many missing fields), the system triggers an autonomous **Self-Refinement Loop**.

![Agentic Workflow](./docs/images/workflow.png)

*   **Step 1:** Initial extraction of financial figures from unstructured text/PDF.
*   **Step 2:** Statistical Validation—the agent checks its own work for mathematical consistency.
*   **Step 3:** Re-Examination—if confidence is low, the agent re-scans the source document using alternate labels (e.g., checking "Net Sales" if "Revenue" was missing).

---

## 🏗️ Technical Architecture

TAM is built with a decoupled, high-performance architecture designed for scale.

*   **Frontend:** Next.js 14, TypeScript, Tailwind CSS, Recharts.
*   **Backend:** FastAPI (Python), SQLAlchemy, Pydantic.
*   **Data Store:** SQLite (Relational) + ChromaDB (Vector Database for RAG-powered Q&A).
*   **Intelligence:** 
    *   **Anthropic API:** Claude 4.5 Sonnet for reasoning and narrative generation.
    *   **ML Engine:** Scikit-Learn (Isolation Forest, StandardScaler), Hugging Face Transformers.
*   **Report Generation:** Playwright (Headless Chromium) renders specialized Tailwind templates into industry-grade PDFs.

---

## 📈 Financial Frameworks (Glossary)

TAM automates the world's most critical financial analyses:

### Quality of Earnings (QoE)
Analyzes "Reported EBITDA" vs. "Adjusted EBITDA" by identifying normalization items (one-time gains, owner-related expenses, or non-recurring legal costs).

### Net Working Capital (NWC)
Calculates historical liquidity and sets a "Working Capital Peg," ensuring acquirers don't overpay for businesses without enough cash to run operations.

### Cash Conversion Cycle (CCC)
Measures operational efficiency. A high CCC indicates cash is trapped in inventory or unpaid customer bills, while a low CCC signals a healthy, cash-generating business.

### Discounted Cash Flow (DCF)
Models the absolute floor and ceiling value of a business by projecting 5-year Free Cash Flows and discounting them back to Net Present Value (NPV).

---

## 💻 Setup & Installation

### 1. Backend Neural Engine
```bash
cd backend
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload
```

### 2. Frontend Analyst UI
```bash
cd frontend
npm install
npm run dev
```

### 3. Environmental Configuration
Create a `.env` in `backend/` with your credentials:
```env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

---

## Team

Built for **MadData 2026** by:

| Name | Major |
|------|-------|
| **Yash Arvind** | B.S. in Data Science & Economics |
| **Diya Kothari** | B.S. in Data Science & Economics |
| **Hriday Thakkar** | B.S. in Computer Science & Math |

---
*Built to automate the future of M&A.*
