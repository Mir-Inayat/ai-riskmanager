import pytest
from app.models.schemas import TransactionInput, BatchScoreRequest
from app.detection.rules_engine import RulesEngine
from app.detection.ml_classifier import MLClassifier
from app.detection.explainer import Explainer
from app.detection.graph_analyzer import GraphAnalyzer
from app.detection.drift_monitor import DriftMonitor
from app.detection.benford_signal import BenfordSignal
from app.triage.cost_policy import CostPolicy
from app.triage.case_builder import CaseBuilder
from app.triage.audit_logger import AuditLogger
from app.services.scoring_pipeline import ScoringPipeline


def test_rules_engine_deterministic_checks():
    rules = RulesEngine()

    # High amount + disposable email + unusual device
    txn_high = TransactionInput(
        amount=15000.0,
        P_emaildomain="user@disposable-mail.xyz",
        DeviceType="proxy",
        dist1=650.0,
        ProductCD="C",
    )
    triggers, reason_codes = rules.evaluate(txn_high)
    trigger_ids = [t.ruleId for t in triggers]
    
    assert "RULE-001" in trigger_ids
    assert "RULE-045" in trigger_ids
    assert "RULE-089" in trigger_ids
    assert "RULE-023" in trigger_ids
    assert "RULE-031" in trigger_ids
    assert "HIGH_VALUE_TRANSACTION" in reason_codes
    assert "NEW_EMAIL_DOMAIN" in reason_codes
    assert "UNUSUAL_DEVICE" in reason_codes
    assert "DISTANCE_ANOMALY" in reason_codes
    assert "HIGH_RISK_MERCHANT_CATEGORY" in reason_codes

    # Normal low-risk transaction
    txn_low = TransactionInput(
        amount=45.0,
        P_emaildomain="gmail.com",
        DeviceType="mobile",
    )
    triggers_low, reason_codes_low = rules.evaluate(txn_low)
    assert len(triggers_low) == 0
    assert len(reason_codes_low) == 0

    # ProtonMail transaction - should NOT be flagged as disposable
    txn_proton = TransactionInput(
        amount=50.0,
        P_emaildomain="proton.me",
        DeviceType="desktop",
    )
    triggers_proton, reason_codes_proton = rules.evaluate(txn_proton)
    assert "RULE-045" not in [t.ruleId for t in triggers_proton]
    assert "NEW_EMAIL_DOMAIN" not in reason_codes_proton


def test_ml_classifier_scoring():
    clf = MLClassifier()
    
    # High risk transaction
    txn_risk = TransactionInput(
        amount=12500.0,
        P_emaildomain="temp-mail.xyz",
        DeviceType="tor",
        ProductCD="C",
    )
    score_high = clf.predict_proba(txn_risk)
    assert 0.0 <= score_high <= 1.0
    assert score_high >= 0.70

    # Low risk transaction
    txn_safe = TransactionInput(
        amount=35.0,
        P_emaildomain="gmail.com",
        DeviceType="mobile",
        ProductCD="W",
    )
    score_low = clf.predict_proba(txn_safe)
    assert 0.0 <= score_low <= 1.0
    assert score_low <= 0.30


def test_explainer_shap_contributions():
    explainer = Explainer()
    txn = TransactionInput(
        amount=25000.0,
        P_emaildomain="temp.xyz",
        DeviceType="emulator",
    )
    shap = explainer.explain(txn, risk_score=0.88)
    assert isinstance(shap, list)
    assert len(shap) > 0
    features = [s.feature for s in shap]
    assert "TransactionAmt" in features
    for item in shap:
        assert isinstance(item.contribution, float)


def test_graph_analyzer_entity_links():
    analyzer = GraphAnalyzer()
    
    # High risk transaction with entity identifiers
    txn = TransactionInput(
        transactionId="TXN-TEST-G1",
        amount=5000.0,
        card1="4412",
        P_emaildomain="xyz.com",
        DeviceInfo="device_test_1",
    )
    ctx = analyzer.analyze(txn, risk_score=0.75)
    assert ctx.clusterId is not None
    assert "CLUSTER-" in ctx.clusterId
    assert ctx.clusterSize > 0
    assert len(ctx.sharedAttributes) >= 2

    # Graph summary network structure
    summary = analyzer.get_graph_summary()
    assert len(summary.nodes) > 0
    assert len(summary.links) > 0


def test_drift_monitor_health():
    monitor = DriftMonitor()
    drift = monitor.check_health()
    assert drift.status in ["HEALTHY", "WARNING", "CRITICAL"]
    assert "TransactionAmt" in drift.ksPValues
    assert "card1" in drift.ksPValues
    assert "delayedRetrospective" in drift.model_dump()
    assert "precision" in drift.delayedRetrospective
    assert "recall" in drift.delayedRetrospective


def test_benford_signal_gating():
    benford = BenfordSignal()
    resp = benford.analyze()
    assert resp.status in ["HIGH_CONFIDENCE", "CAUTION", "NOT_APPLICABLE"]
    assert len(resp.digitDistribution) == 9
    assert resp.mad >= 0.0
    assert "Portfolio-level distribution signal" in resp.disclaimer

    # Small sample triggering NOT_APPLICABLE gate
    small_resp = benford.analyze(amounts=[10.0, 20.0, 30.0])
    assert small_resp.status == "NOT_APPLICABLE"


def test_cost_policy_triage_routing():
    policy = CostPolicy(
        friction_cost_fp=150.0,
        review_cost=25.0,
        hold_threshold=0.75,
        review_threshold=0.40,
    )
    
    # 3-tier routing
    assert policy.route_decision(risk_score=0.85, amount=1000.0) == "SIMULATED_HOLD"
    assert policy.route_decision(risk_score=0.55, amount=1000.0) == "REVIEW"
    assert policy.route_decision(risk_score=0.20, amount=1000.0) == "ALLOW"

    # Cost breakdown
    cb = policy.calculate_cost_breakdown(amount=10000.0, risk_score=0.80)
    assert cb.expectedFraudLoss == 8000.0
    assert cb.frictionCostIfFP == 150.0
    assert cb.reviewCost == 25.0
    assert cb.netExposure == 7850.0

    # Policy simulation
    sim = policy.simulate(friction_cost_fp=200.0, review_cost=30.0, review_capacity=100)
    assert sim.optimalThresholdHold >= 0.50
    assert sim.optimalThresholdReview < sim.optimalThresholdHold
    assert sim.simulatedHoldCount >= 0
    assert sim.simulatedReviewCount >= 0
    assert sim.simulatedAllowCount >= 0


def test_audit_logger_hash_chain_integrity():
    logger = AuditLogger()
    
    h1 = logger.log_decision(
        transaction_id="TXN-001",
        timestamp=1000,
        decision="SIMULATED_HOLD",
        model_version="v1",
        evidence={"score": 0.9},
    )
    assert len(h1) == 64

    h2 = logger.log_decision(
        transaction_id="TXN-002",
        timestamp=2000,
        decision="ALLOW",
        model_version="v1",
        evidence={"score": 0.1},
    )
    assert len(h2) == 64
    assert h1 != h2

    # Analyst decision
    h3 = logger.log_analyst_decision(
        transaction_id="TXN-001",
        decision="APPROVE_HOLD",
        reviewer="analyst_test",
        notes="Confirmed fraudulent cluster",
        timestamp=3000,
    )
    assert len(h3) == 64

    # Cryptographic integrity verification
    assert logger.verify_integrity() is True

    # Audit trail retrieval
    trail = logger.get_audit_trail("TXN-001")
    assert len(trail) == 2
    assert trail[0].step == "COST_POLICY_ROUTING"
    assert trail[1].step == "ANALYST_REVIEW"


def test_scoring_pipeline_end_to_end():
    pipeline = ScoringPipeline()

    txn = TransactionInput(
        transactionId="TXN-E2E-001",
        amount=18000.0,
        P_emaildomain="fraudster@disposable.top",
        DeviceType="tor",
        card1="5500",
    )
    resp = pipeline.process(txn)
    
    # Check Alert
    alert = resp.alert
    assert alert.transactionId == "TXN-E2E-001"
    assert alert.amount == 18000.0
    assert alert.decision == "SIMULATED_HOLD"
    assert alert.riskScore >= 0.75
    assert len(alert.reasonCodes) > 0
    assert alert.expectedCost > 0

    # Check Evidence
    evidence = resp.evidence
    assert len(evidence.shapContributions) > 0
    assert len(evidence.ruleTriggers) > 0
    assert evidence.graphContext.clusterId is not None
    assert evidence.costBreakdown.netExposure > 0
    assert len(evidence.auditHash) == 64

    # Verify Hero Detail retrieval
    detail = pipeline.get_alert_detail("TXN-E2E-001")
    assert detail is not None
    assert detail.transactionId == "TXN-E2E-001"
    assert len(detail.auditTrail) >= 3
    assert detail.latencyMs is not None
    assert detail.latencyMs >= 0.0

    # Verify latency metric in response and alert
    assert resp.latencyMs is not None
    assert resp.latencyMs >= 0.0
    assert alert.latencyMs is not None
    assert alert.latencyMs == resp.latencyMs


def test_scoring_pipeline_batch_50_plus():
    pipeline = ScoringPipeline()
    batch_txns = [
        TransactionInput(
            transactionId=f"TXN-BATCH-{i:03d}",
            amount=50.0 * (i % 20 + 1) if i % 5 != 0 else 12000.0,
            P_emaildomain="disposable.xyz" if i % 5 == 0 else "gmail.com",
            DeviceType="proxy" if i % 10 == 0 else "mobile",
        )
        for i in range(1, 60)
    ]
    batch_req = BatchScoreRequest(transactions=batch_txns)
    batch_resp = pipeline.process_batch(batch_req)

    assert batch_resp.totalProcessed == 59
    assert len(batch_resp.alerts) == 59
    assert batch_resp.summary.simulatedHoldCount >= 0
    assert batch_resp.summary.reviewCount >= 0
    assert batch_resp.summary.allowCount >= 0
    assert batch_resp.summary.totalExpectedLoss > 0
    assert 0.0 <= batch_resp.summary.averageRiskScore <= 1.0
    assert batch_resp.latencyMs is not None
    assert batch_resp.latencyMs > 0.0
    assert batch_resp.summary.averageLatencyMs is not None
    assert batch_resp.summary.averageLatencyMs > 0.0


def test_audit_logger_sqlite_persistence_and_tamper_detection():
    from app.database import get_db

    logger1 = AuditLogger()
    h1 = logger1.log_decision(
        transaction_id="TXN-PERSIST-1",
        timestamp=100000,
        decision="SIMULATED_HOLD",
        model_version="v1",
        evidence={"score": 0.95},
    )
    h2 = logger1.log_decision(
        transaction_id="TXN-PERSIST-2",
        timestamp=100050,
        decision="ALLOW",
        model_version="v1",
        evidence={"score": 0.05},
    )

    # A separate logger instance reading from the same DB should verify integrity
    logger2 = AuditLogger()
    assert logger2.latest_hash == h2
    assert logger2.verify_integrity() is True
    
    entries = logger2.get_entries_for_transaction("TXN-PERSIST-1")
    assert len(entries) == 1
    assert entries[0]["hash"] == h1
    assert entries[0]["evidence"]["score"] == 0.95

    # Tamper with the evidence in SQLite directly
    with get_db(logger1.db_path) as conn:
        conn.execute("UPDATE audit_log SET decision = 'ALLOW' WHERE transaction_id = 'TXN-PERSIST-1'")

    # Cryptographic integrity check should immediately detect tampering and fail
    assert logger2.verify_integrity() is False
