#!/usr/bin/env python3
"""
Sentinel Metric Evaluation Engine (Phase 2)
===========================================
Calculates financial, operational, and statistical metrics on the held-out
frozen test dataset without any data leakage.

Key Metrics Computed:
1. Statistical: Precision, Recall, F1 Score, PR-AUC (Average Precision).
2. Operational: Recall@Budget (capturing fraud within daily review constraints).
3. Financial:
   - Preventable Exposure Captured (fraud value prevented / total fraud value).
   - False-Positive Cost (C_FP * FP_count).
   - Expected Total Cost (Missed Fraud Exposure + FP Cost + Review Cost).
   - Net Prevented Exposure (Prevented Fraud Value - FP Cost - Review Cost).
4. Multi-Model Comparison: Rule Engine Baseline vs LogReg vs LightGBM.

Usage:
    python scripts/evaluate.py --test-features data/processed/test_features.parquet --test-labels data/processed/test_labels.parquet
    python scripts/evaluate.py --model-path data/models/model.joblib --output-json data/processed/metrics.json --output-md data/processed/evaluation_report.md
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure project root in sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sentinel.evaluate")


# Demo Scenario Cost Defaults
DEFAULT_C_FP = 150.0        # Customer friction cost per false positive alert
DEFAULT_C_REVIEW = 25.0     # Analyst triage cost per reviewed alert
DEFAULT_DAILY_BUDGET = 100  # Manual review capacity (alerts per day)
DEFAULT_THRESHOLD = 0.25    # Decision threshold fallback for binary fraud flag
DEFAULT_FALLBACK_THRESHOLD = 0.25  # Fallback default threshold if model optimal_threshold unavailable


def extract_optimal_threshold(model_obj: Any) -> Optional[float]:
    """
    Extract the optimal decision threshold from a trained model artifact or dictionary.
    Checks:
    - model.optimal_threshold attribute
    - model.threshold attribute
    - model.metadata['optimal_threshold']
    - model.triage_thresholds['review']
    - dict keys: 'optimal_threshold', 'threshold', 'config.optimal_threshold'
    """
    if model_obj is None:
        return None

    # Check direct attributes
    if hasattr(model_obj, "optimal_threshold"):
        val = getattr(model_obj, "optimal_threshold")
        if isinstance(val, (int, float)) and 0.0 < float(val) < 1.0:
            return float(val)

    if hasattr(model_obj, "threshold"):
        val = getattr(model_obj, "threshold")
        if isinstance(val, (int, float)) and 0.0 < float(val) < 1.0:
            return float(val)

    # Check dictionary
    if isinstance(model_obj, dict):
        for key in ["optimal_threshold", "threshold"]:
            if key in model_obj and isinstance(model_obj[key], (int, float)) and 0.0 < float(model_obj[key]) < 1.0:
                return float(model_obj[key])
        if "config" in model_obj and isinstance(model_obj["config"], dict):
            cfg = model_obj["config"]
            for key in ["optimal_threshold", "threshold"]:
                if key in cfg and isinstance(cfg[key], (int, float)) and 0.0 < float(cfg[key]) < 1.0:
                    return float(cfg[key])
        if "metadata" in model_obj and isinstance(model_obj["metadata"], dict):
            meta = model_obj["metadata"]
            if "optimal_threshold" in meta and isinstance(meta["optimal_threshold"], (int, float)) and 0.0 < float(meta["optimal_threshold"]) < 1.0:
                return float(meta["optimal_threshold"])
        if "triage_thresholds" in model_obj and isinstance(model_obj["triage_thresholds"], dict):
            tt = model_obj["triage_thresholds"]
            if "review" in tt and isinstance(tt["review"], (int, float)) and 0.0 < float(tt["review"]) < 1.0:
                return float(tt["review"])

    # Check metadata attribute if object
    if hasattr(model_obj, "metadata") and isinstance(getattr(model_obj, "metadata"), dict):
        meta = getattr(model_obj, "metadata")
        if "optimal_threshold" in meta and isinstance(meta["optimal_threshold"], (int, float)) and 0.0 < float(meta["optimal_threshold"]) < 1.0:
            return float(meta["optimal_threshold"])

    # Check triage_thresholds attribute if object
    if hasattr(model_obj, "triage_thresholds") and isinstance(getattr(model_obj, "triage_thresholds"), dict):
        tt = getattr(model_obj, "triage_thresholds")
        if "review" in tt and isinstance(tt["review"], (int, float)) and 0.0 < float(tt["review"]) < 1.0:
            return float(tt["review"])

    return None


class BaselineRuleEngine:
    """
    Deterministic rule-based baseline mimicking conventional risk gates:
    - High transaction amount (> 95th percentile or > 1000)
    - High-risk product codes (C, R)
    - Suspicious email domains (anonymous / unusual)
    - High velocity / transaction frequency count (C1 > 3)
    """
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        scores = np.zeros(len(X), dtype=float)

        if "TransactionAmt" in X.columns:
            scores += np.where(X["TransactionAmt"] > 1000, 0.35, 0.0)
            scores += np.where(X["TransactionAmt"] > 2500, 0.25, 0.0)

        if "ProductCD" in X.columns:
            scores += np.where(X["ProductCD"].isin(["C", "R"]), 0.20, 0.0)

        if "P_emaildomain" in X.columns:
            scores += np.where(X["P_emaildomain"].astype(str).str.contains("anon|mail|proton", case=False, na=False), 0.20, 0.0)

        if "C1" in X.columns:
            scores += np.where(pd.to_numeric(X["C1"], errors="coerce").fillna(0) > 3, 0.20, 0.0)

        # Normalize to valid probability [0.01, 0.99]
        scores = np.clip(scores, 0.02, 0.95)
        # Return 2D array (prob_neg, prob_pos)
        return np.column_stack([1.0 - scores, scores])

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        prob = self.predict_proba(X)[:, 1]
        return (prob >= threshold).astype(int)


def calculate_sentinel_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    amounts: np.ndarray,
    timestamps: Optional[np.ndarray] = None,
    threshold: float = DEFAULT_THRESHOLD,
    c_fp: float = DEFAULT_C_FP,
    c_review: float = DEFAULT_C_REVIEW,
    daily_review_budget: int = DEFAULT_DAILY_BUDGET,
    triage_review_threshold: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calculate full suite of Sentinel metrics on test predictions.
    """
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    amounts = np.asarray(amounts, dtype=float)

    n_total = len(y_true)
    if n_total == 0:
        raise ValueError("Cannot evaluate empty ground-truth arrays.")

    y_pred = (y_prob >= threshold).astype(int)

    # Standard Classification Metrics
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    # PR-AUC & ROC-AUC
    try:
        pr_auc = average_precision_score(y_true, y_prob)
    except Exception:
        pr_auc = 0.0

    try:
        roc_auc = roc_auc_score(y_true, y_prob)
    except Exception:
        roc_auc = 0.5

    # Total exposure statistics
    total_fraud_count = int(np.sum(y_true == 1))
    total_fraud_exposure = float(np.sum(amounts[y_true == 1]))
    total_transaction_exposure = float(np.sum(amounts))

    # Preventable Exposure Captured (Recall on financial loss)
    # Sum of transaction amount for True Positives / Total Fraud Amount
    captured_fraud_exposure = float(np.sum(amounts[(y_true == 1) & (y_pred == 1)]))
    preventable_exposure_captured = (
        (captured_fraud_exposure / total_fraud_exposure) if total_fraud_exposure > 0 else 0.0
    )

    # Recall@Budget calculation
    # Determine number of days in test set from timestamps (or default estimation)
    if timestamps is not None and len(timestamps) > 1:
        dt_span_seconds = float(np.max(timestamps) - np.min(timestamps))
        dt_span_days = max(1.0, dt_span_seconds / 86400.0)
    else:
        # If timestamp not provided, approximate test duration as ~30 days
        dt_span_days = 30.0

    total_review_capacity = int(min(n_total, np.ceil(daily_review_budget * dt_span_days)))
    # Top B transactions by descending risk score
    ranked_indices = np.argsort(y_prob)[::-1]
    budget_top_indices = ranked_indices[:total_review_capacity]
    fraud_captured_at_budget = int(np.sum(y_true[budget_top_indices] == 1))
    recall_at_budget = (
        (fraud_captured_at_budget / total_fraud_count) if total_fraud_count > 0 else 0.0
    )

    # Financial Cost Model
    # False-Positive Cost
    false_positive_cost = float(fp * c_fp)

    # Missed Fraud Loss (False Negatives amount)
    missed_fraud_exposure = float(np.sum(amounts[(y_true == 1) & (y_pred == 0)]))

    # Review Cost (Cases between review_threshold and auto_hold_threshold if triage mode enabled)
    if triage_review_threshold is not None and triage_review_threshold < threshold:
        review_cases = (y_prob >= triage_review_threshold) & (y_prob < threshold)
        n_review = int(np.sum(review_cases))
    else:
        n_review = int(fp + tp)  # Default all flagged cases
    review_cost = float(n_review * c_review)

    # Total Expected Cost
    expected_cost = float(missed_fraud_exposure + false_positive_cost + review_cost)

    # Net Prevented Exposure (Value saved - FP friction - Review operational cost)
    net_prevented_exposure = float(captured_fraud_exposure - false_positive_cost - review_cost)

    return {
        # Core Frontend Contract Schema
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "prAuc": round(float(pr_auc), 4),
        "recallAtBudget": round(float(recall_at_budget), 4),
        "preventableExposureCaptured": round(float(preventable_exposure_captured), 4),
        "falsePositiveCost": round(float(false_positive_cost), 2),
        # Extended Comprehensive Metrics
        "f1": round(float(f1), 4),
        "rocAuc": round(float(roc_auc), 4),
        "expectedCost": round(float(expected_cost), 2),
        "netPreventedExposure": round(float(net_prevented_exposure), 2),
        "totalTransactions": int(n_total),
        "totalFraudTransactions": int(total_fraud_count),
        "totalFraudExposure": round(float(total_fraud_exposure), 2),
        "capturedFraudExposure": round(float(captured_fraud_exposure), 2),
        "missedFraudExposure": round(float(missed_fraud_exposure), 2),
        "reviewCost": round(float(review_cost), 2),
        "operatingParameters": {
            "decisionThreshold": float(threshold),
            "customerFrictionCostFP": float(c_fp),
            "analystReviewCost": float(c_review),
            "dailyReviewBudget": int(daily_review_budget),
            "testDurationDays": round(float(dt_span_days), 1),
            "reviewCapacityTotal": int(total_review_capacity),
        },
        "confusionMatrix": {
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn),
        },
    }


def generate_markdown_report(
    primary_metrics: Dict[str, Any],
    comparison_table: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Generate clean, formatted markdown evaluation summary."""
    cm = primary_metrics.get("confusionMatrix", {})
    params = primary_metrics.get("operatingParameters", {})

    md = [
        "# Sentinel Fraud Triage — Held-Out Test Evaluation Report",
        "",
        f"> **Generated at**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
        "> **Protocol**: Strict chronological split on `TransactionDT` (Zero test-leakage).",
        "",
        "## 1. Executive Performance Summary",
        "",
        "| Metric | Value | Operational Meaning |",
        "|---|---|---|",
        f"| **PR-AUC** | `{primary_metrics['prAuc']:.4f}` | Area under Precision-Recall curve across all thresholds |",
        f"| **Precision** | `{primary_metrics['precision']:.4f}` | Fraction of flagged transactions that were genuine fraud |",
        f"| **Recall** | `{primary_metrics['recall']:.4f}` | Fraction of total fraudulent transactions detected |",
        f"| **F1 Score** | `{primary_metrics.get('f1', 0.0):.4f}` | Harmonic mean of precision and recall |",
        f"| **Recall @ Budget ({params.get('dailyReviewBudget', 100)}/day)** | `{primary_metrics['recallAtBudget']:.4f}` | Fraud captured under human review capacity constraints |",
        f"| **Preventable Exposure Captured** | `{primary_metrics['preventableExposureCaptured'] * 100:.2f}%` | Percentage of total fraud financial exposure prevented |",
        f"| **False-Positive Cost** | `₹{primary_metrics['falsePositiveCost']:,.2f}` | Friction cost from legitimate transactions flagged |",
        f"| **Net Prevented Exposure** | `₹{primary_metrics.get('netPreventedExposure', 0.0):,.2f}` | Financial fraud prevented minus FP friction & review costs |",
        "",
        "## 2. Confusion Matrix & Financial Breakdown",
        "",
        "```",
        f"                    Actual Legitimate (0)    Actual Fraud (1)",
        f"Predicted Allow:    TN = {cm.get('tn', 0):<16} FN = {cm.get('fn', 0)}",
        f"Predicted Flag :    FP = {cm.get('fp', 0):<16} TP = {cm.get('tp', 0)}",
        "```",
        "",
        f"- **Total Scored Transactions**: `{primary_metrics['totalTransactions']:,}`",
        f"- **Total Fraud Cases**: `{primary_metrics['totalFraudTransactions']:,}` (Prevalence: `{primary_metrics['totalFraudTransactions'] / max(1, primary_metrics['totalTransactions']) * 100:.2f}%`)",
        f"- **Total Fraud Exposure**: `₹{primary_metrics.get('totalFraudExposure', 0.0):,.2f}`",
        f"- **Prevented Fraud Exposure**: `₹{primary_metrics.get('capturedFraudExposure', 0.0):,.2f}`",
        f"- **Missed Fraud Exposure**: `₹{primary_metrics.get('missedFraudExposure', 0.0):,.2f}`",
        "",
    ]

    if comparison_table:
        md.extend([
            "## 3. Model Benchmark Comparison",
            "",
            "| Model / Architecture | Precision | Recall | PR-AUC | Recall@Budget | Preventable Exposure | FP Cost (₹) | Net Prevented (₹) |",
            "|---|---|---|---|---|---|---|---|",
        ])
        for row in comparison_table:
            md.append(
                f"| **{row['name']}** | {row['precision']:.4f} | {row['recall']:.4f} | {row['prAuc']:.4f} | "
                f"{row['recallAtBudget']:.4f} | {row['preventableExposureCaptured'] * 100:.1f}% | "
                f"₹{row['falsePositiveCost']:,.0f} | ₹{row.get('netPreventedExposure', 0.0):,.0f} |"
            )
        md.append("")

    md.extend([
        "## 4. Cost Policy Parameters (Demo Assumptions)",
        "",
        f"- Decision Threshold: `{params.get('decisionThreshold', 0.5):.2f}`",
        f"- Customer Friction Cost ($C_{{FP}}$): `₹{params.get('customerFrictionCostFP', 150.0):.2f}` per false alert",
        f"- Analyst Review Cost ($C_{{Review}}$): `₹{params.get('analystReviewCost', 25.0):.2f}` per case",
        f"- Operations Review Capacity: `{params.get('dailyReviewBudget', 100)}` alerts/day",
        "",
    ])

    return "\n".join(md)


def run_evaluation(
    test_features_path: Path,
    test_labels_path: Path,
    model_path: Optional[Path] = None,
    predictions_path: Optional[Path] = None,
    output_json_path: Optional[Path] = None,
    output_md_path: Optional[Path] = None,
    threshold: Optional[float] = None,
    c_fp: float = DEFAULT_C_FP,
    c_review: float = DEFAULT_C_REVIEW,
    daily_budget: int = DEFAULT_DAILY_BUDGET,
) -> Dict[str, Any]:
    """Execute complete evaluation workflow."""
    logger.info("Loading test features: %s", test_features_path)
    test_features = pd.read_parquet(test_features_path)

    logger.info("Loading test labels: %s", test_labels_path)
    test_labels = pd.read_parquet(test_labels_path)

    if len(test_features) != len(test_labels):
        raise ValueError(f"Feature count ({len(test_features)}) != Label count ({len(test_labels)})")

    y_true = test_labels["isFraud"].to_numpy()
    amounts = (
        test_labels["TransactionAmt"].to_numpy()
        if "TransactionAmt" in test_labels.columns
        else test_features["TransactionAmt"].to_numpy()
        if "TransactionAmt" in test_features.columns
        else np.ones(len(y_true)) * 100.0
    )
    timestamps = (
        test_labels["TransactionDT"].to_numpy()
        if "TransactionDT" in test_labels.columns
        else test_features["TransactionDT"].to_numpy()
        if "TransactionDT" in test_features.columns
        else None
    )

    comparison_results: List[Dict[str, Any]] = []

    # 1. Evaluate Rule Baseline
    rule_engine = BaselineRuleEngine()
    rule_probs = rule_engine.predict_proba(test_features)[:, 1]
    rule_metrics = calculate_sentinel_metrics(
        y_true, rule_probs, amounts, timestamps,
        threshold=0.45, c_fp=c_fp, c_review=c_review, daily_review_budget=daily_budget
    )
    rule_metrics["name"] = "Deterministic Rule Baseline"
    comparison_results.append(rule_metrics)

    # 2. Resolve Model Candidate Paths if not specified
    resolved_model_path: Optional[Path] = None
    if model_path is not None and Path(model_path).exists():
        resolved_model_path = Path(model_path)
    elif model_path is None:
        candidate_paths = [
            _project_root / "data" / "models" / "lightgbm_model.joblib",
            _project_root / "data" / "models" / "lgbm_model.joblib",
            Path("data/models/lightgbm_model.joblib"),
            Path("data/models/lgbm_model.joblib"),
        ]
        for cand in candidate_paths:
            if cand.exists():
                resolved_model_path = cand
                break

    # 3. Evaluate Trained Model or Precomputed Predictions
    primary_metrics: Dict[str, Any]
    if predictions_path is not None and Path(predictions_path).exists():
        logger.info("Loading pre-computed predictions from: %s", predictions_path)
        pred_df = pd.read_parquet(predictions_path) if str(predictions_path).endswith(".parquet") else pd.read_csv(predictions_path)
        score_col = "riskScore" if "riskScore" in pred_df.columns else "y_prob" if "y_prob" in pred_df.columns else "score"
        y_prob = pred_df[score_col].to_numpy()

        eval_threshold = threshold if threshold is not None else DEFAULT_FALLBACK_THRESHOLD
        logger.info("Evaluating predictions with decision threshold: %.4f", eval_threshold)
        primary_metrics = calculate_sentinel_metrics(
            y_true, y_prob, amounts, timestamps,
            threshold=eval_threshold, c_fp=c_fp, c_review=c_review, daily_review_budget=daily_budget
        )
        primary_metrics["name"] = "Provided Predictions"
        comparison_results.append(primary_metrics)

    elif resolved_model_path is not None and resolved_model_path.exists():
        logger.info("Loading trained model artifact from: %s", resolved_model_path)
        try:
            model = joblib.load(resolved_model_path)
        except Exception as e:
            logger.error("Failed to load model artifact from %s: %s", resolved_model_path, e)
            model = None

        if model is not None:
            # Extract optimal threshold from model artifact if caller did not specify explicit threshold
            opt_thresh = extract_optimal_threshold(model)
            if threshold is not None:
                eval_threshold = threshold
                logger.info("Using explicitly specified threshold: %.4f", eval_threshold)
            elif opt_thresh is not None:
                eval_threshold = opt_thresh
                logger.info("Using extracted optimal threshold from model artifact: %.4f", eval_threshold)
            else:
                eval_threshold = DEFAULT_FALLBACK_THRESHOLD
                logger.info("Model artifact has no optimal threshold; using fallback default: %.4f", eval_threshold)

            if hasattr(model, "predict_proba"):
                y_prob = model.predict_proba(test_features)[:, 1]
            elif hasattr(model, "predict"):
                y_prob = model.predict(test_features)
            else:
                raise ValueError("Loaded model object has no predict or predict_proba method.")

            primary_metrics = calculate_sentinel_metrics(
                y_true, y_prob, amounts, timestamps,
                threshold=eval_threshold, c_fp=c_fp, c_review=c_review, daily_review_budget=daily_budget
            )
            primary_metrics["name"] = "Trained Model (LightGBM/Calibrated)"
            comparison_results.append(primary_metrics)
        else:
            logger.warning("Could not load model; falling back to rule baseline as primary reference.")
            primary_metrics = rule_metrics

    else:
        logger.info("No trained model or predictions found; using rule baseline as primary reference.")
        primary_metrics = rule_metrics

    # Save output JSON
    if output_json_path is not None:
        output_json_path = Path(output_json_path)
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Writing metrics JSON to: %s", output_json_path)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(primary_metrics, f, indent=2)

    # Save output Markdown
    report_md = generate_markdown_report(primary_metrics, comparison_results)
    if output_md_path is not None:
        output_md_path = Path(output_md_path)
        output_md_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Writing evaluation report Markdown to: %s", output_md_path)
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(report_md)

    logger.info("Evaluation Complete!")
    logger.info("PR-AUC: %.4f | Precision: %.4f | Recall: %.4f | Recall@Budget: %.4f",
                primary_metrics["prAuc"], primary_metrics["precision"], primary_metrics["recall"], primary_metrics["recallAtBudget"])
    logger.info("Preventable Exposure Captured: %.2f%% | FP Cost: ₹%.2f | Net Prevented: ₹%.2f",
                primary_metrics["preventableExposureCaptured"] * 100, primary_metrics["falsePositiveCost"], primary_metrics.get("netPreventedExposure", 0.0))

    return primary_metrics


def main():
    parser = argparse.ArgumentParser(description="Sentinel Frozen Test Metric Evaluation")
    parser.add_argument("--test-features", type=str, default="data/processed/test_features.parquet", help="Path to test_features.parquet")
    parser.add_argument("--test-labels", type=str, default="data/processed/test_labels.parquet", help="Path to test_labels.parquet")
    parser.add_argument("--model-path", type=str, default="data/models/lightgbm_model.joblib", help="Path to trained model artifact (.joblib)")
    parser.add_argument("--predictions-path", type=str, default=None, help="Path to precomputed predictions file")
    parser.add_argument("--output-json", type=str, default="data/processed/metrics.json", help="Path to save metrics JSON")
    parser.add_argument("--output-md", type=str, default="data/processed/evaluation_report.md", help="Path to save markdown report")
    parser.add_argument("--threshold", type=float, default=None, help="Decision threshold for fraud flagging (default: optimal threshold from model artifact or 0.25)")
    parser.add_argument("--c-fp", type=float, default=DEFAULT_C_FP, help="Customer friction cost per false positive (INR)")
    parser.add_argument("--c-review", type=float, default=DEFAULT_C_REVIEW, help="Analyst review cost per case (INR)")
    parser.add_argument("--daily-budget", type=int, default=DEFAULT_DAILY_BUDGET, help="Daily analyst review capacity (alerts/day)")

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    features_path = project_root / args.test_features if not Path(args.test_features).is_absolute() else Path(args.test_features)
    labels_path = project_root / args.test_labels if not Path(args.test_labels).is_absolute() else Path(args.test_labels)
    
    model_path = None
    if args.model_path:
        p = project_root / args.model_path if not Path(args.model_path).is_absolute() else Path(args.model_path)
        if p.exists():
            model_path = p
        else:
            # Check alternative default
            alt = project_root / "data" / "models" / "lgbm_model.joblib"
            if alt.exists():
                model_path = alt
            else:
                model_path = p

    pred_path = (project_root / args.predictions_path if not Path(args.predictions_path).is_absolute() else Path(args.predictions_path)) if args.predictions_path else None
    out_json = project_root / args.output_json if not Path(args.output_json).is_absolute() else Path(args.output_json)
    out_md = project_root / args.output_md if not Path(args.output_md).is_absolute() else Path(args.output_md)

    run_evaluation(
        test_features_path=features_path,
        test_labels_path=labels_path,
        model_path=model_path,
        predictions_path=pred_path,
        output_json_path=out_json,
        output_md_path=out_md,
        threshold=args.threshold,
        c_fp=args.c_fp,
        c_review=args.c_review,
        daily_budget=args.daily_budget,
    )


if __name__ == "__main__":
    main()
