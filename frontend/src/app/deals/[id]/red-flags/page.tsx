"use client";
import { useDeal } from "@/lib/deal-context";
import RedFlagsTab from "@/components/analysis/red-flags-tab";
import { RedFlag, Anomaly } from "@/lib/types";

export default function RedFlagsPage() {
    const { getResults } = useDeal();
    return (
        <RedFlagsTab
            redFlags={getResults("red_flags") as RedFlag[] | null}
            anomalies={getResults("anomalies") as Anomaly[] | null}
        />
    );
}
