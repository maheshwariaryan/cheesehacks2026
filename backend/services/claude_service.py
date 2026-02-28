"""
TAM AI Service — powered by Anthropic Claude.
Uses Claude Sonnet for fast, high-quality financial analysis.

Add to backend/.env:  ANTHROPIC_API_KEY=sk-ant-...
"""

import json
import re
from config import settings

_client = None  # Lazy init

MODEL = "claude-sonnet-4-5-20250929"

def _get_client():
    global _client
    if _client is None:
        api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. "
                "Add ANTHROPIC_API_KEY=sk-ant-... to backend/.env"
            )
        import anthropic
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _chat(system: str, user: str, max_tokens: int = 4096, model: str = MODEL) -> str:
    """Low-level call to Anthropic messages API."""
    client = _get_client()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[
            {"role": "user", "content": user},
        ],
        temperature=0.1,  # Low temperature for deterministic financial analysis
    )
    return response.content[0].text


def _parse_json(text: str) -> dict | None:
    """Try to extract a JSON object from the model's response."""
    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Extract from ```json ... ``` block
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Find first { ... } block
    start = text.find('{')
    end   = text.rfind('}')
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return None


# ── Public API (same signatures as claude_service.py) ─────────────────────────

TARGET_SHAPE = '''{
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

SYSTEM_EXTRACT = (
    "You are a financial data extraction engine for M&A due diligence. "
    "Extract ALL financial figures from the document into the JSON structure below. "
    "Rules: extract exact numbers; if shown in thousands, multiply to full values; "
    "use 0 for missing fields; identify non-recurring items as adjustments. "
    "Return ONLY valid JSON, no comments, no markdown.\n\n"
    + TARGET_SHAPE
)


def extract_financial_data(document_text: str, filename: str = "") -> dict | None:
    """
    Two-pass agentic extraction:
    Pass 1 — initial extraction.
    Pass 2 — if >60% of fields are 0, retry with alternate label guidance.
    """
    user_msg = f"Document filename: {filename}\n\n{document_text[:12000]}"
    raw = _chat(SYSTEM_EXTRACT, user_msg, max_tokens=3000)
    result = _parse_json(raw)
    if not result:
        return None

    # Check how many fields are zero
    zero_fields = []
    for section in ["income_statement", "balance_sheet"]:
        for key, val in result.get(section, {}).items():
            if not val or val == 0:
                zero_fields.append(f"{section}.{key}")

    total_fields = (
        len(result.get("income_statement", {})) +
        len(result.get("balance_sheet", {}))
    )

    if total_fields > 0 and len(zero_fields) / total_fields > 0.6:
        retry_user = (
            f"Document filename: {filename}\n\n{document_text[:12000]}\n\n"
            f"---\nFirst pass found {len(zero_fields)} of {total_fields} fields as 0. "
            f"Missing: {', '.join(zero_fields[:10])}.\n"
            "Common alternate labels:\n"
            "- 'Net sales' or 'Total revenue' = revenue\n"
            "- 'Cost of revenue' or 'Cost of sales' = cogs\n"
            "- 'Total stockholders equity' = total_equity\n"
            "- 'Property and equipment, net' = ppe\n"
            "Re-examine the document carefully and return fully filled JSON."
        )
        retry_raw = _chat(SYSTEM_EXTRACT, retry_user, max_tokens=3000)
        retry_result = _parse_json(retry_raw)
        if retry_result:
            for section in ["income_statement", "balance_sheet", "cash_flow"]:
                for key, val in retry_result.get(section, {}).items():
                    if val and val != 0:
                        result.setdefault(section, {})[key] = val
            if retry_result.get("adjustments"):
                result["adjustments"] = retry_result["adjustments"]

    return result


def generate_insights(
    financial_data: dict, ratios: dict, red_flags: list,
    anomalies: list, qoe: dict, dcf: dict
) -> dict | None:
    """
    Generate expert M&A due diligence insights.
    Returns: executive_summary, key_findings, risk_assessment,
             valuation_opinion, questions_for_management.
    """
    context = json.dumps({
        "financial_data":    financial_data,
        "ratios":            ratios,
        "red_flags":         red_flags,
        "anomalies":         anomalies,
        "quality_of_earnings": qoe,
        "dcf_valuation":     dcf,
    }, indent=2, default=str)

    system = (
        "You are a senior M&A due diligence partner at a top-tier private equity firm. "
        "RULES: (1) Always reference specific numbers from the data — never be vague. "
        "(2) Each finding must include the actual dollar amount or percentage. "
        "(3) Risk assessment must be driven by specific metrics, not generic statements. "
        "(4) Your executive_summary should read like an institutional memo — precise and actionable. "
        "Return ONLY valid JSON (no markdown, no comments) with EXACTLY these keys:\n"
        "- executive_summary: string (3-5 sentences, cite key numbers)\n"
        "- key_findings: list of {finding: str, impact: str, recommendation: str} — at least 4 items\n"
        "- risk_assessment: {overall_risk: 'low'|'medium'|'high', financial_risk: str, "
        "operational_risk: str, deal_recommendation: 'proceed'|'proceed_with_caution'|'significant_concerns'}\n"
        "- valuation_opinion: string (reference EV, EBITDA multiple, and WACC)\n"
        "- questions_for_management: list of 8 specific, probing strings"
    )

    raw = _chat(system, f"Full analysis data:\n{context[:10000]}", max_tokens=3000)
    return _parse_json(raw)


def ask_question(question: str, deal_context: dict) -> tuple[str, list]:
    """
    RAG-powered Q&A for the analyst chatbot.
    deal_context contains financial analysis data + relevant_chunks from ChromaDB.
    Returns: (answer_text, sources_list)
    """
    chunks = deal_context.pop("relevant_chunks", [])
    chunk_text = "\n\n".join(
        f"[Source: {ch.get('filename', 'unknown')}]:\n{ch.get('chunk_text', '')}"
        for ch in chunks
    )

    # Pull key numbers to ground the answer
    qoe = deal_context.get("qoe") or {}
    dcf = deal_context.get("dcf") or {}
    ratios = deal_context.get("ratios") or {}
    red_flags = deal_context.get("red_flags") or []
    anomalies = deal_context.get("anomalies") or []
    ai_insights = deal_context.get("ai_insights") or {}

    # Build a condensed data summary to help the model answer precisely
    data_summary = json.dumps({
        "qoe": qoe,
        "dcf": dcf,
        "ratios": ratios,
        "red_flags": red_flags[:5],
        "anomalies": anomalies[:5],
        "ai_insights_summary": {
            "executive_summary": ai_insights.get("executive_summary", ""),
            "overall_risk": (ai_insights.get("risk_assessment") or {}).get("overall_risk", ""),
            "valuation_opinion": ai_insights.get("valuation_opinion", ""),
            "questions_for_management": ai_insights.get("questions_for_management", []),
            "key_findings": ai_insights.get("key_findings", []),
        },
    }, indent=2, default=str)[:6000]

    system = (
        "You are an expert M&A Financial Due Diligence analyst. Your answers must be:\n"
        "1. PRECISE — always cite actual numbers from the data (dollars, percentages, ratios).\n"
        "2. STRUCTURED — use headers (##), bullet points (-), and bold (**text**) for clarity.\n"
        "3. COMPLETE — answer every part of the question directly.\n"
        "4. SOURCED — mention which document or analysis module the data came from.\n\n"
        "If the data doesn't contain the answer, say so clearly rather than guessing.\n"
        "Do NOT give generic advice. Every statement must be grounded in the provided numbers."
    )

    user = (
        f"Question: {question}\n\n"
        f"--- Relevant Document Excerpts ---\n{chunk_text}\n\n"
        f"--- Financial Analysis Data ---\n{data_summary}"
    )

    answer = _chat(system, user, max_tokens=2000, model=MODEL)

    sources = [
        {
            "chunk_text":      ch.get("chunk_text", "")[:200],
            "filename":        ch.get("filename", ""),
            "relevance_score": ch.get("relevance_score", 0),
        }
        for ch in chunks
    ]
    return answer, sources


def generate_report_content(report_type: str, deal_data: dict) -> dict | None:
    """
    Generate narrative sections for PDF reports.
    """
    prompts = {
        "iar": (
            "You are writing the narrative sections of an Independent Accountants' Report "
            "for a financial due diligence engagement. Use formal, professional language. "
            "Return ONLY valid JSON with keys: scope, procedures_performed, findings, conclusion, limitations."
        ),
        "dcf": (
            "Write narrative sections for a DCF Valuation Report. "
            "Return ONLY valid JSON with keys: methodology_description, key_assumptions_narrative, "
            "sensitivity_discussion, conclusion."
        ),
        "red_flag": (
            "Write narrative sections for a Red Flag Assessment Report. "
            "Return ONLY valid JSON with keys: executive_summary, detailed_findings, "
            "risk_mitigation_recommendations, overall_assessment."
        ),
    }

    system = prompts.get(report_type, prompts["iar"])
    context = json.dumps(deal_data, indent=2, default=str)[:9000]

    raw = _chat(system, f"Deal data:\n{context}", max_tokens=3000)
    return _parse_json(raw)
