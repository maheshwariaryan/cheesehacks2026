"use client";

import { Document } from "@/lib/types";
import { timeSince } from "@/lib/utils";
import { getDocumentDownloadUrl } from "@/lib/api";
import { FileText, Download, CheckCircle2, Clock } from "lucide-react";

interface Props {
    documents: Document[];
}

export default function DocumentsTab({ documents }: Props) {
    if (documents.length === 0) {
        return (
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500">
                No documents found for this deal.
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg font-semibold text-slate-800">Deal Documents</h2>
                <span className="text-xs text-slate-400">{documents.length} files total</span>
            </div>

            <div className="grid grid-cols-1 gap-3">
                {documents.map((doc) => (
                    <div key={doc.id} className="bg-white rounded-xl border border-slate-200 p-4 transition-all hover:border-blue-300 hover:shadow-sm flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="h-10 w-10 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
                                <FileText className="h-5 w-5" />
                            </div>
                            <div>
                                <h3 className="text-sm font-medium text-slate-900">{doc.filename}</h3>
                                <div className="flex items-center gap-2 mt-0.5">
                                    <span className="text-xs text-slate-400">{(doc.file_size / 1024).toFixed(1)} KB</span>
                                    <span className="text-xs text-slate-300">•</span>
                                    <span className="text-xs text-slate-400">Uploaded {timeSince(doc.uploaded_at)}</span>
                                    {doc.doc_type && (
                                        <>
                                            <span className="text-xs text-slate-300">•</span>
                                            <span className="inline-flex items-center gap-1 text-[10px] font-semibold bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded uppercase">
                                                {doc.doc_type}
                                            </span>
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center gap-4">
                            {doc.doc_type ? (
                                <div className="flex items-center gap-1.5 text-emerald-600">
                                    <CheckCircle2 className="h-4 w-4" />
                                    <span className="text-xs font-medium">Classified</span>
                                </div>
                            ) : (
                                <div className="flex items-center gap-1.5 text-amber-500">
                                    <Clock className="h-4 w-4" />
                                    <span className="text-xs font-medium">Processing</span>
                                </div>
                            )}
                            <a
                                href={getDocumentDownloadUrl(doc.id)}
                                download={doc.filename}
                                className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            >
                                <Download className="h-4 w-4" />
                            </a>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
