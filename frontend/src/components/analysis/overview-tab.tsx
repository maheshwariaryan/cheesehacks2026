"use client";

import { DealDetail, AIInsights, QoEResults, WorkingCapitalResults, RatioResults } from "@/lib/types";
import { formatCompactCurrency, formatPercent } from "@/lib/utils";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, BarChart, Bar, Legend, Tooltip } from "recharts";
import { Download, LogOut, ChevronDown } from "lucide-react";

interface Props {
    deal: DealDetail;
    insights: AIInsights | null;
    qoe: QoEResults | null;
    wc: WorkingCapitalResults | null;
    ratios: RatioResults | null;
}

export default function OverviewTab({ deal, insights, qoe, wc, ratios }: Props) {
    // Generate dummy trend data for charts
    const trendData = [
        { month: 'Jan', rev: 4.8, ebitda: 1.1 },
        { month: 'Feb', rev: 4.9, ebitda: 1.05 },
        { month: 'Mar', rev: 5.1, ebitda: 1.2 },
        { month: 'Apr', rev: 5.4, ebitda: 1.4 },
        { month: 'May', rev: 5.3, ebitda: 1.3 },
        { month: 'Jun', rev: 5.6, ebitda: 1.5 },
    ];

    const bridgeData = [
        { name: 'Reported', value: 12.2, fill: '#0d9488' },
        { name: 'Adj 1', value: 0.8, fill: '#f59e0b' },
        { name: 'Adj 2', value: 0.4, fill: '#ef4444' },
        { name: 'Adjusted', value: 13.4, fill: '#0d9488' },
    ];

    const formatM = (v: number) => `$${(v / 1_000_000).toFixed(1)}M`;
    const formatB = (v: number) => `$${(v / 1_000_000_000).toFixed(1)}B`;
    const fv = (v: number) => v > 1000000000 ? formatB(v) : formatM(v);

    const rev = (qoe && qoe.ebitda_margin && qoe.ebitda_margin > 0) ? (qoe.reported_ebitda / (qoe.ebitda_margin / 100)) : 63700000;
    const repEbitda = qoe?.reported_ebitda || 12200000;
    const adjEbitda = qoe?.adjusted_ebitda || 13400000;

    return (
        <div className="space-y-6 pb-20 fade-in animate-in">
            {/* Top Toolbar */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                <div className="text-sm font-medium text-slate-500">Analyst Workspace</div>
                <div className="flex items-center gap-3">
                    <button className="flex items-center gap-2 px-3 py-1.5 border border-slate-200 rounded-md text-sm text-slate-700 bg-white shadow-sm hover:bg-slate-50">
                        {deal.name || "Project Atlas"} <ChevronDown className="h-4 w-4 text-slate-400" />
                    </button>
                    <button className="flex items-center gap-2 px-3 py-1.5 border border-slate-200 rounded-md text-sm text-slate-700 bg-white shadow-sm hover:bg-slate-50">
                        Annual <ChevronDown className="h-4 w-4 text-slate-400" />
                    </button>
                    <button className="flex items-center gap-2 px-3 py-1.5 border border-slate-200 rounded-md text-sm text-slate-700 bg-white shadow-sm hover:bg-slate-50">
                        Normalized <ChevronDown className="h-4 w-4 text-slate-400" />
                    </button>
                    <button className="flex items-center gap-2 px-4 py-1.5 bg-[#1a4a8c] hover:bg-[#153a70] text-white rounded-md text-sm font-medium shadow-sm transition-colors">
                        Export Pack
                    </button>
                    <button className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-600 hover:text-slate-900 transition-colors">
                        <LogOut className="h-4 w-4" /> Sign out
                    </button>
                </div>
            </div>

            <div className="flex items-center justify-between">
                <h2 className="text-xl font-medium text-slate-800 tracking-tight">Executive Overview</h2>
                <div className="text-xs text-slate-400">Last refresh: {new Date().toLocaleDateString()} {new Date().toLocaleTimeString()}</div>
            </div>

            {/* Metric Grid matching Image 4 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard title="REVENUE (LTM)" value={fv(rev)} sub="vs last run: +4.1%" />
                <MetricCard title="REPORTED EBITDA (LTM)" value={fv(repEbitda)} sub="vs last run: +2.6%" />
                <MetricCard title="ADJUSTED EBITDA (LTM)" value={fv(adjEbitda)} sub="vs last run: +3.9%" />
                <MetricCard title="ADJUSTMENTS AS % OF EBITDA" value="9.8%" sub="vs last run: +0.6ppt" badge="Amber" />

                <MetricCard title="AVG NWC (LTM)" value={fv(wc?.net_working_capital || 6100000)} sub="vs last run: +2.1%" />
                <MetricCard title="PROPOSED NWC PEG" value="$6.3M" sub="vs last run: +$0.2M" />
                <MetricCard title="EBITDA -> OPERATING CASH FLOW CONVERSION %" value="52%" sub="vs last run: +3ppt" badge="Amber" />
                <MetricCard title="OVERALL DEAL RISK" value={`${ratios?.overall_health_score ? (10 - ratios.overall_health_score / 10).toFixed(1) : "6.2"} / 10`} sub="vs last run: -0.4" badge="Amber" />

                <MetricCard title="REVENUE GROWTH % (YOY / QOQ)" value="8.4% / 2.1%" sub="vs last run: +0.7ppt" />
                <MetricCard title="EBITDA MARGIN (REPORTED VS ADJUSTED)" value={`${formatPercent(qoe?.ebitda_margin || 19.2)} / ${formatPercent(qoe?.adjusted_ebitda_margin || 21.0)}`} sub="vs last run: +0.4ppt" />
                <MetricCard title="NORMALIZED EARNINGS" value="$13.1M" sub="vs last run: +$0.2M" />
                <MetricCard title="RUN-RATE EARNINGS" value="$13.1M" sub="vs last run: -$0.1M" />

                <MetricCard title="NWC AS % OF REVENUE" value={formatPercent(wc?.nwc_as_pct_revenue || 9.6)} sub="vs last run: +0.2ppt" />
                <MetricCard title="KEY RISK ADJUSTMENTS IMPACT" value="5.4%" sub="vs last run: +0.1ppt" badge="Amber" />
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-4">
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                    <h3 className="text-sm font-semibold text-slate-700 mb-6">Revenue & Adjusted EBITDA trend</h3>
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={trendData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                                <YAxis tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                                <Line type="monotone" dataKey="rev" stroke="#0ea5e9" strokeWidth={2} dot={false} name="Revenue" />
                                <Line type="monotone" dataKey="ebitda" stroke="#1a4a8c" strokeWidth={2} dot={false} name="Adj EBITDA" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                    <h3 className="text-sm font-semibold text-slate-700 mb-6">Reported EBITDA Bridge/Waterfall (Reported → adjustments → Adjusted)</h3>
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={bridgeData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                                <YAxis tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                                <Bar dataKey="value" radius={[2, 2, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
}

function MetricCard({ title, value, sub, badge }: { title: string, value: string, sub: string, badge?: string }) {
    return (
        <div className="bg-white rounded-xl shadow-[0_1px_3px_rgba(0,0,0,0.05)] border border-slate-200/80 p-5 flex flex-col justify-between">
            <h3 className="text-[10px] font-semibold text-slate-500 tracking-wider mb-2 leading-tight uppercase relative pr-10">{title}</h3>
            <div>
                <div className="text-2xl font-bold text-slate-800 tracking-tight">{value}</div>
                <div className="flex items-center justify-between mt-1">
                    <span className="text-xs text-slate-400">{sub}</span>
                    {badge && (
                        <span className="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded font-medium">
                            {badge}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}
