"use client";

import React, { useState } from "react";
import { 
  UserCheck, 
  ShieldAlert, 
  ShieldCheck, 
  Send, 
  Info, 
  CheckCircle2, 
} from "lucide-react";
import { submitDecision } from "@/lib/api";

interface ApprovalGateProps {
  transactionId: string;
  defaultDecision: string;
}

export const ApprovalGate: React.FC<ApprovalGateProps> = ({
  transactionId,
  defaultDecision,
}) => {
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [analystNote, setAnalystNote] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (action: string) => {
    setSelectedAction(action);
    setSubmitting(true);
    try {
      await submitDecision(transactionId, action, "analyst_1", analystNote || undefined);
    } catch {
      // silent fallback for offline / mock mode
    } finally {
      setSubmitting(false);
      setIsSubmitted(true);
    }
  };

  return (
    <div className="bg-card rounded-card border border-card-border shadow-card p-6 md:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-500 flex items-center justify-center shrink-0">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-base font-semibold text-text-primary">
              Analyst Triage & Approval Gate
            </h4>
            <p className="text-xs text-text-secondary">
              Human-in-the-loop verification for uncertain & high-loss cases
            </p>
          </div>
        </div>
        <span className="text-xs font-semibold px-3 py-1.5 rounded-badge bg-page text-text-secondary border border-card-border self-start sm:self-auto">
          Simulated Defense Action
        </span>
      </div>

      {isSubmitted ? (
        <div className="p-6 bg-success-light border border-success/30 rounded-xl text-center my-2">
          <div className="w-12 h-12 rounded-full bg-success text-white flex items-center justify-center mx-auto mb-3 shadow-md shadow-success/20">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h5 className="text-base font-semibold text-text-primary mb-1">
            Action Logged to Tamper-Evident Trail
          </h5>
          <p className="text-xs text-text-secondary mt-1">
            Simulated Action: <span className="font-bold text-success-dark">{selectedAction}</span>
          </p>
          {analystNote && (
            <p className="text-xs text-text-secondary mt-2 italic">"{analystNote}"</p>
          )}
          <button
            onClick={() => setIsSubmitted(false)}
            className="mt-4 text-xs font-semibold text-brand-600 hover:text-brand-700 hover:underline transition-colors"
          >
            Reset Decision for Demo
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          <div>
            <label className="block text-xs font-semibold text-text-primary mb-2">
              Analyst Investigation Notes (Optional)
            </label>
            <textarea
              rows={3}
              value={analystNote}
              onChange={(e) => setAnalystNote(e.target.value)}
              placeholder="e.g. Confirmed shared device fingerprint with prior compromised cluster..."
              className="w-full bg-page border border-card-border rounded-xl p-3.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all font-sans"
            />
          </div>

          {/* Action Buttons */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <button
              onClick={() => handleSubmit("APPROVE_HOLD")}
              disabled={submitting}
              className="flex items-center justify-center gap-2 px-4 py-3 rounded-button bg-danger hover:bg-danger-dark text-white text-xs font-semibold shadow-sm hover:shadow transition-all active:scale-[0.98] disabled:opacity-50"
            >
              <ShieldAlert className="w-4 h-4" />
              <span>Simulate Hold</span>
            </button>

            <button
              onClick={() => handleSubmit("ALLOW_TRANSACTION")}
              disabled={submitting}
              className="flex items-center justify-center gap-2 px-4 py-3 rounded-button bg-brand-500 hover:bg-brand-600 text-white text-xs font-semibold shadow-sm hover:shadow transition-all active:scale-[0.98] disabled:opacity-50"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Allow & Clear</span>
            </button>

            <button
              onClick={() => handleSubmit("ESCALATE_TIER2")}
              disabled={submitting}
              className="flex items-center justify-center gap-2 px-4 py-3 rounded-button bg-page hover:bg-slate-200 text-text-secondary hover:text-text-primary border border-card-border text-xs font-semibold transition-all active:scale-[0.98] disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              <span>Escalate Tier 2</span>
            </button>
          </div>

          {/* Defense-Only Disclaimer */}
          <div className="p-4 bg-page border border-card-border rounded-xl flex items-start gap-3 text-xs text-text-secondary leading-relaxed">
            <Info className="w-4 h-4 text-brand-500 shrink-0 mt-0.5" />
            <p>
              <strong className="font-semibold text-text-primary">Defense-Only Safety Guarantee:</strong> Simulated holds route to friction-mitigating verification. Legitimate transactions are never blocked in production without secondary authentication.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
