"use client";

import { DCFResults } from "@/lib/types";
import { formatCompactCurrency, formatPercent, formatNumber } from "@/lib/utils";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Line, ComposedChart } from "recharts";

interface Props { data: DCFResults | null; }

export default function DCFTab({ data }: Props) {
    if (!data) return <div className="text-center py-12 text-slate-400">No DCF data available.</div>;

    const chartData = data.projected_years.map((y) => ({
        name: `Year ${y.year}`,
        Revenue: y.revenue,
        FCF: y.fcf,
        "PV FCF": y.pv_fcf,
    }));

    return (
        <div className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-800">DCF Valuation</h2>

            {/* Top Metrics */}
            <div className="grid grid-cols-4 gap-4">
                {[
                    { label: "Enterprise Value", value: formatCompactCurrency(data.enterprise_value) },
                    { label: "Equity Value", value: formatCompactCurrency(data.equity_value) },
                    { label: "EV/Revenue", value: `${formatNumber(data.ev_to_revenue)}x` },
                    { label: "EV/EBITDA", value: `${formatNumber(data.ev_to_ebitda)}x` },
                ].map((m) => (
                    <div key={m.label} className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 text-center">
                        <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">{m.label}</p>
                        <p className="text-2xl font-bold text-slate-900">{m.value}</p>
                    </div>
                ))}
            </div>

            {/* Chart */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                <h3 className="text-sm font-semibold text-slate-800 mb-4">5-Year Projection</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <ComposedChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#94a3b8" }} />
                        <YAxis tickFormatter={(v) => formatCompactCurrency(v)} tick={{ fontSize: 12, fill: "#94a3b8" }} />
                        <Tooltip formatter={(value) => formatCompactCurrency(Number(value))} />
                        <Legend />
                        <Bar dataKey="Revenue" fill="#3b82f6" radius={[4, 4, 0, 0]} opacity={0.8} />
                        <Bar dataKey="FCF" fill="#10b981" radius={[4, 4, 0, 0]} opacity={0.8} />
                        <Line type="monotone" dataKey="PV FCF" stroke="#f59e0b" strokeWidth={2} dot={{ fill: "#f59e0b" }} />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>

            {/* Projection Table */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-slate-100 bg-slate-50">
                            <th className="px-5 py-2 text-left text-xs uppercase tracking-wide text-slate-400">Year</th>
                            <th className="px-5 py-2 text-right text-xs uppercase tracking-wide text-slate-400">Growth</th>
                            <th className="px-5 py-2 text-right text-xs uppercase tracking-wide text-slate-400">Revenue</th>
                            <th className="px-5 py-2 text-right text-xs uppercase tracking-wide text-slate-400">EBITDA</th>
                            <th className="px-5 py-2 text-right text-xs uppercase tracking-wide text-slate-400">FCF</th>
                            <th className="px-5 py-2 text-right text-xs uppercase tracking-wide text-slate-400">PV FCF</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.projected_years.map((y) => (
                            <tr key={y.year} className="border-b border-slate-50">
                                <td className="px-5 py-3 font-medium text-slate-700">Year {y.year}</td>
                                <td className="px-5 py-3 text-right text-slate-600">{formatPercent(y.growth_rate)}</td>
                                <td className="px-5 py-3 text-right text-slate-700">{formatCompactCurrency(y.revenue)}</td>
                                <td className="px-5 py-3 text-right text-slate-700">{formatCompactCurrency(y.ebitda)}</td>
                                <td className="px-5 py-3 text-right text-emerald-600">{formatCompactCurrency(y.fcf)}</td>
                                <td className="px-5 py-3 text-right text-slate-700">{formatCompactCurrency(y.pv_fcf)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Valuation Bridge */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                <h3 className="text-sm font-semibold text-slate-800 mb-4">Valuation Bridge</h3>
                <div className="space-y-2">
                    {[
                        { label: "PV of FCFs", value: data.sum_pv_fcf },
                        { label: "PV Terminal Value", value: data.pv_terminal_value },
                        { label: "Enterprise Value", value: data.enterprise_value, bold: true },
                    ].map((row) => (
                        <div key={row.label} className={`flex justify-between py-2 px-3 ${row.bold ? "bg-slate-800 text-white rounded" : ""}`}>
                            <span className={`text-sm ${row.bold ? "font-semibold" : "text-slate-600"}`}>{row.label}</span>
                            <span className={`text-sm ${row.bold ? "font-bold" : "font-medium text-slate-900"}`}>{formatCompactCurrency(row.value)}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Assumptions */}
            <div className="bg-slate-50 rounded-xl p-4">
                <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">Key Assumptions</p>
                <p className="text-sm text-slate-600">
                    WACC: {formatPercent((data.assumptions.wacc || 0.12) * 100)} · Terminal Growth: {formatPercent((data.assumptions.terminal_growth_rate || 0.03) * 100)} · Tax Rate: {formatPercent((data.assumptions.tax_rate || 0.25) * 100)}
                </p>
            </div>
        </div>
    );
}
