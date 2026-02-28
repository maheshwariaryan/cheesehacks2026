import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency", currency: "USD",
    minimumFractionDigits: 0, maximumFractionDigits: 0
  }).format(value);
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function formatNumber(value: number, decimals = 1): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals, maximumFractionDigits: decimals
  }).format(value);
}

export function formatCompactCurrency(value: number): string {
  if (Math.abs(value) >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
  if (Math.abs(value) >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

export function severityColor(severity: string): string {
  switch (severity) {
    case "critical": return "bg-red-700 text-white";
    case "high": return "bg-red-500 text-white";
    case "medium": return "bg-amber-500 text-white";
    case "low": return "bg-blue-500 text-white";
    default: return "bg-gray-400 text-white";
  }
}

export function healthColor(score: number): string {
  if (score >= 80) return "text-emerald-500";
  if (score >= 65) return "text-green-500";
  if (score >= 45) return "text-amber-500";
  if (score >= 25) return "text-orange-500";
  return "text-red-500";
}

export function riskBadgeColor(risk: string): string {
  switch (risk) {
    case "low": return "bg-emerald-100 text-emerald-800 border-emerald-300";
    case "medium": return "bg-amber-100 text-amber-800 border-amber-300";
    case "high": return "bg-red-100 text-red-800 border-red-300";
    default: return "bg-gray-100 text-gray-800";
  }
}

export function recommendationLabel(rec: string): string {
  switch (rec) {
    case "proceed": return "Proceed";
    case "proceed_with_caution": return "Proceed with Caution";
    case "significant_concerns": return "Significant Concerns";
    default: return rec;
  }
}

export function timeSince(dateStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}
