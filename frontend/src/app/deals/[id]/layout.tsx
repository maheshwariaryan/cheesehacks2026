"use client";

import { useEffect, useState, use, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { getDeal, getAnalyses } from "@/lib/api";
import { DealDetail, Analysis } from "@/lib/types";
import { DealProvider } from "@/lib/deal-context";
import { formatCompactCurrency, timeSince, riskBadgeColor } from "@/lib/utils";
import { ArrowLeft, Loader2, LayoutDashboard, FileText, TrendingUp, BarChart3, Calculator, AlertTriangle, Brain, MessageSquare } from "lucide-react";
import ReportPanel from "@/components/reports/report-panel";

const DEAL_NAV = [
    { href: "overview", label: "Overview", icon: LayoutDashboard },
    { href: "documents", label: "Documents", icon: FileText },
    { href: "qoe", label: "QoE", icon: TrendingUp },
    { href: "financials", label: "Financials", icon: BarChart3 },
    { href: "dcf", label: "DCF", icon: Calculator },
    { href: "red-flags", label: "Red Flags", icon: AlertTriangle },
    { href: "insights", label: "Insights", icon: Brain },
    { href: "chat", label: "Chat", icon: MessageSquare },
];

export default function DealLayout({ children, params }: { children: React.ReactNode; params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const dealId = parseInt(id);
    const pathname = usePathname();
    const [deal, setDeal] = useState<DealDetail | null>(null);
    const [analyses, setAnalyses] = useState<Analysis[]>([]);
    const [loading, setLoading] = useState(true);

    const loadData = useCallback(async () => {
        try {
            const d = await getDeal(dealId);
            setDeal(d);
            if (d.status === "completed") {
                const { analyses: a } = await getAnalyses(dealId);
                setAnalyses(a);
            }
            setLoading(false);
        } catch {
            setLoading(false);
        }
    }, [dealId]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    // Poll while analyzing
    useEffect(() => {
        if (!deal || deal.status !== "analyzing") return;
        const interval = setInterval(async () => {
            try {
                const updated = await getDeal(dealId);
                setDeal(updated);
                if (updated.status === "completed") {
                    const { analyses: a } = await getAnalyses(dealId);
                    setAnalyses(a);
                    clearInterval(interval);
                } else if (updated.status === "failed") {
                    clearInterval(interval);
                }
            } catch { /* continue polling */ }
        }, 3000);
        return () => clearInterval(interval);
    }, [deal?.status, dealId]);

    const getResults = (type: string) => {
        const a = analyses.find((x) => x.analysis_type === type);
        return (a?.results as Record<string, unknown>) || null;
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-24">
                <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
            </div>
        );
    }

    if (!deal) {
        return <div className="text-center py-24 text-slate-400">Deal not found.</div>;
    }

    if (deal.status === "analyzing") {
        return (
            <div className="space-y-6">
                <Link href="/deals" className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800">
                    <ArrowLeft className="h-4 w-4" /> Back to Deals
                </Link>
                <div className="flex flex-col items-center justify-center py-24 space-y-4">
                    <Loader2 className="h-12 w-12 text-blue-600 animate-spin" />
                    <p className="text-lg font-medium text-slate-700">Analysis in progress...</p>
                    <p className="text-sm text-slate-400">This may take a minute. The page will update automatically.</p>
                </div>
            </div>
        );
    }

    const riskLevel = (getResults("ai_insights") as { risk_assessment?: { overall_risk?: string } })?.risk_assessment?.overall_risk;
    const activeSegment = pathname.split("/").pop() || "overview";

    return (
        <div className="space-y-6">
            {/* Back link */}
            <Link href="/deals" className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800">
                <ArrowLeft className="h-4 w-4" /> Back to Deals
            </Link>

            {/* Header */}
            <div>
                <div className="flex items-center gap-3">
                    <h1 className="text-2xl font-bold text-slate-900">{deal.name}</h1>
                    {riskLevel && (
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${riskBadgeColor(riskLevel)}`}>
                            {riskLevel.toUpperCase()} RISK
                        </span>
                    )}
                </div>
                <p className="text-sm text-slate-500 mt-1">
                    Target: {deal.target_company}
                    {deal.industry && ` · ${deal.industry}`}
                    {deal.deal_size && ` · ${formatCompactCurrency(deal.deal_size)}`}
                    {` · Created ${timeSince(deal.created_at)}`}
                </p>
            </div>

            {/* Sub-navigation */}
            <nav className="flex items-center gap-1 bg-white border border-slate-200 rounded-xl p-1.5">
                {DEAL_NAV.map((item) => {
                    const isActive = activeSegment === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={`/deals/${id}/${item.href}`}
                            className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${isActive
                                ? "bg-slate-900 text-white shadow-sm"
                                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                                }`}
                        >
                            <item.icon className="h-4 w-4" />
                            {item.label}
                        </Link>
                    );
                })}
            </nav>

            {/* Content */}
            <DealProvider value={{ deal, analyses, getResults }}>
                {children}
            </DealProvider>

            {/* Report Section */}
            <ReportPanel dealId={dealId} />
        </div>
    );
}
