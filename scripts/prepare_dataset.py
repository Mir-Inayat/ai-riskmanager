#!/usr/bin/env python3
"""
Sentinel Data Preparation Pipeline (Phase 1)
===========================================
Prepares IEEE-CIS Fraud Detection transaction and identity datasets with:
1. Robust joining of transaction and identity tables on TransactionID.
2. Strict chronological splitting along the `TransactionDT` time axis:
   - Training Window (first 70%)
   - Validation Window (middle 15%)
   - Frozen Held-Out Test Window (latest 15%)
3. Anti-leakage isolation:
   - Separate `test_features.parquet` (pre-transaction features only, no labels)
   - Separate `test_labels.parquet` (TransactionID, isFraud, TransactionAmt)
4. Comprehensive metadata logging (`data_card.json`).

Usage:
    python scripts/prepare_dataset.py --raw-dir data/raw --processed-dir data/processed
    python scripts/prepare_dataset.py --create-synthetic-sample --n-samples 5000
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sentinel.prepare_dataset")


def find_file_in_dir(directory: Path, candidates: list[str]) -> Optional[Path]:
    """Search for matching candidate filenames in directory (case-insensitive)."""
    if not directory.exists():
        return None
    dir_files = {f.name.lower(): f for f in directory.iterdir() if f.is_file()}
    for candidate in candidates:
        if candidate.lower() in dir_files:
            return dir_files[candidate.lower()]
    return None


def generate_synthetic_ieee_cis(n_samples: int = 5000, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate realistic synthetic IEEE-CIS transaction and identity data
    matching schema and statistical properties for testing and CI validation.
    """
    logger.info("Generating synthetic IEEE-CIS dataset (%d records)...", n_samples)
    rng = np.random.RandomState(random_state)

    # Monotonic chronological timestamps (TransactionDT in seconds across ~180 days)
    dt_intervals = rng.exponential(scale=3000.0, size=n_samples)
    transaction_dt = np.cumsum(dt_intervals).astype(int)

    transaction_ids = 3000000 + np.arange(n_samples)

    # Core transaction features
    amounts = np.round(rng.lognormal(mean=4.0, sigma=1.1, size=n_samples), 2)
    amounts = np.clip(amounts, 5.0, 5000.0)

    product_codes = rng.choice(["W", "C", "H", "R", "S"], size=n_samples, p=[0.70, 0.15, 0.05, 0.07, 0.03])
    card1 = rng.randint(1000, 20000, size=n_samples)
    card2 = rng.choice([111, 222, 333, 444, 555, np.nan], size=n_samples, p=[0.25, 0.25, 0.20, 0.15, 0.10, 0.05])
    card3 = rng.choice([150, 185, np.nan], size=n_samples, p=[0.90, 0.05, 0.05])
    card4 = rng.choice(["visa", "mastercard", "discover", "american express", None], size=n_samples, p=[0.65, 0.30, 0.02, 0.02, 0.01])
    card5 = rng.choice([126, 166, 226, np.nan], size=n_samples, p=[0.4, 0.3, 0.25, 0.05])
    card6 = rng.choice(["debit", "credit", None], size=n_samples, p=[0.70, 0.28, 0.02])

    addr1 = rng.choice([126, 204, 299, 325, 441, np.nan], size=n_samples, p=[0.2, 0.2, 0.2, 0.2, 0.15, 0.05])
    addr2 = rng.choice([87, np.nan], size=n_samples, p=[0.95, 0.05])
    dist1 = rng.choice([0, 10, 25, 100, np.nan], size=n_samples, p=[0.3, 0.2, 0.1, 0.05, 0.35])

    p_email = rng.choice(["gmail.com", "yahoo.com", "hotmail.com", "anonymous.com", "aol.com", None], size=n_samples, p=[0.45, 0.25, 0.15, 0.05, 0.05, 0.05])
    r_email = rng.choice(["gmail.com", "yahoo.com", "hotmail.com", "anonymous.com", None], size=n_samples, p=[0.25, 0.15, 0.10, 0.05, 0.45])

    # Counting/velocity and timedelta features
    c1 = rng.poisson(lam=1.5, size=n_samples)
    c2 = rng.poisson(lam=1.8, size=n_samples)
    d1 = rng.randint(0, 365, size=n_samples)
    d2 = rng.choice([0, 10, 30, np.nan], size=n_samples, p=[0.4, 0.2, 0.1, 0.3])

    # Vesta features subset
    v1 = rng.choice([1.0, 0.0, np.nan], size=n_samples, p=[0.6, 0.3, 0.1])
    v257 = rng.choice([1.0, 2.0, 0.0, np.nan], size=n_samples, p=[0.4, 0.2, 0.3, 0.1])

    # Calculate fraud probability based on realistic risk signals
    fraud_logits = (
        -4.2
        + 1.8 * np.isin(product_codes, ["C", "R"])
        + 2.0 * (p_email == "anonymous.com")
        + 1.5 * (c1 >= 4)
        + 1.3 * (c2 >= 4)
        + 1.1 * (card4 == "discover")
        + 1.2 * (amounts > 500)
    )
    fraud_prob = 1.0 / (1.0 + np.exp(-fraud_logits))
    is_fraud = (rng.uniform(0, 1, size=n_samples) < fraud_prob).astype(int)

    # For fraudulent transactions, scale transaction amounts to realistic fraud amounts ($400 - $3000)
    amounts_final = amounts.copy()
    if np.sum(is_fraud) > 0:
        amounts_final[is_fraud == 1] = np.round(rng.uniform(400.0, 3000.0, size=int(np.sum(is_fraud))), 2)

    transaction_df = pd.DataFrame({
        "TransactionID": transaction_ids,
        "isFraud": is_fraud,
        "TransactionDT": transaction_dt,
        "TransactionAmt": amounts_final,
        "ProductCD": product_codes,
        "card1": card1,
        "card2": card2,
        "card3": card3,
        "card4": card4,
        "card5": card5,
        "card6": card6,
        "addr1": addr1,
        "addr2": addr2,
        "dist1": dist1,
        "P_emaildomain": p_email,
        "R_emaildomain": r_email,
        "C1": c1,
        "C2": c2,
        "D1": d1,
        "D2": d2,
        "V1": v1,
        "V257": v257,
    })

    # Identity table (~30% of transactions have identity metadata)
    has_identity = rng.choice([True, False], size=n_samples, p=[0.35, 0.65])
    identity_ids = transaction_ids[has_identity]
    n_id = len(identity_ids)

    device_types = rng.choice(["mobile", "desktop", None], size=n_id, p=[0.55, 0.40, 0.05])
    device_info = rng.choice(["iOS Device", "Windows", "MacOS", "SM-G960N", "Moto G", None], size=n_id, p=[0.35, 0.30, 0.15, 0.10, 0.05, 0.05])
    id_30 = rng.choice(["iOS 12.1.0", "Windows 10", "Android 9", "Mac OS X 10_13_6", None], size=n_id, p=[0.35, 0.30, 0.15, 0.15, 0.05])
    id_31 = rng.choice(["mobile safari 12.0", "chrome 70.0", "ie 11.0", "safari 12.0", None], size=n_id, p=[0.35, 0.40, 0.05, 0.15, 0.05])

    identity_df = pd.DataFrame({
        "TransactionID": identity_ids,
        "DeviceType": device_types,
        "DeviceInfo": device_info,
        "id_30": id_30,
        "id_31": id_31,
    })

    return transaction_df, identity_df


def load_and_join_data(raw_dir: Path, allow_synthetic_fallback: bool = True) -> pd.DataFrame:
    """
    Load raw transaction and identity CSVs and perform left join on TransactionID.
    If files are missing and fallback is enabled, generates synthetic dataset.
    """
    raw_dir = Path(raw_dir)
    txn_file = find_file_in_dir(raw_dir, ["transaction.csv", "train_transaction.csv", "transactions.csv"])
    id_file = find_file_in_dir(raw_dir, ["identity.csv", "train_identity.csv", "identities.csv"])

    if txn_file is None:
        if allow_synthetic_fallback:
            logger.warning(
                "Raw transaction file not found in %s. Generating synthetic IEEE-CIS sample dataset...",
                raw_dir
            )
            raw_dir.mkdir(parents=True, exist_ok=True)
            synth_txn, synth_id = generate_synthetic_ieee_cis(n_samples=6000)
            synth_txn.to_csv(raw_dir / "transaction.csv", index=False)
            synth_id.to_csv(raw_dir / "identity.csv", index=False)
            txn_file = raw_dir / "transaction.csv"
            id_file = raw_dir / "identity.csv"
            logger.info("Saved synthetic raw CSVs to %s for downstream reproducibility.", raw_dir)
        else:
            raise FileNotFoundError(f"No transaction CSV found in {raw_dir}")

    logger.info("Loading transaction dataset from: %s", txn_file)
    txn_df = pd.read_csv(txn_file)
    logger.info("Loaded %d transactions with %d columns.", len(txn_df), txn_df.shape[1])

    if id_file is not None and id_file.exists():
        logger.info("Loading identity dataset from: %s", id_file)
        id_df = pd.read_csv(id_file)
        logger.info("Loaded %d identity records.", len(id_df))
        merged_df = txn_df.merge(id_df, on="TransactionID", how="left")
    else:
        logger.info("No identity CSV found; proceeding with transaction records.")
        merged_df = txn_df

    logger.info("Merged dataset shape: %s", merged_df.shape)
    return merged_df


def perform_chronological_split(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Perform a strict chronological split along `TransactionDT`.
    Guarantees no future temporal leakage into training or validation windows.
    """
    if "TransactionDT" not in df.columns:
        raise ValueError("Dataset missing required chronological axis column 'TransactionDT'.")

    total_ratio = train_ratio + val_ratio + test_ratio
    if not np.isclose(total_ratio, 1.0):
        raise ValueError(f"Split ratios must sum to 1.0 (got {total_ratio})")

    # Sort deterministically by TransactionDT then TransactionID
    sort_cols = ["TransactionDT"]
    if "TransactionID" in df.columns:
        sort_cols.append("TransactionID")
    df_sorted = df.sort_values(by=sort_cols).reset_index(drop=True)

    n_total = len(df_sorted)
    train_end_idx = int(n_total * train_ratio)
    val_end_idx = int(n_total * (train_ratio + val_ratio))

    train_df = df_sorted.iloc[:train_end_idx].copy()
    val_df = df_sorted.iloc[train_end_idx:val_end_idx].copy()
    test_df = df_sorted.iloc[val_end_idx:].copy()

    # Time boundaries
    dt_min = int(df_sorted["TransactionDT"].min())
    dt_max = int(df_sorted["TransactionDT"].max())
    train_dt_max = int(train_df["TransactionDT"].max()) if len(train_df) > 0 else 0
    val_dt_min = int(val_df["TransactionDT"].min()) if len(val_df) > 0 else 0
    val_dt_max = int(val_df["TransactionDT"].max()) if len(val_df) > 0 else 0
    test_dt_min = int(test_df["TransactionDT"].min()) if len(test_df) > 0 else 0

    # Verification of zero temporal overlap
    assert train_dt_max <= val_dt_min, f"Train-Val temporal overlap detected: train_max={train_dt_max}, val_min={val_dt_min}"
    assert val_dt_max <= test_dt_min, f"Val-Test temporal overlap detected: val_max={val_dt_max}, test_min={test_dt_min}"

    def compute_stats(split_name: str, split_df: pd.DataFrame) -> Dict[str, Any]:
        has_fraud = "isFraud" in split_df.columns
        fraud_count = int(split_df["isFraud"].sum()) if has_fraud else 0
        fraud_rate = float(split_df["isFraud"].mean()) if has_fraud and len(split_df) > 0 else 0.0
        amt_col = "TransactionAmt" if "TransactionAmt" in split_df.columns else None
        total_amt = float(split_df[amt_col].sum()) if amt_col else 0.0
        fraud_amt = float(split_df.loc[split_df["isFraud"] == 1, amt_col].sum()) if (has_fraud and amt_col) else 0.0

        return {
            "split": split_name,
            "rows": len(split_df),
            "dt_min": int(split_df["TransactionDT"].min()) if len(split_df) > 0 else 0,
            "dt_max": int(split_df["TransactionDT"].max()) if len(split_df) > 0 else 0,
            "fraud_count": fraud_count,
            "fraud_rate": round(fraud_rate, 4),
            "total_transaction_amount": round(total_amt, 2),
            "total_fraud_amount": round(fraud_amt, 2),
        }

    train_stats = compute_stats("train", train_df)
    val_stats = compute_stats("val", val_df)
    test_stats = compute_stats("test", test_df)

    metadata: Dict[str, Any] = {
        "dataset_name": "IEEE-CIS Fraud Detection (Chronological Partition)",
        "provenance": "Vesta Corporation & IEEE-CIS",
        "fraud_class": "payment-transaction fraud risk (isFraud)",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_records": n_total,
        "split_protocol": {
            "axis": "TransactionDT",
            "train_ratio": train_ratio,
            "val_ratio": val_ratio,
            "test_ratio": test_ratio,
            "global_dt_min": dt_min,
            "global_dt_max": dt_max,
        },
        "splits": {
            "train": train_stats,
            "val": val_stats,
            "test": test_stats,
        },
        "columns": {
            "all": list(df_sorted.columns),
            "feature_count": len([c for c in df_sorted.columns if c not in ("TransactionID", "isFraud")]),
            "target": "isFraud",
        }
    }

    logger.info("Chronological Split Summary:")
    logger.info("  Train: %d rows (DT %d -> %d) | Frauds: %d (%.2f%%)", train_stats["rows"], train_stats["dt_min"], train_stats["dt_max"], train_stats["fraud_count"], train_stats["fraud_rate"] * 100)
    logger.info("  Val:   %d rows (DT %d -> %d) | Frauds: %d (%.2f%%)", val_stats["rows"], val_stats["dt_min"], val_stats["dt_max"], val_stats["fraud_count"], val_stats["fraud_rate"] * 100)
    logger.info("  Test:  %d rows (DT %d -> %d) | Frauds: %d (%.2f%%)", test_stats["rows"], test_stats["dt_min"], test_stats["dt_max"], test_stats["fraud_count"], test_stats["fraud_rate"] * 100)

    return train_df, val_df, test_df, metadata


def save_processed_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    metadata: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Path]:
    """
    Save train, val, test_features, and test_labels parquets and data_card.json.
    Enforces strict test feature/label separation.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_path = output_dir / "train.parquet"
    val_path = output_dir / "val.parquet"
    test_features_path = output_dir / "test_features.parquet"
    test_labels_path = output_dir / "test_labels.parquet"
    data_card_path = output_dir / "data_card.json"

    # Save train & val with labels
    logger.info("Writing training partition to: %s", train_path)
    train_df.to_parquet(train_path, index=False)

    logger.info("Writing validation partition to: %s", val_path)
    val_df.to_parquet(val_path, index=False)

    # Test features: explicitly exclude ground truth label 'isFraud'
    feature_cols = [col for col in test_df.columns if col != "isFraud"]
    test_features = test_df[feature_cols].copy()
    logger.info("Writing test features (isolated, %d columns) to: %s", len(feature_cols), test_features_path)
    test_features.to_parquet(test_features_path, index=False)

    # Test labels: isolated target store
    label_cols = ["TransactionID", "isFraud"]
    if "TransactionAmt" in test_df.columns:
        label_cols.append("TransactionAmt")
    if "TransactionDT" in test_df.columns:
        label_cols.append("TransactionDT")

    test_labels = test_df[[c for c in label_cols if c in test_df.columns]].copy()
    logger.info("Writing test ground-truth labels to: %s", test_labels_path)
    test_labels.to_parquet(test_labels_path, index=False)

    # Save data card metadata JSON
    logger.info("Writing dataset metadata card to: %s", data_card_path)
    with open(data_card_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return {
        "train": train_path,
        "val": val_path,
        "test_features": test_features_path,
        "test_labels": test_labels_path,
        "data_card": data_card_path,
    }


def main():
    parser = argparse.ArgumentParser(description="Sentinel IEEE-CIS Dataset Preparation & Chronological Split")
    parser.add_argument("--raw-dir", type=str, default="data/raw", help="Path to directory containing raw CSVs")
    parser.add_argument("--processed-dir", type=str, default="data/processed", help="Path to save processed parquet splits")
    parser.add_argument("--train-ratio", type=float, default=0.70, help="Ratio for training set")
    parser.add_argument("--val-ratio", type=float, default=0.15, help="Ratio for validation set")
    parser.add_argument("--test-ratio", type=float, default=0.15, help="Ratio for test set")
    parser.add_argument("--create-synthetic-sample", action="store_true", help="Force synthetic sample generation")
    parser.add_argument("--n-samples", type=int, default=6000, help="Number of synthetic sample records if creating synthetic data")

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / args.raw_dir if not Path(args.raw_dir).is_absolute() else Path(args.raw_dir)
    processed_dir = project_root / args.processed_dir if not Path(args.processed_dir).is_absolute() else Path(args.processed_dir)

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    if args.create_synthetic_sample:
        logger.info("Creating fresh synthetic IEEE-CIS sample in %s...", raw_dir)
        txn_df, id_df = generate_synthetic_ieee_cis(n_samples=args.n_samples)
        txn_df.to_csv(raw_dir / "transaction.csv", index=False)
        id_df.to_csv(raw_dir / "identity.csv", index=False)
        logger.info("Synthetic raw files saved.")

    merged_df = load_and_join_data(raw_dir, allow_synthetic_fallback=True)
    train_df, val_df, test_df, metadata = perform_chronological_split(
        merged_df,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
    )
    saved_files = save_processed_splits(train_df, val_df, test_df, metadata, processed_dir)

    logger.info("Dataset preparation complete! Artifacts created:")
    for key, path in saved_files.items():
        logger.info("  %s: %s", key, path)


if __name__ == "__main__":
    main()
