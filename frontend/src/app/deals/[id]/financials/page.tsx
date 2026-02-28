"use client";
import { useDeal } from "@/lib/deal-context";
import FinancialsTab from "@/components/analysis/financials-tab";
import { WorkingCapitalResults, RatioResults } from "@/lib/types";

export default function FinancialsPage() {
    const { getResults } = useDeal();
    return (
        <FinancialsTab
            wc={getResults("working_capital") as WorkingCapitalResults | null}
            ratios={getResults("ratios") as RatioResults | null}
        />
    );
}
