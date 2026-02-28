"use client";
import { useDeal } from "@/lib/deal-context";
import QoETab from "@/components/analysis/qoe-tab";
import { QoEResults } from "@/lib/types";

export default function QoEPage() {
    const { getResults } = useDeal();
    return <QoETab data={getResults("qoe") as QoEResults | null} />;
}
