# Sentinel Data Card: IEEE-CIS Fraud Detection Dataset

## 1. Dataset Provenance & Overview
- **Source**: IEEE Computational Intelligence Society (IEEE-CIS) Fraud Detection Dataset, provided in partnership with **Vesta Corporation** (leading payment fraud prevention company).
- **Domain**: Real-world e-commerce payment transactions.
- **Tables**:
  - `transaction.csv` / `train_transaction.csv`: Transaction-level features including transaction amounts, product codes, card metadata (`card1`-`card6`), address hashes (`addr1`, `addr2`), distances (`dist1`, `dist2`), email domain fields (`P_emaildomain`, `R_emaildomain`), counting/velocity features (`C1`-`C14`), timedelta features (`D1`-`D15`), match indicators (`M1`-`M9`), and Vesta engineered features (`V1`-`V339`).
  - `identity.csv` / `train_identity.csv`: Identity and device attributes associated with transactions, including device operating system, browser, screen resolution (`id_01`-`id_38`, `DeviceType`, `DeviceInfo`). Joined on `TransactionID` via a left-join (handling missing identity records explicitly, as many legitimate transactions do not capture identity metadata).

---

## 2. Target Class & Label Semantics
- **Target Label**: `isFraud` (Binary: `0` = Legitimate, `1` = Fraudulent).
- **Exact Fraud Class**: **Payment-transaction fraud risk** (as labelled by IEEE-CIS / Vesta).
- **Honest Definition**: This is specifically payment-transaction fraud risk at the authorization/settlement boundary. It is not "account takeover", "return abuse", or "synthetic identity" (unless captured as part of transaction-level chargebacks).
- **Class Imbalance**: Approximately 3.5% positive fraud rate (~96.5% legitimate transactions).

---

## 3. Strict Chronological Split Protocol

### Split Axis: `TransactionDT`
- `TransactionDT` represents a timedelta in seconds from a reference point in time.
- **Zero Temporal Leakage**: Random $k$-fold cross-validation or random train/test splitting falsely inflates validation metrics (by up to ~15% recall) because it leaks future temporal fraud patterns and entity activity into the training window.
- Sentinel enforces a strict **time-ordered partition**:
  1. **Training Split (`train.parquet`)**: First 70% of chronological time (`TransactionDT <= split_1`).
  2. **Validation Split (`val.parquet`)**: Middle 15% of chronological time (`split_1 < TransactionDT <= split_2`). Used exclusively for hyperparameter tuning, probability calibration (Isotonic/Platt), and cost-threshold optimization.
  3. **Held-out Test Split (`test_features.parquet` & `test_labels.parquet`)**: Latest 15% of chronological time (`TransactionDT > split_2`). Strictly frozen and evaluated once.

```
Time Axis (TransactionDT):
[══════════════════════ Train (70%) ══════════════════════][═══ Val (15%) ═══][═══ Test (15%) ═══]
0                                                    split_1             split_2              max(DT)
                                                     (Calibration)        (Frozen Evaluation)
```

---

## 4. Leakage Prevention & Pre-Transaction Integrity
1. **Separation of Test Features and Labels**:
   - `test_features.parquet`: Contains only pre-transaction input features (no `isFraud` column).
   - `test_labels.parquet`: Contains `TransactionID`, ground truth `isFraud`, and `TransactionAmt` for cost/exposure evaluation. Kept isolated from scoring pipelines.
2. **Pre-Transaction Feature Discipline**:
   - Only attributes known *at the time of authorization* are permitted in the scoring path.
   - Any aggregations (e.g., historical velocity, rolling transaction counts) are calculated using strictly prior events.
3. **Fitted Transformations**:
   - Imputers, scalers, target encoders, and frequency encoders must be fitted **exclusively on the training split**. Validation and test sets use the fitted parameters without re-fitting.

---

## 5. Linked-Entity Graph Provenance
- **Dataset-Native Attributes**: Graph entities and relationships derive **purely from real attributes present in the dataset**:
  - `card_fingerprint`: Derived from card attributes (`card1` to `card6`).
  - `addr_hash`: Derived from billing/shipping regions (`addr1`, `addr2`).
  - `email_domain`: Purchaser and recipient domains (`P_emaildomain`, `R_emaildomain`).
  - `device_fingerprint`: Device type, OS, and browser from identity table (`DeviceInfo`, `id_30`, `id_31`, `id_33`).
- **Zero Fabrication Guarantee**:
  - **No fabricated fields** (no artificial IP addresses, synthetic device IDs, or simulated coordinates).
  - **No label density in graph scoring path**: A real-time detector never has ground-truth fraud labels for current transactions. Graph context relies strictly on structural topological signals (cluster size, degree centrality, shared identifier count, and historical score aggregations).

---

## 6. Financial & Operational Cost Assumptions (Demo Scenario)

| Cost Parameter | Default Value | Operational Definition |
|---|---|---|
| **Fraud Loss ($C_{FN}$)** | `TransactionAmt` | Direct exposure loss incurred if a fraudulent transaction is allowed |
| **False-Positive Friction ($C_{FP}$)** | `₹150.00` | Support cost, checkout abandonment risk, and customer friction proxy |
| **Manual Review Cost ($C_{Review}$)** | `₹25.00` | Risk analyst time proxy for triaging medium-risk cases |
| **Daily Review Budget ($K$)** | `100 alerts/day` | Operational capacity constraint for manual investigation |

---

## 7. Artifact Schema Summary

| File | Purpose | Columns / Contents |
|---|---|---|
| `data/raw/transaction.csv` | Raw transaction records | Raw IEEE-CIS transaction table |
| `data/raw/identity.csv` | Raw identity records | Raw IEEE-CIS identity table |
| `data/processed/train.parquet` | Training data (70%) | Features + `isFraud` + `TransactionDT` |
| `data/processed/val.parquet` | Validation data (15%) | Features + `isFraud` + `TransactionDT` |
| `data/processed/test_features.parquet` | Held-out test features (15%) | Pre-transaction features only (no `isFraud`) |
| `data/processed/test_labels.parquet` | Held-out test ground truth (15%) | `TransactionID`, `isFraud`, `TransactionAmt` |
| `data/processed/data_card.json` | Split metadata & statistics | Split boundaries, row counts, fraud rates |
