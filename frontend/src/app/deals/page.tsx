"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getDeals, deleteDeal } from "@/lib/api";
import { Deal } from "@/lib/types";
import { formatCompactCurrency, timeSince } from "@/lib/utils";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function DealsPage() {
    const router = useRouter();
    const [deals, setDeals] = useState<Deal[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getDeals().then(({ deals }) => { setDeals(deals); setLoading(false); }).catch(() => setLoading(false));
    }, []);

    const handleDelete = async (id: number) => {
        if (!window.confirm("Are you sure you want to delete this deal? This action cannot be undone.")) return;
        try {
            await deleteDeal(id);
            setDeals(deals.filter(d => d.id !== id));
        } catch (error) {
            console.error(error);
            alert("Failed to delete deal");
        }
    };

    if (loading) {
        return (
            <div className="space-y-6">
                <h1 className="text-2xl font-bold text-slate-900">All Deals</h1>
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 animate-pulse space-y-4">
                    {[1, 2, 3].map((i) => <div key={i} className="h-12 bg-slate-100 rounded" />)}
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-slate-900">All Deals</h1>
                <Button onClick={() => router.push("/upload")} size="sm">
                    <Plus className="h-4 w-4 mr-1" /> New Deal
                </Button>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-slate-100 text-left bg-slate-50">
                            <th className="px-6 py-3 text-xs uppercase tracking-wide text-slate-400 font-medium">Name</th>
                            <th className="px-6 py-3 text-xs uppercase tracking-wide text-slate-400 font-medium">Target</th>
                            <th className="px-6 py-3 text-xs uppercase tracking-wide text-slate-400 font-medium">Industry</th>
                            <th className="px-6 py-3 text-xs uppercase tracking-wide text-slate-400 font-medium">Size</th>
                            <th className="px-6 py-3 text-xs uppercase tracking-wide text-slate-400 font-medium">Docs</th>
                            <th className="px-6 py-3 text-xs uppercase tracking-wide text-slate-400 font-medium">Status</th>
                            <th className="px-6 py-3 text-xs uppercase tracking-wide text-slate-400 font-medium">Created</th>
                            <th className="px-6 py-3 text-right text-xs uppercase tracking-wide text-slate-400 font-medium">Actions</th>
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
                                <td className="px-6 py-4 text-slate-600">{deal.industry || "—"}</td>
                                <td className="px-6 py-4 text-slate-600">{deal.deal_size ? formatCompactCurrency(deal.deal_size) : "—"}</td>
                                <td className="px-6 py-4 text-slate-600">{deal.document_count}</td>
                                <td className="px-6 py-4">
                                    <StatusBadge status={deal.status} />
                                </td>
                                <td className="px-6 py-4 text-slate-500">{timeSince(deal.created_at)}</td>
                                <td className="px-6 py-4 text-right">
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDelete(deal.id);
                                        }}
                                        className="text-slate-400 hover:text-red-500 transition-colors p-1"
                                        title="Delete Deal"
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {deals.length === 0 && (
                            <tr>
                                <td colSpan={8} className="px-6 py-16 text-center">
                                    <p className="text-slate-400 mb-2">No deals yet.</p>
                                    <Link href="/upload" className="text-blue-600 hover:underline text-sm">
                                        Upload your first financial documents to get started.
                                    </Link>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
                {deals.length > 0 && (
                    <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 text-xs text-slate-400">
                        Showing {deals.length} deal{deals.length !== 1 ? "s" : ""}
                    </div>
                )}
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
    return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.pending}`}>
            {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
    );
}
