import re

def extract_financial_data_local(document_text: str, filename: str = "") -> dict:
    """
    Fallback regex-based financial data extractor for when AI is unavailable.
    Searches for common financial terms like Revenue, EBITDA, Net Income, etc.
    """
    if not document_text:
        document_text = ""
    text_lower = document_text.lower()
    
    def find_number(keyword):
        # looks for keyword, optional characters, then a number (allowing commas and decimals)
        pattern = rf"(?:{keyword})[^\d\n]{{0,30}}([\$€£]?\s*[\d,]+\.?\d*)"
        match = re.search(pattern, text_lower)
        if match and match.group(1):
            num_str = re.sub(r'[^\d.]', '', match.group(1))
            try:
                return float(num_str)
            except ValueError:
                pass
        return 0

    return {
        "company_name": "Unknown Company (Local Extracted)",
        "period": "FY (Local)",
        "currency": "USD",
        "income_statement": {
            "revenue": find_number(r"revenue|sales|net sales"),
            "cogs": find_number(r"cost of goods sold|cogs|cost of revenue|cost of sales"),
            "gross_profit": find_number(r"gross profit|gross margin"),
            "operating_expenses": find_number(r"operating expenses|opex"),
            "ebitda": find_number(r"ebitda"),
            "depreciation": find_number(r"depreciation|amortization"),
            "interest": find_number(r"interest expense|interest"),
            "tax": find_number(r"tax|income tax"),
            "net_income": find_number(r"net income|net loss|net profit")
        },
        "balance_sheet": {
            "cash": find_number(r"cash and cash equivalents|cash"),
            "accounts_receivable": find_number(r"accounts receivable|receivables"),
            "inventory": find_number(r"inventory|inventories"),
            "total_current_assets": find_number(r"total current assets"),
            "ppe": find_number(r"property, plant and equipment|ppe"),
            "total_assets": find_number(r"total assets"),
            "accounts_payable": find_number(r"accounts payable|payables"),
            "short_term_debt": find_number(r"short term debt|short-term debt"),
            "total_current_liabilities": find_number(r"total current liabilities"),
            "long_term_debt": find_number(r"long term debt|long-term debt"),
            "total_liabilities": find_number(r"total liabilities"),
            "total_equity": find_number(r"total equity|stockholders' equity|shareholders' equity")
        },
        "cash_flow": {
            "operating_cf": find_number(r"net cash provided by operating activities|operating cash flow"),
            "investing_cf": find_number(r"net cash used in investing activities|investing cash flow"),
            "financing_cf": find_number(r"net cash used in financing activities|financing cash flow"),
            "net_cf": find_number(r"net change in cash"),
            "capex": find_number(r"capital expenditures|capex"),
            "fcf": find_number(r"free cash flow|fcf")
        },
        "adjustments": [],
        "notes": [{"note": "Data extracted via local fallback due to AI service unavailability."}]
    }
