"use client";

import { useState, useEffect } from "react";
import { generateReport, getReports, getReportDownloadUrl } from "@/lib/api";
import { Report } from "@/lib/types";
import { FileText, Download, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { timeSince } from "@/lib/utils";

interface Props { dealId: number; }

const REPORT_TYPES = [
    { type: "iar" as const, label: "IAR Report", icon: "📄" },
    { type: "dcf" as const, label: "DCF Report", icon: "📊" },
    { type: "red_flag" as const, label: "Red Flag Report", icon: "🚩" },
];

export default function ReportPanel({ dealId }: Props) {
    const [reports, setReports] = useState<Report[]>([]);
    const [generating, setGenerating] = useState<Record<string, boolean>>({});

    useEffect(() => {
        getReports(dealId).then(({ reports }) => setReports(reports)).catch(() => { });
    }, [dealId]);

    const handleGenerate = async (type: "iar" | "dcf" | "red_flag") => {
        setGenerating((prev) => ({ ...prev, [type]: true }));
        try {
            await generateReport(dealId, type);
            // Refresh reports list after a short delay
            setTimeout(async () => {
                try {
                    const { reports } = await getReports(dealId);
                    setReports(reports);
                } catch { /* ignore */ }
                setGenerating((prev) => ({ ...prev, [type]: false }));
            }, 3000);
        } catch {
            setGenerating((prev) => ({ ...prev, [type]: false }));
        }
    };

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-4">
            <h3 className="text-sm font-semibold text-slate-800">Report Generation</h3>

            <div className="flex gap-3">
                {REPORT_TYPES.map((rt) => (
                    <Button
                        key={rt.type}
                        variant="outline"
                        size="sm"
                        onClick={() => handleGenerate(rt.type)}
                        disabled={generating[rt.type]}
                        className="flex items-center gap-2"
                    >
                        {generating[rt.type] ? <Loader2 className="h-4 w-4 animate-spin" /> : <span>{rt.icon}</span>}
                        {rt.label}
                    </Button>
                ))}
            </div>

            {reports.length > 0 && (
                <div className="space-y-2 pt-2">
                    <p className="text-xs uppercase tracking-wide text-slate-400">Generated Reports</p>
                    {reports.map((report) => (
                        <div key={report.id} className="flex items-center justify-between py-2 px-3 bg-slate-50 rounded-lg">
                            <div className="flex items-center gap-2">
                                <FileText className="h-4 w-4 text-slate-400" />
                                <span className="text-sm font-medium text-slate-700">{report.report_type.toUpperCase()} Report</span>
                                <span className="text-xs text-slate-400">{timeSince(report.generated_at)}</span>
                            </div>
                            <a
                                href={getReportDownloadUrl(report.id)}
                                download={`${report.report_type}_report.pdf`}
                                className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
                            >
                                <Download className="h-3 w-3" /> Download
                            </a>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
