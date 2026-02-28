"use client";

import { AIInsights } from "@/lib/types";
import { severityColor, riskBadgeColor, recommendationLabel } from "@/lib/utils";

interface Props { data: AIInsights | null; }

export default function InsightsTab({ data }: Props) {
    if (!data) return <div className="text-center py-12 text-slate-400">No AI insights available.</div>;

    return (
        <div className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-800">AI-Powered Insights</h2>

            {/* Executive Summary */}
            <div className="bg-blue-50 border-l-4 border-blue-400 rounded-r-xl p-5">
                <h3 className="text-sm font-semibold text-blue-800 mb-2">Executive Summary</h3>
                <p className="text-sm text-slate-700 leading-relaxed">{data.executive_summary}</p>
            </div>

            {/* Key Findings */}
            {data.key_findings.length > 0 && (
                <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-slate-700">Key Findings</h3>
                    {data.key_findings.map((finding, i) => (
                        <div key={i} className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                            <div className="flex items-start gap-3">
                                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold uppercase ${severityColor(finding.impact)}`}>
                                    {finding.impact} IMPACT
                                </span>
                                <div className="flex-1">
                                    <p className="text-sm font-medium text-slate-800">{finding.finding}</p>
                                    <p className="text-sm text-slate-500 mt-1">→ {finding.recommendation}</p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Valuation Opinion */}
            {data.valuation_opinion && (
                <div className="bg-purple-50 border-l-4 border-purple-400 rounded-r-xl p-5">
                    <h3 className="text-sm font-semibold text-purple-800 mb-2">Valuation Opinion</h3>
                    <p className="text-sm text-slate-700 leading-relaxed">{data.valuation_opinion}</p>
                </div>
            )}

            {/* Risk Assessment */}
            {data.risk_assessment && (
                <div className={`rounded-xl border p-5 ${riskBadgeColor(data.risk_assessment.overall_risk)}`}>
                    <h3 className="text-sm font-bold uppercase tracking-wide mb-3">
                        Risk Assessment: {recommendationLabel(data.risk_assessment.deal_recommendation)}
                    </h3>
                    <div className="space-y-1 text-sm">
                        <p><span className="font-medium">Financial Risk:</span> {data.risk_assessment.financial_risk}</p>
                        <p><span className="font-medium">Operational Risk:</span> {data.risk_assessment.operational_risk}</p>
                    </div>
                </div>
            )}

            {/* Questions for Management */}
            {data.questions_for_management.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                    <h3 className="text-sm font-semibold text-slate-800 mb-3">
                        Questions for Management ({data.questions_for_management.length})
                    </h3>
                    <ol className="list-decimal list-inside space-y-2">
                        {data.questions_for_management.map((q, i) => (
                            <li key={i} className="text-sm text-slate-700 leading-relaxed">{q}</li>
                        ))}
                    </ol>
                </div>
            )}
        </div>
    );
}
