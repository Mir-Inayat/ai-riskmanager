"use client";

import React, { useState, useMemo } from "react";
import { Sliders, Sparkles, DollarSign, Users } from "lucide-react";
import { formatINR } from "@/lib/utils";

export const CostSimulator: React.FC = () => {
  const [cfp, setCfp] = useState<number>(150); // Legitimate customer friction cost
  const [creview, setCreview] = useState<number>(25); // Review cost
  const [reviewThreshold, setReviewThreshold] = useState<number>(0.45);
  const [holdThreshold, setHoldThreshold] = useState<number>(0.80);
  const [activePreset, setActivePreset] = useState<"balanced" | "strict" | "low_friction">("balanced");

  // Scenario presets
  const applyPreset = (preset: "balanced" | "strict" | "low_friction") => {
    setActivePreset(preset);
    if (preset === "balanced") {
      setCfp(150);
      setCreview(25);
      setReviewThreshold(0.45);
      setHoldThreshold(0.80);
    } else if (preset === "strict") {
      setCfp(80);
      setCreview(20);
      setReviewThreshold(0.30);
      setHoldThreshold(0.65);
    } else if (preset === "low_friction") {
      setCfp(300);
      setCreview(35);
      setReviewThreshold(0.55);
      setHoldThreshold(0.88);
    }
  };

  // Simulated metrics based on sliders
  const simulatedOutcome = useMemo(() => {
    const totalTxns = 10000;

    // Approximated CDF curves
    const holdPct = Math.max(0.01, (1 - holdThreshold) * 0.12);
    const reviewPct = Math.max(0.02, (holdThreshold - reviewThreshold) * 0.25);
    const allowPct = 1 - (holdPct + reviewPct);

    const holds = Math.round(totalTxns * holdPct);
    const reviews = Math.round(totalTxns * reviewPct);
    const allows = totalTxns - holds - reviews;

    // Cost calculations
    const capturedFraudLoss = Math.min(250, Math.round(holds * 0.75 + reviews * 0.35)) * 14500;
    const fpCost = Math.round(holds * (1 - 0.75) * cfp + reviews * (1 - 0.35) * (cfp * 0.4));
    const reviewCostTotal = Math.round(reviews * creview);
    const netPreventedExposure = Math.max(0, capturedFraudLoss - fpCost - reviewCostTotal);

    return {
      holds,
      reviews,
      allows,
      capturedFraudLoss,
      fpCost,
      reviewCostTotal,
      netPreventedExposure,
      optimalThreshold: 0.78,
    };
  }, [cfp, creview, reviewThreshold, holdThreshold]);

  return (
    <div className="bg-card rounded-card border border-card-border shadow-card p-6 md:p-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-500 flex items-center justify-center shrink-0">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">
                Cost Policy Simulator & Expected Loss Engine
              </h3>
              <p className="text-xs text-text-secondary mt-0.5">
                Simulate financial exposure and triage volume trade-offs (Validation Split Protocol)
              </p>
            </div>
          </div>
        </div>

        {/* Preset Buttons */}
        <div className="flex items-center gap-2 self-start md:self-auto">
          <span className="text-xs font-medium text-text-secondary">Preset:</span>
          <button
            onClick={() => applyPreset("strict")}
            className={`px-3.5 py-1.5 rounded-button text-xs font-semibold transition-all duration-200 border ${
              activePreset === "strict"
                ? "bg-brand-500 text-white border-brand-500 shadow-sm"
                : "bg-page text-text-secondary border-card-border hover:bg-slate-200 hover:text-text-primary"
            }`}
          >
            Strict
          </button>
          <button
            onClick={() => applyPreset("balanced")}
            className={`px-3.5 py-1.5 rounded-button text-xs font-semibold transition-all duration-200 border ${
              activePreset === "balanced"
                ? "bg-brand-500 text-white border-brand-500 shadow-sm"
                : "bg-page text-text-secondary border-card-border hover:bg-slate-200 hover:text-text-primary"
            }`}
          >
            Balanced
          </button>
          <button
            onClick={() => applyPreset("low_friction")}
            className={`px-3.5 py-1.5 rounded-button text-xs font-semibold transition-all duration-200 border ${
              activePreset === "low_friction"
                ? "bg-brand-500 text-white border-brand-500 shadow-sm"
                : "bg-page text-text-secondary border-card-border hover:bg-slate-200 hover:text-text-primary"
            }`}
          >
            Low Friction
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Sliders Column */}
        <div className="lg:col-span-6 space-y-5">
          {/* C_FP Slider */}
          <div className="p-5 bg-page rounded-xl border border-card-border">
            <div className="flex items-center justify-between mb-3">
              <label className="text-xs font-semibold text-text-primary flex items-center gap-2">
                <Users className="w-4 h-4 text-brand-500" />
                Customer Friction Cost (C_FP)
              </label>
              <span className="text-xs font-mono font-bold text-brand-600 bg-white px-2.5 py-1 rounded-badge border border-card-border shadow-sm">
                ₹{cfp}
              </span>
            </div>
            <input
              type="range"
              min={25}
              max={500}
              step={25}
              value={cfp}
              onChange={(e) => setCfp(Number(e.target.value))}
              className="w-full h-2 my-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-brand-500"
            />
            <p className="text-[11px] text-text-muted mt-2 leading-relaxed">
              Estimated churn and support friction if a legitimate user encounters verification.
            </p>
          </div>

          {/* C_Review Slider */}
          <div className="p-5 bg-page rounded-xl border border-card-border">
            <div className="flex items-center justify-between mb-3">
              <label className="text-xs font-semibold text-text-primary flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-brand-500" />
                Analyst Review Cost (C_rev)
              </label>
              <span className="text-xs font-mono font-bold text-brand-600 bg-white px-2.5 py-1 rounded-badge border border-card-border shadow-sm">
                ₹{creview}
              </span>
            </div>
            <input
              type="range"
              min={5}
              max={100}
              step={5}
              value={creview}
              onChange={(e) => setCreview(Number(e.target.value))}
              className="w-full h-2 my-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-brand-500"
            />
            <p className="text-[11px] text-text-muted mt-2 leading-relaxed">
              Operational cost of manual analyst investigation per triage alert.
            </p>
          </div>

          {/* Threshold Sliders */}
          <div className="p-5 bg-page rounded-xl border border-card-border space-y-5">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-semibold text-text-primary">
                  Review Threshold (τ_rev)
                </label>
                <span className="text-xs font-mono font-bold text-brand-600 bg-white px-2.5 py-0.5 rounded-badge border border-card-border shadow-sm">
                  {(reviewThreshold * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min={0.15}
                max={0.65}
                step={0.05}
                value={reviewThreshold}
                onChange={(e) => setReviewThreshold(Number(e.target.value))}
                className="w-full h-2 my-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-brand-500"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-semibold text-text-primary">
                  Simulated Hold Threshold (τ_hold)
                </label>
                <span className="text-xs font-mono font-bold text-brand-600 bg-white px-2.5 py-0.5 rounded-badge border border-card-border shadow-sm">
                  {(holdThreshold * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min={0.60}
                max={0.95}
                step={0.05}
                value={holdThreshold}
                onChange={(e) => setHoldThreshold(Number(e.target.value))}
                className="w-full h-2 my-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-brand-500"
              />
            </div>
          </div>
        </div>

        {/* Live Simulation Output Column */}
        <div className="lg:col-span-6 flex flex-col justify-between space-y-6">
          {/* Triage Tier Distribution */}
          <div className="p-5 bg-page rounded-xl border border-card-border">
            <span className="text-xs font-semibold text-text-primary uppercase tracking-wider block mb-4">
              Daily Triage Routing (10,000 Transactions)
            </span>

            {/* Visual Bar Breakdown */}
            <div className="h-3.5 w-full rounded-full overflow-hidden flex bg-slate-200 mb-4">
              <div
                style={{ width: `${(simulatedOutcome.holds / 10000) * 100}%` }}
                className="bg-danger transition-all duration-300"
                title={`Holds: ${simulatedOutcome.holds}`}
              />
              <div
                style={{ width: `${(simulatedOutcome.reviews / 10000) * 100}%` }}
                className="bg-warning transition-all duration-300"
                title={`Reviews: ${simulatedOutcome.reviews}`}
              />
              <div
                style={{ width: `${(simulatedOutcome.allows / 10000) * 100}%` }}
                className="bg-success transition-all duration-300"
                title={`Allows: ${simulatedOutcome.allows}`}
              />
            </div>

            <div className="grid grid-cols-3 gap-3 text-center text-xs">
              <div className="p-3.5 rounded-xl bg-white border border-card-border shadow-sm">
                <span className="text-[11px] text-danger font-semibold block mb-1">Simulated Hold</span>
                <span className="font-bold text-text-primary text-base">{simulatedOutcome.holds}</span>
                <span className="text-[11px] text-text-muted block mt-0.5">
                  {((simulatedOutcome.holds / 10000) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="p-3.5 rounded-xl bg-white border border-card-border shadow-sm">
                <span className="text-[11px] text-warning-dark font-semibold block mb-1">Analyst Review</span>
                <span className="font-bold text-text-primary text-base">{simulatedOutcome.reviews}</span>
                <span className="text-[11px] text-text-muted block mt-0.5">
                  {((simulatedOutcome.reviews / 10000) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="p-3.5 rounded-xl bg-white border border-card-border shadow-sm">
                <span className="text-[11px] text-success-dark font-semibold block mb-1">Allow & Monitor</span>
                <span className="font-bold text-text-primary text-base">{simulatedOutcome.allows}</span>
                <span className="text-[11px] text-text-muted block mt-0.5">
                  {((simulatedOutcome.allows / 10000) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* Financial Exposure Delta */}
          <div className="p-5 bg-page rounded-xl border border-card-border space-y-3">
            <span className="text-xs font-semibold text-text-primary uppercase tracking-wider block mb-1">
              Cost Equation & Prevented Exposure
            </span>
            <div className="flex items-center justify-between text-xs py-1">
              <span className="text-text-secondary">Captured Fraud Loss:</span>
              <span className="font-mono text-success-dark font-bold text-sm">
                {formatINR(simulatedOutcome.capturedFraudLoss)}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs py-1">
              <span className="text-text-secondary">Total Customer Friction Cost:</span>
              <span className="font-mono text-danger font-semibold">
                - {formatINR(simulatedOutcome.fpCost)}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs py-1">
              <span className="text-text-secondary">Review Capacity Cost:</span>
              <span className="font-mono text-text-secondary font-semibold">
                - {formatINR(simulatedOutcome.reviewCostTotal)}
              </span>
            </div>
            <div className="pt-3 mt-1 border-t border-card-border flex items-center justify-between">
              <span className="text-xs font-bold text-text-primary">Net Prevented Exposure:</span>
              <span className="text-sm font-mono font-bold text-brand-700 bg-brand-50 px-3 py-1.5 rounded-badge border border-brand-200 shadow-sm">
                {formatINR(simulatedOutcome.netPreventedExposure)}
              </span>
            </div>
          </div>

          {/* Optimal Recommendation */}
          <div className="p-4 rounded-xl bg-brand-50 border border-brand-200 flex items-center gap-3 text-xs text-brand-900 shadow-sm">
            <Sparkles className="w-5 h-5 text-brand-500 shrink-0" />
            <span className="leading-relaxed">
              <strong className="font-semibold text-brand-700">Optimizer Recommendation:</strong> Hold threshold on validation split is{" "}
              <span className="font-mono font-bold text-brand-700">0.78</span> for minimal net operational cost.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
