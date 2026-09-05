#!/usr/bin/env python3
"""
Sentinel Model Training and Policy Optimization Pipeline (Phase 3)
================================================================
Trains, calibrates, and packages the production LightGBM fraud classifier:
1. Loads strict chronological train.parquet and val.parquet.
2. Fits feature engineering pipeline (fitted on training data only).
3. Evaluates Rule-based, Logistic Regression, and Explainable Boosting Machine (EBM) baselines.
4. Trains LightGBM with class balancing (scale_pos_weight).
5. Performs probability calibration (Beta Calibration / Platt Sigmoid / Isotonic) on the validation partition.
6. Optimizes decision threshold on the validation partition to minimize expected financial cost.
7. Sets up SHAP TreeExplainer for analyst case review.
8. Packages and saves model artifact to data/models/lightgbm_model.joblib.
   STRICT PROTOCOL: The frozen test set is NEVER touched in this script.

Usage:
    python scripts/train_model.py --train-path data/processed/train.parquet --val-path data/processed/val.parquet
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure root directory in sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.model_pipeline import (
    BaselineRuleEngine,
    BetaCalibrator,
    ProbabilityCalibrator,
    SentinelFeatureTransformer,
    SentinelModelWrapper,
)

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
import shap
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sentinel.train_model")


# Demo Scenario Cost Defaults
DEFAULT_C_FP = 150.0        # Legitimate customer friction cost per false positive (INR)
DEFAULT_C_REVIEW = 25.0     # Manual analyst review cost per case (INR)
DEFAULT_DAILY_BUDGET = 100  # Manual review capacity (alerts per day)


def evaluate_predictions(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    amounts: np.ndarray,
    threshold: float = 0.5,
    c_fp: float = DEFAULT_C_FP,
    c_review: float = DEFAULT_C_REVIEW,
) -> Dict[str, Any]:
    """Calculate comprehensive evaluation metrics."""
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    amounts = np.asarray(amounts, dtype=float)

    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    try:
        pr_auc = average_precision_score(y_true, y_prob)
    except Exception:
        pr_auc = 0.0

    try:
        roc_auc = roc_auc_score(y_true, y_prob)
    except Exception:
        roc_auc = 0.5

    brier = brier_score_loss(y_true, y_prob)

    total_fraud_exposure = float(np.sum(amounts[y_true == 1]))
    captured_exposure = float(np.sum(amounts[(y_true == 1) & (y_pred == 1)]))
    missed_exposure = float(np.sum(amounts[(y_true == 1) & (y_pred == 0)]))
    preventable_pct = (captured_exposure / total_fraud_exposure) if total_fraud_exposure > 0 else 0.0

    fp_cost = float(fp * c_fp)
    review_cost = float((tp + fp) * c_review)
    expected_cost = float(missed_exposure + fp_cost + review_cost)
    net_prevented = float(captured_exposure - fp_cost - review_cost)

    return {
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1": round(float(f1), 4),
        "pr_auc": round(float(pr_auc), 4),
        "roc_auc": round(float(roc_auc), 4),
        "brier_score": round(float(brier), 4),
        "preventable_exposure_pct": round(float(preventable_pct), 4),
        "captured_exposure": round(float(captured_exposure), 2),
        "missed_exposure": round(float(missed_exposure), 2),
        "fp_cost": round(float(fp_cost), 2),
        "review_cost": round(float(review_cost), 2),
        "expected_cost": round(float(expected_cost), 2),
        "net_prevented_exposure": round(float(net_prevented), 2),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
    }


def optimize_threshold_for_cost(
    y_val: np.ndarray,
    y_prob_val: np.ndarray,
    amounts_val: np.ndarray,
    c_fp: float = DEFAULT_C_FP,
    c_review: float = DEFAULT_C_REVIEW,
) -> Tuple[float, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Sweep decision thresholds on validation set to find the threshold
    that strictly minimizes expected financial cost.
    """
    threshold_grid = np.linspace(0.01, 0.99, 197)
    best_threshold = 0.5
    min_expected_cost = float("inf")
    best_metrics: Dict[str, Any] = {}
    cost_curve: List[Dict[str, Any]] = []

    for t in threshold_grid:
        m = evaluate_predictions(y_val, y_prob_val, amounts_val, threshold=t, c_fp=c_fp, c_review=c_review)
        cost_curve.append({
            "threshold": round(float(t), 4),
            "expected_cost": m["expected_cost"],
            "net_prevented_exposure": m["net_prevented_exposure"],
            "precision": m["precision"],
            "recall": m["recall"],
            "fp": m["fp"],
            "tp": m["tp"],
            "fn": m["fn"],
        })
        if m["expected_cost"] < min_expected_cost:
            min_expected_cost = m["expected_cost"]
            best_threshold = float(t)
            best_metrics = m

    logger.info(
        "Cost optimization on validation set: Optimal Threshold = %.4f | Min Expected Cost = INR %.2f (Net Prevented = INR %.2f)",
        best_threshold,
        min_expected_cost,
        best_metrics.get("net_prevented_exposure", 0.0),
    )
    return best_threshold, best_metrics, cost_curve


def train_sentinel_model(
    train_path: Path,
    val_path: Path,
    model_output_path: Path,
    c_fp: float = DEFAULT_C_FP,
    c_review: float = DEFAULT_C_REVIEW,
    calibration_method: str = "sigmoid",
    random_state: int = 42,
) -> SentinelModelWrapper:
    """Execute complete training, calibration, and policy optimization workflow."""
    logger.info("Loading training partition: %s", train_path)
    train_df = pd.read_parquet(train_path)

    logger.info("Loading validation partition: %s", val_path)
    val_df = pd.read_parquet(val_path)

    logger.info("Train rows: %d | Val rows: %d", len(train_df), len(val_df))
    logger.info("Train fraud rate: %.2f%% | Val fraud rate: %.2f%%",
                train_df["isFraud"].mean() * 100, val_df["isFraud"].mean() * 100)

    y_train = train_df["isFraud"].to_numpy()
    y_val = val_df["isFraud"].to_numpy()

    amounts_train = (
        train_df["TransactionAmt"].to_numpy()
        if "TransactionAmt" in train_df.columns
        else np.ones(len(y_train)) * 100.0
    )
    amounts_val = (
        val_df["TransactionAmt"].to_numpy()
        if "TransactionAmt" in val_df.columns
        else np.ones(len(y_val)) * 100.0
    )

    # 1. Fit Feature Transformer strictly on Train
    transformer = SentinelFeatureTransformer(
        id_cols=["TransactionID"],
        target_col="isFraud",
        time_col="TransactionDT",
        amount_col="TransactionAmt",
    )
    transformer.fit(train_df)

    X_train_trans = transformer.transform(train_df)
    X_val_trans = transformer.transform(val_df)
    feature_names = transformer.get_feature_names_out()

    logger.info("Transformed feature matrix shape: %s", X_train_trans.shape)

    # 2. Baseline 1: Rule Engine Baseline
    rule_engine = BaselineRuleEngine()
    rule_probs_val = rule_engine.predict_proba(val_df)[:, 1]
    rule_val_metrics = evaluate_predictions(
        y_val, rule_probs_val, amounts_val, threshold=0.45, c_fp=c_fp, c_review=c_review
    )
    logger.info("Baseline 1 (Rules) Val Metrics: PR-AUC=%.4f, Prec=%.4f, Rec=%.4f, Cost=INR %.2f",
                rule_val_metrics["pr_auc"], rule_val_metrics["precision"], rule_val_metrics["recall"], rule_val_metrics["expected_cost"])

    # 3. Baseline 2: Class-Weighted Logistic Regression
    lr_imputer = SimpleImputer(strategy="median")
    lr_scaler = StandardScaler()
    X_train_lr = lr_scaler.fit_transform(lr_imputer.fit_transform(X_train_trans))
    X_val_lr = lr_scaler.transform(lr_imputer.transform(X_val_trans))

    log_reg = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=random_state,
        solver="lbfgs",
    )
    log_reg.fit(X_train_lr, y_train)
    lr_probs_val = log_reg.predict_proba(X_val_lr)[:, 1]
    lr_val_metrics = evaluate_predictions(
        y_val, lr_probs_val, amounts_val, threshold=0.5, c_fp=c_fp, c_review=c_review
    )
    logger.info("Baseline 2 (LogReg) Val Metrics: PR-AUC=%.4f, Prec=%.4f, Rec=%.4f, Cost=INR %.2f",
                lr_val_metrics["pr_auc"], lr_val_metrics["precision"], lr_val_metrics["recall"], lr_val_metrics["expected_cost"])

    # 4. Baseline 3: Explainable Boosting Machine (EBM) Baseline
    ebm_val_metrics: Optional[Dict[str, Any]] = None
    try:
        from interpret.glassbox import ExplainableBoostingClassifier

        logger.info("Training Baseline 3: Explainable Boosting Machine (EBM)...")
        ebm_clf = ExplainableBoostingClassifier(
            random_state=random_state,
            max_bins=64,
            outer_bags=4,
            inner_bags=0,
            n_jobs=1,
        )
        ebm_clf.fit(X_train_trans, y_train)
        ebm_probs_val = ebm_clf.predict_proba(X_val_trans)[:, 1]
        ebm_val_metrics = evaluate_predictions(
            y_val, ebm_probs_val, amounts_val, threshold=0.5, c_fp=c_fp, c_review=c_review
        )
        logger.info(
            "Baseline 3 (EBM) Val Metrics: PR-AUC=%.4f, ROC-AUC=%.4f, Prec=%.4f, Rec=%.4f, Cost=INR %.2f",
            ebm_val_metrics["pr_auc"],
            ebm_val_metrics["roc_auc"],
            ebm_val_metrics["precision"],
            ebm_val_metrics["recall"],
            ebm_val_metrics["expected_cost"],
        )
    except ImportError:
        logger.warning("interpret package is not installed; skipping EBM baseline.")
    except Exception as e:
        logger.warning("Failed to train EBM baseline: %s", e)

    # 5. Main Model: LightGBM Classifier with Class Balancing
    n_pos = np.sum(y_train == 1)
    n_neg = np.sum(y_train == 0)
    scale_pos_weight = float(n_neg / max(1, n_pos))
    logger.info("LightGBM scale_pos_weight: %.2f (class imbalance ratio)", scale_pos_weight)

    raw_lgbm = lgb.LGBMClassifier(
        objective="binary",
        boosting_type="gbdt",
        n_estimators=150,
        learning_rate=0.04,
        num_leaves=24,
        max_depth=5,
        scale_pos_weight=scale_pos_weight,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_samples=8,
        random_state=random_state,
        verbose=-1,
        importance_type="gain",
    )
    raw_lgbm.fit(
        X_train_trans,
        y_train,
        eval_set=[(X_val_trans, y_val)],
        eval_metric="auc",
        callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)],
    )

    raw_val_probs = raw_lgbm.predict_proba(X_val_trans)[:, 1]
    raw_val_metrics = evaluate_predictions(
        y_val, raw_val_probs, amounts_val, threshold=0.5, c_fp=c_fp, c_review=c_review
    )
    logger.info("Raw LightGBM Val Metrics: PR-AUC=%.4f, ROC-AUC=%.4f, Brier=%.4f, Cost=INR %.2f",
                raw_val_metrics["pr_auc"], raw_val_metrics["roc_auc"], raw_val_metrics["brier_score"], raw_val_metrics["expected_cost"])

    # 6. Probability Calibration on Validation Partition
    logger.info("Performing probability calibration (%s) on validation set...", calibration_method)
    calibrator = ProbabilityCalibrator(
        base_estimator=raw_lgbm,
        method=calibration_method,
    )
    calibrator.fit(X_val_trans, y_val)
    calibrated_val_probs = calibrator.predict_proba(X_val_trans)[:, 1]

    cal_val_metrics_default = evaluate_predictions(
        y_val, calibrated_val_probs, amounts_val, threshold=0.5, c_fp=c_fp, c_review=c_review
    )
    logger.info("Calibrated LightGBM (T=0.50): PR-AUC=%.4f, ROC-AUC=%.4f, Brier=%.4f, Cost=INR %.2f",
                cal_val_metrics_default["pr_auc"], cal_val_metrics_default["roc_auc"], cal_val_metrics_default["brier_score"], cal_val_metrics_default["expected_cost"])

    # 7. Decision Threshold Optimization on Validation Set
    optimal_threshold, opt_val_metrics, cost_curve = optimize_threshold_for_cost(
        y_val, calibrated_val_probs, amounts_val, c_fp=c_fp, c_review=c_review
    )

    triage_thresholds = {
        "allow": 0.0,
        "review": round(float(optimal_threshold), 4),
        "hold": round(float(min(0.95, max(0.65, optimal_threshold + 0.25))), 4),
    }
    logger.info("Triage Policy Thresholds: %s", triage_thresholds)

    # 8. Model Benchmark Comparison Logging
    logger.info("=" * 88)
    logger.info("MODEL BENCHMARK COMPARISON SUMMARY (Validation Partition):")
    logger.info("-" * 88)
    logger.info("%-35s | %-7s | %-7s | %-7s | %-8s | %-14s", "Model / Baseline", "PR-AUC", "Prec", "Recall", "Brier", "Exp Cost (INR)")
    logger.info("-" * 88)
    logger.info("%-35s | %7.4f | %7.4f | %7.4f | %-8s | %14.2f", "1. Deterministic Rule Baseline", rule_val_metrics["pr_auc"], rule_val_metrics["precision"], rule_val_metrics["recall"], "-", rule_val_metrics["expected_cost"])
    logger.info("%-35s | %7.4f | %7.4f | %7.4f | %8.4f | %14.2f", "2. Class-Weighted LogReg", lr_val_metrics["pr_auc"], lr_val_metrics["precision"], lr_val_metrics["recall"], lr_val_metrics["brier_score"], lr_val_metrics["expected_cost"])
    if ebm_val_metrics is not None:
        logger.info("%-35s | %7.4f | %7.4f | %7.4f | %8.4f | %14.2f", "3. Explainable Boosting Machine (EBM)", ebm_val_metrics["pr_auc"], ebm_val_metrics["precision"], ebm_val_metrics["recall"], ebm_val_metrics["brier_score"], ebm_val_metrics["expected_cost"])
    logger.info("%-35s | %7.4f | %7.4f | %7.4f | %8.4f | %14.2f", "4. Raw LightGBM (T=0.50)", raw_val_metrics["pr_auc"], raw_val_metrics["precision"], raw_val_metrics["recall"], raw_val_metrics["brier_score"], raw_val_metrics["expected_cost"])
    logger.info("%-35s | %7.4f | %7.4f | %7.4f | %8.4f | %14.2f", f"5. LightGBM + {calibration_method.capitalize()} Cal (T=0.50)", cal_val_metrics_default["pr_auc"], cal_val_metrics_default["precision"], cal_val_metrics_default["recall"], cal_val_metrics_default["brier_score"], cal_val_metrics_default["expected_cost"])
    logger.info("%-35s | %7.4f | %7.4f | %7.4f | %8.4f | %14.2f", f"6. Sentinel Production (Opt T={optimal_threshold:.2f})", opt_val_metrics["pr_auc"], opt_val_metrics["precision"], opt_val_metrics["recall"], opt_val_metrics["brier_score"], opt_val_metrics["expected_cost"])
    logger.info("=" * 88)

    # 9. Setup SHAP TreeExplainer
    logger.info("Setting up SHAP TreeExplainer on LightGBM booster...")
    try:
        explainer = shap.TreeExplainer(raw_lgbm)
        logger.info("SHAP TreeExplainer initialized successfully.")
    except Exception as e:
        logger.warning("Could not initialize SHAP TreeExplainer directly: %s. Using fallback explainer.", e)
        explainer = None

    # 10. Package production Sentinel Model Wrapper
    metadata = {
        "model_name": "Sentinel-LightGBM-Calibrated",
        "version": "1.0.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "train_samples": len(train_df),
        "val_samples": len(val_df),
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "scale_pos_weight": scale_pos_weight,
        "calibration_method": calibration_method,
        "optimal_threshold": optimal_threshold,
        "triage_thresholds": triage_thresholds,
        "cost_parameters": {
            "customer_friction_cost_fp": c_fp,
            "analyst_review_cost": c_review,
            "daily_review_budget": DEFAULT_DAILY_BUDGET,
        },
        "validation_metrics": {
            "rule_baseline": rule_val_metrics,
            "logreg_baseline": lr_val_metrics,
            "ebm_baseline": ebm_val_metrics,
            "raw_lgbm": raw_val_metrics,
            "calibrated_lgbm_default_thresh": cal_val_metrics_default,
            "calibrated_lgbm_optimal_thresh": opt_val_metrics,
        },
    }

    wrapper = SentinelModelWrapper(
        transformer=transformer,
        calibrated_model=calibrator,
        raw_lgbm_model=raw_lgbm,
        explainer=explainer,
        optimal_threshold=optimal_threshold,
        triage_thresholds=triage_thresholds,
        metadata=metadata,
    )

    # Save to model artifact path
    model_output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Saving complete model pipeline artifact to: %s", model_output_path)
    joblib.dump(wrapper, model_output_path, compress=3)

    # Also save copy to default lgbm_model.joblib for backend config compatibility
    alt_model_path = model_output_path.parent / "lgbm_model.joblib"
    if alt_model_path != model_output_path:
        logger.info("Saving secondary model artifact copy to: %s", alt_model_path)
        joblib.dump(wrapper, alt_model_path, compress=3)

    logger.info("Training and serialization completed successfully!")
    return wrapper


def main():
    parser = argparse.ArgumentParser(description="Sentinel Final LightGBM Model and Policy Training")
    parser.add_argument("--train-path", type=str, default="data/processed/train.parquet", help="Path to train.parquet")
    parser.add_argument("--val-path", type=str, default="data/processed/val.parquet", help="Path to val.parquet")
    parser.add_argument("--model-output", type=str, default="data/models/lightgbm_model.joblib", help="Output path for model artifact")
    parser.add_argument("--c-fp", type=float, default=DEFAULT_C_FP, help="Customer friction cost per false positive alert (INR)")
    parser.add_argument("--c-review", type=float, default=DEFAULT_C_REVIEW, help="Analyst manual review cost per case (INR)")
    parser.add_argument("--calibration-method", type=str, default="beta", choices=["beta", "isotonic", "sigmoid"], help="Calibration method (default: beta)")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed for reproducibility")

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    train_path = project_root / args.train_path if not Path(args.train_path).is_absolute() else Path(args.train_path)
    val_path = project_root / args.val_path if not Path(args.val_path).is_absolute() else Path(args.val_path)
    out_path = project_root / args.model_output if not Path(args.model_output).is_absolute() else Path(args.model_output)

    train_sentinel_model(
        train_path=train_path,
        val_path=val_path,
        model_output_path=out_path,
        c_fp=args.c_fp,
        c_review=args.c_review,
        calibration_method=args.calibration_method,
        random_state=args.random_state,
    )


if __name__ == "__main__":
    main()
