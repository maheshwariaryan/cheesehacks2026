"use client";
import { useDeal } from "@/lib/deal-context";
import OverviewTab from "@/components/analysis/overview-tab";
import { AIInsights, QoEResults, WorkingCapitalResults, RatioResults } from "@/lib/types";

export default function OverviewPage() {
    const { deal, getResults } = useDeal();
    return (
        <OverviewTab
            deal={deal}
            insights={getResults("ai_insights") as AIInsights | null}
            qoe={getResults("qoe") as QoEResults | null}
            wc={getResults("working_capital") as WorkingCapitalResults | null}
            ratios={getResults("ratios") as RatioResults | null}
        />
    );
}
