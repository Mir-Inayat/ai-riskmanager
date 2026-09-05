import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatINR(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp);
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  });
}

export function getRiskTier(riskScore: number): {
  tier: "HIGH" | "MEDIUM" | "LOW";
  color: string;
  bgColor: string;
  borderColor: string;
} {
  if (riskScore >= 0.8) {
    return {
      tier: "HIGH",
      color: "text-rose-400",
      bgColor: "bg-rose-950/40",
      borderColor: "border-rose-800/60",
    };
  } else if (riskScore >= 0.4) {
    return {
      tier: "MEDIUM",
      color: "text-amber-400",
      bgColor: "bg-amber-950/40",
      borderColor: "border-amber-800/60",
    };
  }
  return {
    tier: "LOW",
    color: "text-emerald-400",
    bgColor: "bg-emerald-950/40",
    borderColor: "border-emerald-800/60",
  };
}

export function getDecisionBadge(decision: "ALLOW" | "REVIEW" | "SIMULATED_HOLD" | string) {
  switch (decision) {
    case "SIMULATED_HOLD":
      return {
        label: "SIMULATED HOLD",
        color: "text-rose-300",
        bg: "bg-rose-950/60",
        border: "border-rose-600/40",
        dot: "bg-rose-500",
      };
    case "REVIEW":
      return {
        label: "ANALYST REVIEW",
        color: "text-amber-300",
        bg: "bg-amber-950/60",
        border: "border-amber-600/40",
        dot: "bg-amber-500",
      };
    case "ALLOW":
      return {
        label: "ALLOW & MONITOR",
        color: "text-emerald-300",
        bg: "bg-emerald-950/60",
        border: "border-emerald-600/40",
        dot: "bg-emerald-500",
      };
    default:
      return {
        label: decision,
        color: "text-slate-300",
        bg: "bg-slate-800/60",
        border: "border-slate-700",
        dot: "bg-slate-400",
      };
  }
}
