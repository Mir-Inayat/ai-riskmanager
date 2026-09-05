"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  TrendingUp, 
  Layers, 
  Activity, 
  ArrowRight, 
  SlidersHorizontal, 
  FileSearch,
  Cpu,
  ExternalLink,
  Shield,
  Network,
  Scale
} from "lucide-react";
import { KPICard } from "@/components/KPICard";
import { RiskScoreBadge, DecisionBadge } from "@/components/RiskBadge";
import { getAllAlerts, getSystemMetrics } from "@/lib/mockData";
import { fetchAlerts, fetchMetrics } from "@/lib/api";
import { formatINR, formatPercent, formatTimestamp } from "@/lib/utils";
import { Alert, SystemMetrics } from "@/types";

export default function CommandCenterPage() {
  const [alerts, setAlerts] = useState<Alert[]>(getAllAlerts());
  const [metrics, setMetrics] = useState<SystemMetrics>(getSystemMetrics());

  useEffect(() => {
    fetchAlerts().then((data) => setAlerts(data)).catch(() => {});
    fetchMetrics().then((data) => setMetrics(data)).catch(() => {});
  }, []);

  // High-priority alerts (Simulated Hold & Review)
  const highPriorityAlerts = alerts.filter(
    (a) => a.decision === "SIMULATED_HOLD" || a.decision === "REVIEW"
  );

  return (
    <div className="space-y-6">
      {/* Page Title & Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Dashboard</h1>
          <p className="text-text-secondary text-sm mt-0.5">
            Real-time fraud detection overview
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/alerts/TXN-98234-A"
            className="bg-brand-500 text-white rounded-button px-4 py-2 text-sm font-medium hover:bg-brand-600 transition-colors inline-flex items-center gap-2 shadow-sm"
          >
            <FileSearch className="w-4 h-4" />
            <span>Launch Hero Case</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>

          <Link
            href="/policy"
            className="bg-page border border-card-border text-text-secondary hover:text-text-primary rounded-button px-4 py-2 text-sm font-medium transition-colors inline-flex items-center gap-2"
          >
            <SlidersHorizontal className="w-4 h-4" />
            <span>Policy Simulator</span>
          </Link>
        </div>
      </div>

      {/* 4 KPI Cards in a row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <KPICard
          title="Prevented Exposure"
          value={formatPercent(metrics.preventableExposureCaptured)}
          subtitle="₹1,32,450 estimated exposure"
          badge="76.0% Recall"
          badgeType="positive"
          icon={TrendingUp}
        />

        <KPICard
          title="Model Precision"
          value={formatPercent(metrics.precision)}
          subtitle={`PR-AUC: ${metrics.prAuc.toFixed(2)} (Held-out Test)`}
          badge="LightGBM v1.0"
          badgeType="accent"
          icon={Cpu}
        />

        <KPICard
          title="Queue Status"
          value={`${highPriorityAlerts.length} Pending`}
          subtitle="Operational Cap: 100/day"
          badge="Load: 3%"
          badgeType="warning"
          icon={Layers}
        />

        <KPICard
          title="Pipeline Health"
          value="0.42 KS p-val"
          subtitle="Zero distribution drift detected"
          badge="Healthy"
          badgeType="positive"
          icon={Activity}
        />
      </div>

      {/* Two-Column Grid: Priority Alert Feed (Left) & 4-Layer Defense (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left (Wider): Priority Alert Feed */}
        <div className="lg:col-span-8 bg-card rounded-card shadow-card border border-card-border p-6">
          <div className="flex items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="text-base font-bold text-text-primary">
                Priority Alert Feed
              </h2>
              <p className="text-xs text-text-secondary mt-0.5">
                Transactions requiring simulated hold or analyst review
              </p>
            </div>

            <Link
              href="/alerts"
              className="text-brand-500 hover:text-brand-600 font-medium text-sm inline-flex items-center gap-1"
            >
              <span>View All ({alerts.length}) Alerts</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-card-border text-xs font-medium text-text-muted uppercase tracking-wide">
                  <th className="pb-3 px-3 text-left">Transaction ID</th>
                  <th className="pb-3 px-3 text-left">Timestamp</th>
                  <th className="pb-3 px-3 text-right">Amount</th>
                  <th className="pb-3 px-3 text-center">Risk Score</th>
                  <th className="pb-3 px-3 text-center">Triage Action</th>
                  <th className="pb-3 px-3 text-right">Expected Cost</th>
                  <th className="pb-3 px-3 text-left">Primary Trigger</th>
                  <th className="pb-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-card-border">
                {highPriorityAlerts.slice(0, 5).map((alert) => (
                  <tr
                    key={alert.transactionId}
                    className="border-b border-card-border hover:bg-page transition-colors"
                  >
                    <td className="py-3.5 px-3 text-left font-semibold font-mono text-text-primary">
                      <Link
                        href={`/alerts/${alert.transactionId}`}
                        className="text-brand-500 hover:text-brand-600 inline-flex items-center gap-1"
                      >
                        {alert.transactionId}
                        <ExternalLink className="w-3 h-3 opacity-60" />
                      </Link>
                    </td>
                    <td className="py-3.5 px-3 text-left text-text-secondary text-xs">
                      {formatTimestamp(alert.timestamp)}
                    </td>
                    <td className="py-3.5 px-3 text-right font-semibold text-text-primary">
                      {formatINR(alert.amount)}
                    </td>
                    <td className="py-3.5 px-3 text-center">
                      <RiskScoreBadge score={alert.riskScore} />
                    </td>
                    <td className="py-3.5 px-3 text-center">
                      <DecisionBadge decision={alert.decision} />
                    </td>
                    <td className="py-3.5 px-3 text-right font-semibold text-text-primary">
                      {formatINR(alert.expectedCost)}
                    </td>
                    <td className="py-3.5 px-3 text-left">
                      {alert.reasonCodes.length > 0 ? (
                        <span className="inline-block text-xs px-2 py-0.5 rounded bg-brand-50 text-brand-700 font-medium">
                          {alert.reasonCodes[0]}
                        </span>
                      ) : (
                        <span className="text-text-muted text-xs">Normal Pattern</span>
                      )}
                    </td>
                    <td className="py-3.5 px-3 text-right">
                      <Link
                        href={`/alerts/${alert.transactionId}`}
                        className="text-brand-500 hover:text-brand-600 font-medium text-xs inline-flex items-center gap-1"
                      >
                        <span>Investigate</span>
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: 4-Layer Defense Summary Cards Stacked Vertically */}
        <div className="lg:col-span-4 bg-card rounded-card shadow-card border border-card-border p-6 space-y-4">
          <div>
            <h2 className="text-base font-bold text-text-primary">
              4-Layer Defense Architecture
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Multi-stage automated risk triage pipeline
            </p>
          </div>

          <div className="space-y-3">
            {/* Layer 1 */}
            <div className="p-3.5 rounded-xl border border-card-border bg-page/40 hover:bg-page transition-colors">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-brand-50 text-brand-600 flex items-center justify-center text-xs font-bold">
                    1
                  </div>
                  <span className="text-xs font-semibold text-text-primary">Rules Engine</span>
                </div>
                <span className="text-[11px] font-semibold text-success-dark bg-success-light px-2 py-0.5 rounded-badge border border-success/20">
                  Active
                </span>
              </div>
              <p className="text-xs text-text-secondary leading-relaxed">
                Deterministic velocity counters and 99th-percentile amount thresholds.
              </p>
            </div>

            {/* Layer 2 */}
            <div className="p-3.5 rounded-xl border border-card-border bg-page/40 hover:bg-page transition-colors">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-brand-50 text-brand-600 flex items-center justify-center text-xs font-bold">
                    2
                  </div>
                  <span className="text-xs font-semibold text-text-primary">ML Classifier</span>
                </div>
                <span className="text-[11px] font-semibold text-brand-700 bg-brand-50 px-2 py-0.5 rounded-badge border border-brand-200">
                  Calibrated
                </span>
              </div>
              <p className="text-xs text-text-secondary leading-relaxed">
                Supervised LightGBM model with TreeSHAP explainability attributions.
              </p>
            </div>

            {/* Layer 3 */}
            <div className="p-3.5 rounded-xl border border-card-border bg-page/40 hover:bg-page transition-colors">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-brand-50 text-brand-600 flex items-center justify-center text-xs font-bold">
                    3
                  </div>
                  <span className="text-xs font-semibold text-text-primary">Entity Graph</span>
                </div>
                <span className="text-[11px] font-semibold text-info-dark bg-info-light px-2 py-0.5 rounded-badge border border-info/20">
                  Cluster Sync
                </span>
              </div>
              <p className="text-xs text-text-secondary leading-relaxed">
                Device fingerprint, email domain, and card co-occurrence clusters.
              </p>
            </div>

            {/* Layer 4 */}
            <div className="p-3.5 rounded-xl border border-card-border bg-page/40 hover:bg-page transition-colors">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-brand-50 text-brand-600 flex items-center justify-center text-xs font-bold">
                    4
                  </div>
                  <span className="text-xs font-semibold text-text-primary">Cost & Audit</span>
                </div>
                <span className="text-[11px] font-semibold text-brand-700 bg-brand-50 px-2 py-0.5 rounded-badge border border-brand-200">
                  Deterministic
                </span>
              </div>
              <p className="text-xs text-text-secondary leading-relaxed">
                Expected-loss optimal triage with SHA-256 cryptographic audit chain.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
