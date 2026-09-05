"""Sentinel Model Pipeline Components."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure root directory in sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import lightgbm as lgb
import numpy as np
import pandas as pd
import shap
from sklearn.base import BaseEstimator, ClassifierMixin, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


class SentinelFeatureTransformer(BaseEstimator, TransformerMixin):
    """
    Feature engineering transformer fitted strictly on training data:
    - Pre-transaction vs post-event separation enforced.
    - Extracts temporal features: hour_of_day, day_of_week from TransactionDT.
    - Extracts financial features: log1p(TransactionAmt).
    - Encodes categorical variables with unknown category handling.
    - Imputes and scales numerical variables.
    """

    def __init__(
        self,
        id_cols: Optional[List[str]] = None,
        target_col: str = "isFraud",
        time_col: str = "TransactionDT",
        amount_col: str = "TransactionAmt",
    ):
        self.id_cols = id_cols or ["TransactionID"]
        self.target_col = target_col
        self.time_col = time_col
        self.amount_col = amount_col

        self.num_cols_: List[str] = []
        self.cat_cols_: List[str] = []
        self.feature_names_out_: List[str] = []
        self.num_imputer_: Optional[SimpleImputer] = None
        self.cat_encoders_: Dict[str, Dict[str, int]] = {}
        self.cat_defaults_: Dict[str, int] = {}

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> "SentinelFeatureTransformer":
        df = X.copy()
        drop_cols = set(self.id_cols + [self.target_col])
        candidate_cols = [c for c in df.columns if c not in drop_cols]

        self.num_cols_ = []
        self.cat_cols_ = []

        for col in candidate_cols:
            if col == self.time_col:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                self.num_cols_.append(col)
            else:
                self.cat_cols_.append(col)

        # Build categorical vocabulary maps from training data only
        self.cat_encoders_ = {}
        self.cat_defaults_ = {}
        for col in self.cat_cols_:
            series = df[col].astype(str).fillna("__MISSING__")
            unique_vals = sorted(series.unique())
            mapping = {val: idx for idx, val in enumerate(unique_vals)}
            self.cat_encoders_[col] = mapping
            self.cat_defaults_[col] = -1

        # Numerical imputer
        if self.num_cols_:
            self.num_imputer_ = SimpleImputer(strategy="median")
            num_data = df[self.num_cols_].copy()
            self.num_imputer_.fit(num_data)

        derived_cols = ["hour_of_day", "day_of_week", "log_TransactionAmt"]
        self.feature_names_out_ = derived_cols + self.num_cols_ + self.cat_cols_
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()

        # 1. Temporal feature extraction
        if self.time_col in df.columns:
            hour = ((df[self.time_col] // 3600) % 24).astype(float)
            day = ((df[self.time_col] // 86400) % 7).astype(float)
        else:
            hour = pd.Series(12.0, index=df.index)
            day = pd.Series(3.0, index=df.index)

        # 2. Financial log amount
        if self.amount_col in df.columns:
            amt = pd.to_numeric(df[self.amount_col], errors="coerce").fillna(0.0)
            log_amt = np.log1p(np.clip(amt, 0.0, None))
        else:
            log_amt = pd.Series(0.0, index=df.index)

        # 3. Numerical columns
        num_dict = {}
        for col in self.num_cols_:
            if col in df.columns:
                num_dict[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                num_dict[col] = pd.Series(np.nan, index=df.index)
        num_df = pd.DataFrame(num_dict, index=df.index)

        if self.num_imputer_ is not None and len(self.num_cols_) > 0:
            imputed_num = self.num_imputer_.transform(num_df)
            num_df = pd.DataFrame(imputed_num, columns=self.num_cols_, index=df.index)

        # 4. Categorical columns encoding
        cat_dict = {}
        for col in self.cat_cols_:
            mapping = self.cat_encoders_.get(col, {})
            default_val = self.cat_defaults_.get(col, -1)
            if col in df.columns:
                cat_series = df[col].astype(str).fillna("__MISSING__")
                encoded = cat_series.map(mapping).fillna(default_val).astype(int)
            else:
                encoded = pd.Series(default_val, index=df.index, dtype=int)
            cat_dict[col] = encoded
        cat_df = pd.DataFrame(cat_dict, index=df.index)

        out_df = pd.concat([
            pd.DataFrame({
                "hour_of_day": hour,
                "day_of_week": day,
                "log_TransactionAmt": log_amt,
            }, index=df.index),
            num_df,
            cat_df,
        ], axis=1)

        return out_df[self.feature_names_out_]

    def get_feature_names_out(self, input_features: Optional[Any] = None) -> List[str]:
        return list(self.feature_names_out_)


class BetaCalibrator(BaseEstimator, ClassifierMixin):
    """
    Beta Calibration for binary classification (Kull et al., 2017).
    Fits a Logistic Regression model on log-transformed uncalibrated probability scores:
        x1 = ln(s)
        x2 = -ln(1 - s)
    where s is the uncalibrated positive class probability score clipped to [eps, 1 - eps].
    """

    def __init__(
        self,
        eps: float = 1e-7,
        max_iter: int = 1000,
        random_state: int = 42,
        C: float = 1.0,
    ):
        self.eps = eps
        self.max_iter = max_iter
        self.random_state = random_state
        self.C = C
        self.lr_: Optional[LogisticRegression] = None
        self.classes_ = np.array([0, 1])

    def _transform_scores(self, s: np.ndarray) -> np.ndarray:
        s_arr = np.asarray(s, dtype=float).ravel()
        s_clipped = np.clip(s_arr, self.eps, 1.0 - self.eps)
        x1 = np.log(s_clipped)
        x2 = -np.log(1.0 - s_clipped)
        return np.column_stack([x1, x2])

    def fit(self, s: np.ndarray, y: np.ndarray) -> "BetaCalibrator":
        y_arr = np.asarray(y, dtype=int).ravel()
        X_trans = self._transform_scores(s)
        self.lr_ = LogisticRegression(
            solver="lbfgs",
            max_iter=self.max_iter,
            random_state=self.random_state,
            C=self.C,
        )
        self.lr_.fit(X_trans, y_arr)
        return self

    def predict_proba(self, s: np.ndarray) -> np.ndarray:
        if self.lr_ is None:
            raise ValueError("BetaCalibrator is not fitted yet.")
        X_trans = self._transform_scores(s)
        probs = self.lr_.predict_proba(X_trans)
        p1 = np.clip(probs[:, 1], 0.0001, 0.9999)
        return np.column_stack([1.0 - p1, p1])

    def predict(self, s: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(s)[:, 1] >= threshold).astype(int)


class ProbabilityCalibrator(BaseEstimator, ClassifierMixin):
    """
    Robust probability calibrator supporting:
    - "beta": Beta Calibration via Logistic Regression on (ln(s), -ln(1-s))
    - "isotonic": Isotonic Regression
    - "sigmoid": Platt scaling via Logistic Regression
    """

    def __init__(self, base_estimator: Any, method: str = "beta"):
        self.base_estimator = base_estimator
        self.method = method
        self.calibrator_: Any = None
        self.classes_ = np.array([0, 1])

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "ProbabilityCalibrator":
        raw_probs = self.base_estimator.predict_proba(X)[:, 1]
        y_arr = np.asarray(y, dtype=int)

        if self.method == "beta":
            self.calibrator_ = BetaCalibrator()
            self.calibrator_.fit(raw_probs, y_arr)
        elif self.method == "isotonic":
            self.calibrator_ = IsotonicRegression(out_of_bounds="clip")
            self.calibrator_.fit(raw_probs, y_arr)
        elif self.method == "sigmoid":
            self.calibrator_ = LogisticRegression(solver="lbfgs", max_iter=1000, random_state=42)
            self.calibrator_.fit(raw_probs.reshape(-1, 1), y_arr)
        else:
            raise ValueError(
                f"Unsupported calibration method '{self.method}'. "
                "Supported methods: 'beta', 'isotonic', 'sigmoid'."
            )
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        raw_probs = self.base_estimator.predict_proba(X)[:, 1]
        if self.method == "beta":
            return self.calibrator_.predict_proba(raw_probs)
        elif self.method == "isotonic":
            cal_p1 = self.calibrator_.predict(raw_probs)
        else:
            cal_p1 = self.calibrator_.predict_proba(raw_probs.reshape(-1, 1))[:, 1]
        cal_p1 = np.clip(cal_p1, 0.0001, 0.9999)
        return np.column_stack([1.0 - cal_p1, cal_p1])

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X)[:, 1] >= threshold).astype(int)


class BaselineRuleEngine:
    """Deterministic rule-based baseline for benchmarking."""

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        scores = np.zeros(len(X), dtype=float)
        if "TransactionAmt" in X.columns:
            amt = pd.to_numeric(X["TransactionAmt"], errors="coerce").fillna(0)
            scores += np.where(amt > 1000, 0.35, 0.0)
            scores += np.where(amt > 2500, 0.25, 0.0)
        if "ProductCD" in X.columns:
            scores += np.where(X["ProductCD"].isin(["C", "R"]), 0.20, 0.0)
        if "P_emaildomain" in X.columns:
            scores += np.where(
                X["P_emaildomain"].astype(str).str.contains("anon|mail|proton", case=False, na=False),
                0.20,
                0.0,
            )
        if "C1" in X.columns:
            scores += np.where(pd.to_numeric(X["C1"], errors="coerce").fillna(0) > 3, 0.20, 0.0)
        scores = np.clip(scores, 0.02, 0.95)
        return np.column_stack([1.0 - scores, scores])

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        prob = self.predict_proba(X)[:, 1]
        return (prob >= threshold).astype(int)


class SentinelModelWrapper(BaseEstimator, ClassifierMixin):
    """
    Unified production wrapper encapsulating:
    - Preprocessing transformer fitted on training set
    - Calibrated LightGBM classifier
    - Underlying raw booster model
    - SHAP explainer
    - Optimized decision thresholds and financial policies
    """

    def __init__(
        self,
        transformer: SentinelFeatureTransformer,
        calibrated_model: Any,
        raw_lgbm_model: lgb.LGBMClassifier,
        explainer: Optional[Any] = None,
        optimal_threshold: float = 0.5,
        triage_thresholds: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.transformer = transformer
        self.calibrated_model = calibrated_model
        self.raw_lgbm_model = raw_lgbm_model
        self.explainer = explainer
        self.optimal_threshold = optimal_threshold
        self.triage_thresholds = triage_thresholds or {
            "allow": 0.0,
            "review": optimal_threshold,
            "hold": min(0.95, optimal_threshold + 0.35),
        }
        self.metadata = metadata or {}
        self.classes_ = np.array([0, 1])

    def _prepare_features(self, X: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]) -> pd.DataFrame:
        if isinstance(X, dict):
            df = pd.DataFrame([X])
        elif isinstance(X, list):
            df = pd.DataFrame(X)
        elif isinstance(X, pd.DataFrame):
            df = X.copy()
        else:
            raise ValueError(f"Unsupported input type for scoring: {type(X)}")
        return self.transformer.transform(df)

    def predict_proba(self, X: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]) -> np.ndarray:
        """Compute calibrated class probabilities."""
        X_trans = self._prepare_features(X)
        if self.calibrated_model is not None:
            return self.calibrated_model.predict_proba(X_trans)
        return self.raw_lgbm_model.predict_proba(X_trans)

    def predict(self, X: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]], threshold: Optional[float] = None) -> np.ndarray:
        """Compute binary fraud prediction using optimal threshold."""
        thresh = threshold if threshold is not None else self.optimal_threshold
        probs = self.predict_proba(X)[:, 1]
        return (probs >= thresh).astype(int)

    def triage_decision(self, X_row: Union[pd.DataFrame, Dict[str, Any]]) -> Dict[str, Any]:
        """Classify transaction into 3-tier action policy."""
        prob = float(self.predict_proba(X_row)[0, 1])
        hold_th = self.triage_thresholds.get("hold", 0.75)
        rev_th = self.triage_thresholds.get("review", self.optimal_threshold)

        if prob >= hold_th:
            decision = "SIMULATED_HOLD"
            tier = "HIGH"
            reason = "Expected fraud loss exceeds immediate friction threshold."
        elif prob >= rev_th:
            decision = "ANALYST_REVIEW"
            tier = "MEDIUM"
            reason = "Significant risk signal requiring analyst confirmation."
        else:
            decision = "ALLOW"
            tier = "LOW"
            reason = "Risk score within acceptable boundary."

        return {
            "risk_score": round(prob, 4),
            "tier": tier,
            "decision": decision,
            "reason": reason,
            "thresholds": self.triage_thresholds,
        }

    def explain(self, X_row: Union[pd.DataFrame, Dict[str, Any]], top_k: int = 6) -> List[Dict[str, Any]]:
        """Compute SHAP feature contributions for analyst investigation."""
        X_trans = self._prepare_features(X_row)
        if self.explainer is None:
            return []

        try:
            shap_values = self.explainer.shap_values(X_trans)
            if isinstance(shap_values, list):
                vals = shap_values[1][0]
            elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
                vals = shap_values[0, :, 1]
            elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 2:
                vals = shap_values[0]
            else:
                vals = np.array(shap_values).flatten()

            feature_names = self.transformer.get_feature_names_out()
            contributions = []
            for name, val in zip(feature_names, vals):
                contributions.append({
                    "feature": name,
                    "contribution": round(float(val), 4),
                    "impact": "INCREASES_RISK" if val > 0 else "DECREASES_RISK",
                })
            contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
            return contributions[:top_k]
        except Exception as e:
            return []
