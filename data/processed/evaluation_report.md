# Sentinel Fraud Triage — Held-Out Test Evaluation Report

> **Generated at**: 2026-09-01 09:55:13 UTC  
> **Protocol**: Strict chronological split on `TransactionDT` (Zero test-leakage).

## 1. Executive Performance Summary

| Metric | Value | Operational Meaning |
|---|---|---|
| **PR-AUC** | `0.8818` | Area under Precision-Recall curve across all thresholds |
| **Precision** | `0.5370` | Fraction of flagged transactions that were genuine fraud |
| **Recall** | `0.9355` | Fraction of total fraudulent transactions detected |
| **F1 Score** | `0.6824` | Harmonic mean of precision and recall |
| **Recall @ Budget (100/day)** | `1.0000` | Fraud captured under human review capacity constraints |
| **Preventable Exposure Captured** | `94.59%` | Percentage of total fraud financial exposure prevented |
| **False-Positive Cost** | `₹3,750.00` | Friction cost from legitimate transactions flagged |
| **Net Prevented Exposure** | `₹41,557.16` | Financial fraud prevented minus FP friction & review costs |

## 2. Confusion Matrix & Financial Breakdown

```
                    Actual Legitimate (0)    Actual Fraud (1)
Predicted Allow:    TN = 844              FN = 2
Predicted Flag :    FP = 25               TP = 29
```

- **Total Scored Transactions**: `900`
- **Total Fraud Cases**: `31` (Prevalence: `3.44%`)
- **Total Fraud Exposure**: `₹49,327.68`
- **Prevented Fraud Exposure**: `₹46,657.16`
- **Missed Fraud Exposure**: `₹2,670.52`

## 3. Model Benchmark Comparison

| Model / Architecture | Precision | Recall | PR-AUC | Recall@Budget | Preventable Exposure | FP Cost (₹) | Net Prevented (₹) |
|---|---|---|---|---|---|---|---|
| **Deterministic Rule Baseline** | 0.8929 | 0.8065 | 0.8041 | 1.0000 | 92.9% | ₹450 | ₹44,672 |
| **Trained Model (LightGBM/Calibrated)** | 0.5370 | 0.9355 | 0.8818 | 1.0000 | 94.6% | ₹3,750 | ₹41,557 |

## 4. Cost Policy Parameters (Demo Assumptions)

- Decision Threshold: `0.08`
- Customer Friction Cost ($C_{FP}$): `₹150.00` per false alert
- Analyst Review Cost ($C_{Review}$): `₹25.00` per case
- Operations Review Capacity: `100` alerts/day
