import os
import sys
import math
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
from app.models.schemas import TransactionInput
from app.config import settings

# Ensure repository root is in sys.path for unpickling model wrappers
_repo_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)
_backend_root = str(Path(__file__).resolve().parent.parent.parent)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

logger = logging.getLogger(__name__)


class MLClassifier:
    """
    Layer 2: Calibrated LightGBM model scorer.
    Loads pre-trained LightGBM model from joblib file or computes
    calibrated probability score from IEEE-CIS features.
    Yields calibrated fraud risk probability in [0.0, 1.0].
    """

    FEATURE_NAMES: List[str] = [
        "TransactionAmt",
        "ProductCD",
        "card1",
        "card2",
        "card3",
        "card4",
        "card5",
        "card6",
        "addr1",
        "addr2",
        "dist1",
        "P_emaildomain",
        "R_emaildomain",
        "C1",
        "C2",
        "D1",
        "D2",
        "V1",
        "V257",
        "DeviceType",
        "DeviceInfo",
        "id_30",
        "id_31",
    ]

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or settings.MODEL_PATH
        self.model = None
        self.feature_names = self.FEATURE_NAMES
        self._load_model_if_exists()

    def _load_model_if_exists(self):
        """Attempts to load pre-trained LightGBM model from multiple candidate locations."""
        candidates = [
            settings.resolve_path(self.model_path),
            settings.resolve_path("data/models/lightgbm_model.joblib"),
            settings.resolve_path("../data/models/lightgbm_model.joblib"),
            settings.resolve_path("data/models/lgbm_model.joblib"),
        ]

        for path in candidates:
            if path and os.path.exists(path):
                try:
                    import joblib
                    loaded = joblib.load(path)
                    if isinstance(loaded, dict) and "model" in loaded:
                        self.model = loaded["model"]
                        if "features" in loaded:
                            self.feature_names = loaded["features"]
                    else:
                        self.model = loaded
                    logger.info(f"Successfully loaded LightGBM model from {path}")
                    return
                except Exception as e:
                    logger.warning(f"Failed to load model from {path}: {e}")
                    self.model = None

    def transform_to_features(self, txn: TransactionInput) -> pd.DataFrame:
        """Converts TransactionInput to DataFrame matching model features."""
        data: Dict[str, Any] = {
            "TransactionAmt": float(txn.amount),
            "ProductCD": txn.ProductCD or "W",
            "card1": float(txn.card1) if txn.card1 and str(txn.card1).isdigit() else 0.0,
            "card2": float(txn.card2) if txn.card2 and str(txn.card2).isdigit() else 0.0,
            "card3": float(txn.card3) if txn.card3 and str(txn.card3).isdigit() else 150.0,
            "card4": txn.card4 or "visa",
            "card5": float(txn.card5) if txn.card5 and str(txn.card5).isdigit() else 226.0,
            "card6": txn.card6 or "debit",
            "addr1": float(txn.addr1) if txn.addr1 and str(txn.addr1).isdigit() else 0.0,
            "addr2": float(txn.addr2) if txn.addr2 and str(txn.addr2).isdigit() else 87.0,
            "dist1": float(txn.dist1) if txn.dist1 is not None else -1.0,
            "P_emaildomain": txn.P_emaildomain or "missing",
            "R_emaildomain": txn.R_emaildomain or "missing",
            "C1": float(getattr(txn, "C1", 1.0) or 1.0),
            "C2": float(getattr(txn, "C2", 1.0) or 1.0),
            "D1": float(getattr(txn, "D1", 0.0) or 0.0),
            "D2": float(getattr(txn, "D2", 0.0) or 0.0),
            "V1": float(getattr(txn, "V1", 1.0) or 1.0),
            "V257": float(getattr(txn, "V257", 1.0) or 1.0),
            "DeviceType": txn.DeviceType or "missing",
            "DeviceInfo": txn.DeviceInfo or "missing",
            "id_30": getattr(txn, "id_30", "missing") or "missing",
            "id_31": getattr(txn, "id_31", "missing") or "missing",
        }
        df = pd.DataFrame([data])
        # Ensure categoricals are object/category
        for col in ["ProductCD", "card4", "card6", "P_emaildomain", "R_emaildomain", "DeviceType", "DeviceInfo", "id_30", "id_31"]:
            if col in df.columns:
                df[col] = df[col].astype("category")
        return df

    def predict_proba(self, txn: TransactionInput) -> float:
        """
        Returns calibrated probability score in [0.0, 1.0].
        Uses loaded model directly without manual indicator adjustments.
        """
        if self.model is not None:
            try:
                features_df = self.transform_to_features(txn)
                raw_prob = 0.0
                if hasattr(self.model, "predict_proba"):
                    probs = self.model.predict_proba(features_df)
                    if len(probs.shape) > 1 and probs.shape[1] >= 2:
                        raw_prob = float(probs[0, 1])
                    else:
                        raw_prob = float(probs[0])
                elif hasattr(self.model, "predict"):
                    preds = self.model.predict(features_df)
                    raw_prob = float(preds[0])

                clamped = min(max(raw_prob, 0.02), 0.98)
                return float(round(clamped, 2))
            except Exception as e:
                logger.warning(f"Error during model prediction, falling back to calibrated score: {e}")

        # Calibrated logistic scoring fallback
        return self._compute_calibrated_heuristic(txn)

    def _compute_calibrated_heuristic(self, txn: TransactionInput) -> float:
        """
        Calibrated probabilistic scoring function representing base log-odds
        and additive feature contributions on the logit scale.
        """
        amount = float(txn.amount)
        # Base log-odds (-2.2 corresponds to base fraud prevalence ~10%)
        logit = -2.2

        # Amount log-scale scaling
        if amount > 10000.0:
            logit += 2.4 + math.log10(amount / 10000.0) * 0.5
        elif amount > 2000.0:
            logit += 1.3 + math.log10(amount / 2000.0) * 0.4
        elif amount > 500.0:
            logit += 0.4
        else:
            logit -= 0.6

        # Disposable or suspicious email domain
        if txn.P_emaildomain:
            domain = str(txn.P_emaildomain).lower()
            if any(k in domain for k in ["temp", "xyz", "top", "disposable", "trashmail"]):
                logit += 1.8
            elif any(k in domain for k in ["gmail", "yahoo", "hotmail", "outlook", "icloud"]):
                logit -= 0.2

        # Anomalous device
        if txn.DeviceType:
            device = str(txn.DeviceType).lower()
            if any(k in device for k in ["proxy", "tor", "emulator", "vpn", "unknown"]):
                logit += 1.6
            elif device in ["desktop", "mobile"]:
                logit -= 0.1

        # High risk product CD
        if txn.ProductCD in ["C", "R"]:
            logit += 0.8
        elif txn.ProductCD == "W":
            logit -= 0.2

        # Distance anomaly
        if txn.dist1 is not None and float(txn.dist1) > 500.0:
            logit += 0.7

        # Convert logit to calibrated probability via Sigmoid
        prob = 1.0 / (1.0 + math.exp(-logit))
        return float(round(min(max(prob, 0.02), 0.98), 2))


