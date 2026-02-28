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
import os
import joblib

class DocumentClassifier:

    def __init__(self):
        self.model_path = "./models/fine_tuned_doc_classifier"
        self.use_ml = os.path.exists(self.model_path)
        if self.use_ml:
            try:
                from transformers import pipeline
                self.pipe = pipeline("text-classification", model=self.model_path, tokenizer=self.model_path)
                self.label_map = {
                    "LABEL_0": "income_statement",
                    "LABEL_1": "balance_sheet",
                    "LABEL_2": "cash_flow_statement",
                    "LABEL_3": "audit_report",
                }
            except Exception as e:
                print(f"Failed to load HF model: {e}")
                self.use_ml = False

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
        if getattr(self, 'use_ml', False):
            try:
                result = self.pipe(text[:512], truncation=True, max_length=512)[0]
                pred_label = result['label']
                doc_type = self.label_map.get(pred_label, "other")
                confidence = round(result['score'], 2)
                return doc_type, confidence
            except Exception as e:
                print(f"ML classification failed: {e}. Falling back to heuristics.")

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

    def __init__(self):
        self.model_dir = "./models"
        self.iso_path = os.path.join(self.model_dir, 'sec_isolation_forest.joblib')
        self.scaler_path = os.path.join(self.model_dir, 'sec_scaler.joblib')
        self.features_path = os.path.join(self.model_dir, 'sec_features.joblib')
        self.use_ml = all(os.path.exists(p) for p in [self.iso_path, self.scaler_path, self.features_path])
        if self.use_ml:
            try:
                self.sec_iso = joblib.load(self.iso_path)
                self.sec_scaler = joblib.load(self.scaler_path)
                self.sec_features_list = joblib.load(self.features_path)
            except Exception as e:
                print(f"Failed to load SEC models: {e}")
                self.use_ml = False

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
        has_sec_ml = getattr(self, 'use_ml', False)
        if has_sec_ml:
            try:
                model_features = [features.get(f, 0) for f in self.sec_features_list]
                X = np.array([model_features])
                X_scaled = self.sec_scaler.transform(X)
                prediction = self.sec_iso.predict(X_scaled)
                score = self.sec_iso.decision_function(X_scaled)[0]

                if prediction[0] == -1:  # Anomaly detected
                    anomalies.append({
                        "anomaly": "SEC Multivariate Profile Anomaly",
                        "severity": "high" if score < -0.1 else "medium",
                        "category": "statistical",
                        "description": f"The combination of margins diverges from the SEC EDGAR benchmark for public companies (score: {score:.2f}).",
                        "metric": "multivariate_profile",
                        "value": round(score, 3),
                        "expected_range": "> 0 (normal)"
                    })
            except Exception as e:
                print(f"SEC Isolation Forest failed: {e}")
                has_sec_ml = False

        if not has_sec_ml:
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
