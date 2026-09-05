#!/usr/bin/env python3
"""
Sentinel Online Drift Baseline Computation Engine (Phase 3)
==========================================================
Computes reference feature, score, and missingness distributions from `train.parquet`
and saves them to `data/processed/drift_baseline.json` for real-time online drift monitoring.

Key Computed Baseline Structures:
1. Numerical Features:
   - Parametric & non-parametric summary statistics (mean, std, min, max, quantiles p1..p99).
   - Decile bin edges & expected probability distributions for Population Stability Index (PSI).
   - Reference quantile vectors for fast 2-sample Kolmogorov-Smirnov (KS) tests.
   - Baseline missingness rates.
2. Categorical Features:
   - Discrete frequency and probability distributions.
   - Unique cardinality and baseline null rates.
3. Calibrated Risk Scores:
   - Score distribution percentiles from production LightGBM model.
   - Baseline alert rates across triage policy tiers (ALLOW / REVIEW / SIMULATED_HOLD).
4. Operational Thresholds:
   - Critical p-value (< 0.05), PSI boundaries (0.10 moderate, 0.25 severe), missingness tolerances.

Usage:
    python scripts/compute_drift_baseline.py --train-path data/processed/train.parquet --model-path data/models/lightgbm_model.joblib --output-json data/processed/drift_baseline.json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Ensure root in sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import joblib
import numpy as np
import pandas as pd
from scipy import stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sentinel.drift_baseline")


def compute_numerical_baseline(series: pd.Series, n_bins: int = 10) -> Dict[str, Any]:
    """Compute comprehensive statistical reference for continuous numerical feature."""
    valid = pd.to_numeric(series, errors="coerce").dropna().to_numpy()
    n_total = len(series)
    n_missing = int(series.isnull().sum())
    missing_rate = round(float(n_missing / max(1, n_total)), 4)

    if len(valid) == 0:
        return {
            "type": "numerical",
            "count": 0,
            "missing_count": n_missing,
            "missing_rate": missing_rate,
            "mean": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "median": 0.0,
            "quantiles": {},
            "psi_bins": [],
            "expected_bin_probs": [],
        }

    # Summary stats
    mean_val = float(np.mean(valid))
    std_val = float(np.std(valid))
    min_val = float(np.min(valid))
    max_val = float(np.max(valid))
    median_val = float(np.median(valid))

    # Standard Percentiles
    qs = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
    quantile_vals = {f"p{int(q*100):02d}": round(float(np.percentile(valid, q * 100)), 4) for q in qs}

    # Equal-frequency quantile bins for PSI computation
    bin_quantiles = np.linspace(0.0, 1.0, n_bins + 1)
    bin_edges = np.percentile(valid, bin_quantiles * 100)
    # Ensure strictly monotonic bin edges
    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf
    for i in range(1, len(bin_edges) - 1):
        if bin_edges[i] <= bin_edges[i - 1]:
            bin_edges[i] = bin_edges[i - 1] + 1e-5

    # Empirical bin probabilities
    counts, _ = np.histogram(valid, bins=bin_edges)
    bin_probs = (counts / max(1, len(valid))).tolist()

    # Sample quantiles (100 points) for fast 2-sample KS test approximation
    ks_reference_quantiles = np.percentile(valid, np.linspace(0, 100, 101)).tolist()

    return {
        "type": "numerical",
        "count": int(len(valid)),
        "missing_count": n_missing,
        "missing_rate": missing_rate,
        "mean": round(mean_val, 4),
        "std": round(std_val, 4),
        "min": round(min_val, 4),
        "max": round(max_val, 4),
        "median": round(median_val, 4),
        "quantiles": quantile_vals,
        "psi_bins": [float(b) if not np.isneginf(b) and not np.isposinf(b) else ("-inf" if np.isneginf(b) else "inf") for b in bin_edges],
        "expected_bin_probs": [round(float(p), 6) for p in bin_probs],
        "ks_reference_quantiles": [round(float(q), 4) for q in ks_reference_quantiles],
    }


def compute_categorical_baseline(series: pd.Series, top_k: int = 20) -> Dict[str, Any]:
    """Compute categorical probability distribution baseline."""
    n_total = len(series)
    n_missing = int(series.isnull().sum())
    missing_rate = round(float(n_missing / max(1, n_total)), 4)

    str_series = series.dropna().astype(str).str.strip()
    value_counts = str_series.value_counts()
    unique_count = len(value_counts)

    top_values = value_counts.head(top_k)
    prob_dist: Dict[str, float] = {}
    for val, count in top_values.items():
        prob_dist[str(val)] = round(float(count / max(1, len(str_series))), 4)

    # Remaining tail probability
    other_prob = max(0.0, 1.0 - sum(prob_dist.values()))
    if other_prob > 0.001:
        prob_dist["__OTHER__"] = round(other_prob, 4)

    return {
        "type": "categorical",
        "count": int(len(str_series)),
        "missing_count": n_missing,
        "missing_rate": missing_rate,
        "unique_categories": unique_count,
        "top_categories": prob_dist,
    }


def compute_drift_baseline(
    train_path: Path,
    model_path: Optional[Path] = None,
    output_json_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Compute complete online drift monitoring reference baseline."""
    logger.info("Loading training partition for drift baseline computation: %s", train_path)
    train_df = pd.read_parquet(train_path)

    # Exclude IDs and target
    ignore_cols = {"TransactionID", "isFraud"}
    feature_cols = [c for c in train_df.columns if c not in ignore_cols]

    feature_baselines: Dict[str, Any] = {}

    for col in feature_cols:
        series = train_df[col]
        if pd.api.types.is_numeric_dtype(series):
            # Numerical column
            feature_baselines[col] = compute_numerical_baseline(series)
        else:
            # Categorical column
            feature_baselines[col] = compute_categorical_baseline(series)

    # Derived temporal & amount feature baselines
    if "TransactionDT" in train_df.columns:
        hours = ((train_df["TransactionDT"] // 3600) % 24).astype(float)
        days = ((train_df["TransactionDT"] // 86400) % 7).astype(float)
        feature_baselines["hour_of_day"] = compute_numerical_baseline(hours)
        feature_baselines["day_of_week"] = compute_numerical_baseline(days)

    if "TransactionAmt" in train_df.columns:
        log_amt = np.log1p(np.clip(pd.to_numeric(train_df["TransactionAmt"], errors="coerce").fillna(0), 0, None))
        feature_baselines["log_TransactionAmt"] = compute_numerical_baseline(log_amt)

    # Model Risk Score Distribution Baseline
    score_baseline: Dict[str, Any] = {}
    if model_path is not None and model_path.exists():
        logger.info("Scoring training set to compute risk-score distribution baseline: %s", model_path)
        try:
            model = joblib.load(model_path)
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(train_df)[:, 1]
            elif hasattr(model, "predict"):
                probs = model.predict(train_df)
            else:
                probs = np.array([])

            if len(probs) > 0:
                opt_thresh = getattr(model, "optimal_threshold", 0.25)
                triage_thresh = getattr(model, "triage_thresholds", {"allow": 0.0, "review": 0.25, "hold": 0.65})

                hold_thresh = triage_thresh.get("hold", 0.65)
                review_thresh = triage_thresh.get("review", opt_thresh)

                score_num = compute_numerical_baseline(pd.Series(probs), n_bins=10)
                score_baseline = {
                    "distribution": score_num,
                    "mean_risk_score": score_num["mean"],
                    "median_risk_score": score_num["median"],
                    "p90_risk_score": score_num["quantiles"].get("p90", 0.0),
                    "p95_risk_score": score_num["quantiles"].get("p95", 0.0),
                    "p99_risk_score": score_num["quantiles"].get("p99", 0.0),
                    "baseline_alert_rate_optimal_threshold": round(float(np.mean(probs >= opt_thresh)), 4),
                    "baseline_hold_rate": round(float(np.mean(probs >= hold_thresh)), 4),
                    "baseline_review_rate": round(float(np.mean((probs >= review_thresh) & (probs < hold_thresh))), 4),
                    "baseline_allow_rate": round(float(np.mean(probs < review_thresh)), 4),
                    "thresholds_used": {
                        "optimal": opt_thresh,
                        "review": review_thresh,
                        "hold": hold_thresh,
                    }
                }
                logger.info("Baseline Alert Rate (T=%.3f): %.2f%% | Hold Rate: %.2f%% | Review Rate: %.2f%%",
                            opt_thresh, score_baseline["baseline_alert_rate_optimal_threshold"] * 100,
                            score_baseline["baseline_hold_rate"] * 100, score_baseline["baseline_review_rate"] * 100)
        except Exception as e:
            logger.warning("Could not compute score distribution baseline: %s", e)

    monitoring_policy = {
        "ks_test": {
            "p_value_alert_threshold": 0.05,
            "description": "p-value < 0.05 indicates statistically significant distribution shift against baseline.",
        },
        "psi": {
            "moderate_drift_threshold": 0.10,
            "severe_drift_threshold": 0.25,
            "description": "PSI < 0.10: Stable, 0.10-0.25: Moderate Drift, > 0.25: Significant Drift.",
        },
        "missingness": {
            "max_relative_increase": 0.15,
            "description": "Alert if column null percentage increases by >15% relative to baseline.",
        },
        "score_distribution": {
            "max_mean_score_shift": 0.05,
            "max_alert_rate_shift": 0.05,
            "description": "Alert if model score distribution or alert volume shifts noticeably.",
        },
    }

    baseline_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_name": "IEEE-CIS Training Partition (Strict Chronological)",
        "total_baseline_samples": len(train_df),
        "total_features": len(feature_baselines),
        "target_fraud_prevalence": round(float(train_df["isFraud"].mean()), 4) if "isFraud" in train_df else None,
        "features": feature_baselines,
        "risk_score_baseline": score_baseline,
        "monitoring_policy": monitoring_policy,
        "metadata": {
            "version": "1.0.0",
            "protocol": "Zero test-set access. Reference distributions computed exclusively from training data.",
        }
    }

    if output_json_path is not None:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Writing drift baseline reference JSON to: %s", output_json_path)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(baseline_payload, f, indent=2)

    logger.info("Drift baseline computation complete for %d features!", len(feature_baselines))
    return baseline_payload


def main():
    parser = argparse.ArgumentParser(description="Sentinel Online Drift Baseline Computation")
    parser.add_argument("--train-path", type=str, default="data/processed/train.parquet", help="Path to train.parquet")
    parser.add_argument("--model-path", type=str, default="data/models/lightgbm_model.joblib", help="Path to trained model artifact")
    parser.add_argument("--output-json", type=str, default="data/processed/drift_baseline.json", help="Path to save drift baseline JSON")

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    train_path = project_root / args.train_path if not Path(args.train_path).is_absolute() else Path(args.train_path)
    model_path = (project_root / args.model_path if not Path(args.model_path).is_absolute() else Path(args.model_path)) if args.model_path else None
    output_path = project_root / args.output_json if not Path(args.output_json).is_absolute() else Path(args.output_json)

    compute_drift_baseline(
        train_path=train_path,
        model_path=model_path,
        output_json_path=output_path,
    )


if __name__ == "__main__":
    main()
