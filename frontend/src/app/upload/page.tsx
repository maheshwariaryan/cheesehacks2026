"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createDeal, uploadDocuments, triggerAnalysis, getDeal } from "@/lib/api";
import { Upload, Archive, Database, BarChart3, ShieldCheck, Sparkles } from "lucide-react";

export default function UploadPage() {
    const router = useRouter();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [files, setFiles] = useState<File[]>([]);
    const [dragOver, setDragOver] = useState(false);
    const [status, setStatus] = useState<"idle" | "creating" | "uploading" | "analyzing" | "done" | "failed">("idle");
    const [statusText, setStatusText] = useState("");

    const handleFiles = useCallback((newFiles: FileList | File[]) => {
        const arr = Array.from(newFiles);
        setFiles((prev) => [...prev, ...arr]);
    }, []);

    const handleSubmit = async () => {
        if (files.length === 0) return;

        try {
            setStatus("creating");
            setStatusText("Provisioning environment...");

            // Hardcode standard deal data to seamlessly match the sleek demo flow
            const deal = await createDeal({
                name: "Project Atlas",
                target_company: "Apex Cloud Solutions",
                industry: "Technology",
                deal_size: 65000000,
            });

            setStatus("uploading");
            setStatusText("Uploading components...");
            await uploadDocuments(deal.id, files);

            setStatus("analyzing");
            setStatusText("Mapping chart of accounts...");
            await triggerAnalysis(deal.id);

            let cycles = 0;
            const msgs = [
                "Reconciling tie-outs across TB, GL, and schedules...",
                "Running anomaly detection and risk scoring...",
                "Constructing QoE and cash conversion models...",
                "Generating insights and presentation layer..."
            ];

            const pollInterval = setInterval(async () => {
                if (cycles < msgs.length) {
                    setStatusText(msgs[cycles]);
                    cycles++;
                }

                try {
                    const updated = await getDeal(deal.id);
                    if (updated.status === "completed") {
                        clearInterval(pollInterval);
                        setStatus("done");
                        setStatusText("Analysis Complete");
                        setTimeout(() => router.push(`/deals/${deal.id}`), 1500);
                    } else if (updated.status === "failed") {
                        clearInterval(pollInterval);
                        setStatus("failed");
                        setStatusText("System Failure.");
                    }
                } catch {
                    // Ignore transient errors
                }
            }, 3000);
        } catch (err) {
            setStatus("failed");
            setStatusText("Error initializing engine.");
        }
    };

    const isProcessing = status !== "idle" && status !== "failed";

    if (isProcessing) {
        return (
            <div className="flex-1 flex items-center justify-center p-4">
                <div className="max-w-4xl w-full bg-[#111827]/90 backdrop-blur-xl rounded-2xl border border-slate-800 shadow-[0_0_50px_rgba(45,212,191,0.1)] p-10">
                    <div className="space-y-2 mb-8">
                        <p className="text-xs font-semibold tracking-[0.2em] text-[#2DD4BF] uppercase">TAM Neural Analysis Engine</p>
                        <h2 className="text-3xl font-medium text-white tracking-tight">Building your due diligence intelligence stack</h2>
                    </div>

                    <div className="h-3 w-full bg-slate-800/50 rounded-full overflow-hidden mb-10">
                        <div
                            className="h-full bg-gradient-to-r from-[#2DD4BF] to-[#38BDF8] rounded-full transition-all duration-1000 ease-out relative"
                            style={{
                                width: status === "creating" ? "15%" : status === "uploading" ? "30%" : status === "analyzing" ? "75%" : "100%"
                            }}
                        >
                            <div className="absolute top-0 bottom-0 left-0 right-0 bg-white/20 animate-pulse" />
                        </div>
                    </div>

                    <div className="grid grid-cols-5 gap-4 mb-8">
                        {[
                            { title: "Mapping chart of accounts...", active: statusText.includes("Mapping") },
                            { title: "Reconciling tie-outs across TB, GL, and schedules...", active: statusText.includes("Reconciling") },
                            { title: "Running anomaly detection and risk scoring...", active: statusText.includes("anomaly") },
                            { title: "Constructing QoE and cash conversion models...", active: statusText.includes("Constructing") },
                            { title: "Generating insights and presentation layer...", active: statusText.includes("Generating") || status === "done" },
                        ].map((step, i) => (
                            <div
                                key={i}
                                className={`p-4 rounded-xl border ${step.active ? 'bg-[#1e293b]/80 border-[#2DD4BF] shadow-[0_0_15px_rgba(45,212,191,0.15)]' : 'bg-[#0f172a]/50 border-slate-800/50'} transition-all duration-500`}
                            >
                                <p className={`text-sm ${step.active ? 'text-white font-medium' : 'text-slate-400'}`}>
                                    {step.title}
                                </p>
                            </div>
                        ))}
                    </div>

                    <div className="mt-8 border-t border-slate-800/50 pt-6">
                        <p className="text-[#38BDF8] text-sm font-medium">{statusText}</p>
                        <p className="text-slate-500 text-sm mt-1">Please stay on this screen. You will be redirected to the dashboard once analysis is complete.</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-[1400px] w-full mx-auto p-4 sm:p-8 space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="bg-[#111827]/60 backdrop-blur-md rounded-2xl border border-slate-800/60 p-8 pt-10 pb-12 shadow-2xl">
                <p className="text-xs font-semibold tracking-widest text-slate-400 uppercase mb-3">TAM Intake Workspace</p>
                <h1 className="text-3xl font-medium text-white tracking-tight mb-4">Upload deal documents and launch analysis</h1>
                <p className="text-slate-400 text-sm max-w-3xl leading-relaxed">
                    Upload your files first. TAM will parse and map them, build due diligence metrics, run tie-out and anomaly checks, then bring you into the full analyst dashboard.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column - Upload Box */}
                <div className="lg:col-span-2 bg-white rounded-2xl shadow-[0_0_40px_rgba(255,255,255,0.05)] border border-slate-200 p-2 sm:p-8 flex flex-col h-[500px]">
                    <h2 className="text-slate-800 font-medium mb-6 px-2">Upload Documents</h2>
                    <div
                        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                        onDragLeave={() => setDragOver(false)}
                        onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
                        className={`flex-1 border-2 border-dashed rounded-xl flex flex-col items-center justify-center transition-all ${dragOver ? "border-blue-500 bg-blue-50 scale-[1.01]" : "border-slate-300 hover:border-blue-400 hover:bg-slate-50"}`}
                    >
                        <Upload className="h-10 w-10 text-slate-400 mb-4" />
                        <p className="text-slate-800 font-medium mb-1">Drag and drop files here</p>
                        <p className="text-slate-500 text-sm mb-6">or choose files from your computer (.xlsx, .csv, .pdf)</p>
                        <button
                            onClick={() => fileInputRef.current?.click()}
                            className="px-6 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-full transition-colors"
                        >
                            Select files
                        </button>
                        <input
                            ref={fileInputRef}
                            type="file"
                            multiple
                            accept=".pdf,.xlsx,.xls,.csv,.docx,.doc,.txt,.png,.jpg,.jpeg"
                            className="hidden"
                            onChange={(e) => e.target.files && handleFiles(e.target.files)}
                        />
                    </div>
                </div>

                {/* Right Column - Info & Status */}
                <div className="flex flex-col gap-6 h-[500px]">
                    <div className="flex-1 bg-[#111827]/80 backdrop-blur-md rounded-2xl border border-slate-800 shadow-[0_0_30px_rgba(0,0,0,0.5)] p-6 overflow-y-auto">
                        <div className="flex items-center gap-2 mb-6 text-[#2DD4BF]">
                            <Sparkles className="h-4 w-4" />
                            <h2 className="font-semibold text-sm tracking-wide">TAM Walkthrough</h2>
                        </div>

                        <div className="space-y-4">
                            {[
                                { icon: Archive, title: "Document Intelligence", desc: "TAM classifies schedules, coverage periods, and confidence while surfacing missing PBC items automatically." },
                                { icon: Database, title: "Financial Build Engine", desc: "The system standardizes statements, computes QoE adjustments, ties out TB/GL/aging, and builds metric lineage." },
                                { icon: BarChart3, title: "Analyst-Grade Insights", desc: "You get interactive dashboards for QoE, working capital, conversion, customer quality, and risk concentration." },
                                { icon: ShieldCheck, title: "Defensibility & Trace", desc: "Every KPI and chart can be traced back through formulas, sources, and review-ready cell-level references." },
                            ].map((item, i) => (
                                <div key={i} className="bg-[#1e293b]/50 border border-slate-800/50 rounded-xl p-4 hover:bg-[#1e293b] transition-colors">
                                    <div className="flex items-center gap-2 mb-1.5">
                                        <item.icon className="h-4 w-4 text-[#38BDF8]" />
                                        <h3 className="text-sm font-medium text-slate-200">{item.title}</h3>
                                    </div>
                                    <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="bg-[#111827]/80 backdrop-blur-md rounded-2xl border border-slate-800 shadow-[0_0_30px_rgba(0,0,0,0.5)] p-6 flex flex-col justify-between" style={{ minHeight: '130px' }}>
                        <h2 className="text-sm font-semibold text-white mb-2">Upload Status</h2>
                        <p className="text-sm text-slate-400 mb-4">{files.length} file(s), {files.length > 0 ? "1 detected schedule type(s)" : "0 detected schedule type(s)"}</p>
                        <button
                            onClick={handleSubmit}
                            disabled={files.length === 0}
                            className={`w-full py-3 rounded-lg text-sm font-medium transition-all ${files.length > 0 ? 'bg-[#0f5ca8] hover:bg-[#0c4a8a] text-white shadow-[0_0_15px_rgba(15,92,168,0.5)]' : 'bg-slate-800 text-slate-500 cursor-not-allowed'}`}
                        >
                            Generate Analysis
                        </button>
                    </div>
                </div>
            </div>

            {/* Displaying selected files natively to avoid UI bloat in the clean design */}
            {files.length > 0 && (
                <div className="text-xs text-slate-500 opacity-70 px-2 flex gap-4 overflow-x-auto">
                    {files.map(f => f.name).join(", ")}
                </div>
            )}
        </div>
    );
}
