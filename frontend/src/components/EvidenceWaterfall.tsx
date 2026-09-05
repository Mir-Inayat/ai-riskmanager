"use client";

import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ReferenceLine,
} from "recharts";
import { TrendingUp } from "lucide-react";

interface SHAPItem {
  feature: string;
  contribution: number;
}

interface EvidenceWaterfallProps {
  shapContributions: SHAPItem[];
}

export const EvidenceWaterfall: React.FC<EvidenceWaterfallProps> = ({
  shapContributions,
}) => {
  // Sort by absolute contribution descending
  const sortedData = [...shapContributions].sort(
    (a, b) => Math.abs(b.contribution) - Math.abs(a.contribution)
  );

  const formattedData = sortedData.map((item) => ({
    name: item.feature,
    value: item.contribution,
    displayVal: `${item.contribution > 0 ? "+" : ""}${(item.contribution * 100).toFixed(1)}%`,
    isRisk: item.contribution > 0,
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white border border-card-border p-3 rounded-card shadow-card text-xs">
          <p className="text-text-primary font-semibold mb-1">{data.name}</p>
          <div className="flex items-center gap-2">
            <span className="text-text-secondary">SHAP Impact:</span>
            <span className={`font-mono font-bold ${data.isRisk ? "text-brand-600" : "text-slate-500"}`}>
              {data.displayVal}
            </span>
          </div>
          <p className="text-[11px] text-text-muted mt-1">
            {data.isRisk
              ? "Increases probability of fraud"
              : "Protective feature (lowers fraud score)"}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-card rounded-card border border-card-border shadow-card p-6 md:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-500 flex items-center justify-center shrink-0">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-base font-semibold text-text-primary">
              SHAP Feature Contributions (Waterfall)
            </h4>
            <p className="text-xs text-text-secondary">
              TreeExplainer attribution on Tree Ensembles (IEEE-CIS attributes)
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs self-start sm:self-auto">
          <div className="flex items-center gap-1.5 text-text-secondary font-medium">
            <span className="w-2.5 h-2.5 rounded-sm bg-brand-500" />
            <span>Increases Risk</span>
          </div>
          <div className="flex items-center gap-1.5 text-text-secondary font-medium">
            <span className="w-2.5 h-2.5 rounded-sm bg-slate-300" />
            <span>Mitigating</span>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-72 w-full my-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={formattedData}
            margin={{ top: 10, right: 30, left: 80, bottom: 5 }}
          >
            <XAxis
              type="number"
              domain={[-0.2, 0.5]}
              tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
              stroke="#94A3B8"
              fontSize={11}
              axisLine={{ stroke: "#E8EAF0" }}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="name"
              stroke="#475569"
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine x={0} stroke="#94A3B8" strokeOpacity={0.6} strokeDasharray="3 3" />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {formattedData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.isRisk ? "#6366F1" : "#CBD5E1"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-card-border flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-text-secondary">
        <span>Attribution model: TreeSHAP (Additive feature importance)</span>
        <span className="font-mono text-brand-600 font-medium">Base value: E[f(x)] = 0.035</span>
      </div>
    </div>
  );
};
