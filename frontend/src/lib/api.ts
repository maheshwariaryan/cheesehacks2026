import { Deal, DealDetail, Document, Analysis, ChatMessage, Report } from "./types";

const API_BASE = "/api";

// --- Helper ---
async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE}${url}`, {
        headers: { "Content-Type": "application/json", ...options?.headers },
        ...options,
    });
    if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
    return res.json();
}

// --- Deals ---
export async function createDeal(data: {
    name: string; target_company: string; industry?: string; deal_size?: number;
}): Promise<Deal> {
    return fetchJSON("/deals", { method: "POST", body: JSON.stringify(data) });
}

export async function getDeals(): Promise<{ deals: Deal[] }> {
    return fetchJSON("/deals");
}

export async function getDeal(id: number): Promise<DealDetail> {
    return fetchJSON(`/deals/${id}`);
}

export async function deleteDeal(id: number): Promise<void> {
    return fetchJSON(`/deals/${id}`, { method: "DELETE" });
}

// --- Documents ---
export async function uploadDocuments(dealId: number, files: File[]): Promise<{ documents: Document[] }> {
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));
    const res = await fetch(`${API_BASE}/deals/${dealId}/documents`, {
        method: "POST",
        body: formData,
    });
    if (!res.ok) throw new Error("Upload failed");
    return res.json();
}

export async function getDocuments(dealId: number): Promise<{ documents: Document[] }> {
    return fetchJSON(`/deals/${dealId}/documents`);
}

// --- Analysis ---
export async function triggerAnalysis(dealId: number): Promise<{ status: string }> {
    return fetchJSON(`/deals/${dealId}/analyze`, { method: "POST" });
}

export async function getAnalyses(dealId: number): Promise<{ analyses: Analysis[] }> {
    return fetchJSON(`/deals/${dealId}/analysis`);
}

export async function getAnalysis(dealId: number, type: string): Promise<Analysis> {
    return fetchJSON(`/deals/${dealId}/analysis/${type}`);
}

// --- Chat ---
export async function sendChatMessage(dealId: number, message: string): Promise<ChatMessage> {
    return fetchJSON(`/deals/${dealId}/chat`, { method: "POST", body: JSON.stringify({ message }) });
}

export async function getChatHistory(dealId: number): Promise<{ messages: ChatMessage[] }> {
    return fetchJSON(`/deals/${dealId}/chat`);
}

export async function clearChat(dealId: number): Promise<void> {
    return fetchJSON(`/deals/${dealId}/chat`, { method: "DELETE" });
}

// --- Reports ---
export async function generateReport(dealId: number, type: "iar" | "dcf" | "red_flag"): Promise<{ report_id: number }> {
    return fetchJSON(`/deals/${dealId}/reports/${type}`, { method: "POST" });
}

export async function getReports(dealId: number): Promise<{ reports: Report[] }> {
    return fetchJSON(`/deals/${dealId}/reports`);
}

export function getReportDownloadUrl(reportId: number): string {
    return `${API_BASE}/reports/${reportId}/download`;
}

export function getDocumentDownloadUrl(docId: number): string {
    return `${API_BASE}/documents/${docId}/download`;
}

export async function getReportStatus(dealId: number, type: string): Promise<{ status: string }> {
    return fetchJSON(`/deals/${dealId}/reports/${type}/status`);
}
