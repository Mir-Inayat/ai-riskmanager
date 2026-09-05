# Sentinel — Cost-Aware Payment-Transaction Fraud Triage

**Track 2: AI Risk Manager** | Razorpay AI Buildathon 2026 | Deadline: 5 September 2026

---

## Problem Statement

> Risk teams must detect fraudulent payment transactions early without blocking too many legitimate customers. Sentinel ranks transaction alerts by expected loss, explains evidence to an analyst, exposes linked-entity risk from real data attributes, and routes only uncertain cases to human review.

**Exact fraud class**: Payment-transaction fraud risk (as labelled by IEEE-CIS `isFraud`).
Not "account takeover," not "chargeback fraud," not "return abuse." One class, honestly named.

**Core pitch**:

> Sentinel is a cost-aware payment-fraud triage system that detects suspicious e-commerce transactions, ranks them by expected loss, explains evidence to an analyst, exposes linked-entity risk, and routes only uncertain cases to human review.

---

## How This Meets Razorpay's Bar

| Track requirement | Sentinel component | Assessment |
|---|---|---|
| One class of loss | Payment-transaction fraud triage | Strong — precisely named, not overclaimed |
| Working detector | Rules + calibrated LightGBM model | Strong |
| Held-out precision and recall | Strict time-based train/val/test split | Unusually mature for a hackathon |
| False-positive cost | Cost-policy simulator + threshold optimization | Strongest differentiator |
| Defense-only | Simulated hold, enhanced verification, or analyst review | Never blocks or penalizes real users |
| "Risk and ML-minded builders" | Class imbalance, calibration, real graph features, drift monitoring, auditability | Very strong |

---

## User Review Required

> [!IMPORTANT]
> **Dataset**: Switching to **IEEE-CIS Fraud Detection** (real e-commerce data from Vesta). It contains transaction + identity tables with card fingerprint, address, email domain, device info, and product codes — giving us real graph edges without fabricating anything. PaySim becomes fallback only if IEEE-CIS download/processing fails in the first 2–3 hours.

> [!WARNING]
> **No LLM dependency in v1**. Deterministic structured investigation summaries are safer, faster, reproducible, and sufficient. Optional LLM provider only after core is complete.

> [!IMPORTANT]
> **Deployment**: Single Dockerized app on Railway (local Docker as fallback). No split deployment of backend/frontend to separate services.

## Open Questions

> [!IMPORTANT]
> 1. **IEEE-CIS Access**: Can you download the IEEE-CIS dataset from [Kaggle](https://www.kaggle.com/competitions/ieee-fraud-detection/data)? You need a Kaggle account. If blocked, we fall back to PaySim and rename to "Account-Draining Transfer Fraud Triage."
> 2. **LightGBM vs XGBoost**: Which is already in your toolkit? I recommend LightGBM for IEEE-CIS (handles high-dimensional, missing, and categorical-heavy data well). Use XGBoost only if it's your faster route.
> 3. **Railway account**: Do you have one, or should we plan for Docker-only local demo?

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    SENTINEL                               │
│                                                           │
│  ┌────────────┐     ┌──────────────────────────────────┐ │
│  │  Next.js   │     │       FastAPI Backend             │ │
│  │  Frontend  │◄───►│                                   │ │
│  │            │     │  ┌──────────────────────────────┐ │ │
│  │ 4 Views:   │     │  │  Layer 1: Rules Engine       │ │ │
│  │            │     │  │  velocity, amount, type gates │ │ │
│  │ • Command  │     │  ├──────────────────────────────┤ │ │
│  │   Center   │     │  │  Layer 2: ML Classifier      │ │ │
│  │ • Alert    │     │  │  LightGBM + calibration      │ │ │
│  │   Queue    │     │  │  + SHAP + reason codes       │ │ │
│  │ • Case     │     │  ├──────────────────────────────┤ │ │
│  │   Invest.  │     │  │  Layer 3: Linked-Entity      │ │ │
│  │ • Policy   │     │  │  Graph (real attributes)     │ │ │
│  │   & Health │     │  ├──────────────────────────────┤ │ │
│  │            │     │  │  Layer 4: Drift Monitor      │ │ │
│  │            │     │  │  online vs delayed metrics   │ │ │
│  │            │     │  └──────────────────────────────┘ │ │
│  │            │     │                                   │ │
│  │            │     │  ┌────────┐ ┌──────────────────┐  │ │
│  │            │     │  │ SQLite │ │ Tamper-Evident   │  │ │
│  │            │     │  │   DB   │ │ Audit Log        │  │ │
│  │            │     │  └────────┘ │ (SHA-256 chain)  │  │ │
│  │            │     │             └──────────────────┘  │ │
│  └────────────┘     └──────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

---

## What Was Cut (and Why)

| Cut item | Reason |
|---|---|
| Fabricated device_id / ip_hash pseudo-fields | Undermines "honest metrics" — graph would rediscover injected relationships |
| Fraud-label density in graph scoring | Label leakage — a live detector never has current ground-truth labels |
| LLM dependency | Unnecessary risk and latency; deterministic summaries are sufficient |
| Both LightGBM AND XGBoost | Train one final model + one baseline, not two final models |
| Isolation Forest | Supervised detector already covers anomaly ranking better with labels |
| Louvain community detection | Deferred — connected components + degree/shared-identifier counts are enough |
| 7 separate dashboard pages | Collapsed to 4 views — narrower and more polished |
| Polars, async SQLAlchemy, rapidfuzz | Unnecessary complexity for demo |
| Full CSV export infrastructure | Deferred — not needed for the demo |
| `<0.1ms` runtime claims | Cannot claim without benchmarking on target device including preprocessing |
| PaySim as primary dataset | IEEE-CIS provides real entity attributes for graph edges |

---

## Proposed Changes

### Component 1: Project Root & Configuration

#### [NEW] [README.md](file:///c:/Users/inayat/Desktop/AI-risk-manager/README.md)
- Two-line problem statement
- Architecture diagram
- How to run (`docker-compose up` + local instructions)
- Dataset methodology: IEEE-CIS provenance, chronological split protocol
- Evaluation protocol: "The scoring service has no access to the held-out test labels. Model selection, calibration, and threshold selection were completed before final test evaluation."
- Results table: precision, recall, F1, PR-AUC, recall@budget, preventable fraud exposure captured, false-positive cost
- Known limitations, safety boundaries, failure modes

#### [NEW] [ARCHITECTURE.md](file:///c:/Users/inayat/Desktop/AI-risk-manager/ARCHITECTURE.md)
- Four-layer defense rationale
- Data flow, decision routing, audit hash-chain design
- Delayed-label vs online drift monitoring design decision

#### [NEW] [docker-compose.yml](file:///c:/Users/inayat/Desktop/AI-risk-manager/docker-compose.yml)
- Single-service build: backend + frontend served together
- Volume mounts for data and models

#### [NEW] [Dockerfile](file:///c:/Users/inayat/Desktop/AI-risk-manager/Dockerfile)
- Multi-stage: Python backend + Node frontend build

#### [NEW] [.env.example](file:///c:/Users/inayat/Desktop/AI-risk-manager/.env.example)
- Database path, model path, cost parameter defaults

#### [NEW] [.gitignore](file:///c:/Users/inayat/Desktop/AI-risk-manager/.gitignore)
- Standard Python/Node ignores + data files + model artifacts

---

### Component 2: Data Pipeline

#### [NEW] [data/README.md](file:///c:/Users/inayat/Desktop/AI-risk-manager/data/README.md)
- Data card: IEEE-CIS provenance (Vesta real e-commerce data), scope, limitations
- Label meaning: `isFraud` = payment-transaction fraud risk
- Explicit statement: "No fields were fabricated. Graph edges derive from dataset-native attributes."

#### [NEW] [scripts/prepare_dataset.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/scripts/prepare_dataset.py)
- Loads IEEE-CIS `transaction.csv` + `identity.csv`
- Joins on `TransactionID` (handles missing identity records explicitly)
- **Chronological split using TransactionDT**:
  - Early window → training
  - Middle window → validation / calibration / threshold selection
  - Latest window → frozen held-out test (evaluated once)
- Fits all imputers, encoders, normalizers on **training only**
- Saves: `train.parquet`, `val.parquet`, `test_features.parquet`, `test_labels.parquet` (separate)
- Saves: `data_card.json` documenting split boundaries and row counts

#### [NEW] [scripts/evaluate.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/scripts/evaluate.py)
- Standalone evaluation against hidden `test_labels.parquet`
- Metrics:
  - Precision, Recall, F1, PR-AUC
  - Recall@Review Budget (e.g., top 100 alerts/day)
  - Preventable Fraud Exposure Captured = `sum(flagged fraud amounts) / sum(all fraud amounts)`
  - False-Positive Cost = `C_FP × FP_count`
  - Expected Cost = `Missed Fraud Value + C_FP × FP + C_review × N_review`
  - Net Prevented Exposure = `Fraud Value Held/Reviewed Correctly - FP Cost - Review Cost`
- Outputs JSON + markdown summary
- Model comparison table: Rules vs LogReg vs LightGBM

---

### Component 3: Backend — FastAPI

#### [NEW] [backend/requirements.txt](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/requirements.txt)
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pandas>=2.1.0
numpy>=1.24.0
scikit-learn>=1.3.0
lightgbm>=4.1.0
shap>=0.43.0
networkx>=3.2.0
scipy>=1.11.0
sqlalchemy>=2.0.0
python-multipart>=0.0.6
joblib>=1.3.0
hashlib  # stdlib
```

#### [NEW] [backend/app/main.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/main.py)
- FastAPI app, CORS middleware, router registration
- Startup: load model, initialize DB, precompute graph summaries

#### [NEW] [backend/app/config.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/config.py)
- Pydantic Settings
- Cost parameter defaults (clearly labelled as "demo scenario assumptions"):

| Parameter | Default | What it represents |
|---|---|---|
| Fraud loss if missed | Transaction amount | Exposure proxy, not confirmed recovery loss |
| Legitimate-customer friction cost | ₹150 | Support, conversion, and trust proxy |
| Manual-review cost | ₹25 | Analyst-time proxy |
| Review capacity | 100 alerts/day | Operational constraint for Recall@K |

#### [NEW] [backend/app/database.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/database.py)
- SQLAlchemy sync engine + SQLite
- Tables: `alerts`, `audit_log`, `analyst_decisions`, `drift_snapshots`

#### [NEW] [backend/app/models/schemas.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/models/schemas.py)
- Frozen API contract types (see below)

#### [NEW] [backend/app/models/db_models.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/models/db_models.py)
- SQLAlchemy ORM models matching the tables

---

#### Layer 1: Rules Engine

#### [NEW] [backend/app/detection/rules_engine.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/detection/rules_engine.py)
- Deterministic rule-based checks:
  - High-value transaction above percentile threshold
  - Transaction amount vs card/address historical average
  - Velocity: multiple transactions in short time window
  - Mismatched billing/shipping address indicators
  - Known high-risk product codes
- Each rule → `RuleResult(rule_id, triggered, reason_code, severity, explanation)`
- Rules enabled/disabled via config

---

#### Layer 2: ML Classifier + Explainability

#### [NEW] [backend/app/detection/ml_classifier.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/detection/ml_classifier.py)
- Loads pre-trained LightGBM model from `.joblib`
- Feature engineering pipeline (fitted on training data only):
  - Transaction features: amount, product code, card details
  - Identity features: device info, email domain
  - Temporal features: hour, day-of-week from TransactionDT
  - Aggregation features: rolling counts/sums per card (using only prior transactions)
- **Pre-transaction vs post-event separation** enforced
- Returns calibrated probability

#### [NEW] [backend/app/detection/explainer.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/detection/explainer.py)
- **Deterministic reason codes** for real-time:
  - `HIGH_VALUE_TRANSACTION`, `VELOCITY_SPIKE`, `MISMATCHED_ADDRESS`, `HIGH_RISK_PRODUCT`, `UNUSUAL_DEVICE`, `NEW_EMAIL_DOMAIN`
- **SHAP TreeExplainer** for analyst-facing investigation:
  - Per-prediction feature contribution waterfall
  - Reserved for review-queue cases (not real-time gating)
- Dual strategy explicitly documented:
  - Fast reason codes → instant alert text
  - SHAP → deeper case investigation page

---

#### Layer 3: Linked-Entity Graph

#### [NEW] [backend/app/detection/graph_analyzer.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/detection/graph_analyzer.py)
- Builds graph using **NetworkX** from **real IEEE-CIS attributes only**:
  - Nodes: transactions, card fingerprints, address hashes, email domains, device identifiers
  - Edges: shared card, shared address, shared email domain, shared device
  - **No fabricated fields. No fraud-label density in scoring path.**
- Deterministic graph analytics:
  - Connected components (cluster candidates)
  - Degree centrality (hub entities)
  - Shared-identifier counts per transaction
  - Simple cluster-risk heuristic: size × average score of prior-scored transactions (no labels)
- Returns: `GraphContext(cluster_id, shared_attributes[], cluster_size, linked_entity_count)`
- Exports nodes + edges JSON for frontend mini-visualization

---

#### Layer 4: Drift Monitor

#### [NEW] [backend/app/detection/drift_monitor.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/detection/drift_monitor.py)

Split explicitly into two categories:

**Online / immediately observable** (no labels needed):
- Feature-distribution drift (rolling KS-test on key input features)
- Risk-score distribution drift
- Alert-rate drift
- Missingness drift
- Entity-link concentration drift

**Delayed / retrospective** (requires confirmed outcomes):
- Precision, Recall, False-positive rate
- Loss captured
- Analyst-confirmation rate

Dashboard explicitly states:
> "Precision and recall are delayed-label metrics, refreshed after confirmed outcomes; live model health uses input and score-distribution drift."

---

#### Benford Module (P2 — Portfolio Signal Only)

#### [NEW] [backend/app/detection/benford_signal.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/detection/benford_signal.py)
- Population-level first-digit analysis on transaction amounts
- **Applicability gate**:
  - Sample size check (>500)
  - Price-banding detection
  - Bounded-range detection
  - Returns: `HIGH_CONFIDENCE | CAUTION | NOT_APPLICABLE`
- MAD score, chi-square statistic
- UI copy: "Portfolio-level distribution signal. Not transaction-level evidence and never a trigger for an automated action."
- For IEEE-CIS: may correctly return `NOT_APPLICABLE` or `CAUTION` — this is by design, proving the gate works

---

#### Decision & Workflow

#### [NEW] [backend/app/triage/cost_policy.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/triage/cost_policy.py)
- Three-tier triage based on expected cost:

| Risk tier | Decision | Why |
|---|---|---|
| HIGH | Simulated "hold + enhanced verification" | Expected fraud loss exceeds friction cost |
| MEDIUM | Route to analyst review queue | Evidence is meaningful but not decisive |
| LOW | Allow and monitor | Avoids unnecessary friction |

- Threshold optimization: sweep thresholds on **validation set only**, minimize expected cost
- Interactive: frontend can adjust cost parameters and see triage distribution change

#### [NEW] [backend/app/triage/case_builder.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/triage/case_builder.py)
- Assembles complete case from all layers:
  - Transaction details
  - Rule triggers + reason codes
  - ML risk score + SHAP contributions
  - Graph context (cluster membership, shared attributes)
  - Cost-based routing decision
  - Recommended action
- All evidence is **deterministic and structured** — no LLM generation

#### [NEW] [backend/app/triage/audit_logger.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/triage/audit_logger.py)
- **Append-only, tamper-evident audit trail** with SHA-256 hash chain:

```python
entry_hash = SHA256(
    previous_entry_hash +
    decision_run_id +
    transaction_id +
    model_version +
    timestamp +
    final_decision +
    canonical_evidence_json
)
```

- Each entry stores `previous_entry_hash` and `entry_hash`
- **No update/delete endpoints** for audit entries
- Not claimed as "immutable" — honestly described as "append-only, tamper-evident"

---

#### API Routes

#### [NEW] [backend/app/routes/transactions.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/routes/transactions.py)
- `POST /api/transactions/score` — score a single transaction
- `POST /api/transactions/batch` — score a batch (meets 50+ record requirement)

#### [NEW] [backend/app/routes/alerts.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/routes/alerts.py)
- `GET /api/alerts` — paginated alert queue (filter: risk tier, status)
- `GET /api/alerts/{id}` — full case detail with all evidence
- `POST /api/alerts/{id}/decision` — analyst approves/rejects (simulated)

#### [NEW] [backend/app/routes/metrics.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/routes/metrics.py)
- `GET /api/metrics/detection` — precision, recall, F1, PR-AUC, recall@budget
- `GET /api/metrics/cost` — expected cost, net prevented exposure, false-positive cost
- `POST /api/metrics/simulate-cost` — adjust cost params → see new triage distribution
- `GET /api/metrics/threshold-curve` — precision/recall/cost at various thresholds
- `GET /api/metrics/model-comparison` — rules vs logistic regression vs LightGBM

#### [NEW] [backend/app/routes/analytics.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/routes/analytics.py)
- `GET /api/analytics/benford` — Benford analysis with applicability gate
- `GET /api/analytics/graph-summary` — graph clusters for visualization
- `GET /api/analytics/drift` — online drift indicators + delayed retrospective metrics
- `GET /api/analytics/distributions` — amount/type distributions

#### [NEW] [backend/app/services/scoring_pipeline.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/app/services/scoring_pipeline.py)
- Orchestrates all layers in order: rules → ML → graph context → triage → audit
- Single entry point for scoring

---

### Component 4: Model Training Pipeline

#### [NEW] [scripts/train_model.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/scripts/train_model.py)
1. Load prepared train/val splits
2. Feature engineering (fitted on train only)
3. **Rule baseline** → log metrics
4. **Logistic Regression** with class weights → log metrics
5. **LightGBM** with class weighting → log metrics
6. Probability calibration on validation split
7. Threshold selection on validation (minimize expected cost)
8. Save model + feature pipeline as `.joblib`
9. **Do not touch test set** — that happens only via `evaluate.py`

#### [NEW] [scripts/build_graph.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/scripts/build_graph.py)
- Builds NetworkX graph from real IEEE-CIS attributes
- Computes centrality metrics, connected components
- Saves graph analytics JSON

#### [NEW] [scripts/compute_drift_baseline.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/scripts/compute_drift_baseline.py)
- Computes baseline feature distributions from training data
- Saves reference for online drift monitoring

---

### Component 5: Frontend — Next.js (4 Views)

#### [NEW] [frontend/package.json](file:///c:/Users/inayat/Desktop/AI-risk-manager/frontend/package.json)
- Next.js 14+, React 18, TypeScript, Tailwind CSS
- Dependencies: recharts (charts), react-force-graph-2d (graph viz), framer-motion (micro-animations), lucide-react (icons)

---

#### View 1: Command Center (`/`)

#### [NEW] [frontend/src/app/page.tsx](file:///c:/Users/inayat/Desktop/AI-risk-manager/frontend/src/app/page.tsx)
- KPI cards: total scored, fraud detection rate, precision, recall, PR-AUC
- Alert volume indicator + review queue count
- Estimated prevented exposure (₹)
- Model-health indicator (online drift status)
- Mini alert feed (latest HIGH/MEDIUM alerts)

---

#### View 2: Alert Queue (`/alerts`)

#### [NEW] [frontend/src/app/alerts/page.tsx](file:///c:/Users/inayat/Desktop/AI-risk-manager/frontend/src/app/alerts/page.tsx)
- Sortable table: risk tier badge, amount, score, linked-entity count, top reason code, recommendation
- Filter by: risk tier (HIGH/MEDIUM/LOW), status (pending/reviewed/dismissed)
- Quick-action: click row → navigate to case investigation

---

#### View 3: Case Investigation (`/alerts/[id]`) — THE HERO PAGE

#### [NEW] [frontend/src/app/alerts/[id]/page.tsx](file:///c:/Users/inayat/Desktop/AI-risk-manager/frontend/src/app/alerts/[id]/page.tsx)

This is the demo slide. Contains:

- **Transaction detail card**: amount, type, card info, timestamp
- **Risk score gauge** with confidence band
- **Evidence waterfall**: SHAP feature contributions (horizontal bar chart)
- **Rule triggers panel**: which rules fired, severity, explanation
- **Graph mini-view**: linked entities (modal launches full graph view)
  - Shared card/address/email/device relationships
  - Cluster size and shared attribute list
- **Cost-based decision**: "Expected fraud loss: ₹X. Friction cost: ₹Y. → Recommendation: REVIEW"
- **Approval gate**: simulated analyst action (Approve Hold / Dismiss / Escalate)
  - Clear "This is a simulated action" disclaimer
- **Audit trail timeline**: hash-chain entries showing full decision history

---

#### View 4: Policy & Model Health (`/policy`)

#### [NEW] [frontend/src/app/policy/page.tsx](file:///c:/Users/inayat/Desktop/AI-risk-manager/frontend/src/app/policy/page.tsx)

Combined page with tabs or sections:

**Cost Policy Simulator**:
- Sliders for C_FP, C_FN_multiplier, C_review (labelled as "demo scenario assumptions")
- Threshold slider
- Real-time: precision/recall curve, triage distribution pie, review budget curve
- Optimal threshold recommendation

**Model Health**:
- Confusion matrix heatmap
- PR curve + precision/recall at selected threshold
- Model comparison table (Rules vs LogReg vs LightGBM)
- Online drift indicators (feature/score distribution KS p-values)
- Delayed-label metrics section (clearly labelled: "Refreshed after confirmed outcomes")

**Portfolio Integrity** (small card):
- Benford analysis with applicability gate + disclaimer
- "Portfolio-level distribution signal. Not transaction-level evidence."

---

#### Frontend Components

- [NEW] `frontend/src/components/Sidebar.tsx` — navigation (4 items)
- [NEW] `frontend/src/components/KPICard.tsx` — animated stat cards with micro-animations
- [NEW] `frontend/src/components/RiskBadge.tsx` — HIGH (red) / MEDIUM (amber) / LOW (green) badges
- [NEW] `frontend/src/components/EvidenceWaterfall.tsx` — SHAP horizontal bar chart
- [NEW] `frontend/src/components/GraphMiniView.tsx` — small force-directed graph, expandable to modal
- [NEW] `frontend/src/components/AuditTrail.tsx` — timeline with hash chain entries
- [NEW] `frontend/src/components/ApprovalGate.tsx` — simulated action modal with disclaimer
- [NEW] `frontend/src/components/CostSliders.tsx` — interactive cost parameter controls
- [NEW] `frontend/src/components/ThresholdCurve.tsx` — precision/recall/cost at thresholds
- [NEW] `frontend/src/components/ConfusionMatrix.tsx` — heatmap
- [NEW] `frontend/src/components/BenfordCard.tsx` — small card with applicability gate
- [NEW] `frontend/src/components/DriftIndicators.tsx` — online vs delayed indicators

#### Frontend Utilities

- [NEW] `frontend/src/lib/api.ts` — API client for all backend routes
- [NEW] `frontend/src/lib/types.ts` — TypeScript types matching backend schemas

---

### Component 6: Tests

#### [NEW] [backend/tests/conftest.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/tests/conftest.py)
- Shared fixtures: sample transactions, mock model, test DB

#### [NEW] [backend/tests/test_rules_engine.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/tests/test_rules_engine.py)
- Each rule independently with known inputs + composition

#### [NEW] [backend/tests/test_ml_classifier.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/tests/test_ml_classifier.py)
- Feature pipeline shapes, model loads and scores, calibration output range

#### [NEW] [backend/tests/test_cost_policy.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/tests/test_cost_policy.py)
- Three-tier routing correctness, cost calculation

#### [NEW] [backend/tests/test_audit_chain.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/tests/test_audit_chain.py)
- Hash chain integrity, append-only enforcement, no update/delete

#### [NEW] [backend/tests/test_failure_modes.py](file:///c:/Users/inayat/Desktop/AI-risk-manager/backend/tests/test_failure_modes.py)
- Missing columns, invalid values, model unavailable, empty batch, no fraud predicted

---

### Component 7: Documentation

#### [NEW] [docs/failure-modes.md](file:///c:/Users/inayat/Desktop/AI-risk-manager/docs/failure-modes.md)
- Corrupt CSV handling, missing model, empty batch, all-zero predictions

#### [NEW] [docs/demo-script.md](file:///c:/Users/inayat/Desktop/AI-risk-manager/docs/demo-script.md)
- 5-minute pitch script (below)

---

## Frozen API Contract

> [!IMPORTANT]
> This contract must be frozen in the **first 90 minutes** before any parallel work begins.

```typescript
// Alert (queue + list view)
type Alert = {
  transactionId: string
  timestamp: number
  amount: number
  riskScore: number             // calibrated probability
  decision: "ALLOW" | "REVIEW" | "SIMULATED_HOLD"
  reasonCodes: string[]
  expectedCost: number
  linkedEntityCount: number
  modelVersion: string
}

// Case evidence (investigation view)
type CaseEvidence = {
  shapContributions: {
    feature: string
    contribution: number
  }[]
  ruleTriggers: {
    ruleId: string
    severity: string
    explanation: string
  }[]
  graphContext: {
    clusterId?: string
    sharedAttributes: string[]
    clusterSize: number
  }
  costBreakdown: {
    expectedFraudLoss: number
    frictionCostIfFP: number
    reviewCost: number
    netExposure: number
  }
  auditHash: string
}
```

Frontend builds against **static JSON fixtures** of these shapes. Backend implements them. Integration happens after both sides work independently.

---

## Complete File Tree (Revised — ~40 files)

```
AI-risk-manager/
├── README.md
├── ARCHITECTURE.md
├── AGENTS.md                            # (existing)
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .gitignore
│
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py              # Pydantic request/response types
│   │   │   └── db_models.py            # SQLAlchemy ORM
│   │   │
│   │   ├── detection/
│   │   │   ├── __init__.py
│   │   │   ├── rules_engine.py         # Layer 1
│   │   │   ├── ml_classifier.py        # Layer 2
│   │   │   ├── explainer.py            # SHAP + reason codes
│   │   │   ├── graph_analyzer.py       # Layer 3
│   │   │   ├── drift_monitor.py        # Layer 4
│   │   │   └── benford_signal.py       # P2 portfolio signal
│   │   │
│   │   ├── triage/
│   │   │   ├── __init__.py
│   │   │   ├── cost_policy.py
│   │   │   ├── case_builder.py
│   │   │   └── audit_logger.py         # SHA-256 hash chain
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── transactions.py
│   │   │   ├── alerts.py
│   │   │   ├── metrics.py
│   │   │   └── analytics.py
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       └── scoring_pipeline.py     # Orchestrates all layers
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_rules_engine.py
│       ├── test_ml_classifier.py
│       ├── test_cost_policy.py
│       ├── test_audit_chain.py
│       └── test_failure_modes.py
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   │
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx                # View 1: Command Center
│       │   ├── globals.css
│       │   ├── alerts/
│       │   │   ├── page.tsx            # View 2: Alert Queue
│       │   │   └── [id]/
│       │   │       └── page.tsx        # View 3: Case Investigation
│       │   └── policy/
│       │       └── page.tsx            # View 4: Policy & Model Health
│       │
│       ├── components/
│       │   ├── Sidebar.tsx
│       │   ├── KPICard.tsx
│       │   ├── RiskBadge.tsx
│       │   ├── EvidenceWaterfall.tsx
│       │   ├── GraphMiniView.tsx
│       │   ├── AuditTrail.tsx
│       │   ├── ApprovalGate.tsx
│       │   ├── CostSliders.tsx
│       │   ├── ThresholdCurve.tsx
│       │   ├── ConfusionMatrix.tsx
│       │   ├── BenfordCard.tsx
│       │   └── DriftIndicators.tsx
│       │
│       ├── lib/
│       │   ├── api.ts
│       │   └── types.ts
│       │
│       └── fixtures/                   # Static JSON for parallel dev
│           ├── alerts.json
│           ├── case-evidence.json
│           ├── metrics.json
│           └── graph-data.json
│
├── scripts/
│   ├── prepare_dataset.py
│   ├── train_model.py
│   ├── build_graph.py
│   ├── compute_drift_baseline.py
│   └── evaluate.py
│
├── data/
│   ├── README.md                       # Data card
│   ├── raw/                            # IEEE-CIS CSVs (gitignored)
│   ├── processed/                      # Parquet splits (gitignored)
│   └── models/                         # Trained model artifacts
│
├── docs/
│   ├── failure-modes.md
│   └── demo-script.md
│
├── shared/
│   └── types.ts                        # Shared API contract types
│
└── perplexity_brainstorming_chats/     # (existing research)
```

---

## Strict Build Order

> [!CAUTION]
> Do not begin with all four views. The hero case page and metrics will win the submission; everything else supports them.

### Phase 1: Dataset + Leakage Audit (Day 1 morning)
1. Download IEEE-CIS from Kaggle
2. Join transaction + identity tables
3. Chronological split on TransactionDT
4. Verify no post-event features in scoring path
5. Document in data card

### Phase 2: Baseline + Frozen Metric Script (Day 1 afternoon)
1. Rule baseline → log metrics
2. Logistic Regression baseline → log metrics
3. Freeze `evaluate.py` — this script does not change after this point
4. Freeze API contract JSON shapes

### Phase 3: Final Model + Threshold Policy (Day 2)
1. LightGBM with class weights
2. Probability calibration on validation
3. Threshold selection on validation (minimize expected cost)
4. SHAP explainer setup
5. Cost-aware three-tier triage routing
6. **Evaluate once on frozen test set**

### Phase 4: End-to-End Flow (Day 2–3)
1. Scoring pipeline orchestrating all layers
2. Alert → case → evidence → simulated decision → audit hash chain
3. All API routes working
4. Graph analyzer on real attributes

### Phase 5: UI (Day 3–4)
1. Case Investigation page (hero page — build first)
2. Alert Queue
3. Command Center
4. Policy & Model Health

### Phase 6: Polish (Day 4–5)
1. Benford card with applicability gate
2. Drift indicators
3. 10+ backend tests
4. Docker build
5. Failure mode handling
6. README, ARCHITECTURE.md
7. Deploy to Railway

### Phase 7: Submit (Day 5)
1. Record 5-minute video
2. Metric screenshots
3. "What broke" story
4. Final repo cleanup

---

## Parallel Work Lanes

| Lane | Deliverable | Must finish before |
|---|---|---|
| **Core ML** | Dataset card, temporal split, model, calibrated probabilities, frozen evaluation script | Any real dashboard metrics |
| **Risk Workflow** | Cost routing, case/evidence schema, audit hash chain | Case page integration |
| **Frontend** | Command Center, Queue, Case page using **fixture JSON** | API integration |
| **Graph/Health** | Linked-entity aggregation, graph JSON, drift summaries | Final polish |
| **Docs/Demo** | README, architecture, demo script, metric screenshots | Submission day |

---

## 5-Minute Pitch

| Time | Section | Content |
|---|---|---|
| 0:00–0:30 | **Hook** | "A fraud model that scores 95% accuracy but blocks legitimate customers destroys trust. Real risk teams need to know how much is at stake, why it was flagged, and what to do next." |
| 0:30–1:00 | **What Sentinel is** | "A cost-aware payment-fraud triage system: detect, rank by expected loss, explain, expose linked entities, and route uncertain cases to humans." |
| 1:00–2:00 | **Live demo** | Run batch → Command Center KPIs populate → Alert Queue fills |
| 2:00–3:00 | **Hero: Case Investigation** | Click HIGH alert → evidence waterfall, rule triggers, graph context, cost breakdown → approval gate with disclaimer |
| 3:00–3:30 | **Cost simulator** | Adjust C_FP slider → watch threshold and triage change |
| 3:30–4:00 | **Metrics** | Held-out PR-AUC, recall@budget, preventable exposure captured, model comparison table |
| 4:00–4:30 | **What broke** | Chronological split story (see below) |
| 4:30–5:00 | **Close** | "Sentinel is a decision system, not a classifier. It triages, explains, costs, audits — because a fraud model that can't be trusted is worse than no model at all." |

---

## "What Broke" Story

> "Initial random train/test splits leaked temporal patterns, inflating validation recall by ~15%. Moving to strict chronological splitting corrected this. Then the model was over-flagging legitimate high-value transactions — the most damaging false positive for customer trust. We replaced F1-maximized thresholds with cost-minimized thresholds: instead of optimizing a statistical metric, we optimized the financial cost of wrong decisions. This deliberately accepted lower alert coverage to reduce false-positive friction. The system is designed to escalate ambiguity rather than manufacture certainty."

---

## Verification Plan

### Automated Tests
```bash
cd backend && python -m pytest tests/ -v --tb=short
python scripts/evaluate.py --features data/processed/test_features.parquet --labels data/processed/test_labels.parquet
```

### Manual Verification
- Clean-clone test: `git clone → docker-compose up → full workflow`
- Batch score 300+ transactions
- Verify all 4 views render correctly
- Alert queue → case detail → approval flow → audit chain
- Test failure modes: corrupt input, missing model, empty batch
- Verify audit hash chain integrity

### Target Metrics (Realistic for IEEE-CIS)

| Metric | Target Range | Notes |
|---|---|---|
| Precision | 0.80–0.92 | At selected cost-optimal threshold |
| Recall | 0.65–0.80 | Constrained by false-positive tolerance |
| PR-AUC | 0.75–0.85 | IEEE-CIS is harder than PaySim |
| Recall@100 reviews | 0.50–0.65 | Realistic operational constraint |
| Preventable exposure captured | 60–80% | Amount-weighted, not count-weighted |

---

## Execution Timeline

| Day | Date | Focus | Non-Negotiable Deliverable |
|---|---|---|---|
| **Day 1** | Sep 1 | Data + Baselines + Contract | IEEE-CIS downloaded/split, rule + LogReg baselines with metrics, `evaluate.py` frozen, API contract frozen, frontend scaffolded with fixtures |
| **Day 2** | Sep 2 | Final Model + Workflow | LightGBM trained/calibrated, SHAP working, cost-triage routing, audit hash chain, all API routes returning data |
| **Day 3** | Sep 3 | Hero Page + Integration | Case Investigation page complete with real data, Alert Queue working, graph analyzer on real attributes |
| **Day 4** | Sep 4 | Remaining Views + Polish | Command Center + Policy page, Benford card, drift indicators, Docker working, tests passing |
| **Day 5** | Sep 5 | Submit | README complete, failure modes handled, 5-min video recorded, deployed, final repo cleanup |
