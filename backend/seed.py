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
