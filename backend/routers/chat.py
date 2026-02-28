import json
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Deal, ChatMessage, Analysis
from schemas import ChatRequest, ChatMessageResponse
from utils import parse_json_field

router = APIRouter()


def build_deal_context(db: Session, deal_id: int) -> dict:
    """Load all analysis results for a deal to provide context to the AI."""
    analyses = db.query(Analysis).filter(Analysis.deal_id == deal_id).all()
    context = {}
    for a in analyses:
        context[a.analysis_type] = parse_json_field(a.results)
    return context


def safe_get(d, *keys, default=None):
    """Safe nested dict access."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
        if d is None:
            return default
    return d


def fmt(val, prefix="$", decimals=1):
    """Format a number nicely."""
    try:
        f = float(val)
        if abs(f) >= 1_000_000:
            return f"{prefix}{f/1_000_000:.{decimals}f}M"
        if abs(f) >= 1_000:
            return f"{prefix}{f/1_000:.{decimals}f}K"
        return f"{prefix}{f:.{decimals}f}"
    except Exception:
        return str(val)


def pct(val):
    try:
        return f"{float(val):.1f}%"
    except Exception:
        return str(val)


def local_answer(question: str, context: dict, deal) -> str:
    """
    Rule-based analytical fallback using the pre-computed analysis data.
    Matches question intent and synthesises a response from structured data.
    """
    q = question.lower()

    qoe      = context.get("qoe") or context.get("quality_of_earnings") or {}
    ratios   = context.get("ratios") or {}
    wc       = context.get("working_capital") or context.get("nwc") or {}
    dcf      = context.get("dcf") or {}
    flags    = context.get("red_flags") or []
    anomalies= context.get("anomalies") or []
    insights = context.get("ai_insights") or {}
    fin      = context.get("financial_data") or {}
    inc      = (fin.get("income_statement") or {}) if isinstance(fin, dict) else {}

    # ── QoE / EBITDA ──────────────────────────────────────────────────────────
    if any(kw in q for kw in ["ebitda", "earnings quality", "qoe", "adjusted", "adjustment", "quality of earnings"]):
        reported = safe_get(qoe, "reported_ebitda", default=0)
        adjusted = safe_get(qoe, "adjusted_ebitda", default=0)
        total_adj = safe_get(qoe, "total_adjustments", default=0)
        score = safe_get(qoe, "quality_score", default="N/A")
        sustainability = safe_get(qoe, "earnings_sustainability", default="N/A")
        adj_list = safe_get(qoe, "adjustments") or []

        lines = [
            "## Quality of Earnings Summary",
            f"",
            f"**Reported EBITDA:** {fmt(reported)}",
            f"**Adjusted EBITDA:** {fmt(adjusted)} ({fmt(total_adj)} in net adjustments)",
            f"**Earnings Quality Score:** {score}/100",
            f"**Sustainability Rating:** {str(sustainability).capitalize()}",
        ]
        if adj_list:
            lines += ["", "### Key Adjustments"]
            for a in adj_list[:5]:
                desc = a.get("description", "")
                amt  = a.get("amount", 0)
                cat  = a.get("category", "")
                sign = "+" if float(amt or 0) > 0 else ""
                lines.append(f"- **{desc}**: {sign}{fmt(amt)} _{cat}_")
        if sustainability in ("low", "medium"):
            lines += ["", "⚠️ **Note:** Earnings sustainability is flagged. Scrutinise recurring vs. non-recurring items carefully before applying a full EBITDA multiple."]
        return "\n".join(lines)

    # ── Revenue / sustainability ───────────────────────────────────────────────
    if any(kw in q for kw in ["revenue", "recurring", "sustainable", "sales", "top line"]):
        revenue = safe_get(inc, "revenue") or safe_get(qoe, "reported_ebitda")
        sustainability = safe_get(qoe, "earnings_sustainability", default="N/A")
        gm = safe_get(ratios, "profitability", "gross_margin", default=None)
        lines = [
            "## Revenue & Sustainability",
            f"",
            f"**Reported Revenue:** {fmt(revenue) if revenue else 'Not extracted'}",
            f"**Earnings Sustainability:** {str(sustainability).capitalize()}",
        ]
        if gm is not None:
            lines.append(f"**Gross Margin:** {pct(gm)}")
        lines += ["",
            "To determine whether revenue is recurring or one-time, review the QoE adjustments tab — non-recurring items are classified there.",
            "A high concentration of revenue from a single customer or single contract would typically appear as a red flag."]
        return "\n".join(lines)

    # ── Red Flags ──────────────────────────────────────────────────────────────
    if any(kw in q for kw in ["red flag", "risk", "concern", "issue", "problem", "warning", "biggest"]):
        overall_risk = safe_get(insights, "risk_assessment", "overall_risk", default="N/A")
        lines = [
            "## Risk Assessment & Red Flags",
            f"",
            f"**Overall Risk Rating:** {str(overall_risk).upper()}",
        ]
        if flags:
            high = [f for f in flags if f.get("severity") in ("high", "critical")]
            med  = [f for f in flags if f.get("severity") == "medium"]
            if high:
                lines += ["", "### 🔴 High-Priority Flags"]
                for f in high[:5]:
                    lines.append(f"- **{f.get('flag', '')}** — {f.get('description', '')}")
            if med:
                lines += ["", "### 🟡 Medium-Priority Flags"]
                for f in med[:3]:
                    lines.append(f"- **{f.get('flag', '')}** — {f.get('description', '')}")
        elif anomalies:
            lines += ["", "### Statistical Anomalies Detected"]
            for a in anomalies[:4]:
                lines.append(f"- **{a.get('anomaly', '')}** ({a.get('severity','')}): {a.get('description','')}")
        else:
            lines.append("No material red flags were detected in the financial data.")
        return "\n".join(lines)

    # ── Working Capital ────────────────────────────────────────────────────────
    if any(kw in q for kw in ["working capital", "nwc", "cash conversion", "ccc", "receivable", "payable", "inventory", "liquidity"]):
        nwc     = safe_get(wc, "net_working_capital", default=0)
        ccc     = safe_get(wc, "cash_conversion_cycle", default=0)
        dso     = safe_get(wc, "dso", default=0)
        dio     = safe_get(wc, "dio", default=0)
        dpo     = safe_get(wc, "dpo", default=0)
        cr      = safe_get(wc, "current_ratio", default=0)
        assessment = safe_get(wc, "assessment", default="")
        lines = [
            "## Net Working Capital & Liquidity",
            f"",
            f"**Net Working Capital:** {fmt(nwc)}",
            f"**Current Ratio:** {float(cr):.2f}x" if cr else "",
            f"",
            f"### Cash Conversion Cycle: {float(ccc):.0f} days",
            f"- Days Sales Outstanding (DSO): {float(dso):.0f} days",
            f"- Days Inventory Outstanding (DIO): {float(dio):.0f} days",
            f"- Days Payable Outstanding (DPO): {float(dpo):.0f} days",
        ]
        if assessment:
            lines += ["", f"**Assessment:** {assessment}"]
        if float(ccc or 0) > 60:
            lines += ["", "⚠️ A CCC above 60 days suggests the business has meaningful working capital intensity — cash is tied up in operations longer than typical. Verify the NWC peg carefully."]
        return "\n".join([l for l in lines if l is not None])

    # ── DCF / Valuation ────────────────────────────────────────────────────────
    if any(kw in q for kw in ["dcf", "valuation", "enterprise value", "equity value", "wacc", "ev/ebitda", "ev/revenue", "multiple", "price"]):
        ev      = safe_get(dcf, "enterprise_value", default=0)
        equity  = safe_get(dcf, "equity_value", default=0)
        ev_eb   = safe_get(dcf, "ev_to_ebitda", default=0)
        ev_rev  = safe_get(dcf, "ev_to_revenue", default=0)
        wacc    = safe_get(dcf, "assumptions", "wacc", default=0)
        tgr     = safe_get(dcf, "assumptions", "terminal_growth_rate", default=0)
        tv      = safe_get(dcf, "terminal_value", default=0)
        lines = [
            "## DCF Valuation Summary",
            f"",
            f"**Enterprise Value:** {fmt(ev)}",
            f"**Equity Value:** {fmt(equity)}",
            f"",
            f"### Implied Multiples",
            f"- EV / EBITDA: {float(ev_eb):.1f}x" if ev_eb else "- EV / EBITDA: N/A",
            f"- EV / Revenue: {float(ev_rev):.1f}x" if ev_rev else "- EV / Revenue: N/A",
            f"",
            f"### Key Assumptions",
            f"- WACC: {pct(float(wacc)*100) if wacc else 'N/A'}",
            f"- Terminal Growth Rate: {pct(float(tgr)*100) if tgr else 'N/A'}",
            f"- Terminal Value: {fmt(tv)}",
            f"",
            "These figures are model outputs. The valuation is sensitive to WACC and terminal growth rate — a ±1% shift in WACC can move enterprise value by 15–25%.",
        ]
        return "\n".join(lines)

    # ── Management Questions ───────────────────────────────────────────────────
    if any(kw in q for kw in ["management", "ask", "question", "diligence"]):
        questions = safe_get(insights, "questions_for_management") or []
        lines = ["## Suggested Questions for Management", ""]
        if questions:
            for i, q_item in enumerate(questions[:8], 1):
                lines.append(f"{i}. {q_item}")
        else:
            # Fallback universal questions
            lines += [
                "1. What percentage of revenue is under contract vs. at-will?",
                "2. Were there any one-time revenues or expenses in the reported period?",
                "3. What is the customer concentration — is any single customer >10% of revenue?",
                "4. What capex is required to maintain current revenue levels?",
                "5. Are any current liabilities disputed or subject to contingency?",
                "6. What is the management team's equity ownership post-close?",
                "7. Are there any off-balance-sheet obligations or guarantees?",
                "8. What IT or ERP transitions are in flight?",
            ]
        return "\n".join(lines)

    # ── Summary / Key Findings ────────────────────────────────────────────────
    if any(kw in q for kw in ["summarize", "summary", "overview", "key finding", "highlight", "tell me about"]):
        exec_sum = safe_get(insights, "executive_summary", default="")
        findings = safe_get(insights, "key_findings") or []
        lines = ["## Executive Summary", ""]
        if exec_sum:
            lines.append(exec_sum)
        if findings:
            lines += ["", "### Key Findings"]
            for f in findings[:5]:
                finding = f.get("finding", "")
                impact  = f.get("impact", "")
                lines.append(f"- **{finding}** — {impact}")
        if not exec_sum and not findings:
            # Build from raw data
            adj_ebitda = safe_get(qoe, "adjusted_ebitda", default=0)
            ev = safe_get(dcf, "enterprise_value", default=0)
            n_flags = len(flags)
            lines += [
                f"Based on the analysis of **{deal.target_company}**:",
                f"",
                f"- **Adjusted EBITDA:** {fmt(adj_ebitda)}",
                f"- **Enterprise Value (DCF):** {fmt(ev)}",
                f"- **Red Flags Identified:** {n_flags}",
                f"",
                "Review the individual tabs (QoE, Financials, Red Flags, DCF) for full detail.",
            ]
        return "\n".join(lines)

    # ── Anomalies / Balance sheet ──────────────────────────────────────────────
    if any(kw in q for kw in ["anomaly", "anomalies", "balance sheet", "unusual", "statistical"]):
        lines = ["## Anomaly Detection Results", ""]
        if anomalies:
            for a in anomalies:
                sev = a.get("severity", "")
                icon = "🔴" if sev in ("critical", "high") else "🟡" if sev == "medium" else "🟢"
                lines.append(f"{icon} **{a.get('anomaly','')}** ({sev})")
                lines.append(f"  {a.get('description','')}")
                if a.get("expected_range"):
                    lines.append(f"  _Expected range: {a['expected_range']}_")
                lines.append("")
        else:
            lines.append("No statistical anomalies were detected. The financial profile is within expected industry ranges.")
        return "\n".join(lines)

    # ── Financial Ratios ──────────────────────────────────────────────────────
    if any(kw in q for kw in ["ratio", "margin", "leverage", "debt", "interest coverage", "health"]):
        health = safe_get(ratios, "health_rating", default="N/A")
        score  = safe_get(ratios, "overall_health_score", default="N/A")
        prof   = ratios.get("profitability") or {}
        lev    = ratios.get("leverage") or {}
        liq    = ratios.get("liquidity") or {}
        lines = [
            "## Financial Ratio Analysis",
            f"",
            f"**Overall Health Rating:** {health} (Score: {score}/100)",
            f"",
            f"### Profitability",
            f"- Gross Margin: {pct(prof.get('gross_margin', 0))}",
            f"- EBITDA Margin: {pct(prof.get('ebitda_margin', 0))}",
            f"- Net Margin: {pct(prof.get('net_margin', 0))}",
            f"",
            f"### Leverage",
            f"- Debt / Equity: {float(lev.get('debt_to_equity', 0)):.2f}x",
            f"- Debt / EBITDA: {float(lev.get('debt_to_ebitda', 0)):.2f}x",
            f"- Interest Coverage: {float(lev.get('interest_coverage', 0)):.1f}x",
            f"",
            f"### Liquidity",
            f"- Current Ratio: {float(liq.get('current_ratio', 0)):.2f}x",
            f"- Quick Ratio: {float(liq.get('quick_ratio', 0)):.2f}x",
        ]
        return "\n".join(lines)

    # ── Generic fallback ──────────────────────────────────────────────────────
    adj_ebitda = safe_get(qoe, "adjusted_ebitda", default=0)
    ev = safe_get(dcf, "enterprise_value", default=0)
    overall_risk = safe_get(insights, "risk_assessment", "overall_risk", default="N/A")
    n_flags = len(flags)
    return (
        f"## {deal.target_company} — Deal Summary\n\n"
        f"Here's a quick snapshot based on the analysis:\n\n"
        f"- **Adjusted EBITDA:** {fmt(adj_ebitda)}\n"
        f"- **Enterprise Value (DCF):** {fmt(ev)}\n"
        f"- **Overall Risk:** {str(overall_risk).upper()}\n"
        f"- **Red Flags:** {n_flags} identified\n\n"
        f"Try asking me something more specific, such as:\n"
        f"- *What are the red flags?*\n"
        f"- *Summarise the earnings quality*\n"
        f"- *What WACC was used in the DCF?*\n"
        f"- *What questions should I ask management?*"
    )


@router.post("/deals/{deal_id}/chat", response_model=ChatMessageResponse)
def chat(deal_id: int, request: ChatRequest, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    # Save user message
    user_msg = ChatMessage(
        deal_id=deal_id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)
    db.commit()

    answer = None
    sources = []

    # ── Attempt 1: Claude + RAG ───────────────────────────────────────────────
    try:
        from services.rag_service import RAGService
        from services.claude_service import ask_question

        rag = RAGService()
        chunks = rag.retrieve(deal_id=deal_id, query=request.message, top_k=5)
        deal_context = build_deal_context(db, deal_id)
        deal_context["relevant_chunks"] = chunks
        answer, sources = ask_question(request.message, deal_context)

    except ImportError:
        pass  # Fall through to local answer

    except Exception as e:
        err_str = str(e).lower()
        # Credit exhausted or auth error — fall back silently
        if any(kw in err_str for kw in ["credit", "billing", "insufficient", "quota", "rate limit", "authentication"]):
            pass  # Fall through to local answer
        else:
            # Unexpected error — still fall back but log it
            print(f"Claude error (falling back): {e}")

    # ── Attempt 2: Local analytical engine ───────────────────────────────────
    if not answer:
        deal_context = build_deal_context(db, deal_id)
        # Still try RAG for document sources even without Claude
        try:
            from services.rag_service import RAGService
            rag = RAGService()
            sources = rag.retrieve(deal_id=deal_id, query=request.message, top_k=3)
        except Exception:
            sources = []

        answer = local_answer(request.message, deal_context, deal)

    # Save assistant message
    assistant_msg = ChatMessage(
        deal_id=deal_id,
        role="assistant",
        content=answer,
        sources=json.dumps(sources) if sources else None,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatMessageResponse(
        id=assistant_msg.id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        sources=parse_json_field(assistant_msg.sources),
        created_at=assistant_msg.created_at,
    )


@router.get("/deals/{deal_id}/chat")
def get_chat_history(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    messages = db.query(ChatMessage).filter(
        ChatMessage.deal_id == deal_id
    ).order_by(ChatMessage.created_at).all()

    return {
        "messages": [
            ChatMessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                sources=parse_json_field(msg.sources),
                created_at=msg.created_at,
            )
            for msg in messages
        ]
    }


@router.delete("/deals/{deal_id}/chat")
def clear_chat(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    db.query(ChatMessage).filter(ChatMessage.deal_id == deal_id).delete()
    db.commit()
    return {"message": "chat history cleared"}
