import React from "react";
import { LucideIcon } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  badge?: string;
  badgeType?: "neutral" | "positive" | "warning" | "danger" | "accent";
  icon: LucideIcon;
  iconColor?: string;
  glow?: "rose" | "amber" | "cyan" | "emerald" | "none";
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  badge,
  badgeType = "neutral",
  icon: Icon,
  iconColor,
  glow = "none",
}) => {
  const getBadgeClass = () => {
    switch (badgeType) {
      case "positive":
        return "bg-success-light text-success-dark border border-success/20";
      case "warning":
        return "bg-warning-light text-warning-dark border border-warning/20";
      case "danger":
        return "bg-danger-light text-danger-dark border border-danger/20";
      case "accent":
        return "bg-brand-50 text-brand-700 border border-brand-200";
      default:
        return "bg-page text-text-secondary border border-card-border";
    }
  };

  const getIconContainerClass = () => {
    switch (badgeType) {
      case "positive":
        return "bg-success-light text-success-dark";
      case "warning":
        return "bg-warning-light text-warning-dark";
      case "danger":
        return "bg-danger-light text-danger-dark";
      case "accent":
        return "bg-brand-50 text-brand-600";
      default:
        return "bg-brand-50 text-brand-600";
    }
  };

  return (
    <div className="bg-card rounded-card shadow-card border border-card-border p-6 transition-all duration-200 hover:shadow-card-hover flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between gap-3 mb-3">
          <span className="text-xs font-semibold text-text-muted uppercase tracking-wide">
            {title}
          </span>
          <div className={`p-2.5 rounded-xl shrink-0 ${getIconContainerClass()}`}>
            <Icon className="w-5 h-5" />
          </div>
        </div>
        <div className="text-2xl font-bold text-text-primary tracking-tight">
          {value}
        </div>
      </div>

      {(subtitle || badge) && (
        <div className="mt-4 pt-3 flex items-center justify-between gap-2 border-t border-card-border text-xs">
          {subtitle && (
            <span className="text-text-secondary truncate">{subtitle}</span>
          )}
          {badge && (
            <span
              className={`px-2.5 py-0.5 rounded-badge text-[11px] font-semibold shrink-0 ${getBadgeClass()}`}
            >
              {badge}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
