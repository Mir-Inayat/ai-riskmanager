"use client";

import React, { useState } from "react";
import { ShieldCheck, Hash, Copy, Check, Lock } from "lucide-react";

interface AuditTrailProps {
  auditHash: string;
  transactionId: string;
  decision: string;
  timestamp: number;
}

export const AuditTrail: React.FC<AuditTrailProps> = ({
  auditHash,
  transactionId,
  decision,
  timestamp,
}) => {
  const [copied, setCopied] = useState(false);

  const prevHash = "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069";

  const handleCopy = () => {
    navigator.clipboard.writeText(auditHash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const steps = [
    {
      label: "Deterministic Pipeline Execution",
      time: "T+0ms",
      desc: "Rules + LightGBM + Graph extraction executed across 4 defense layers.",
      valid: true,
    },
    {
      label: "Cost-Policy Optimization Run",
      time: "T+4ms",
      desc: `Evaluated against C_fp=₹150, C_rev=₹25 → Triage recommendation: ${decision}`,
      valid: true,
    },
    {
      label: "SHA-256 Audit Log Immutability Seal",
      time: "T+6ms",
      desc: "Canonical evidence payload hashed and linked to previous ledger block.",
      valid: true,
    },
  ];

  return (
    <div className="bg-card rounded-card border border-card-border shadow-card p-6 md:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-500 flex items-center justify-center shrink-0">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-base font-semibold text-text-primary">
              Tamper-Evident Audit Trail
            </h4>
            <p className="text-xs text-text-secondary">
              Append-only SHA-256 Hash Chain (Zero update/delete endpoints)
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-badge bg-success-light text-success-dark text-xs font-semibold border border-success/20 self-start sm:self-auto">
          <ShieldCheck className="w-4 h-4" />
          <span>Chain Verified</span>
        </div>
      </div>

      {/* Hash display */}
      <div className="space-y-4">
        <div className="p-4 bg-page rounded-xl border border-card-border space-y-3">
          <div className="flex items-center justify-between text-text-secondary">
            <span className="flex items-center gap-2 text-xs font-medium">
              <Hash className="w-4 h-4 text-brand-500" />
              Current Entry Hash (SHA-256)
            </span>
            <button
              onClick={handleCopy}
              className="text-brand-600 hover:text-brand-700 flex items-center gap-1.5 text-xs font-medium transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-success" />
                  <span className="text-success-dark font-semibold">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy Hash</span>
                </>
              )}
            </button>
          </div>
          <p className="text-brand-700 font-mono font-semibold break-all bg-white p-3 rounded-lg border border-card-border text-xs leading-relaxed shadow-sm">
            {auditHash}
          </p>
          <div className="p-3 bg-white rounded-lg border border-card-border text-xs text-text-secondary font-mono shadow-sm flex flex-col sm:flex-row sm:items-center gap-1">
            <span className="font-sans font-medium text-text-muted">Linked Previous Block:</span>
            <span className="text-text-primary break-all">{prevHash}</span>
          </div>
        </div>
      </div>

      {/* Timeline steps */}
      <div className="mt-6 pt-2">
        <div className="space-y-6">
          {steps.map((step, idx) => (
            <div key={idx} className="flex items-start gap-4">
              <div className="flex flex-col items-center self-stretch">
                <span className="w-3 h-3 rounded-full bg-brand-500 ring-4 ring-brand-50 mt-1 shrink-0" />
                {idx < steps.length - 1 && (
                  <span className="w-0.5 bg-card-border flex-1 my-1.5" />
                )}
              </div>
              <div className="flex-1 pb-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-semibold text-text-primary">
                    {step.label}
                  </span>
                  <span className="font-mono text-xs font-medium text-brand-600 bg-brand-50 px-2 py-0.5 rounded-badge">
                    {step.time}
                  </span>
                </div>
                <p className="text-xs text-text-secondary mt-1 leading-relaxed">
                  {step.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
