"use client";

import { QoEResults } from "@/lib/types";
import { formatCurrency, formatCompactCurrency, formatPercent, healthColor } from "@/lib/utils";

interface Props { data: QoEResults | null; }

export default function QoETab({ data }: Props) {
    if (!data) return <div className="text-center py-12 text-slate-400">No QoE data available.</div>;

    const scoreColor = data.quality_score >= 70 ? "text-emerald-500 border-emerald-500" : data.quality_score >= 40 ? "text-amber-500 border-amber-500" : "text-red-500 border-red-500";
    const sustainColor = data.earnings_sustainability === "high" ? "bg-emerald-100 text-emerald-700" : data.earnings_sustainability === "medium" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700";

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-800">Quality of Earnings</h2>
                <div className={`h-16 w-16 rounded-full border-4 flex items-center justify-center ${scoreColor}`}>
                    <span className="text-xl font-bold">{data.quality_score}</span>
                </div>
            </div>

            {/* EBITDA Bridge */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                <h3 className="text-sm font-semibold text-slate-800 mb-4">EBITDA Bridge</h3>
                <div className="space-y-2">
                    <div className="flex justify-between py-2 px-3 bg-slate-50 rounded">
                        <span className="text-sm font-medium text-slate-700">Reported EBITDA</span>
                        <span className="text-sm font-semibold text-slate-900">{formatCurrency(data.reported_ebitda)}</span>
                    </div>
                    {data.adjustments.map((adj, i) => (
                        <div key={i} className="flex justify-between py-2 px-3">
                            <span className="text-sm text-slate-600">
                                {adj.amount >= 0 ? "+" : "−"} {adj.description}
                            </span>
                            <span className={`text-sm font-medium ${adj.amount >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                                {adj.amount >= 0 ? "+" : "−"}{formatCompactCurrency(Math.abs(adj.amount))}
                            </span>
                        </div>
                    ))}
                    <div className="flex justify-between py-2 px-3 bg-slate-800 text-white rounded mt-2">
                        <span className="text-sm font-semibold">Adjusted EBITDA</span>
                        <span className="text-sm font-bold">{formatCurrency(data.adjusted_ebitda)}</span>
                    </div>
                </div>
            </div>

            {/* Sustainability + Margins */}
            <div className="grid grid-cols-3 gap-4">
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 text-center">
                    <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">Earnings Sustainability</p>
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${sustainColor}`}>
                        {data.earnings_sustainability.toUpperCase()}
                    </span>
                </div>
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 text-center">
                    <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">EBITDA Margin</p>
                    <p className="text-2xl font-bold text-slate-900">{formatPercent(data.ebitda_margin)}</p>
                </div>
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 text-center">
                    <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">Adjusted EBITDA Margin</p>
                    <p className="text-2xl font-bold text-slate-900">{formatPercent(data.adjusted_ebitda_margin)}</p>
                </div>
            </div>

            {/* Adjustments Table */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-5 py-3 border-b border-slate-100">
                    <h3 className="text-sm font-semibold text-slate-800">Adjustments Detail</h3>
                </div>
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-slate-100 bg-slate-50">
                            <th className="px-5 py-2 text-left text-xs uppercase tracking-wide text-slate-400">Category</th>
                            <th className="px-5 py-2 text-left text-xs uppercase tracking-wide text-slate-400">Description</th>
                            <th className="px-5 py-2 text-right text-xs uppercase tracking-wide text-slate-400">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.adjustments.map((adj, i) => (
                            <tr key={i} className="border-b border-slate-50">
                                <td className="px-5 py-3">
                                    <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">{adj.category.replace(/_/g, " ")}</span>
                                </td>
                                <td className="px-5 py-3 text-slate-700">{adj.description}</td>
                                <td className={`px-5 py-3 text-right font-medium ${adj.amount >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                                    {adj.amount >= 0 ? "+" : ""}{formatCompactCurrency(adj.amount)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
