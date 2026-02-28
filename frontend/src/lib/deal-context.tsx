"use client";

import { createContext, useContext } from "react";
import { DealDetail, Analysis } from "@/lib/types";

export interface DealContextValue {
    deal: DealDetail;
    analyses: Analysis[];
    getResults: (type: string) => Record<string, unknown> | null;
}

const DealContext = createContext<DealContextValue | null>(null);

export function DealProvider({ children, value }: { children: React.ReactNode; value: DealContextValue }) {
    return <DealContext.Provider value={value}>{children}</DealContext.Provider>;
}

export function useDeal(): DealContextValue {
    const ctx = useContext(DealContext);
    if (!ctx) throw new Error("useDeal must be used within DealProvider");
    return ctx;
}
