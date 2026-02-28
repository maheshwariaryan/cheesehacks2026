"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getDeals, getAnalysis } from "@/lib/api";
import { Deal, AIInsights } from "@/lib/types";
import { formatCompactCurrency, timeSince, riskBadgeColor } from "@/lib/utils";
import { Briefcase, FileText, BarChart3, Heart, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  const router = useRouter();
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);
  const [avgScore, setAvgScore] = useState<number | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const { deals: d } = await getDeals();
        setDeals(d);

        // Compute average health score
        const completed = d.filter((deal) => deal.status === "completed");
        const scores: number[] = [];
        for (const deal of completed) {
          try {
            const analysis = await getAnalysis(deal.id, "ratios");
            if (analysis?.results?.overall_health_score) {
              scores.push(analysis.results.overall_health_score);
            }
          } catch { /* skip */ }
        }
        if (scores.length > 0) {
          setAvgScore(Math.round(scores.reduce((a, b) => a + b, 0) / scores.length));
        }
      } catch { /* ignore */ }
      setLoading(false);
    }
    load();
  }, []);

  const totalDocs = deals.reduce((sum, d) => sum + d.document_count, 0);
  const totalAnalyses = deals.reduce((sum, d) => sum + d.analysis_count, 0);

  const stats = [
    { label: "Total Deals", value: deals.length, icon: Briefcase, color: "bg-blue-100 text-blue-600" },
    { label: "Documents", value: totalDocs, icon: FileText, color: "bg-purple-100 text-purple-600" },
    { label: "Analyses", value: totalAnalyses, icon: BarChart3, color: "bg-emerald-100 text-emerald-600" },
    { label: "Avg Health", value: avgScore ?? "—", icon: Heart, color: "bg-rose-100 text-rose-600" },
  ];

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Financial Due Diligence Dashboard</h1>
        <div className="grid grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 animate-pulse">
              <div className="h-10 w-10 rounded-full bg-slate-200 mb-4" />
              <div className="h-8 w-16 bg-slate-200 rounded mb-2" />
              <div className="h-4 w-24 bg-slate-100 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-900">Financial Due Diligence Dashboard</h1>

      <div className="grid grid-cols-4 gap-6">
        {stats.map((s) => (
          <div key={s.label} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <div className={`h-10 w-10 rounded-full ${s.color} flex items-center justify-center mb-4`}>
              <s.icon className="h-5 w-5" />
            </div>
            <p className="text-3xl font-bold text-slate-900">{s.value}</p>
            <p className="text-sm text-slate-500 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200">
        <div className="p-6 flex items-center justify-between border-b border-slate-100">
          <h2 className="text-lg font-semibold text-slate-800">Recent Deals</h2>
          <Button onClick={() => router.push("/upload")} size="sm">
            <Plus className="h-4 w-4 mr-1" /> New Deal
          </Button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left">
                <th className="px-6 py-3 text-xs uppercase tracking-wide text-slate-400 font-medium">Name</th>
                <th className="px-6 py-3 text-xs uppercase tracking-wide text-slate-400 font-medium">Target</th>
                <th className="px-6 py-3 text-xs uppercase tracking-wide text-slate-400 font-medium">Size</th>
                <th className="px-6 py-3 text-xs uppercase tracking-wide text-slate-400 font-medium">Status</th>
                <th className="px-6 py-3 text-xs uppercase tracking-wide text-slate-400 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {deals.map((deal) => (
                <tr
                  key={deal.id}
                  onClick={() => router.push(`/deals/${deal.id}`)}
                  className="border-b border-slate-50 hover:bg-slate-50 cursor-pointer transition-colors"
                >
                  <td className="px-6 py-4 font-medium text-slate-900">{deal.name}</td>
                  <td className="px-6 py-4 text-slate-600">{deal.target_company}</td>
                  <td className="px-6 py-4 text-slate-600">{deal.deal_size ? formatCompactCurrency(deal.deal_size) : "—"}</td>
                  <td className="px-6 py-4">
                    <StatusBadge status={deal.status} />
                  </td>
                  <td className="px-6 py-4 text-slate-500">{timeSince(deal.created_at)}</td>
                </tr>
              ))}
              {deals.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-slate-400">
                    No deals yet.{" "}
                    <Link href="/upload" className="text-blue-600 hover:underline">
                      Upload your first financial documents
                    </Link>
                    .
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "bg-emerald-100 text-emerald-700",
    analyzing: "bg-amber-100 text-amber-700 animate-pulse",
    pending: "bg-slate-100 text-slate-600",
    failed: "bg-red-100 text-red-700",
  };
  const labels: Record<string, string> = {
    completed: "Completed",
    analyzing: "Analyzing",
    pending: "Pending",
    failed: "Failed",
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.pending}`}>
      {labels[status] || status}
    </span>
  );
}
