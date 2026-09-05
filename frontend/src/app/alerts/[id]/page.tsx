"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { 
  ArrowLeft, 
  CreditCard, 
  Clock, 
  Cpu, 
  Sparkles, 
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  Layers,
  AlertTriangle
} from "lucide-react";
import { getAlertById, getCaseEvidence, getGraphData } from "@/lib/mockData";
import { fetchAlertById } from "@/lib/api";
import { RiskScoreBadge, DecisionBadge } from "@/components/RiskBadge";
import { EvidenceWaterfall } from "@/components/EvidenceWaterfall";
import { RuleTriggersList } from "@/components/RuleTriggersList";
import { GraphView } from "@/components/GraphView";
import { AuditTrail } from "@/components/AuditTrail";
import { ApprovalGate } from "@/components/ApprovalGate";
import { formatINR, formatPercent, formatTimestamp } from "@/lib/utils";
import { Alert, CaseEvidence, GraphData } from "@/types";

export default function CaseInvestigationPage() {
  const params = useParams();
  const id = typeof params?.id === "string" ? params.id : "TXN-98234-A";

  const [alert, setAlert] = useState<Alert | undefined>(() => getAlertById(id));
  const [evidence, setEvidence] = useState<CaseEvidence>(() => getCaseEvidence(id));
  const [graphData] = useState<GraphData>(() => getGraphData());

  useEffect(() => {
    setAlert(getAlertById(id));
    setEvidence(getCaseEvidence(id));

    fetchAlertById(id)
      .then((data) => {
        if (data) {
          setAlert({
            transactionId: data.transactionId,
            timestamp: data.timestamp,
            amount: data.amount,
            riskScore: data.riskScore,
            decision: data.decision,
            reasonCodes: data.reasonCodes || [],
            expectedCost: data.expectedCost,
            linkedEntityCount: data.linkedEntityCount,
            modelVersion: data.modelVersion,
          });
          setEvidence({
            shapContributions: data.shapContributions || [],
            ruleTriggers: data.ruleTriggers || [],
            graphContext: data.graphContext || { sharedAttributes: [], clusterSize: 0 },
            costBreakdown: data.costBreakdown || {
              expectedFraudLoss: 0,
              frictionCostIfFP: 150,
              reviewCost: 25,
              netExposure: 0,
            },
            auditHash: data.auditHash || "",
          });
        }
      })
      .catch(() => {});
  }, [id]);

  if (!alert) {
    return (
      <div className="py-20 text-center space-y-4">
        <h2 className="text-2xl font-bold text-text-primary">Case Not Found</h2>
        <p className="text-text-secondary text-sm">
          No transaction record found for ID: {id}
        </p>
        <Link
          href="/alerts"
          className="text-brand-500 hover:text-brand-600 font-medium text-sm inline-flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Alert Queue</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header: Title, Decision Badge & Quick Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            href="/alerts"
            className="p-2 rounded-button bg-page border border-card-border text-text-secondary hover:text-text-primary hover:bg-card transition-colors"
            title="Back to Alert Queue"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-text-primary font-mono">
                {alert.transactionId}
              </h1>
              <DecisionBadge decision={alert.decision} />
            </div>
            <p className="text-text-secondary text-sm mt-0.5">
              Logged at {formatTimestamp(alert.timestamp)} • Evaluated via {alert.modelVersion}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3.5 py-2 bg-card rounded-card border border-card-border shadow-card flex items-center gap-2">
            <span className="text-xs text-text-muted uppercase tracking-wide font-medium">Risk Probability:</span>
            <span className="text-sm font-bold text-text-primary">{(alert.riskScore * 100).toFixed(1)}%</span>
            <RiskScoreBadge score={alert.riskScore} showPercent={false} />
          </div>
        </div>
      </div>

      {/* Cost-Based Decision Rationale Banner */}
      <div className="bg-card rounded-card shadow-card border border-card-border border-l-4 border-l-brand-500 p-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-1.5 max-w-2xl">
            <div className="flex items-center gap-2 text-xs font-semibold text-brand-600 uppercase tracking-wide">
              <Sparkles className="w-4 h-4" />
              <span>Layer IV Cost Optimization Engine: Recommendation Rationale</span>
            </div>
            <p className="text-sm font-semibold text-text-primary">
              Expected Fraud Loss (<span className="text-danger-dark font-bold">{formatINR(evidence.costBreakdown.expectedFraudLoss)}</span>) exceeds Customer Friction Cost (<span className="text-text-primary font-bold">{formatINR(evidence.costBreakdown.frictionCostIfFP)}</span>)
            </p>
            <p className="text-xs text-text-secondary leading-relaxed">
              Optimal action: <strong className="text-text-primary font-semibold">{alert.decision === "SIMULATED_HOLD" ? "Simulate Hold & Prompt Verification" : "Route to Human Review"}</strong> to protect ₹{evidence.costBreakdown.netExposure.toLocaleString("en-IN")} in net exposure.
            </p>
          </div>

          <div className="flex items-center gap-2 bg-page/60 p-3 rounded-xl border border-card-border text-xs font-mono shrink-0">
            <div className="text-center px-3.5 border-r border-card-border">
              <span className="text-[10px] text-text-muted block uppercase tracking-wider font-sans mb-0.5">Gross Value</span>
              <span className="font-bold text-text-primary text-sm">{formatINR(alert.amount)}</span>
            </div>
            <div className="text-center px-3.5 border-r border-card-border">
              <span className="text-[10px] text-text-muted block uppercase tracking-wider font-sans mb-0.5">FP Friction</span>
              <span className="font-bold text-text-secondary text-sm">₹{evidence.costBreakdown.frictionCostIfFP}</span>
            </div>
            <div className="text-center px-3.5">
              <span className="text-[10px] text-text-muted block uppercase tracking-wider font-sans mb-0.5">Net Exposure</span>
              <span className="font-bold text-brand-600 text-sm">{formatINR(evidence.costBreakdown.netExposure)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Transaction Details, Probability, SHAP Waterfall & Rules */}
        <div className="lg:col-span-6 space-y-6">
          {/* Transaction Metadata Card */}
          <div className="bg-card rounded-card shadow-card border border-card-border p-6">
            <div className="flex items-center gap-2.5 mb-4">
              <div className="p-2 rounded-xl bg-brand-50 text-brand-600">
                <CreditCard className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-text-primary">
                  Transaction Details
                </h3>
                <p className="text-xs text-text-secondary">
                  IEEE-CIS core attributes and system scoring
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-page/50 border border-card-border">
                <span className="text-[10px] text-text-muted uppercase tracking-wider block font-medium mb-1">Transaction ID</span>
                <span className="font-semibold text-text-primary font-mono">{alert.transactionId}</span>
              </div>
              <div className="p-3 rounded-xl bg-page/50 border border-card-border">
                <span className="text-[10px] text-text-muted uppercase tracking-wider block font-medium mb-1">Amount</span>
                <span className="font-bold text-text-primary text-sm">{formatINR(alert.amount)}</span>
              </div>
              <div className="p-3 rounded-xl bg-page/50 border border-card-border">
                <span className="text-[10px] text-text-muted uppercase tracking-wider block font-medium mb-1">Scored Timestamp</span>
                <span className="font-medium text-text-secondary">{formatTimestamp(alert.timestamp)}</span>
              </div>
              <div className="p-3 rounded-xl bg-page/50 border border-card-border">
                <span className="text-[10px] text-text-muted uppercase tracking-wider block font-medium mb-1">Model Version</span>
                <span className="font-semibold text-text-primary">{alert.modelVersion}</span>
              </div>
              <div className="p-3 rounded-xl bg-page/50 border border-card-border">
                <span className="text-[10px] text-text-muted uppercase tracking-wider block font-medium mb-1">Linked Entities</span>
                <span className="font-semibold text-brand-600">{alert.linkedEntityCount} Unique Nodes</span>
              </div>
              <div className="p-3 rounded-xl bg-page/50 border border-card-border">
                <span className="text-[10px] text-text-muted uppercase tracking-wider block font-medium mb-1">Audit Log Status</span>
                <span className="font-semibold text-success-dark">SEALED (SHA-256)</span>
              </div>
            </div>
          </div>

          {/* Calibrated Risk Probability Card */}
          <div className="bg-card rounded-card shadow-card border border-card-border p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-text-primary">
                  Calibrated Risk Probability
                </h3>
                <p className="text-xs text-text-secondary">
                  Posterior estimate P(Fraud | X)
                </p>
              </div>
              <RiskScoreBadge score={alert.riskScore} />
            </div>

            <div className="my-4">
              <div className="flex items-baseline justify-between mb-1.5">
                <span className="text-3xl font-bold text-text-primary font-mono">
                  {(alert.riskScore * 100).toFixed(1)}%
                </span>
                <span className="text-xs text-text-secondary">
                  Confidence Score
                </span>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2.5 bg-page rounded-full border border-card-border overflow-hidden">
                <div
                  style={{ width: `${alert.riskScore * 100}%` }}
                  className={`h-full rounded-full transition-all duration-500 ${
                    alert.riskScore >= 0.8
                      ? "bg-danger"
                      : alert.riskScore >= 0.4
                      ? "bg-warning"
                      : "bg-success"
                  }`}
                />
              </div>

              <div className="mt-3 flex items-center justify-between text-xs text-text-muted font-medium">
                <span>Hold Threshold: 0.80</span>
                <span>Review Threshold: 0.45</span>
              </div>
            </div>
          </div>

          {/* Evidence Waterfall (SHAP Feature Contributions) */}
          <EvidenceWaterfall shapContributions={evidence.shapContributions} />

          {/* Rule Triggers List */}
          <RuleTriggersList ruleTriggers={evidence.ruleTriggers} />
        </div>

        {/* Right Column: Graph View, Approval Gate & Audit Trail */}
        <div className="lg:col-span-6 space-y-6">
          {/* Layer III Entity Graph View */}
          <GraphView
            graphData={graphData}
            clusterId={evidence.graphContext.clusterId}
            clusterSize={evidence.graphContext.clusterSize}
            sharedAttributes={evidence.graphContext.sharedAttributes}
          />

          {/* Layer IV Analyst Approval Gate */}
          <ApprovalGate
            transactionId={alert.transactionId}
            defaultDecision={alert.decision}
          />

          {/* SHA-256 Deterministic Audit Trail */}
          <AuditTrail
            auditHash={evidence.auditHash}
            transactionId={alert.transactionId}
            decision={alert.decision}
            timestamp={alert.timestamp}
          />
        </div>
      </div>
    </div>
  );
}
