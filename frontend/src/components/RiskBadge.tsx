import React from "react";
import { getRiskTier, getDecisionBadge } from "@/lib/utils";

interface RiskScoreBadgeProps {
  score: number;
  showPercent?: boolean;
}

export const RiskScoreBadge: React.FC<RiskScoreBadgeProps> = ({
  score,
  showPercent = true,
}) => {
  const { tier } = getRiskTier(score);

  const getTierStyles = () => {
    switch (tier) {
      case "HIGH":
        return {
          container: "bg-danger-light text-danger-dark border-danger/20",
          dot: "bg-danger",
        };
      case "MEDIUM":
        return {
          container: "bg-warning-light text-warning-dark border-warning/20",
          dot: "bg-warning",
        };
      case "LOW":
      default:
        return {
          container: "bg-success-light text-success-dark border-success/20",
          dot: "bg-success",
        };
    }
  };

  const styles = getTierStyles();

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${styles.container} transition-all`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${styles.dot}`} />
      <span>{tier} RISK</span>
      {showPercent && (
        <span className="font-mono text-[11px] opacity-80">
          ({(score * 100).toFixed(0)}%)
        </span>
      )}
    </div>
  );
};

interface DecisionBadgeProps {
  decision: "ALLOW" | "REVIEW" | "SIMULATED_HOLD" | string;
}

export const DecisionBadge: React.FC<DecisionBadgeProps> = ({ decision }) => {
  const badge = getDecisionBadge(decision);

  const getBadgeStyles = () => {
    switch (decision.toUpperCase()) {
      case "SIMULATED_HOLD":
      case "REJECT":
      case "HOLD":
        return {
          container: "bg-danger-light text-danger-dark border-danger/20",
          dot: "bg-danger",
          label: "Simulated Hold",
        };
      case "REVIEW":
        return {
          container: "bg-warning-light text-warning-dark border-warning/20",
          dot: "bg-warning",
          label: "Analyst Review",
        };
      case "ALLOW":
      case "ALLOW_TRANSACTION":
        return {
          container: "bg-success-light text-success-dark border-success/20",
          dot: "bg-success",
          label: "Allow & Monitor",
        };
      default:
        return {
          container: "bg-page text-text-secondary border-card-border",
          dot: "bg-slate-400",
          label: badge.label || decision,
        };
    }
  };

  const styles = getBadgeStyles();

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${styles.container} transition-all`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${styles.dot}`} />
      <span>{styles.label}</span>
    </div>
  );
};
