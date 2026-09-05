# Sentinel — System Architecture & Technical Design

> **Razorpay AI Buildathon 2026 — Track 02: AI Risk Manager**  
> *Defense-Only Payment Fraud Triage Engine with Calibrated Risk Modeling, Deterministic Explainability, Linked-Entity Graphs, and Tamper-Evident Auditing.*

---

## 1. Architectural Philosophy & Design Principles

Payment gateway infrastructure operates under uncompromising engineering requirements: **sub-100ms end-to-end SLAs**, **extreme class imbalance (~3.5% fraud base rate)**, **asymmetric financial costs of error**, and **strict regulatory compliance (RBI / PCI-DSS / Fair Lending)**.

Sentinel is engineered around four core tenets:
1. **Defense-Only Actioning**: Sentinel never unilaterally terminates user accounts or rejects payments outright. Actions are restricted to passive monitoring (`ALLOW`), human expert triage (`ANALYST_REVIEW`), and friction step-up (`SIMULATED_HOLD` / 3D-Secure step-up verification).
2. **Cost-Aware Triage**: Rather than optimizing for raw accuracy, thresholds minimize total expected financial cost by weighing missed fraud exposure against customer friction cost ($C_{FP} = ₹150$) and analyst triage cost ($C_{\text{Review}} = ₹25$).
3. **Deterministic & Auditable Decisions**: Decisions must be 100% reproducible and verifiable via mathematical feature attributions (TreeSHAP) and cryptographic hash chaining (SHA-256).
4. **Dataset-Native Graph Integrity**: Entity relationships derive strictly from real transactional identifiers (cards, addresses, domains, devices) with zero artificial field fabrication or ground-truth label leakage.

---

## 2. AI Judgment: What We Used, What We Didn't, and Why

Sentinel's architecture prioritizes statistical rigor, latency compliance, and operational reliability over unneeded modeling complexity.

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                             SENTINEL AI JUDGMENT MATRIX                                  │
├──────────────────────────────┬──────────────────────────────┬────────────────────────────┤
│ Dimension                    │ Selected Choice              │ Rejected Alternative       │
├──────────────────────────────┼──────────────────────────────┼────────────────────────────┤
│ Core ML Architecture         │ LightGBM (GBDT)              │ Deep Learning (TabNet/MLP) │
│ Probability Calibration      │ Beta / Parametric Scaling    │ Isotonic Step Regression   │
│ Real-Time Explainability     │ TreeSHAP + Reason Codes      │ LLM Real-Time Generation   │
│ Model Interpretability Trade │ GBDT + Post-Hoc TreeSHAP     │ Glassbox EBMs (InterpretML)│
│ Production SLA Compliance    │ ~11ms Multi-Layer Pipeline   │ Async Heavyweight Services │
└──────────────────────────────┴──────────────────────────────┴────────────────────────────┘
```

### 2.1. Why LightGBM (Tabular Data Suitability vs. Deep Learning)
* **What We Used**: LightGBM (Gradient Boosted Decision Tree ensemble) with histogram-based binning and class-weighted objective optimization.
* **What We Rejected**: Deep Tabular Architectures (TabNet, FT-Transformer, Multi-Layer Perceptrons).
* **Engineering & Statistical Rationale**:
  - **Tabular Data Geometry**: Payment data comprises heterogeneous columns: discrete product codes, unscaled amounts, timedelta features, and sparse device metadata. GBDT models partition feature spaces along axis-aligned hyperplanes, making them invariant to monotonic transformations and scaling issues that destabilize gradient descent in deep neural networks.
  - **Native Missing Value Handling**: In real-world e-commerce data (such as IEEE-CIS / Vesta), guest checkout transactions frequently lack device/identity records. LightGBM natively determines the optimal split direction for missing values during tree construction, avoiding synthetic imputation artifacts that distort data geometry.
  - **Execution Latency & Memory Footprint**: Evaluating an ensemble of decision trees compiled into fast C++ branch lookups takes **<5ms** on modest CPU instances with tiny memory overhead. Deep neural networks require tensor matrix multiplications, heavy GPU memory caches, and custom CUDA runtimes that escalate hosting costs and introduce latency variance incompatible with gateway gateways.

---

### 2.2. Why Beta Calibration over Isotonic Regression (Preserving Tail-End Granularity)
* **What We Used**: Beta Calibration (parametric calibration tailored for bounded $(0, 1)$ probability support).
* **What We Rejected**: Non-Parametric Isotonic Regression.
* **Statistical Rationale**:
  - **The Step-Function Collapse in Extreme Tails**: Payment fraud is a severe rare-event problem (~3.5% positive rate). Risk scoring operates in the extreme tail of the distribution ($P(\text{fraud}) > 0.80$). Non-parametric Isotonic Regression applies the Pool Adjacent Violators (PAV) algorithm to fit a monotonic step function. In sparse tail regions with few validation samples, Isotonic Regression produces flat plateaus, mapping all raw scores above $0.85$ to identical calibrated probabilities (e.g., exactly $0.9200$).
  - **Preserving Expected Loss Differentiation**: In a cost-aware triage engine, the ranking of expected loss ($\text{Expected Loss} = P(\text{fraud}) \times \text{Amount}$) requires continuous, high-resolution tail discrimination. A transaction of ₹50,000 with raw score $0.95$ must be differentiated from a ₹50,000 transaction with score $0.86$. Isotonic ties destroy this ranking granularity.
  - **Smooth Monotonic Calibration**: Beta Calibration assumes that raw scores follow a beta distribution under each class, deriving a smooth, strictly monotonic calibration map:
    $$P(Y=1 \mid s) = \frac{1}{1 + \frac{1}{\exp(c)} \cdot s^{-a} \cdot (1-s)^b}$$
    This guarantees continuous probability estimates across the entire $(0, 1)$ domain while correcting base-rate miscalibration induced by class re-weighting.

---

### 2.3. Why NO LLM for Real-Time Explanations (Deterministic SHAP & Reason Codes)
* **What We Used**: Fast deterministic rule reason codes (`HIGH_VALUE_TRANSACTION`, `VELOCITY_SPIKE`, `MISMATCHED_ADDRESS`) for real-time alerting, combined with native LightGBM TreeSHAP for exact local feature attribution.
* **What We Rejected**: Real-time Large Language Model (LLM) prompts generating natural-language risk summaries during transaction authorization.
* **Operational & Regulatory Rationale**:
  - **Payment Gateway Latency SLA**: Payment authorization enforces a strict **sub-100ms total budget** (with fraud screening allocated 20–50ms). External LLM API calls require 500ms–2500ms for network transit and autoregressive token generation, causing severe checkout abandonment.
  - **Inference Cost at Scale**: At gateway scale (millions of daily transactions), per-call LLM API costs (₹0.20–₹1.50/call) would drastically exceed the financial value of the fraud prevented.
  - **Hallucinations & Regulatory Compliance**: Financial regulators (RBI, PCI-DSS, Fair Lending) mandate that risk decisions be explainable, consistent, and provable. LLMs can hallucinate non-existent transaction patterns or provide differing rationales for identical input vectors.
  - **Mathematical Exactness**: TreeSHAP computes exact Shapley values directly from the tree ensemble ($\sum \phi_i = f(x) - E[f(x)]$) in **<4ms**. Every explanation is 100% deterministic, reproducible, and cryptographically committed into the SHA-256 audit chain.

---

### 2.4. The Accuracy vs. Interpretability Trade-Off (Explainable Boosting Machine Baseline)
* **What We Used**: High-capacity LightGBM tree ensembles with post-hoc local TreeSHAP attribution.
* **What We Evaluated**: Explainable Boosting Machines (EBM / InterpretML Generalized Additive Models with Pairwise Interactions: $g(E[y]) = \beta_0 + \sum f_i(x_i) + \sum f_{ij}(x_i, x_j)$).
* **Trade-Off Analysis**:
  - **Higher-Order Fraud Topologies**: Fraud syndicates coordinate attacks across complex, multi-way interactions (e.g., `rapid velocity` $\times$ `disposable email domain` $\times$ `unusual device type` $\times$ `high amount relative to regional baseline`). Restricting models to additive single-feature curves ($f_i$) and pairwise interactions ($f_{ij}$) degrades detection capability on complex fraud schemes.
  - **Empirical Detection Delta**: LightGBM captured **94.59% of preventable fraud exposure** with a **PR-AUC of 0.8818** on the held-out test split, outperforming shallow additive models.
  - **Uncompromising Dual Benefit**: By deploying LightGBM with TreeSHAP, Sentinel captures deep non-linear interactions while delivering glassbox-equivalent feature attribution waterfalls for investigating analysts.

---

### 2.5. Real-Time Latency Awareness & Profiling (Sub-100ms Gate Budget)
* **Gateway SLA Target**: <100ms total end-to-end authorization budget.
* **Measured Scoring Pipeline Latency**:
  Sentinel's multi-layered synchronous pipeline executes in **~11.0ms** total on standard commodity CPU instances.

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                       SCORING PIPELINE LATENCY PROFILE (~11.0ms)                        │
├───────────────────────────────────────────────────────────────────┬──────────┬──────────┤
│ Pipeline Stage                                                    │ Latency  │ % Share  │
├───────────────────────────────────────────────────────────────────┼──────────┼──────────┤
│ Layer 1: Deterministic Rules Engine (Velocity, Percentile Gates)  │ 0.42 ms  │  3.8%    │
│ Layer 2: Feature Transformation & Calibrated LightGBM Inference   │ 4.18 ms  │ 37.9%    │
│ Layer 2: Fast TreeSHAP Feature Attribution Computation            │ 3.85 ms  │ 34.9%    │
│ Layer 3: Linked-Entity Graph Cluster & Shared-Identifier Lookup   │ 2.10 ms  │ 19.0%    │
│ Layer 4: Cost Policy Routing & SHA-256 Hash Chain Auditing        │ 0.48 ms  │  4.4%    │
├───────────────────────────────────────────────────────────────────┼──────────┼──────────┤
│ Total Synchronous Execution Time                                  │ 11.03 ms │ 100.0%   │
└───────────────────────────────────────────────────────────────────┴──────────┴──────────┘
```

---

## 3. Detailed Multi-Layer System Architecture

```
                                  INCOMING TRANSACTION PAYLOAD
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: DETERMINISTIC RULES ENGINE                                                         │
│ Fast gating: velocity bursts, extreme amount thresholds, high-risk product/email categories │
│ Output: RuleTriggers[], ReasonCodes[]                                                       │
└──────────────────────────────────────┬──────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: CALIBRATED ML CLASSIFIER & TREE-SHAP EXPLAINER                                     │
│ 1. Feature pipeline transforms categorical, temporal, and numerical fields                  │
│ 2. LightGBM computes raw logit score                                                        │
│ 3. Beta Calibrator maps raw score to calibrated P(fraud) in [0, 1]                           │
│ 4. Native TreeSHAP computes local feature contribution waterfall                            │
│ Output: Calibrated Probability P(fraud), ShapContributions[]                                │
└──────────────────────────────────────┬──────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: LINKED-ENTITY GRAPH ANALYZER                                                       │
│ 1. Matches real IEEE-CIS attributes: card_fingerprint, addr_hash, email_domain, device_info │
│ 2. Computes bipartite graph adjacency, connected component cluster ID, and hub centrality   │
│ 3. Zero label leakage: uses purely structural topological signals & prior scored histories  │
│ Output: GraphContext(clusterId, sharedAttributes[], clusterSize, linkedEntityCount)         │
└──────────────────────────────────────┬──────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ LAYER 4: COST-AWARE TRIAGE ENGINE                                                           │
│ 1. Computes Expected Fraud Loss: E[Loss] = P(fraud) × TransactionAmt                        │
│ 2. Evaluates against False-Positive Friction (C_FP = ₹150) and Review Cost (C_Review = ₹25) │
│ 3. Decision Routing:                                                                        │
│    • P(fraud) >= 0.75 or E[Loss] >> C_FP ──► SIMULATED_HOLD (Step-Up 2FA / Friction)        │
│    • 0.07 <= P(fraud) < 0.75             ──► ANALYST_REVIEW (Triage Queue)                  │
│    • P(fraud) < 0.07                     ──► ALLOW (Pass-Through)                           │
│ Output: TriageDecision, CostBreakdown                                                       │
└──────────────────────────────────────┬──────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ LAYER 5: TAMPER-EVIDENT SHA-256 AUDIT LEDGER                                                │
│ Computes recursive cryptographic hash:                                                      │
│ entry_hash = SHA256(prev_hash + txn_id + timestamp + decision + model_version + evidence)   │
│ Appends entry to SQLite ledger (No UPDATE/DELETE endpoints permitted)                       │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Subsystem Deep-Dives

### 4.1. Layer 1: Deterministic Rules Engine
* **Purpose**: Immediate pre-filtering of high-confidence patterns before ML scoring.
* **Checks**:
  - `HIGH_VALUE_TRANSACTION`: Transaction amount exceeding 95th percentile (> ₹10,000).
  - `VELOCITY_SPIKE`: Rapid card usage burst within a short sliding window ($C1 > 3$).
  - `HIGH_RISK_PRODUCT`: Product categories associated with high fraud incidence (`ProductCD in ['C', 'R']`).
  - `SUSPICIOUS_EMAIL_DOMAIN`: Disposable or temporary domain extensions.
* **Output**: Structured `RuleTrigger` records with human-readable explanations and severity ratings.

---

### 4.2. Layer 2: Calibrated Machine Learning & Explainability
* **Transformer Pipeline**:
  - Strictly fitted on training data (`train.parquet`) with zero test leakage.
  - Temporal feature extraction: `hour_of_day`, `day_of_week` derived from `TransactionDT`.
  - Financial scaling: $\log(1 + \text{TransactionAmt})$.
  - Categorical encoding: Vocabulary mapping with explicit `-1` default for unknown test tokens.
  - Numerical median imputation.
* **Model Inference**:
  - LightGBM Booster trained with `class_weight='balanced'` to handle 3.5% fraud prevalence.
* **Probability Calibration**:
  - Maps uncalibrated booster outputs to true posterior probabilities using the validation split.
* **Explainability Engine**:
  - Computes exact local Shapley values ($\phi_i$) using fast C-level tree traversal.
  - Returns top-6 positive and negative risk contributors for analyst inspection.

---

### 4.3. Layer 3: Linked-Entity Graph Analyzer
* **Dataset-Native Graph Topology**:
  Constructs a multi-modal bipartite graph from native IEEE-CIS columns:
  - **Transaction Nodes**: $T_i$
  - **Card Entity Nodes**: $C_j = \text{hash}(\text{card1}, \dots, \text{card6})$
  - **Address Entity Nodes**: $A_k = \text{hash}(\text{addr1}, \text{addr2})$
  - **Email Domain Nodes**: $E_l = \text{domain}(\text{P\_emaildomain})$
  - **Device Nodes**: $D_m = \text{hash}(\text{DeviceType}, \text{DeviceInfo})$
* **Zero-Leakage Guarantee**:
  - **No synthetic identifiers**: No fabricated IPs or fake GPS coordinates.
  - **No ground-truth labels in scoring**: Live graph scoring uses structural metrics (connected component size, hub degree centrality, count of shared identifiers) and historical rolling score averages.

---

### 4.4. Layer 4: Cost Policy & Triage Math
* **Expected Cost Formulation**:
  The total expected cost of a triage policy is given by:
  $$E[\text{Cost}] = \sum_{i \in \text{FN}} \text{Amount}_i + C_{\text{FP}} \cdot N_{\text{FP}} + C_{\text{Review}} \cdot N_{\text{Review}}$$
* **Threshold Optimization**:
  - The decision threshold ($\theta^* = 0.07$) was selected via a fine-grained grid sweep on the **validation partition only** to strictly minimize $E[\text{Cost}]$.
* **Action Tiers**:
  - **ALLOW** ($P < 0.07$): Transaction allowed immediately; zero customer friction.
  - **ANALYST_REVIEW** ($0.07 \le P < 0.75$): Routed to the analyst queue; captures ambiguous signals without customer disruption.
  - **SIMULATED_HOLD** ($P \ge 0.75$): High-confidence risk; triggers 3D-Secure step-up verification.

---

### 4.5. Layer 5: Cryptographic Audit Trail (SHA-256 Hash Chain)
To satisfy regulatory scrutiny and prevent retroactive tampering, every triage event creates an immutable hash-chain entry:

$$\text{Hash}_t = \text{SHA256}(\text{Hash}_{t-1} \,\|\, \text{TxnID}_t \,\|\, \text{Timestamp}_t \,\|\, \text{Decision}_t \,\|\, \text{ModelVersion} \,\|\, \text{EvidenceJSON}_t)$$

* **Guarantees**:
  - Append-only storage: The database schema prohibits `UPDATE` and `DELETE` queries on the audit table.
  - Chain integrity: Altering any historical decision invalidates all subsequent hash signatures in the ledger.

---

### 4.6. Model Health & Dual-Horizon Drift Monitoring
Sentinel explicitly decouples model health monitoring into two distinct operational horizons:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DUAL-HORIZON DRIFT MONITORING MATRIX                            │
├──────────────────────────────┬──────────────────────────────┬──────────────────────────┤
│ Horizon                      │ Indicators Monitored         │ Update Frequency         │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────┤
│ 1. Online / Immediate        │ • Input Feature KS-Test      │ Real-time / Sliding      │
│    (Zero Labels Required)    │ • Calibrated Score Drift     │ Hourly Window            │
│                              │ • Missingness Rate Anomaly   │                          │
│                              │ • Graph Degree Concentration │                          │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────┤
│ 2. Delayed / Retrospective   │ • Confirmed Precision/Recall │ 30–90 Day Settlement     │
│    (Ground-Truth Labels)     │ • Net Prevented Loss (₹)     │ Chargeback Window        │
│                              │ • Analyst Confirmation Rate  │                          │
└──────────────────────────────┴──────────────────────────────┴──────────────────────────┘
```

---

## 5. Defense-Only Posture & Failure Mode Resilience

Sentinel implements strict fail-safe mechanisms:
1. **Model Unavailable / Degraded**: If ML inference times out or fails, the pipeline automatically falls back to Layer 1 deterministic rules and routes edge cases to the analyst review queue.
2. **Missing Identity Record**: Gracefully handles guest transactions lacking identity tables by adjusting feature weights via tree split routing.
3. **Extreme Volume Spikes**: Under review queue saturation ($>100\text{ alerts/day}$), the triage engine dynamically raises the review threshold to prioritize transactions by highest expected loss ($\text{Expected Loss} = P \times \text{Amount}$).
