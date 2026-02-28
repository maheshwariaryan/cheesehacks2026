"use client";

import { usePathname } from "next/navigation";
import Sidebar from "@/components/layout/sidebar";

export default function AppShell({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();

    // The login and upload pages don't have the normal dashboard sidebar
    const isFullScreenPage = pathname === "/login" || pathname === "/upload";

    if (isFullScreenPage) {
        return (
            <main className="min-h-screen bg-[#070B14] relative overflow-hidden flex flex-col items-center">
                {/* Custom faint grid background */}
                <div
                    className="absolute inset-0 z-0 opacity-20"
                    style={{
                        backgroundImage: `linear-gradient(to right, #4f4f4f12 1px, transparent 1px), linear-gradient(to bottom, #4f4f4f12 1px, transparent 1px)`,
                        backgroundSize: '24px 24px'
                    }}
                />
                <div className="z-10 w-full flex-1 flex flex-col">
                    {children}
                </div>
            </main>
        );
    }

    return (
        <div className="flex min-h-screen overflow-hidden bg-slate-50 dark:bg-slate-950">
            <Sidebar />
            <main className="flex-1 ml-64 p-8 overflow-y-auto">
                {children}
            </main>
        </div>
    );
}
