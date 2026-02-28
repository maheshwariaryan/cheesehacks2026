"use client";

import { useEffect, useState, useCallback } from "react";

export function usePolling<T>(
    fetcher: () => Promise<T>,
    intervalMs: number,
    shouldPoll: boolean
) {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);

    const stableFetcher = useCallback(fetcher, [fetcher]);

    useEffect(() => {
        if (!shouldPoll) return;
        let active = true;

        const poll = async () => {
            try {
                const result = await stableFetcher();
                if (active) { setData(result); setLoading(false); }
            } catch {
                if (active) setLoading(false);
            }
        };

        poll();
        const id = setInterval(poll, intervalMs);
        return () => { active = false; clearInterval(id); };
    }, [shouldPoll, intervalMs, stableFetcher]);

    return { data, loading };
}
