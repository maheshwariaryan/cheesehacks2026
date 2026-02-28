"use client";
import { useDeal } from "@/lib/deal-context";
import DCFTab from "@/components/analysis/dcf-tab";
import { DCFResults } from "@/lib/types";

export default function DCFPage() {
    const { getResults } = useDeal();
    return <DCFTab data={getResults("dcf") as DCFResults | null} />;
}
