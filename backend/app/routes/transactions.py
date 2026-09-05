from fastapi import APIRouter, HTTPException, status
from app.models.schemas import (
    TransactionInput,
    ScoreResponse,
    BatchScoreRequest,
    BatchScoreResponse,
)
from app.services.scoring_pipeline import scoring_pipeline

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/score", response_model=ScoreResponse, summary="Score a single transaction")
async def score_transaction(txn: TransactionInput):
    """
    Score an incoming payment transaction through the 4-layer Sentinel pipeline.
    Returns calibrated fraud probability, cost-optimal decision, and case evidence.
    """
    return scoring_pipeline.process(txn)


@router.post("/batch", response_model=BatchScoreResponse, summary="Score a batch of transactions")
async def score_batch(batch: BatchScoreRequest):
    """
    Score a batch of transactions for simulation or high-throughput stream evaluation.
    Meets the requirement for evaluating 50+ transactions.
    """
    if not batch.transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction batch cannot be empty."
        )

    return scoring_pipeline.process_batch(batch)

