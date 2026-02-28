"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const mainNav = [
    { label: "All Deals", href: "/deals" },
];

const dealSubNav = [
    { label: "Dashboard", href: "overview" },
    { label: "Documents", href: "documents" },
    { label: "Financial Analysis", href: "financials" },
    { label: "Risk Assessment", href: "red-flags" },
    { label: "Customer Analytics", href: "analytics" },
    { label: "Reports", href: "qoe" },
    { label: "Inquiry", href: "chat" },
    { label: "Notes", href: "notes" },
    { label: "Settings", href: "settings" },
];

export default function Sidebar() {
    const pathname = usePathname();

    // Check if we're on a deal detail page
    const dealMatch = pathname.match(/^\/deals\/(\d+)/);
    const dealId = dealMatch ? dealMatch[1] : null;
    const activeSegment = dealId ? pathname.split("/").pop() : null;

    return (
        <aside className="fixed left-0 top-0 z-40 h-screen w-64 bg-white border-r border-slate-200 flex flex-col pt-6">
            <div className="px-5 mb-8">
                <div className="bg-[#1a4a8c] rounded-xl p-4 text-white shadow-md">
                    <h1 className="text-xs font-bold tracking-widest opacity-90 mb-1">TAM</h1>
                    <p className="text-[17px] font-medium leading-tight">Due Diligence OS</p>
                </div>
            </div>

            <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
                <p className="px-4 pb-2 text-[11px] uppercase tracking-wider text-slate-400 font-semibold mt-2">
                    Global
                </p>
                {mainNav.map((item) => {
                    const isActive = pathname === item.href || (item.href === "/" && pathname === "/");
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 py-2.5 px-4 rounded-lg text-sm font-medium transition-colors mb-4",
                                isActive
                                    ? "bg-blue-50 text-[#1a4a8c]"
                                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                            )}
                        >
                            {item.label}
                        </Link>
                    );
                })}

                <div className="pt-2">
                    <p className="px-4 pb-2 text-[11px] uppercase tracking-wider text-slate-400 font-semibold mb-1">
                        Workspace
                    </p>
                    <div className="space-y-1">
                        {dealSubNav.map((item) => {
                            const isActive = activeSegment === item.href;
                            const isClickable = !!dealId || item.href === "documents";
                            return (
                                <Link
                                    key={item.href}
                                    href={dealId ? `/deals/${dealId}/${item.href}` : "#"}
                                    onClick={(e) => {
                                        if (!dealId) e.preventDefault();
                                    }}
                                    className={cn(
                                        "flex items-center gap-2.5 py-2.5 px-4 rounded-xl text-sm transition-colors font-medium",
                                        isActive
                                            ? "bg-[#eef4fb] text-[#1a4a8c]"
                                            : isClickable
                                                ? "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                                                : "text-slate-400 cursor-not-allowed"
                                    )}
                                >
                                    {item.label}
                                </Link>
                            );
                        })}
                    </div>
                </div>
            </nav>
        </aside>
    );
}
