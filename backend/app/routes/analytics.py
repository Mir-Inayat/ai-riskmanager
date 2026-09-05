from fastapi import APIRouter
from app.models.schemas import (
    BenfordResponse,
    GraphDataResponse,
    DriftResponse,
    DistributionsResponse,
    AmountBin,
    RiskScoreDistributionItem,
    ProductCodeDistributionItem,
)
from app.detection.benford_signal import BenfordSignal
from app.detection.graph_analyzer import GraphAnalyzer
from app.detection.drift_monitor import DriftMonitor

router = APIRouter(prefix="/analytics", tags=["Analytics"])

benford_service = BenfordSignal()
graph_service = GraphAnalyzer()
drift_service = DriftMonitor()


@router.get("/benford", response_model=BenfordResponse, summary="Benford's Law analysis with applicability gating")
async def get_benford_analysis():
    """
    Portfolio integrity signal on transaction amounts.
    Explicitly gated with applicability checks (sample size, pricing bounds, banding).
    """
    return benford_service.analyze()


@router.get("/graph-summary", response_model=GraphDataResponse, summary="Linked-entity graph visualization network")
async def get_graph_summary():
    """
    Returns graph nodes and links representing shared card, device, and email relationships.
    Strictly conforms to frontend/src/fixtures/graph-data.json.
    """
    return graph_service.get_graph_summary()


@router.get("/drift", response_model=DriftResponse, summary="Model health and feature distribution drift")
async def get_drift_indicators():
    """
    Returns online immediately-observable drift signals (KS tests, score drift)
    along with delayed retrospective metrics.
    """
    return drift_service.check_health()


@router.get("/distributions", response_model=DistributionsResponse, summary="Transaction attribute distributions")
async def get_distributions():
    """
    Returns amount bins, risk score distribution, and product code breakdown for analytics dashboards.
    """
    return DistributionsResponse(
        amountBins=[
            AmountBin(bin="0-50", count=4200, fraudRate=0.012),
            AmountBin(bin="50-100", count=3600, fraudRate=0.019),
            AmountBin(bin="100-500", count=4500, fraudRate=0.038),
            AmountBin(bin="500-1000", count=1200, fraudRate=0.075),
            AmountBin(bin="1000+", count=750, fraudRate=0.142),
        ],
        riskScoreDistribution=[
            RiskScoreDistributionItem(range="0.0-0.2", count=9800, decision="ALLOW"),
            RiskScoreDistributionItem(range="0.2-0.4", count=2800, decision="ALLOW"),
            RiskScoreDistributionItem(range="0.4-0.7", count=1150, decision="REVIEW"),
            RiskScoreDistributionItem(range="0.7-1.0", count=500, decision="SIMULATED_HOLD"),
        ],
        productCodeDistribution=[
            ProductCodeDistributionItem(code="W", count=8200, fraudCount=180),
            ProductCodeDistributionItem(code="C", count=2900, fraudCount=195),
            ProductCodeDistributionItem(code="R", count=1800, fraudCount=65),
            ProductCodeDistributionItem(code="H", count=900, fraudCount=35),
            ProductCodeDistributionItem(code="S", count=450, fraudCount=11),
        ],
    )

