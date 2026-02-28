export interface Deal {
  id: number;
  name: string;
  target_company: string;
  industry: string | null;
  deal_size: number | null;
  status: "pending" | "analyzing" | "completed" | "failed";
  created_at: string;
  document_count: number;
  analysis_count: number;
}

export interface DealDetail extends Deal {
  documents: Document[];
  analyses: AnalysisSummary[];
}

export interface Document {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  doc_type: string | null;
  doc_type_confidence: number | null;
  uploaded_at: string;
}

export interface AnalysisSummary {
  analysis_type: string;
  status: string;
  completed_at: string | null;
}

export interface Analysis {
  id: number;
  analysis_type: string;
  status: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  results: any;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  sources: { chunk_text: string; filename: string; relevance_score: number }[] | null;
  created_at: string;
}

export interface Report {
  id: number;
  report_type: "iar" | "dcf" | "red_flag";
  generated_at: string;
  download_url: string;
}

// --- Analysis Result Shapes ---

export interface QoEResults {
  reported_ebitda: number;
  adjusted_ebitda: number;
  total_adjustments: number;
  adjustments: { description: string; amount: number; category: string; impact: string }[];
  quality_score: number;
  earnings_sustainability: "high" | "medium" | "low";
  ebitda_margin: number;
  adjusted_ebitda_margin: number;
}

export interface WorkingCapitalResults {
  current_assets: number;
  current_liabilities: number;
  net_working_capital: number;
  current_ratio: number;
  dso: number;
  dio: number;
  dpo: number;
  cash_conversion_cycle: number;
  nwc_as_pct_revenue: number;
  assessment: string;
}

export interface RatioResults {
  liquidity: { current_ratio: number; quick_ratio: number; cash_ratio: number };
  profitability: { gross_margin: number; ebitda_margin: number; operating_margin: number; net_margin: number; roe: number; roa: number };
  leverage: { debt_to_equity: number; debt_to_assets: number; interest_coverage: number; debt_to_ebitda: number };
  efficiency: { asset_turnover: number; inventory_turnover: number; receivables_turnover: number };
  cash_flow: { ocf_to_net_income: number; fcf_margin: number };
  overall_health_score: number;
  health_rating: "Excellent" | "Good" | "Fair" | "Concerning" | "Critical";
}

export interface DCFResults {
  assumptions: Record<string, number>;
  projected_years: { year: number; revenue: number; ebitda: number; fcf: number; discount_factor: number; pv_fcf: number; growth_rate: number }[];
  terminal_value: number;
  pv_terminal_value: number;
  sum_pv_fcf: number;
  enterprise_value: number;
  equity_value: number;
  ev_to_revenue: number;
  ev_to_ebitda: number;
  current_ebitda_margin: number;
}

export interface RedFlag {
  flag: string;
  severity: "high" | "medium" | "low";
  description: string;
  metric: string;
  value: number;
  threshold: number;
}

export interface Anomaly {
  anomaly: string;
  severity: "critical" | "high" | "medium" | "low";
  category: "statistical" | "rule_based";
  description: string;
  metric: string;
  value: number;
  expected_range: string;
}

export interface AIInsights {
  executive_summary: string;
  key_findings: { finding: string; impact: string; recommendation: string }[];
  risk_assessment: {
    overall_risk: "low" | "medium" | "high";
    financial_risk: string;
    operational_risk: string;
    deal_recommendation: "proceed" | "proceed_with_caution" | "significant_concerns";
  };
  valuation_opinion: string;
  questions_for_management: string[];
}
