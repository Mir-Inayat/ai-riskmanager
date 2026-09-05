"use client";

import React, { useState, useEffect } from "react";
import { 
  SlidersHorizontal, 
  Activity, 
  Scale, 
  Layers, 
  ShieldCheck, 
  TrendingUp, 
  Cpu 
} from "lucide-react";
import { KPICard } from "@/components/KPICard";
import { CostSimulator } from "@/components/CostSimulator";
import { ModelHealthView } from "@/components/ModelHealthView";
import { BenfordCard } from "@/components/BenfordCard";
import { fetchCostMetrics, fetchMetrics } from "@/lib/api";
import { getSystemMetrics } from "@/lib/mockData";
import { formatPercent } from "@/lib/utils";
import { CostMetrics, SystemMetrics } from "@/types";

export default function PolicyAndHealthPage() {
  const [activeTab, setActiveTab] = useState<"all" | "simulator" | "health" | "benford">("all");
  const [metrics, setMetrics] = useState<SystemMetrics>(getSystemMetrics());
  const [costMetrics, setCostMetrics] = useState<CostMetrics | null>(null);

  useEffect(() => {
    fetchMetrics().then((data) => setMetrics(data)).catch(() => {});
    fetchCostMetrics().then((data) => setCostMetrics(data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Title & View Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">
            Policy & Model Health
          </h1>
          <p className="text-text-secondary text-sm mt-0.5">
            Triage threshold optimization, statistical drift monitoring, and held-out benchmark evaluation
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-1.5 bg-card p-1.5 rounded-card border border-card-border shadow-card self-start md:self-auto overflow-x-auto">
          {[
            { id: "all", label: "Consolidated View" },
            { id: "simulator", label: "Cost Simulator" },
            { id: "health", label: "Model Evaluation" },
            { id: "benford", label: "Benford Gate" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-3.5 py-1.5 rounded-button text-xs font-medium transition-all ${
                activeTab === tab.id
                  ? "bg-brand-500 text-white font-semibold shadow-sm"
                  : "text-text-secondary hover:text-text-primary hover:bg-page"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <KPICard
          title="Champion Precision"
          value={formatPercent(metrics.precision)}
          subtitle="Held-out Test Split (70/15/15)"
          badge="Champion"
          badgeType="positive"
          icon={Cpu}
        />

        <KPICard
          title="PR-AUC Score"
          value={metrics.prAuc.toFixed(2)}
          subtitle="Baseline XGBoost: 0.81"
          badge="+0.07 Delta"
          badgeType="accent"
          icon={TrendingUp}
        />

        <KPICard
          title="Distribution Drift"
          value="0.42 KS p-val"
          subtitle="Zero distribution drift detected"
          badge="Healthy"
          badgeType="positive"
          icon={Activity}
        />

        <KPICard
          title="Optimal Exposure Cut"
          value={formatPercent(metrics.preventableExposureCaptured)}
          subtitle="Expected loss minimization"
          badge="76.0% Recall"
          badgeType="warning"
          icon={Scale}
        />
      </div>

      {/* Main Content Sections */}
      <div className="space-y-6">
        {(activeTab === "all" || activeTab === "simulator") && (
          <section>
            <CostSimulator />
          </section>
        )}

        {(activeTab === "all" || activeTab === "health") && (
          <section>
            <ModelHealthView />
          </section>
        )}

        {(activeTab === "all" || activeTab === "benford") && (
          <section>
            <BenfordCard />
          </section>
        )}
      </div>
    </div>
  );
}
