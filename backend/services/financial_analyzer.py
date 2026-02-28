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
    if magnitude > 0.25:
        score -= 30
    elif magnitude > 0.10:
        score -= 15
    elif magnitude > 0.05:
        score -= 5
    for adj in adjustments:
        cat = adj.get("category", "")
        if cat == "non_recurring":
            score -= 10
        elif cat == "related_party":
            score -= 8
        elif cat == "owner_compensation":
            score -= 5
    op_exp = inc.get("operating_expenses", 0)
    if revenue > 0 and revenue < op_exp:
        score -= 15
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

    if ccc < 30:
        assessment = "Excellent cash conversion — business collects fast and pays strategically."
    elif ccc < 60:
        assessment = "Healthy working capital cycle within normal operating range."
    elif ccc < 90:
        assessment = "Moderate efficiency — cash tied up for a notable period. Investigate AR aging."
    else:
        assessment = "Poor cash conversion — significant capital locked in working capital. Immediate attention needed."

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
