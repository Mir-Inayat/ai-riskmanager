"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { 
  Search, 
  ArrowUpDown, 
  ExternalLink, 
  ArrowRight, 
  Users, 
  AlertCircle,
  TrendingDown,
  ShieldCheck,
  Clock
} from "lucide-react";
import { getAllAlerts } from "@/lib/mockData";
import { fetchAlerts } from "@/lib/api";
import { RiskScoreBadge, DecisionBadge } from "@/components/RiskBadge";
import { formatINR, formatTimestamp } from "@/lib/utils";
import { Alert } from "@/types";

export default function AlertQueuePage() {
  const [allAlerts, setAllAlerts] = useState<Alert[]>(getAllAlerts());

  useEffect(() => {
    fetchAlerts().then((data) => setAllAlerts(data)).catch(() => {});
  }, []);

  const [filterDecision, setFilterDecision] = useState<string>("ALL");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [sortBy, setSortBy] = useState<"cost" | "score" | "amount" | "time">("cost");

  // Filtering and sorting logic
  const filteredAlerts = useMemo(() => {
    let result = [...allAlerts];

    // Filter by decision tab
    if (filterDecision !== "ALL") {
      result = result.filter((a) => a.decision === filterDecision);
    }

    // Filter by search term
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      result = result.filter(
        (a) =>
          a.transactionId.toLowerCase().includes(q) ||
          a.reasonCodes.some((code) => code.toLowerCase().includes(q))
      );
    }

    // Sort
    result.sort((a, b) => {
      if (sortBy === "cost") return b.expectedCost - a.expectedCost;
      if (sortBy === "score") return b.riskScore - a.riskScore;
      if (sortBy === "amount") return b.amount - a.amount;
      return b.timestamp - a.timestamp;
    });

    return result;
  }, [allAlerts, filterDecision, searchTerm, sortBy]);

  // Queue summary stats
  const totalQueueExposure = filteredAlerts.reduce((acc, curr) => acc + curr.expectedCost, 0);
  const highRiskCount = filteredAlerts.filter((a) => a.riskScore >= 0.8).length;
  const reviewCount = filteredAlerts.filter((a) => a.decision === "REVIEW").length;

  return (
    <div className="space-y-6">
      {/* Page Title & Queue Summary Chips */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Alert Queue</h1>
          <p className="text-text-secondary text-sm mt-0.5">
            Showing {filteredAlerts.length} of {allAlerts.length} alerts ranked by expected financial loss
          </p>
        </div>

        {/* Top Summary Stat Cards */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="px-3.5 py-2 bg-card rounded-card border border-card-border shadow-card flex items-center gap-2">
            <span className="text-xs text-text-muted uppercase tracking-wide font-medium">Queue Exposure:</span>
            <span className="text-sm font-bold text-text-primary">{formatINR(totalQueueExposure)}</span>
          </div>
          <div className="px-3.5 py-2 bg-card rounded-card border border-card-border shadow-card flex items-center gap-2">
            <span className="text-xs text-text-muted uppercase tracking-wide font-medium">Pending Review:</span>
            <span className="text-sm font-bold text-warning-dark">{reviewCount} cases</span>
          </div>
          <div className="px-3.5 py-2 bg-card rounded-card border border-card-border shadow-card flex items-center gap-2">
            <span className="text-xs text-text-muted uppercase tracking-wide font-medium">High Risk:</span>
            <span className="text-sm font-bold text-danger-dark">{highRiskCount} alerts</span>
          </div>
        </div>
      </div>

      {/* Control Bar: Tabs, Search & Sort */}
      <div className="bg-card rounded-card shadow-card border border-card-border p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Decision Filter Tabs */}
        <div className="flex items-center gap-1.5 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
          {[
            { id: "ALL", label: `All Alerts (${allAlerts.length})` },
            {
              id: "SIMULATED_HOLD",
              label: `Simulated Holds (${
                allAlerts.filter((a) => a.decision === "SIMULATED_HOLD").length
              })`,
            },
            {
              id: "REVIEW",
              label: `Review Queue (${
                allAlerts.filter((a) => a.decision === "REVIEW").length
              })`,
            },
            {
              id: "ALLOW",
              label: `Allowed (${
                allAlerts.filter((a) => a.decision === "ALLOW").length
              })`,
            },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilterDecision(tab.id)}
              className={`px-3.5 py-1.5 rounded-button text-xs font-medium transition-all ${
                filterDecision === tab.id
                  ? "bg-brand-500 text-white font-semibold shadow-sm"
                  : "bg-page border border-card-border text-text-secondary hover:text-text-primary"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search & Sort Controls */}
        <div className="flex items-center gap-3 w-full md:w-auto justify-between">
          <div className="relative flex-1 md:w-64">
            <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search TXN ID or reason..."
              className="w-full bg-page border border-card-border rounded-button pl-9 pr-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 font-mono transition-all"
            />
          </div>

          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-text-muted shrink-0" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-page border border-card-border rounded-button px-3 py-1.5 text-xs text-text-secondary focus:outline-none focus:border-brand-500 font-medium"
            >
              <option value="cost">Expected Cost ↓</option>
              <option value="score">Risk Score ↓</option>
              <option value="amount">Amount ↓</option>
              <option value="time">Time (Newest)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Queue Data Table */}
      <div className="bg-card rounded-card shadow-card border border-card-border p-6 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-card-border text-xs font-medium text-text-muted uppercase tracking-wide">
                <th className="pb-3.5 px-4 text-left">Transaction ID</th>
                <th className="pb-3.5 px-4 text-left">Timestamp</th>
                <th className="pb-3.5 px-4 text-right">Amount</th>
                <th className="pb-3.5 px-4 text-center">Calibrated Risk</th>
                <th className="pb-3.5 px-4 text-center">Routing Decision</th>
                <th className="pb-3.5 px-4 text-right">Expected Loss</th>
                <th className="pb-3.5 px-4 text-center">Linked Entities</th>
                <th className="pb-3.5 px-4 text-left">Trigger Codes</th>
                <th className="pb-3.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-card-border">
              {filteredAlerts.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-16 text-center text-text-secondary text-sm">
                    <AlertCircle className="w-8 h-8 mx-auto mb-2 text-text-muted" />
                    No alerts match the selected criteria.
                  </td>
                </tr>
              ) : (
                filteredAlerts.map((alert) => (
                  <tr
                    key={alert.transactionId}
                    className="border-b border-card-border hover:bg-page transition-colors"
                  >
                    <td className="py-3.5 px-4 text-left font-semibold font-mono text-text-primary">
                      <Link
                        href={`/alerts/${alert.transactionId}`}
                        className="text-brand-500 hover:text-brand-600 inline-flex items-center gap-1.5"
                      >
                        <span>{alert.transactionId}</span>
                        <ExternalLink className="w-3 h-3 opacity-60" />
                      </Link>
                    </td>
                    <td className="py-3.5 px-4 text-left text-text-secondary text-xs">
                      {formatTimestamp(alert.timestamp)}
                    </td>
                    <td className="py-3.5 px-4 text-right font-semibold text-text-primary">
                      {formatINR(alert.amount)}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <RiskScoreBadge score={alert.riskScore} />
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <DecisionBadge decision={alert.decision} />
                    </td>
                    <td className="py-3.5 px-4 text-right font-semibold text-text-primary">
                      {formatINR(alert.expectedCost)}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-badge bg-page border border-card-border text-xs text-text-secondary font-medium">
                        <Users className="w-3 h-3" />
                        <span>{alert.linkedEntityCount}</span>
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-left">
                      <div className="flex flex-wrap gap-1.5 max-w-xs">
                        {alert.reasonCodes.length > 0 ? (
                          alert.reasonCodes.map((code, i) => (
                            <span
                              key={i}
                              className="text-xs px-2 py-0.5 rounded bg-brand-50 text-brand-700 font-medium"
                            >
                              {code}
                            </span>
                          ))
                        ) : (
                          <span className="text-text-muted text-xs">Normal Pattern</span>
                        )}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        href={`/alerts/${alert.transactionId}`}
                        className="text-brand-500 hover:text-brand-600 font-medium text-xs inline-flex items-center gap-1"
                      >
                        <span>Investigate</span>
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
