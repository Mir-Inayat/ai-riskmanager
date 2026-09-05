import React from "react";
import { AlertCircle, AlertTriangle, Info } from "lucide-react";

interface RuleTrigger {
  ruleId: string;
  severity: string;
  explanation: string;
}

interface RuleTriggersListProps {
  ruleTriggers: RuleTrigger[];
}

export const RuleTriggersList: React.FC<RuleTriggersListProps> = ({ ruleTriggers }) => {
  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case "CRITICAL":
      case "HIGH":
        return {
          icon: AlertCircle,
          iconColor: "text-danger",
          dot: "bg-danger",
          badge: "bg-danger-light text-danger-dark border-danger/20",
        };
      case "MEDIUM":
        return {
          icon: AlertTriangle,
          iconColor: "text-warning",
          dot: "bg-warning",
          badge: "bg-warning-light text-warning-dark border-warning/20",
        };
      default:
        return {
          icon: Info,
          iconColor: "text-info",
          dot: "bg-info",
          badge: "bg-info-light text-info-dark border-info/20",
        };
    }
  };

  return (
    <div className="bg-card rounded-card border border-card-border shadow-card p-6 md:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-500 flex items-center justify-center shrink-0">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-base font-semibold text-text-primary">
              Layer 1: Deterministic Rule Triggers
            </h4>
            <p className="text-xs text-text-secondary">
              Heuristic velocity & anomaly gates triggered prior to ML inference
            </p>
          </div>
        </div>
        <span className="text-xs font-mono font-medium text-brand-700 bg-brand-50 px-3 py-1.5 rounded-badge border border-brand-100 self-start sm:self-auto">
          {ruleTriggers.length} Active {ruleTriggers.length === 1 ? "Rule" : "Rules"}
        </span>
      </div>

      {/* Rules list */}
      <div className="space-y-3">
        {ruleTriggers.map((rule, idx) => {
          const style = getSeverityBadge(rule.severity);
          const Icon = style.icon;

          return (
            <div
              key={idx}
              className="p-4 rounded-xl border border-card-border bg-page/50 hover:bg-white hover:border-brand-200 hover:shadow-card-hover transition-all duration-200"
            >
              <div className="flex items-start gap-3">
                <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${style.iconColor}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-xs font-semibold text-text-primary">
                      {rule.ruleId}
                    </span>
                    <span
                      className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-badge border ${style.badge}`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />
                      {rule.severity}
                    </span>
                  </div>
                  <p className="text-xs text-text-secondary leading-relaxed">
                    {rule.explanation}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
