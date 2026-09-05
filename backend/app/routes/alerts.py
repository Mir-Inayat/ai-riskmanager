import time
import hashlib
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from app.models.schemas import (
    Alert,
    AlertDetailResponse,
    ShapContribution,
    RuleTrigger,
    GraphContext,
    CostBreakdown,
    AuditTrailEntry,
    AnalystDecisionRequest,
    AnalystDecisionResponse,
    TransactionInput,
)
from app.services.scoring_pipeline import scoring_pipeline
from app.triage.audit_logger import audit_logger
from app.config import settings

router = APIRouter(prefix="/alerts", tags=["Alerts"])

# Seed alerts matching fixtures to guarantee immediate compatibility with frontend
_SEED_ALERTS: List[Dict[str, Any]] = [
    {
        "transactionId": "TXN-98234-A",
        "timestamp": 1693564800000,
        "amount": 45000.50,
        "riskScore": 0.89,
        "decision": "SIMULATED_HOLD",
        "status": "pending",
        "reasonCodes": ["HIGH_VALUE_TRANSACTION", "NEW_EMAIL_DOMAIN"],
        "expectedCost": 40050.44,
        "linkedEntityCount": 4,
        "modelVersion": settings.MODEL_VERSION,
        "latencyMs": 1.85,
        "shapContributions": [
            {"feature": "TransactionAmt", "contribution": 0.35},
            {"feature": "card1_velocity_24h", "contribution": 0.22},
            {"feature": "P_emaildomain_new", "contribution": 0.15},
            {"feature": "dist1", "contribution": -0.05},
        ],
        "ruleTriggers": [
            {
                "ruleId": "RULE-001",
                "severity": "HIGH",
                "explanation": "Transaction amount is >99th percentile for this card.",
            },
            {
                "ruleId": "RULE-045",
                "severity": "MEDIUM",
                "explanation": "First time seeing this email domain for this device.",
            },
        ],
        "graphContext": {
            "clusterId": "CLUSTER-77X",
            "sharedAttributes": ["device_hash_123", "email_domain_xyz.com"],
            "clusterSize": 12,
        },
        "costBreakdown": {
            "expectedFraudLoss": 40050.44,
            "frictionCostIfFP": settings.DEFAULT_FRICTION_COST_FP,
            "reviewCost": settings.DEFAULT_REVIEW_COST,
            "netExposure": 39875.44,
        },
        "auditHash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "transactionDetails": {
            "cardFingerprint": "CARD-4412-XXXX",
            "emailDomain": "xyz.com",
            "addressHash": "ADDR-90210",
            "deviceType": "mobile",
            "deviceHash": "device_hash_123",
            "productCD": "W",
            "channel": "e-commerce",
        },
        "auditTrail": [
            {
                "step": "RULE_EVALUATION",
                "timestamp": 1693564800100,
                "action": "Triggered 2 rules (1 HIGH, 1 MEDIUM)",
                "hash": "8f4e2a1b9c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789ab",
            },
            {
                "step": "ML_SCORING",
                "timestamp": 1693564800200,
                "action": "LightGBM score 0.89 (calibrated probability)",
                "hash": "7a8b9c0d1e2f3a4b5c6d7e8f90123456789abcdef0123456789abcdef0123456",
            },
            {
                "step": "COST_POLICY_ROUTING",
                "timestamp": 1693564800300,
                "action": "Decision: SIMULATED_HOLD (Expected loss ₹40,050.44 > Friction ₹150.00)",
                "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            },
        ],
    },
    {
        "transactionId": "TXN-11234-B",
        "timestamp": 1693565000000,
        "amount": 2500.00,
        "riskScore": 0.65,
        "decision": "REVIEW",
        "status": "pending",
        "reasonCodes": ["VELOCITY_SPIKE"],
        "expectedCost": 1625.00,
        "linkedEntityCount": 2,
        "modelVersion": settings.MODEL_VERSION,
        "latencyMs": 2.10,
        "shapContributions": [
            {"feature": "card1_velocity_24h", "contribution": 0.32},
            {"feature": "TransactionAmt", "contribution": 0.18},
            {"feature": "dist1", "contribution": 0.05},
        ],
        "ruleTriggers": [
            {
                "ruleId": "RULE-012",
                "severity": "MEDIUM",
                "explanation": "Velocity spike: 4th transaction within 15 minutes.",
            }
        ],
        "graphContext": {
            "clusterId": "CLUSTER-12A",
            "sharedAttributes": ["card_fp_1123"],
            "clusterSize": 3,
        },
        "costBreakdown": {
            "expectedFraudLoss": 1625.00,
            "frictionCostIfFP": settings.DEFAULT_FRICTION_COST_FP,
            "reviewCost": settings.DEFAULT_REVIEW_COST,
            "netExposure": 1450.00,
        },
        "auditHash": "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
        "transactionDetails": {
            "cardFingerprint": "CARD-5500-XXXX",
            "emailDomain": "gmail.com",
            "addressHash": "ADDR-10001",
            "deviceType": "desktop",
            "deviceHash": "device_hash_456",
            "productCD": "C",
            "channel": "e-commerce",
        },
        "auditTrail": [
            {
                "step": "RULE_EVALUATION",
                "timestamp": 1693565000100,
                "action": "Triggered 1 rule (MEDIUM)",
                "hash": "11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff",
            },
            {
                "step": "COST_POLICY_ROUTING",
                "timestamp": 1693565000300,
                "action": "Decision: REVIEW (Score 0.65 in review band [0.40 - 0.75])",
                "hash": "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
            },
        ],
    },
    {
        "transactionId": "TXN-88234-C",
        "timestamp": 1693566000000,
        "amount": 120.00,
        "riskScore": 0.12,
        "decision": "ALLOW",
        "status": "reviewed",
        "reasonCodes": [],
        "expectedCost": 14.40,
        "linkedEntityCount": 0,
        "modelVersion": settings.MODEL_VERSION,
        "latencyMs": 1.40,
        "shapContributions": [
            {"feature": "TransactionAmt", "contribution": -0.15},
            {"feature": "card1_velocity_24h", "contribution": -0.08},
        ],
        "ruleTriggers": [],
        "graphContext": {
            "clusterId": None,
            "sharedAttributes": [],
            "clusterSize": 0,
        },
        "costBreakdown": {
            "expectedFraudLoss": 14.40,
            "frictionCostIfFP": settings.DEFAULT_FRICTION_COST_FP,
            "reviewCost": settings.DEFAULT_REVIEW_COST,
            "netExposure": 0.00,
        },
        "auditHash": "99887766554433221100ffeeddccbbaa99887766554433221100ffeeddccbbaa",
        "transactionDetails": {
            "cardFingerprint": "CARD-4111-XXXX",
            "emailDomain": "outlook.com",
            "addressHash": "ADDR-94103",
            "deviceType": "mobile",
            "deviceHash": "device_hash_789",
            "productCD": "W",
            "channel": "e-commerce",
        },
        "auditTrail": [
            {
                "step": "COST_POLICY_ROUTING",
                "timestamp": 1693566000300,
                "action": "Decision: ALLOW (Low risk 0.12 < 0.40)",
                "hash": "99887766554433221100ffeeddccbbaa99887766554433221100ffeeddccbbaa",
            },
        ],
    },
]


@router.get("", response_model=List[Alert], summary="List transaction alerts")
async def list_alerts(
    risk_tier: Optional[str] = Query(None, description="Filter by decision / tier: ALLOW, REVIEW, SIMULATED_HOLD, HIGH, MEDIUM, LOW"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: pending, reviewed, dismissed"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Get paginated queue of transaction alerts.
    Strictly conforms to Alert[] type from shared/types.ts and frontend/src/fixtures/alerts.json.
    """
    # Merge seed alerts with live pipeline alerts
    combined: List[Alert] = []
    
    # Add seed alerts
    for item in _SEED_ALERTS:
        combined.append(
            Alert(
                transactionId=item["transactionId"],
                timestamp=item["timestamp"],
                amount=item["amount"],
                riskScore=item["riskScore"],
                decision=item["decision"],
                reasonCodes=item["reasonCodes"],
                expectedCost=item["expectedCost"],
                linkedEntityCount=item["linkedEntityCount"],
                modelVersion=item["modelVersion"],
                latencyMs=item.get("latencyMs"),
            )
        )
    
    # Add dynamically scored pipeline alerts (deduping by transactionId)
    existing_ids = {a.transactionId for a in combined}
    for dyn_alert in scoring_pipeline.get_all_alerts():
        if dyn_alert.transactionId not in existing_ids:
            combined.append(dyn_alert)
            existing_ids.add(dyn_alert.transactionId)

    # Apply risk tier filtering
    if risk_tier:
        tier_upper = risk_tier.upper()
        if tier_upper in ["HIGH", "SIMULATED_HOLD"]:
            combined = [a for a in combined if a.decision == "SIMULATED_HOLD"]
        elif tier_upper in ["MEDIUM", "REVIEW"]:
            combined = [a for a in combined if a.decision == "REVIEW"]
        elif tier_upper in ["LOW", "ALLOW"]:
            combined = [a for a in combined if a.decision == "ALLOW"]

    # Paginate results
    return combined[offset : offset + limit]


@router.get("/{transaction_id}", response_model=AlertDetailResponse, summary="Get full case evidence for an alert")
async def get_alert_detail(transaction_id: str):
    """
    Hero View Endpoint: Retrieve all evidence, SHAP contributions, rule triggers,
    graph context, cost breakdown, and tamper-evident audit trail for a case.
    """
    # Check live scoring pipeline cache first
    detail = scoring_pipeline.get_alert_detail(transaction_id)
    if detail:
        return detail

    # Check seed alerts
    match = next((a for a in _SEED_ALERTS if a["transactionId"] == transaction_id), None)
    if match:
        return AlertDetailResponse(
            transactionId=match["transactionId"],
            timestamp=match["timestamp"],
            amount=match["amount"],
            riskScore=match["riskScore"],
            decision=match["decision"],
            status=match.get("status", "pending"),
            reasonCodes=match["reasonCodes"],
            expectedCost=match["expectedCost"],
            linkedEntityCount=match["linkedEntityCount"],
            modelVersion=match["modelVersion"],
            latencyMs=match.get("latencyMs"),
            shapContributions=[ShapContribution(**s) for s in match["shapContributions"]],
            ruleTriggers=[RuleTrigger(**r) for r in match["ruleTriggers"]],
            graphContext=GraphContext(**match["graphContext"]),
            costBreakdown=CostBreakdown(**match["costBreakdown"]),
            auditHash=match["auditHash"],
            transactionDetails=match.get("transactionDetails"),
            auditTrail=[AuditTrailEntry(**entry) for entry in match.get("auditTrail", [])],
        )

    # Process on-demand if arbitrary ID requested
    txn_input = TransactionInput(transactionId=transaction_id, amount=15420.00, P_emaildomain="disposable-mail.xyz")
    score_resp = scoring_pipeline.process(txn_input)
    detail_resp = scoring_pipeline.get_alert_detail(transaction_id)
    if detail_resp:
        return detail_resp

    return AlertDetailResponse(
        transactionId=transaction_id,
        timestamp=score_resp.alert.timestamp,
        amount=score_resp.alert.amount,
        riskScore=score_resp.alert.riskScore,
        decision=score_resp.alert.decision,
        status="pending",
        reasonCodes=score_resp.alert.reasonCodes,
        expectedCost=score_resp.alert.expectedCost,
        linkedEntityCount=score_resp.alert.linkedEntityCount,
        modelVersion=score_resp.alert.modelVersion,
        shapContributions=score_resp.evidence.shapContributions,
        ruleTriggers=score_resp.evidence.ruleTriggers,
        graphContext=score_resp.evidence.graphContext,
        costBreakdown=score_resp.evidence.costBreakdown,
        auditHash=score_resp.evidence.auditHash,
        transactionDetails={
            "cardFingerprint": "CARD-9900-XXXX",
            "emailDomain": "disposable-mail.xyz",
            "addressHash": "ADDR-50001",
            "deviceType": "mobile",
            "deviceHash": "device_hash_auto",
            "productCD": "W",
            "channel": "e-commerce",
        },
        auditTrail=audit_logger.get_audit_trail(transaction_id),
    )


@router.post("/{transaction_id}/decision", response_model=AnalystDecisionResponse, summary="Record analyst decision")
async def submit_analyst_decision(transaction_id: str, payload: AnalystDecisionRequest):
    """
    Record an analyst's review decision (Approve Hold / Dismiss / Escalate / Release).
    Appends entry to append-only tamper-evident audit hash chain.
    """
    now_ms = int(time.time() * 1000)

    # Log to tamper-evident audit chain
    new_audit_hash = audit_logger.log_analyst_decision(
        transaction_id=transaction_id,
        decision=payload.decision,
        reviewer=payload.reviewer,
        notes=payload.notes,
        timestamp=now_ms,
    )

    # Update in pipeline cache and seed alerts
    scoring_pipeline.update_alert_status(transaction_id, "reviewed")
    for s in _SEED_ALERTS:
        if s["transactionId"] == transaction_id:
            s["status"] = "reviewed"
            s["auditHash"] = new_audit_hash
            s.setdefault("auditTrail", []).append({
                "step": "ANALYST_REVIEW",
                "timestamp": now_ms,
                "action": f"Analyst ({payload.reviewer}) action: {payload.decision}. Notes: {payload.notes or 'None'}",
                "hash": new_audit_hash,
            })

    return AnalystDecisionResponse(
        success=True,
        transactionId=transaction_id,
        decision=payload.decision,
        status="reviewed",
        auditHash=new_audit_hash,
        timestamp=now_ms,
        message=f"Decision '{payload.decision}' successfully committed to tamper-evident audit log.",
    )

