import pytest


def test_health_checks(client):
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "online"

    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"


def test_score_single_transaction(client):
    payload = {
        "transactionId": "TXN-TEST-001",
        "amount": 45000.50,
        "P_emaildomain": "disposable-mail.xyz",
        "DeviceType": "proxy",
    }
    response = client.post("/api/transactions/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Validate Alert contract
    assert "alert" in data
    alert = data["alert"]
    assert alert["transactionId"] == "TXN-TEST-001"
    assert alert["amount"] == 45000.50
    assert 0.0 <= alert["riskScore"] <= 1.0
    assert alert["decision"] in ["ALLOW", "REVIEW", "SIMULATED_HOLD"]
    assert isinstance(alert["reasonCodes"], list)
    assert alert["expectedCost"] > 0
    assert "modelVersion" in alert

    # Validate latency benchmarking
    assert "latencyMs" in data
    assert data["latencyMs"] is not None
    assert data["latencyMs"] >= 0.0
    assert "latencyMs" in alert
    assert alert["latencyMs"] is not None

    # Validate CaseEvidence contract
    assert "evidence" in data
    evidence = data["evidence"]
    assert "shapContributions" in evidence
    assert isinstance(evidence["shapContributions"], list)
    assert "ruleTriggers" in evidence
    assert "graphContext" in evidence
    assert "costBreakdown" in evidence
    assert "auditHash" in evidence


def test_score_batch_transactions(client):
    batch = {
        "transactions": [
            {"transactionId": f"TXN-BATCH-{i}", "amount": 100.0 * i}
            for i in range(1, 10)
        ]
    }
    response = client.post("/api/transactions/batch", json=batch)
    assert response.status_code == 200
    data = response.json()
    assert data["totalProcessed"] == 9
    assert len(data["alerts"]) == 9
    assert "summary" in data
    assert data["summary"]["simulatedHoldCount"] >= 0
    assert "latencyMs" in data
    assert data["latencyMs"] is not None
    assert data["latencyMs"] > 0.0
    assert "averageLatencyMs" in data["summary"]
    assert data["summary"]["averageLatencyMs"] is not None
    assert data["summary"]["averageLatencyMs"] > 0.0


def test_list_alerts(client):
    response = client.get("/api/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert isinstance(alerts, list)
    assert len(alerts) >= 3

    # Check filtering by risk tier
    res_hold = client.get("/api/alerts?risk_tier=SIMULATED_HOLD")
    assert res_hold.status_code == 200
    holds = res_hold.json()
    for h in holds:
        assert h["decision"] == "SIMULATED_HOLD"


def test_get_alert_detail(client):
    response = client.get("/api/alerts/TXN-98234-A")
    assert response.status_code == 200
    detail = response.json()
    assert detail["transactionId"] == "TXN-98234-A"
    assert "shapContributions" in detail
    assert "ruleTriggers" in detail
    assert "graphContext" in detail
    assert "costBreakdown" in detail
    assert "auditTrail" in detail
    assert len(detail["auditTrail"]) > 0


def test_submit_analyst_decision(client):
    payload = {
        "decision": "APPROVE_HOLD",
        "reviewer": "senior_analyst_42",
        "notes": "Verified fraudulent pattern across linked device cluster."
    }
    response = client.post("/api/alerts/TXN-98234-A/decision", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["decision"] == "APPROVE_HOLD"
    assert len(data["auditHash"]) == 64  # SHA-256 length


def test_detection_metrics(client):
    response = client.get("/api/metrics/detection")
    assert response.status_code == 200
    metrics = response.json()
    assert "precision" in metrics
    assert "recall" in metrics
    assert "prAuc" in metrics
    assert "recallAtBudget" in metrics
    assert "preventableExposureCaptured" in metrics
    assert "falsePositiveCost" in metrics
    assert 0.0 <= metrics["precision"] <= 1.0
    assert 0.0 <= metrics["recall"] <= 1.0


def test_cost_metrics(client):
    response = client.get("/api/metrics/cost")
    assert response.status_code == 200
    data = response.json()
    assert "expectedCost" in data
    assert "netPreventedExposure" in data
    assert "falsePositiveCost" in data
    assert "totalExposure" in data
    assert data["expectedCost"] >= 0.0


def test_simulate_cost(client):
    payload = {
        "frictionCostIfFP": 200.0,
        "reviewCost": 30.0,
        "reviewCapacity": 120,
    }
    response = client.post("/api/metrics/simulate-cost", json=payload)
    assert response.status_code == 200
    sim = response.json()
    assert "optimalThresholdHold" in sim
    assert "optimalThresholdReview" in sim
    assert sim["simulatedHoldCount"] >= 0
    assert sim["simulatedReviewCount"] >= 0


def test_threshold_curve(client):
    response = client.get("/api/metrics/threshold-curve")
    assert response.status_code == 200
    curve = response.json()
    assert "points" in curve
    assert len(curve["points"]) == 9
    assert curve["recommendedThreshold"] == 0.50


def test_model_comparison(client):
    response = client.get("/api/metrics/model-comparison")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) == 3
    assert data["models"][2]["name"] == "LightGBM + Calibrated Cost Policy (Sentinel)"


def test_analytics_endpoints(client):
    # Benford
    res_benford = client.get("/api/analytics/benford")
    assert res_benford.status_code == 200
    assert res_benford.json()["status"] in ["CAUTION", "HIGH_CONFIDENCE"]
    assert len(res_benford.json()["digitDistribution"]) == 9

    # Graph Summary
    res_graph = client.get("/api/analytics/graph-summary")
    assert res_graph.status_code == 200
    assert "nodes" in res_graph.json()
    assert "links" in res_graph.json()

    # Drift
    res_drift = client.get("/api/analytics/drift")
    assert res_drift.status_code == 200
    assert res_drift.json()["status"] == "HEALTHY"

    # Distributions
    res_dist = client.get("/api/analytics/distributions")
    assert res_dist.status_code == 200
    assert "amountBins" in res_dist.json()
    assert "riskScoreDistribution" in res_dist.json()
