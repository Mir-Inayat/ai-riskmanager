from typing import List, Optional, Dict, Any
from app.models.schemas import (
    TransactionInput,
    Alert,
    CaseEvidence,
    ShapContribution,
    RuleTrigger,
    GraphContext,
    CostBreakdown,
    AlertDetailResponse,
    AuditTrailEntry,
)
from app.config import settings


class CaseBuilder:
    """
    Assembles deterministic case evidence from all detection layers.
    No LLM dependency for reproducible, instant investigation evidence.
    """

    def build_alert(
        self,
        transaction_id: str,
        timestamp: int,
        amount: float,
        risk_score: float,
        decision: str,
        reason_codes: List[str],
        expected_cost: float,
        linked_entity_count: int,
        model_version: Optional[str] = None,
        latency_ms: Optional[float] = None,
    ) -> Alert:
        return Alert(
            transactionId=transaction_id,
            timestamp=timestamp,
            amount=amount,
            riskScore=risk_score,
            decision=decision,
            reasonCodes=reason_codes,
            expectedCost=expected_cost,
            linkedEntityCount=linked_entity_count,
            modelVersion=model_version or settings.MODEL_VERSION,
            latencyMs=latency_ms,
        )

    def build_evidence(
        self,
        shap_contributions: List[ShapContribution],
        rule_triggers: List[RuleTrigger],
        graph_context: GraphContext,
        cost_breakdown: CostBreakdown,
        audit_hash: str,
    ) -> CaseEvidence:
        return CaseEvidence(
            shapContributions=shap_contributions,
            ruleTriggers=rule_triggers,
            graphContext=graph_context,
            costBreakdown=cost_breakdown,
            auditHash=audit_hash,
        )

    def build_audit_trail_steps(
        self,
        timestamp: int,
        rule_triggers: List[RuleTrigger],
        risk_score: float,
        decision: str,
        cost_breakdown: CostBreakdown,
        audit_hash: str,
    ) -> List[AuditTrailEntry]:
        """Creates structured audit trail steps for each phase of detection."""
        rules_desc = f"Triggered {len(rule_triggers)} rules" if rule_triggers else "Zero deterministic rules triggered"
        if rule_triggers:
            high_count = sum(1 for r in rule_triggers if r.severity == "HIGH")
            med_count = sum(1 for r in rule_triggers if r.severity == "MEDIUM")
            rules_desc += f" ({high_count} HIGH, {med_count} MEDIUM)"

        return [
            AuditTrailEntry(
                step="RULE_EVALUATION",
                timestamp=timestamp,
                action=rules_desc,
                hash=f"{audit_hash[:16]}...rule",
            ),
            AuditTrailEntry(
                step="ML_SCORING",
                timestamp=timestamp + 50,
                action=f"LightGBM score {risk_score:.2f} (calibrated probability)",
                hash=f"{audit_hash[16:32]}...ml",
            ),
            AuditTrailEntry(
                step="COST_POLICY_ROUTING",
                timestamp=timestamp + 100,
                action=f"Decision: {decision} (Expected loss ₹{cost_breakdown.expectedFraudLoss:,.2f} vs Friction ₹{cost_breakdown.frictionCostIfFP:,.2f})",
                hash=audit_hash,
            ),
        ]

    def build_case_detail(
        self,
        alert: Alert,
        evidence: CaseEvidence,
        txn: Optional[TransactionInput] = None,
        status: str = "pending",
        audit_trail: Optional[List[AuditTrailEntry]] = None,
    ) -> AlertDetailResponse:
        """Assembles full Hero Case Investigation response."""
        txn_details: Dict[str, Any] = {}
        if txn:
            txn_details = {
                "cardFingerprint": f"CARD-{txn.card1 or 'XXXX'}",
                "emailDomain": txn.P_emaildomain or "N/A",
                "addressHash": f"ADDR-{txn.addr1 or 'N/A'}",
                "deviceType": txn.DeviceType or "N/A",
                "deviceHash": txn.DeviceInfo or "N/A",
                "productCD": txn.ProductCD or "W",
                "channel": "e-commerce",
            }
        else:
            txn_details = {
                "cardFingerprint": "CARD-4412-XXXX",
                "emailDomain": "xyz.com",
                "addressHash": "ADDR-90210",
                "deviceType": "mobile",
                "deviceHash": "device_hash_123",
                "productCD": "W",
                "channel": "e-commerce",
            }

        base_steps = self.build_audit_trail_steps(
            timestamp=alert.timestamp,
            rule_triggers=evidence.ruleTriggers,
            risk_score=alert.riskScore,
            decision=alert.decision,
            cost_breakdown=evidence.costBreakdown,
            audit_hash=evidence.auditHash,
        )
        if audit_trail:
            for entry in audit_trail:
                if entry.step == "ANALYST_REVIEW":
                    base_steps.append(entry)
        trail = base_steps


        return AlertDetailResponse(
            transactionId=alert.transactionId,
            timestamp=alert.timestamp,
            amount=alert.amount,
            riskScore=alert.riskScore,
            decision=alert.decision,
            status=status,
            reasonCodes=alert.reasonCodes,
            expectedCost=alert.expectedCost,
            linkedEntityCount=alert.linkedEntityCount,
            modelVersion=alert.modelVersion,
            latencyMs=alert.latencyMs,
            shapContributions=evidence.shapContributions,
            ruleTriggers=evidence.ruleTriggers,
            graphContext=evidence.graphContext,
            costBreakdown=evidence.costBreakdown,
            auditHash=evidence.auditHash,
            transactionDetails=txn_details,
            auditTrail=trail,
        )

