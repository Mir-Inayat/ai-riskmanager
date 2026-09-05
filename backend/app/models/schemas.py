from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# --- Core Frozen Contract Types (Strictly matching shared/types.ts) ---

class Alert(BaseModel):
    transactionId: str
    timestamp: int
    amount: float
    riskScore: float = Field(..., description="Calibrated fraud probability (0.0 to 1.0)")
    decision: Literal["ALLOW", "REVIEW", "SIMULATED_HOLD"]
    reasonCodes: List[str] = Field(default_factory=list)
    expectedCost: float
    linkedEntityCount: int
    modelVersion: str
    latencyMs: Optional[float] = Field(default=None, description="Scoring latency in milliseconds")

    model_config = ConfigDict(populate_by_name=True)


class ShapContribution(BaseModel):
    feature: str
    contribution: float


class RuleTrigger(BaseModel):
    ruleId: str
    severity: str
    explanation: str


class GraphContext(BaseModel):
    clusterId: Optional[str] = None
    sharedAttributes: List[str] = Field(default_factory=list)
    clusterSize: int = 0


class CostBreakdown(BaseModel):
    expectedFraudLoss: float
    frictionCostIfFP: float
    reviewCost: float
    netExposure: float


class CaseEvidence(BaseModel):
    shapContributions: List[ShapContribution] = Field(default_factory=list)
    ruleTriggers: List[RuleTrigger] = Field(default_factory=list)
    graphContext: GraphContext
    costBreakdown: CostBreakdown
    auditHash: str

    model_config = ConfigDict(populate_by_name=True)


# --- Request and Response Schemas ---

class TransactionInput(BaseModel):
    transactionId: Optional[str] = None
    timestamp: Optional[int] = None
    amount: float
    card1: Optional[str] = None
    card2: Optional[str] = None
    card3: Optional[str] = None
    card4: Optional[str] = None
    card5: Optional[str] = None
    card6: Optional[str] = None
    addr1: Optional[str] = None
    addr2: Optional[str] = None
    dist1: Optional[float] = None
    dist2: Optional[float] = None
    P_emaildomain: Optional[str] = None
    R_emaildomain: Optional[str] = None
    ProductCD: Optional[str] = None
    DeviceType: Optional[str] = None
    DeviceInfo: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ScoreResponse(BaseModel):
    alert: Alert
    evidence: CaseEvidence
    latencyMs: Optional[float] = Field(default=None, description="Inference latency in milliseconds")


class BatchScoreRequest(BaseModel):
    transactions: List[TransactionInput]


class BatchScoreSummary(BaseModel):
    simulatedHoldCount: int
    reviewCount: int
    allowCount: int
    totalExpectedLoss: float
    averageRiskScore: float
    averageLatencyMs: Optional[float] = Field(default=None, description="Average transaction scoring latency in milliseconds")


class BatchScoreResponse(BaseModel):
    totalProcessed: int
    alerts: List[Alert]
    summary: BatchScoreSummary
    latencyMs: Optional[float] = Field(default=None, description="Total batch execution latency in milliseconds")


class AuditTrailEntry(BaseModel):
    step: str
    timestamp: int
    action: str
    hash: str


class AlertDetailResponse(BaseModel):
    transactionId: str
    timestamp: int
    amount: float
    riskScore: float
    decision: Literal["ALLOW", "REVIEW", "SIMULATED_HOLD"]
    status: Literal["pending", "reviewed", "dismissed"] = "pending"
    reasonCodes: List[str] = Field(default_factory=list)
    expectedCost: float
    linkedEntityCount: int
    modelVersion: str
    latencyMs: Optional[float] = Field(default=None, description="Scoring latency in milliseconds")
    shapContributions: List[ShapContribution] = Field(default_factory=list)
    ruleTriggers: List[RuleTrigger] = Field(default_factory=list)
    graphContext: GraphContext
    costBreakdown: CostBreakdown
    auditHash: str
    transactionDetails: Optional[Dict[str, Any]] = None
    auditTrail: List[AuditTrailEntry] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class AnalystDecisionRequest(BaseModel):
    decision: Literal["APPROVE_HOLD", "DISMISS", "ESCALATE", "RELEASE"]
    reviewer: str = "analyst_1"
    notes: Optional[str] = None


class AnalystDecisionResponse(BaseModel):
    success: bool
    transactionId: str
    decision: str
    status: str
    auditHash: str
    timestamp: int
    message: str


# --- Metrics & Health Schemas ---

class DetectionMetrics(BaseModel):
    precision: float
    recall: float
    prAuc: float
    recallAtBudget: float
    preventableExposureCaptured: float
    falsePositiveCost: float
    f1Score: Optional[float] = None
    totalScored: Optional[int] = None
    fraudDetected: Optional[int] = None
    reviewQueueSize: Optional[int] = None

    model_config = ConfigDict(populate_by_name=True)


class CostMetrics(BaseModel):
    expectedCost: float
    netPreventedExposure: float
    falsePositiveCost: float
    manualReviewCost: float
    missedFraudCost: float
    totalExposure: float
    costReductionPct: float

    model_config = ConfigDict(populate_by_name=True)


class CostSimulationRequest(BaseModel):
    frictionCostIfFP: float = 150.0
    reviewCost: float = 25.0
    reviewCapacity: int = 100
    thresholdHold: Optional[float] = 0.75
    thresholdReview: Optional[float] = 0.40


class CostSimulationResponse(BaseModel):
    optimalThresholdHold: float
    optimalThresholdReview: float
    simulatedHoldCount: int
    simulatedReviewCount: int
    simulatedAllowCount: int
    expectedTotalCost: float
    netPreventedExposure: float
    reviewCapacityUtilization: float
    precision: float
    recall: float

    model_config = ConfigDict(populate_by_name=True)


class ThresholdPoint(BaseModel):
    threshold: float
    precision: float
    recall: float
    f1: float
    expectedCost: float
    fpCount: int
    fnCount: int


class ThresholdCurveResponse(BaseModel):
    points: List[ThresholdPoint]
    recommendedThreshold: float


class ModelComparisonItem(BaseModel):
    name: str
    precision: float
    recall: float
    f1: float
    prAuc: float
    preventedExposure: float
    falsePositiveCost: float
    totalCost: float


class ModelComparisonResponse(BaseModel):
    models: List[ModelComparisonItem]


# --- Analytics & Graph Schemas ---

class BenfordDigit(BaseModel):
    digit: int
    actual: float
    expected: float


class BenfordResponse(BaseModel):
    status: Literal["HIGH_CONFIDENCE", "CAUTION", "NOT_APPLICABLE"]
    mad: float
    chiSquare: float
    pValue: float
    sampleSize: int
    digitDistribution: List[BenfordDigit]
    disclaimer: str = (
        "Portfolio-level distribution signal. Not transaction-level evidence and never a trigger for an automated action."
    )


class GraphNode(BaseModel):
    id: str
    group: str
    val: int = 5


class GraphLink(BaseModel):
    source: str
    target: str


class GraphDataResponse(BaseModel):
    nodes: List[GraphNode]
    links: List[GraphLink]
    clustersCount: Optional[int] = None
    maxClusterSize: Optional[int] = None


class DriftResponse(BaseModel):
    status: Literal["HEALTHY", "WARNING", "CRITICAL"]
    ksPValues: Dict[str, float]
    scoreDistributionDrift: float
    alertRateDrift: float
    missingnessDrift: float
    delayedRetrospective: Dict[str, Any]
    note: str = (
        "Precision and recall are delayed-label metrics, refreshed after confirmed outcomes; live model health uses input and score-distribution drift."
    )


class AmountBin(BaseModel):
    bin: str
    count: int
    fraudRate: float


class RiskScoreDistributionItem(BaseModel):
    range: str
    count: int
    decision: str


class ProductCodeDistributionItem(BaseModel):
    code: str
    count: int
    fraudCount: int


class DistributionsResponse(BaseModel):
    amountBins: List[AmountBin]
    riskScoreDistribution: List[RiskScoreDistributionItem]
    productCodeDistribution: List[ProductCodeDistributionItem]
