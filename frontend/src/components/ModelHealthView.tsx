"use client";

import React from "react";
import { 
  Activity, 
  BarChart2, 
  Layers, 
  Info,
} from "lucide-react";
import { modelComparisonData, driftMetrics } from "@/lib/mockData";
import { formatPercent } from "@/lib/utils";

export const ModelHealthView: React.FC = () => {
  return (
    <div className="space-y-10">
      {/* Benchmark Model Comparison Table */}
      <div className="bg-card rounded-card border border-card-border shadow-card p-6 md:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-500 flex items-center justify-center shrink-0">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">
                Model Evaluation Benchmark (Held-out Test Split)
              </h3>
              <p className="text-xs text-text-secondary">
                Chronological test evaluation — strictly isolated from training & threshold tuning
              </p>
            </div>
          </div>
          <span className="text-xs font-mono font-medium px-3 py-1.5 rounded-badge bg-page text-text-secondary border border-card-border self-start sm:self-auto">
            Split: Chronological 70/15/15
          </span>
        </div>

        <div className="overflow-x-auto rounded-xl border border-card-border">
          <table className="w-full text-left text-xs">
            <thead className="bg-page/70 border-b border-card-border text-text-secondary font-semibold">
              <tr>
                <th className="py-3.5 px-4 text-left">Model Architecture</th>
                <th className="py-3.5 px-4 text-left">Type</th>
                <th className="py-3.5 px-4 text-right">Precision</th>
                <th className="py-3.5 px-4 text-right">Recall</th>
                <th className="py-3.5 px-4 text-right">F1-Score</th>
                <th className="py-3.5 px-4 text-right">PR-AUC</th>
                <th className="py-3.5 px-4 text-right">Exposure Captured</th>
                <th className="py-3.5 px-4 text-right">Latency</th>
                <th className="py-3.5 px-4 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-card-border font-sans">
              {modelComparisonData.map((row, idx) => (
                <tr
                  key={idx}
                  className={`even:bg-page hover:bg-slate-50 transition-colors ${
                    row.status.includes("Champion") ? "border-l-4 border-l-brand-500 bg-brand-50/20" : ""
                  }`}
                >
                  <td className="py-3.5 px-4 text-left font-semibold text-text-primary flex items-center gap-2">
                    {row.status.includes("Champion") && (
                      <span className="w-2 h-2 rounded-full bg-brand-500" />
                    )}
                    {row.model}
                  </td>
                  <td className="py-3.5 px-4 text-left text-text-secondary">{row.type}</td>
                  <td className="py-3.5 px-4 text-right font-mono font-semibold text-text-primary">
                    {formatPercent(row.precision)}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono font-semibold text-text-primary">
                    {formatPercent(row.recall)}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono text-text-secondary">
                    {formatPercent(row.f1)}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono font-semibold text-brand-600">
                    {formatPercent(row.prAuc)}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono font-semibold text-success-dark">
                    {formatPercent(row.preventedExposure)}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono text-text-muted">{row.latencyMs}</td>
                  <td className="py-3.5 px-4 text-center">
                    <span
                      className={`text-[11px] font-semibold px-2.5 py-1 rounded-badge border ${
                        row.status.includes("Champion")
                          ? "bg-brand-50 text-brand-700 border-brand-200"
                          : row.status.includes("Active")
                          ? "bg-success-light text-success-dark border-success/20"
                          : "bg-page text-text-secondary border-card-border"
                      }`}
                    >
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Online Drift vs Delayed-Label Outcomes Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Drift Monitoring */}
        <div className="lg:col-span-7 bg-card rounded-card border border-card-border shadow-card p-6 md:p-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-500 flex items-center justify-center shrink-0">
                <Activity className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-base font-semibold text-text-primary">
                  Statistical Drift Monitor (Online KS-Test)
                </h4>
                <p className="text-xs text-text-secondary">
                  Continuous distribution checks against baseline reference
                </p>
              </div>
            </div>
            <span className="text-xs font-semibold px-3 py-1.5 rounded-badge bg-success-light text-success-dark border border-success/20 self-start sm:self-auto">
              0 Drift Alerts
            </span>
          </div>

          <div className="space-y-3">
            {driftMetrics.map((item, idx) => (
              <div
                key={idx}
                className="p-4 bg-page rounded-xl border border-card-border flex items-center justify-between gap-4 text-xs"
              >
                <div>
                  <span className="font-mono font-semibold text-text-primary block mb-0.5">
                    {item.feature}
                  </span>
                  <span className="text-[11px] text-text-secondary">{item.driftType}</span>
                </div>
                <div className="flex items-center gap-3">
                  {item.ksPValue !== null ? (
                    <span className="font-mono text-xs text-text-secondary">
                      p-val: <strong className="text-text-primary">{item.ksPValue}</strong>
                    </span>
                  ) : (
                    <span className="font-mono text-xs text-brand-600 font-semibold">
                      val: {item.value}
                    </span>
                  )}
                  <span
                    className={`text-[11px] font-semibold px-2.5 py-1 rounded-badge border ${
                      item.status === "HEALTHY" || item.status === "STABLE"
                        ? "bg-success-light text-success-dark border-success/20"
                        : "bg-warning-light text-warning-dark border-warning/20"
                    }`}
                  >
                    {item.status}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 rounded-xl bg-page border border-card-border flex items-start gap-3 text-xs text-text-secondary leading-relaxed">
            <Info className="w-4 h-4 text-brand-500 shrink-0 mt-0.5" />
            <p>
              <strong className="font-semibold text-text-primary">Methodology Note:</strong> Precision and recall are delayed-label metrics, refreshed after confirmed outcomes; live model health uses input and score-distribution drift.
            </p>
          </div>
        </div>

        {/* Confusion Matrix & Calibration */}
        <div className="lg:col-span-5 bg-card rounded-card border border-card-border shadow-card p-6 md:p-8 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-500 flex items-center justify-center shrink-0">
                <BarChart2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-base font-semibold text-text-primary">
                  Confusion Matrix (Test Evaluation)
                </h4>
                <p className="text-xs text-text-secondary">Held-out test split outcomes</p>
              </div>
            </div>

            {/* 2x2 Matrix */}
            <div className="grid grid-cols-2 gap-4 text-center my-6">
              <div className="p-4 rounded-xl bg-page border border-card-border">
                <span className="text-xs font-medium text-text-secondary block mb-1">
                  True Negative
                </span>
                <span className="text-2xl font-bold text-text-primary block font-mono">9,520</span>
                <span className="text-[11px] text-success-dark font-medium mt-1 block">Legitimate Cleared</span>
              </div>
              <div className="p-4 rounded-xl bg-page border border-card-border">
                <span className="text-xs font-medium text-warning-dark block mb-1">
                  False Positive
                </span>
                <span className="text-2xl font-bold text-text-primary block font-mono">42</span>
                <span className="text-[11px] text-text-muted mt-1 block">₹6,300 Friction Cost</span>
              </div>
              <div className="p-4 rounded-xl bg-page border border-card-border">
                <span className="text-xs font-medium text-danger block mb-1">
                  False Negative
                </span>
                <span className="text-2xl font-bold text-text-primary block font-mono">70</span>
                <span className="text-[11px] text-text-muted mt-1 block">Missed Exposure</span>
              </div>
              <div className="p-4 rounded-xl bg-brand-50/60 border border-brand-200">
                <span className="text-xs font-semibold text-brand-700 block mb-1">
                  True Positive
                </span>
                <span className="text-2xl font-bold text-brand-600 block font-mono">180</span>
                <span className="text-[11px] text-brand-700 font-medium mt-1 block">Prevented Fraud</span>
              </div>
            </div>
          </div>

          <div className="p-4 bg-page rounded-xl border border-card-border text-xs flex items-center justify-between">
            <span className="text-text-secondary font-medium">Recall @ Review Budget (Top 100):</span>
            <span className="text-brand-700 font-bold text-sm bg-white px-2.5 py-1 rounded-badge border border-card-border shadow-sm">
              58.0%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
