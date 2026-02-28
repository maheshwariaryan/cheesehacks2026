"use client";

import { RedFlag, Anomaly } from "@/lib/types";
import { severityColor, formatNumber } from "@/lib/utils";

interface Props { redFlags: RedFlag[] | null; anomalies: Anomaly[] | null; }

export default function RedFlagsTab({ redFlags, anomalies }: Props) {
    const flags = redFlags || [];
    const anoms = anomalies || [];

    const highCount = flags.filter((f) => f.severity === "high").length;
    const medCount = flags.filter((f) => f.severity === "medium").length;
    const lowCount = flags.filter((f) => f.severity === "low").length;

    return (
        <div className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-800">Red Flags & Anomaly Detection</h2>

            {/* Summary Bar */}
            <div className="flex items-center gap-4">
                {highCount > 0 && (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-100 text-red-700 text-sm font-medium">
                        🔴 {highCount} High
                    </span>
                )}
                {medCount > 0 && (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-100 text-amber-700 text-sm font-medium">
                        🟡 {medCount} Medium
                    </span>
                )}
                {lowCount > 0 && (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm font-medium">
                        🔵 {lowCount} Low
                    </span>
                )}
                {flags.length === 0 && <span className="text-sm text-slate-400">No red flags detected</span>}
            </div>

            {/* Red Flags */}
            {flags.length > 0 && (
                <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-slate-700">Red Flags</h3>
                    {flags.map((flag, i) => (
                        <div key={i} className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                            <div className="flex items-start gap-3">
                                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold uppercase ${severityColor(flag.severity)}`}>
                                    {flag.severity}
                                </span>
                                <div className="flex-1">
                                    <p className="text-sm font-semibold text-slate-800">{flag.flag}</p>
                                    <p className="text-sm text-slate-600 mt-1">{flag.description}</p>
                                    <p className="text-xs text-slate-400 mt-2">
                                        Metric: {formatNumber(flag.value)} / Threshold: {flag.threshold}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Anomalies */}
            {anoms.length > 0 && (
                <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-slate-700">ML Anomaly Detection</h3>
                    {anoms.map((anom, i) => (
                        <div key={i} className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                            <div className="flex items-start gap-3">
                                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold uppercase ${severityColor(anom.severity)}`}>
                                    {anom.severity}
                                </span>
                                <div className="flex-1">
                                    <div className="flex items-center gap-2">
                                        <p className="text-sm font-semibold text-slate-800">{anom.anomaly}</p>
                                        <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                                            {anom.category === "statistical" ? "Statistical" : "Rule-based"}
                                        </span>
                                    </div>
                                    <p className="text-sm text-slate-600 mt-1">{anom.description}</p>
                                    <p className="text-xs text-slate-400 mt-2">
                                        Value: {formatNumber(anom.value)} · Expected: {anom.expected_range}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {flags.length === 0 && anoms.length === 0 && (
                <div className="text-center py-12 text-slate-400">
                    No red flags or anomalies detected. The financial data appears clean.
                </div>
            )}
        </div>
    );
}
