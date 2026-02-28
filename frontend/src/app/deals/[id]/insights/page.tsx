"use client";
import { useDeal } from "@/lib/deal-context";
import InsightsTab from "@/components/analysis/insights-tab";
import { AIInsights } from "@/lib/types";

export default function InsightsPage() {
    const { getResults } = useDeal();
    return <InsightsTab data={getResults("ai_insights") as AIInsights | null} />;
}
