import time
import uuid
import threading
import logging
from typing import List, Dict, Optional, Any
from app.models.schemas import (
    TransactionInput,
    Alert,
    CaseEvidence,
    ScoreResponse,
    BatchScoreRequest,
    BatchScoreResponse,
    BatchScoreSummary,
    AlertDetailResponse,
)
from app.detection.rules_engine import RulesEngine
from app.detection.ml_classifier import MLClassifier
from app.detection.explainer import Explainer
from app.detection.graph_analyzer import GraphAnalyzer
from app.triage.cost_policy import CostPolicy
from app.triage.case_builder import CaseBuilder
from app.triage.audit_logger import audit_logger, AuditLogger
from app.config import settings

logger = logging.getLogger("sentinel.scoring_pipeline")


class ScoringPipeline:
    """
    Central orchestration service executing all 4 layers in order:
    1. Layer 1: Rules Engine (deterministic gating)
    2. Layer 2: Calibrated ML Classifier + SHAP explanations
    3. Layer 3: Linked-Entity Graph Context
    4. Layer 4: Cost Policy Decision Routing & Cryptographic Audit Trail Generation
    
    Includes precision latency benchmarking across the 4-layer scoring path.
    """

    def __init__(self):
        self.rules_engine = RulesEngine()
        self.ml_classifier = MLClassifier()
        self.explainer = Explainer()
        self.graph_analyzer = GraphAnalyzer()
        self.cost_policy = CostPolicy()
        self.case_builder = CaseBuilder()
        self.audit_logger = audit_logger

        self._lock = threading.Lock()
        self._scored_alerts: Dict[str, Dict[str, Any]] = {}

    def process(self, txn: TransactionInput) -> ScoreResponse:
        """
        Executes end-to-end scoring pipeline on a single payment transaction.
        Measures execution latency across the 4-layer inference execution path.
        """
        txn_id = txn.transactionId or f"TXN-{uuid.uuid4().hex[:8].upper()}"
        now_ms = int(time.time() * 1000) if txn.timestamp is None else txn.timestamp
        amount = float(txn.amount)

        # Latency Benchmark Start
        start_time = time.perf_counter()

        # Layer 1: Deterministic Rules
        rule_triggers, reason_codes = self.rules_engine.evaluate(txn)

        # Layer 2: Calibrated ML Classifier & SHAP Explanations
        risk_score = self.ml_classifier.predict_proba(txn)
        shap_contributions = self.explainer.explain(
            txn,
            risk_score,
            model=self.ml_classifier.model,
        )

        # Layer 3: Linked-Entity Graph
        graph_context = self.graph_analyzer.analyze(txn, risk_score)
        if graph_context.clusterId and "GRAPH_CLUSTER_RISK" not in reason_codes and risk_score >= 0.4:
            reason_codes.append("GRAPH_CLUSTER_RISK")

        # Layer 4: Cost Policy & Decision Routing
        decision = self.cost_policy.route_decision(risk_score, amount)
        cost_breakdown = self.cost_policy.calculate_cost_breakdown(amount, risk_score)

        # Calculate inference latency in milliseconds
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            f"[Sentinel Pipeline] Transaction {txn_id} scored in {latency_ms:.2f}ms "
            f"(Decision: {decision}, Risk: {risk_score:.4f}, ExpectedLoss: ₹{cost_breakdown.expectedFraudLoss:,.2f})"
        )

        # Audit Logger Hash Chain Entry (persisted to SQLite)
        evidence_dict = {
            "amount": amount,
            "risk_score": risk_score,
            "decision": decision,
            "rules_count": len(rule_triggers),
            "cluster_id": graph_context.clusterId,
            "expected_fraud_loss": cost_breakdown.expectedFraudLoss,
        }
        audit_hash = self.audit_logger.log_decision(
            transaction_id=txn_id,
            timestamp=now_ms,
            decision=decision,
            model_version=settings.MODEL_VERSION,
            evidence=evidence_dict,
        )

        # Build Alert and CaseEvidence objects
        alert = self.case_builder.build_alert(
            transaction_id=txn_id,
            timestamp=now_ms,
            amount=amount,
            risk_score=risk_score,
            decision=decision,
            reason_codes=reason_codes,
            expected_cost=cost_breakdown.expectedFraudLoss,
            linked_entity_count=graph_context.clusterSize,
            model_version=settings.MODEL_VERSION,
            latency_ms=latency_ms,
        )

        evidence = self.case_builder.build_evidence(
            shap_contributions=shap_contributions,
            rule_triggers=rule_triggers,
            graph_context=graph_context,
            cost_breakdown=cost_breakdown,
            audit_hash=audit_hash,
        )

        # Store in pipeline cache for rapid hero view lookup
        with self._lock:
            self._scored_alerts[txn_id] = {
                "alert": alert,
                "evidence": evidence,
                "txn": txn,
                "status": "pending",
                "latency_ms": latency_ms,
            }

        return ScoreResponse(alert=alert, evidence=evidence, latencyMs=latency_ms)

    def process_batch(self, batch: BatchScoreRequest) -> BatchScoreResponse:
        """
        Executes high-throughput scoring on a batch of transactions.
        Calculates aggregate batch and per-transaction latency benchmarks.
        """
        batch_start_time = time.perf_counter()
        alerts: List[Alert] = []
        hold_count = 0
        review_count = 0
        allow_count = 0
        total_expected_loss = 0.0
        total_risk_score = 0.0
        total_latency_ms = 0.0

        for idx, txn in enumerate(batch.transactions):
            if not txn.transactionId:
                txn.transactionId = f"TXN-B{(idx + 1):04d}-{uuid.uuid4().hex[:4].upper()}"

            resp = self.process(txn)
            alert = resp.alert
            alerts.append(alert)

            if alert.decision == "SIMULATED_HOLD":
                hold_count += 1
            elif alert.decision == "REVIEW":
                review_count += 1
            else:
                allow_count += 1

            total_expected_loss += alert.expectedCost
            total_risk_score += alert.riskScore
            if alert.latencyMs is not None:
                total_latency_ms += alert.latencyMs

        total_batch_latency_ms = round((time.perf_counter() - batch_start_time) * 1000, 2)
        avg_score = round(total_risk_score / len(alerts), 4) if alerts else 0.0
        avg_latency_ms = round(total_latency_ms / len(alerts), 2) if alerts else 0.0

        logger.info(
            f"[Sentinel Pipeline] Batch processed {len(alerts)} transactions in {total_batch_latency_ms:.2f}ms "
            f"(Avg: {avg_latency_ms:.2f}ms/txn, Holds: {hold_count}, Reviews: {review_count}, Allows: {allow_count})"
        )

        return BatchScoreResponse(
            totalProcessed=len(alerts),
            alerts=alerts,
            summary=BatchScoreSummary(
                simulatedHoldCount=hold_count,
                reviewCount=review_count,
                allowCount=allow_count,
                totalExpectedLoss=round(total_expected_loss, 2),
                averageRiskScore=avg_score,
                averageLatencyMs=avg_latency_ms,
            ),
            latencyMs=total_batch_latency_ms,
        )

    def get_alert_detail(self, transaction_id: str) -> Optional[AlertDetailResponse]:
        """Retrieves complete case detail for an alert if present in scored cache."""
        with self._lock:
            cached = self._scored_alerts.get(transaction_id)
            if not cached:
                return None
            
            alert: Alert = cached["alert"]
            evidence: CaseEvidence = cached["evidence"]
            txn: Optional[TransactionInput] = cached.get("txn")
            status: str = cached.get("status", "pending")
            
            trail = self.audit_logger.get_audit_trail(transaction_id)
            return self.case_builder.build_case_detail(
                alert=alert,
                evidence=evidence,
                txn=txn,
                status=status,
                audit_trail=trail,
            )

    def update_alert_status(self, transaction_id: str, status: str):
        with self._lock:
            if transaction_id in self._scored_alerts:
                self._scored_alerts[transaction_id]["status"] = status

    def get_all_alerts(self) -> List[Alert]:
        with self._lock:
            return [data["alert"] for data in self._scored_alerts.values()]


scoring_pipeline = ScoringPipeline()
