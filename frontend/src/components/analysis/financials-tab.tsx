"use client";

import { WorkingCapitalResults, RatioResults } from "@/lib/types";
import { formatCompactCurrency, formatPercent, formatNumber, healthColor } from "@/lib/utils";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
    Legend
} from "recharts";

interface Props { wc: WorkingCapitalResults | null; ratios: RatioResults | null; }

function dot(good: boolean, ok: boolean) {
    return good ? "🟢" : ok ? "🟡" : "🔴";
}

export default function FinancialsTab({ wc, ratios }: Props) {
    return (
        <div className="space-y-8">
            {/* Working Capital */}
            <div className="space-y-4">
                <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <span className="w-2 h-6 bg-blue-600 rounded-full inline-block"></span>
                    Net Working Capital (NWC) Profile
                </h2>
                {wc ? (
                    <>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                            {[
                                { label: "DSO", value: `${formatNumber(wc.dso)}`, sub: "days" },
                                { label: "DIO", value: `${formatNumber(wc.dio)}`, sub: "days" },
                                { label: "DPO", value: `${formatNumber(wc.dpo)}`, sub: "days" },
                                { label: "Cash Conversion", value: `${formatNumber(wc.cash_conversion_cycle)}`, sub: "days" },
                                { label: "NWC", value: formatCompactCurrency(wc.net_working_capital), sub: `${formatPercent(wc.nwc_as_pct_revenue)} rev` },
                            ].map((m) => (
                                <div key={m.label} className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-4 text-center">
                                    <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400 mb-2 font-semibold">{m.label}</p>
                                    <p className="text-2xl font-bold text-slate-900 dark:text-white">{m.value}</p>
                                    <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">{m.sub}</p>
                                </div>
                            ))}
                        </div>

                        {/* Chart Area */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-4">
                            <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-6">
                                <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-6">Cash Conversion Cycle Breakdown</h3>
                                <div className="h-64 w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart
                                            data={[
                                                { name: "Receivables (DSO)", value: wc.dso, fill: "#3b82f6" },
                                                { name: "Inventory (DIO)", value: wc.dio, fill: "#8b5cf6" },
                                                { name: "Payables (DPO)", value: -wc.dpo, fill: "#ef4444" },
                                            ]}
                                            margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
                                        >
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2} />
                                            <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                                            <YAxis tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                                            <Tooltip
                                                cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }}
                                                contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff' }}
                                                itemStyle={{ color: '#fff' }}
                                            />
                                            <Bar dataKey="value" radius={[4, 4, 4, 4]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            <div className="bg-blue-50/50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-900/30 rounded-xl p-6 flex flex-col justify-center">
                                <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-400 mb-3">Consultant Assessment</h3>
                                <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                                    {wc.assessment}
                                </p>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-slate-400">No working capital data available.</div>
                )}
            </div>

            {/* Financial Ratios */}
            <div className="space-y-6 pt-6 border-t border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                        <span className="w-2 h-6 bg-emerald-500 rounded-full inline-block"></span>
                        Executive Financial Ratios
                    </h2>
                    {ratios && (
                        <div className="flex items-center gap-3 bg-white dark:bg-slate-900 px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm">
                            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Overall Health</span>
                            <span className={`text-xl font-bold ${healthColor(ratios.overall_health_score)}`}>
                                {ratios.overall_health_score}/100
                            </span>
                            <span className="text-sm font-medium text-slate-700 dark:text-slate-300 ml-2 border-l border-slate-200 dark:border-slate-700 pl-3 block">{ratios.health_rating}</span>
                        </div>
                    )}
                </div>

                {ratios ? (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                        {/* Summary Radar Chart */}
                        <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 lg:col-span-1 flex flex-col items-center">
                            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 w-full mb-2">Performance Spider</h3>
                            <div className="h-64 w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <RadarChart cx="50%" cy="50%" outerRadius="70%" data={[
                                        { subject: 'Liquidity', A: Math.min(ratios.liquidity.current_ratio * 30, 100) },
                                        { subject: 'Profitability', A: Math.min(ratios.profitability.ebitda_margin * 2, 100) },
                                        { subject: 'Efficiency', A: Math.min(ratios.efficiency.asset_turnover * 50, 100) },
                                        { subject: 'Cash Flow', A: Math.min(ratios.cash_flow.ocf_to_net_income * 50, 100) },
                                        { subject: 'Solvency (Inv)', A: Math.max(100 - (ratios.leverage.debt_to_equity * 20), 0) },
                                    ]}>
                                        <PolarGrid stroke="#334155" opacity={0.2} />
                                        <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 10 }} />
                                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                                        <Radar name="Target Company" dataKey="A" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
                                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff' }} />
                                    </RadarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Ratio Grids */}
                        <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Liquidity */}
                            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-5">
                                <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4 border-b border-slate-100 dark:border-slate-800 pb-2">Liquidity</h3>
                                <div className="space-y-3">
                                    <RatioRow label="Current Ratio" value={ratios.liquidity.current_ratio} fmt={formatNumber} indicator={dot(ratios.liquidity.current_ratio >= 1.5, ratios.liquidity.current_ratio >= 1.0)} />
                                    <RatioRow label="Quick Ratio" value={ratios.liquidity.quick_ratio} fmt={formatNumber} indicator={dot(ratios.liquidity.quick_ratio >= 1.0, ratios.liquidity.quick_ratio >= 0.5)} />
                                    <RatioRow label="Cash Ratio" value={ratios.liquidity.cash_ratio} fmt={formatNumber} indicator={dot(ratios.liquidity.cash_ratio >= 0.5, ratios.liquidity.cash_ratio >= 0.2)} />
                                </div>
                            </div>

                            {/* Profitability */}
                            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-5">
                                <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4 border-b border-slate-100 dark:border-slate-800 pb-2">Profitability</h3>
                                <div className="space-y-3">
                                    <RatioRow label="Gross Margin" value={ratios.profitability.gross_margin} fmt={(v) => formatPercent(v)} indicator={dot(ratios.profitability.gross_margin >= 40, ratios.profitability.gross_margin >= 20)} />
                                    <RatioRow label="EBITDA Margin" value={ratios.profitability.ebitda_margin} fmt={(v) => formatPercent(v)} indicator={dot(ratios.profitability.ebitda_margin >= 20, ratios.profitability.ebitda_margin >= 10)} />
                                    <RatioRow label="Net Margin" value={ratios.profitability.net_margin} fmt={(v) => formatPercent(v)} indicator={dot(ratios.profitability.net_margin >= 10, ratios.profitability.net_margin >= 0)} />
                                </div>
                            </div>

                            {/* Leverage */}
                            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-5">
                                <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4 border-b border-slate-100 dark:border-slate-800 pb-2">Leverage & Coverage</h3>
                                <div className="space-y-3">
                                    <RatioRow label="Debt/Equity" value={ratios.leverage.debt_to_equity} fmt={formatNumber} indicator={dot(ratios.leverage.debt_to_equity <= 1.5, ratios.leverage.debt_to_equity <= 3.0)} />
                                    <RatioRow label="Debt/EBITDA" value={ratios.leverage.debt_to_ebitda} fmt={(v) => `${formatNumber(v)}x`} indicator={dot(ratios.leverage.debt_to_ebitda <= 2, ratios.leverage.debt_to_ebitda <= 4)} />
                                    <RatioRow label="Interest Coverage" value={ratios.leverage.interest_coverage} fmt={(v) => `${formatNumber(v)}x`} indicator={dot(ratios.leverage.interest_coverage >= 5, ratios.leverage.interest_coverage >= 2)} />
                                </div>
                            </div>

                            {/* Efficiency + Cash Flow */}
                            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-5">
                                <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4 border-b border-slate-100 dark:border-slate-800 pb-2">Efficiency & Cash Flow</h3>
                                <div className="space-y-3">
                                    <RatioRow label="Asset Turnover" value={ratios.efficiency.asset_turnover} fmt={(v) => `${formatNumber(v)}x`} indicator={dot(ratios.efficiency.asset_turnover >= 1.0, ratios.efficiency.asset_turnover >= 0.5)} />
                                    <RatioRow label="OCF/Net Income" value={ratios.cash_flow.ocf_to_net_income} fmt={(v) => `${formatNumber(v)}x`} indicator={dot(ratios.cash_flow.ocf_to_net_income >= 1.0, ratios.cash_flow.ocf_to_net_income >= 0.5)} />
                                    <RatioRow label="FCF Margin" value={ratios.cash_flow.fcf_margin} fmt={(v) => formatPercent(v)} indicator={dot(ratios.cash_flow.fcf_margin >= 10, ratios.cash_flow.fcf_margin >= 0)} />
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-slate-400">No ratio data available.</div>
                )}
            </div>
        </div>
    );
}

function RatioRow({ label, value, fmt, indicator }: { label: string; value: number; fmt: (v: number) => string; indicator: string }) {
    return (
        <div className="flex items-center justify-between group">
            <span className="text-sm text-slate-600 dark:text-slate-400 font-medium">{label}</span>
            <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-slate-900 dark:text-slate-100 font-mono">{fmt(value)}</span>
                <span className="text-xs" title="Benchmark Performance">{indicator}</span>
            </div>
        </div>
    );
}
