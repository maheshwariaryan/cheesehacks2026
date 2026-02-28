"use client";
import { useDeal } from "@/lib/deal-context";
import DocumentsTab from "@/components/analysis/documents-tab";

export default function DocumentsPage() {
    const { deal } = useDeal();
    return (
        <DocumentsTab documents={deal.documents || []} />
    );
}
