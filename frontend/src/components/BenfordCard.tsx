"use client";

import React from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from "recharts";
import { Scale, CheckCircle, Info } from "lucide-react";
import { benfordExpected } from "@/lib/mockData";

export const BenfordCard: React.FC = () => {
  return (
    <div className="bg-card rounded-card border border-card-border shadow-card p-6 md:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-500 flex items-center justify-center shrink-0">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-base font-semibold text-text-primary">
              Portfolio Integrity: Benford's Law Analysis
            </h4>
            <p className="text-xs text-text-secondary">
              First-digit distribution screening on overall transaction amount population
            </p>
          </div>
        </div>

        {/* Applicability Gate Badge */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="text-xs font-semibold px-3 py-1.5 rounded-badge bg-success-light text-success-dark border border-success/20 flex items-center gap-1.5">
            <CheckCircle className="w-3.5 h-3.5 text-success" />
            <span>Gate: Pass (High Confidence)</span>
          </span>
        </div>
      </div>

      {/* Chart */}
      <div className="h-64 w-full my-6">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={benfordExpected} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <XAxis dataKey="digit" stroke="#94A3B8" fontSize={11} axisLine={{ stroke: "#E8EAF0" }} tickLine={false} />
            <YAxis stroke="#94A3B8" fontSize={11} unit="%" axisLine={{ stroke: "#E8EAF0" }} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#FFFFFF",
                borderColor: "#E8EAF0",
                borderRadius: "10px",
                fontSize: "12px",
                color: "#1E293B",
                boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
              }}
            />
            <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "12px" }} />
            <Bar dataKey="expected" name="Benford Expected %" fill="#6366F1" radius={[4, 4, 0, 0]} />
            <Bar dataKey="observed" name="Observed Population %" fill="#94A3B8" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Statistical Gate Metrics */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4 text-center text-xs">
        <div className="p-4 bg-page rounded-xl border border-card-border">
          <span className="text-xs text-text-secondary font-medium block mb-1">Sample Size</span>
          <span className="text-text-primary font-bold text-base">12,450 txns</span>
        </div>
        <div className="p-4 bg-page rounded-xl border border-card-border">
          <span className="text-xs text-text-secondary font-medium block mb-1">MAD Statistic</span>
          <span className="text-brand-600 font-bold text-base">0.0042 (Close Fit)</span>
        </div>
        <div className="p-4 bg-page rounded-xl border border-card-border">
          <span className="text-xs text-text-secondary font-medium block mb-1">Chi-Square p-value</span>
          <span className="text-text-primary font-bold text-base">0.68 (Normal)</span>
        </div>
      </div>

      {/* Mandatory Disclaimer */}
      <div className="mt-6 p-4 bg-brand-50/60 border border-brand-100 rounded-xl flex items-start gap-3 text-xs text-text-secondary leading-relaxed">
        <Info className="w-4 h-4 text-brand-500 shrink-0 mt-0.5" />
        <p>
          <strong className="font-semibold text-text-primary">Portfolio-Level Distribution Signal:</strong> Not transaction-level evidence and never a trigger for an automated action. Used exclusively to assess macroeconomic population naturalness and detect wholesale synthetic payload injection.
        </p>
      </div>
    </div>
  );
};
