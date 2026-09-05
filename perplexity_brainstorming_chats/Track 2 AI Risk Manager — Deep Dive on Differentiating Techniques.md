## Overview

This report catalogs everything worth considering for **Track 2 — AI Risk Manager** in the Razorpay AI Buildathon, so that Benford's Law becomes one supporting signal among several, not the centerpiece. The goal is to identify additional, research-backed techniques and real-world workflow patterns that can differentiate a submission while remaining feasible in the remaining build window.

## Core principle: layered defense, not one model

Modern fraud systems in industry and literature consistently combine multiple complementary layers rather than relying on a single statistical test or classifier — rules/velocity checks, statistical/distribution checks, supervised ML, graph/network analysis, and behavioral biometrics, fused into one decision [^1][^2][^3]. This "defense-in-depth" framing itself is a strong narrative device: it shows you understand that no single technique (including Benford) is sufficient alone, and your system's value comes from combining weak signals into a defensible case.

## Graph and network analysis (strong differentiator)

Fraud rings rarely show up in row-level statistics — they show up in *relationships*. Graph-based fraud detection models transactions as a network of accounts, devices, merchants, and payment instruments, then looks for structural signals: shared identifiers, dense clusters, unusual centrality, and community structure [^4][^5][^6].

- **Graph Neural Networks (GNNs)** — GCN, GAT, GraphSAGE, R-GCN, and Heterogeneous Graph Transformers — learn node embeddings by aggregating neighbor information, letting the model capture both individual transaction features and network topology simultaneously [^4][^7][^8][^6]. AWS's own fraud-detection reference architecture uses R-GCNs on a heterogeneous graph built from tabular transaction data, benchmarked against XGBoost as a baseline [^6].
- **Simpler, still-credible alternative for 5 days**: you don't need a trained GNN. Deterministic graph analytics — connected components, degree/betweenness centrality, community detection — applied with NetworkX can surface the same "syndicate" and "cluster risk" signals used in production heuristics, such as a weighted score combining in-degree, out-degree, and betweenness, further adjusted by an XGBoost score [^8].
- **RL-augmented GNNs** (e.g., FraudGNN-RL, RL-GNN) dynamically tune detection thresholds and feature weights using reinforcement learning, reporting reduced false positives (31–33%) versus static GNN baselines [^9][^10]. This is too heavy for 5 days, but citing it in your README as "future work" signals research awareness.
- Graph methods are reported to significantly outperform traditional row-level fraud detection in capturing complex relational patterns, per a systematic review of 100+ studies [^4].

**Practical takeaway**: Build a lightweight, explainable graph layer (shared device/account/instrument links → connected components → cluster risk score) as a second detection pillar alongside your supervised classifier. This is very achievable without deep learning infrastructure.

## Explainability (XAI) — a must-have, not an extra

Razorpay's own bar explicitly calls for "honest metrics" and audit-friendly systems, and Explainable AI is now treated as a regulatory necessity in fraud detection, not a nice-to-have.

- **SHAP (SHapley Additive exPlanations)** is the dominant technique: it decomposes each prediction into additive per-feature contributions with theoretical consistency guarantees, and is widely used with tree-based models (XGBoost, Random Forest, CatBoost) [^11][^12][^13]. One study combining SHAP with t-SNE + k-means clustering on SHAP values *discovered distinct fraud typologies* (e.g., high-amount fraud vs. identity-theft patterns) that traditional rule-based methods missed — a genuinely differentiated angle if you have time [^11].
- **Regulatory framing**: black-box fraud models face real obstacles under regulations like OCC Bulletin 2011-12 and Federal Reserve SR 11-7, which require transparent, auditable explanations; papers now benchmark explanation "faithfulness" (sufficiency/comprehensiveness) and "stability" (consistency across bootstrap samples) — XGBoost + TreeExplainer scored a near-perfect 0.99 stability score, versus 0.50 for LSTM-based explainers [^14]. Citing this shows you understand *why* model choice affects explainability quality, not just accuracy.
- **Latency tradeoff you can showcase**: SHAP's KernelExplainer takes roughly 30ms per prediction and needs a maintained background dataset; a deterministic rule/symbolic layer can generate an explanation in under 1ms as a byproduct of the forward pass, with identical fraud recall [^15]. This is an excellent point to make in your architecture doc: "we use fast deterministic reason codes for real-time gating, and reserve SHAP for deeper analyst-facing investigation, because production risk systems cannot always afford 30ms explainer latency."
- Anchor Explainable AI generates human-readable **if-then rules** on top of SHAP-based instance weighting, directly aligned with what an analyst needs to action a case rather than stare at feature-importance bars [^12].

**Practical takeaway**: Use SHAP (TreeExplainer) on your gradient-boosted model for case-level explanations, but also build a lightweight deterministic reason-code layer for instant "why was this flagged" text — combining both shows engineering maturity around latency/interpretability tradeoffs.

## Concept drift and adversarial adaptation (advanced differentiator)

This is one of the most research-credible, rarely-implemented-in-hackathons themes: **fraud is non-stationary and adversarial** — fraudsters actively adapt to evade deployed models, so a model trained once will silently decay [^16][^17][^18][^19].

- **Concept drift detectors**: DDM (Drift Detection Method) tracks error rates; ADWIN (Adaptive Windowing) dynamically resizes the training window in response to detected shifts [^16].
- A hybrid framework combining adaptive-learning with drift detection reported fraud recall improving from 35% to 85%, adversarial attack success rate dropping from 35% to 5%, and drift recovery within 24 hours, while keeping latency under 150ms [^16].
- **Adversarial training**: exposing the model to synthetically perturbed fraud samples during training builds robustness to evolving attacker strategies without major performance loss on historical data, avoiding drops that can exceed 50% under naive non-adversarial training when attackers adapt [^18].
- A large cross-sectional study (242 valid responses from fraud analysts/data scientists/compliance officers) found drift detection & dynamic adaptation, and adaptive ML maturity, were the *strongest predictors* of detection resilience (R² = 0.526, p < .001) — reinforcing that this is an operationally central concern, not academic trivia [^19].
- **Label delay**: audit-confirmed fraud labels often arrive long after the transaction, compounding drift; a recent framework (DDAF) explicitly models this dual challenge with Hawkes-process-based temporal risk propagation and was deployed at a real bank, surfacing 1,449 previously unknown fraud accounts [^20].

**Practical takeaway for 5 days**: You cannot build full adversarial training, but you *can* add a "drift monitor" panel: track your model's alert rate, feature distributions, and precision over rolling time windows in your held-out test set, and show a simple ADWIN-style or rolling-Kolmogorov-Smirnov-test chart flagging when distributions shift. This single panel signals deep understanding of a problem most hackathon teams never mention.

## Synthetic identity fraud and account-linkage detection

Since your PaySim-based track leans toward account-takeover/cash-out, synthetic identity and linkage techniques are directly relevant to the "abuse-ring" and "return/refund abuse" example directions Razorpay lists.

- Best-practice detection layers multiple signal types: identity-attribute consistency, document/biometric verification, device/network/behavioral signals, and identity graphs/link analysis — no single indicator is treated as conclusive, and a combination of weak signals is what triggers investigation [^1][^21].
- **Key linkage red flags** consistently cited across sources: shared devices/IPs/phone numbers across "unrelated" accounts, thin history followed by a sudden burst of high-value activity, mismatched geography/demographic consistency, and identical digital footprints across multiple accounts [^22][^2][^23][^24].
- **Behavioral biometrics** — keystroke dynamics, mouse/touch cadence, navigation patterns — are an emerging layer that differentiates bots/fraud rings from genuine users, though this is likely out of scope for a 5-day build without instrumentation access [^22][^2].
- **Entity resolution**: merging fragmented identity data across accounts to reveal hidden synthetic links is described as foundational to synthetic-fraud defense-in-depth strategies [^3].

**Practical takeaway**: If your dataset allows pseudo-identifiers (device/account/IP-like fields), build an entity-resolution + link-analysis layer that flags clusters of "unrelated" accounts sharing identifiers — this maps directly to the "Abuse-ring sentinel" example direction Razorpay explicitly names.

## Cost-sensitive and imbalance-aware modeling (must-do, not optional)

This is less flashy but essential to make your metrics credible, since fraud datasets are severely imbalanced and naive accuracy is misleading.

- Multiple papers stress that **class imbalance handling** (SHAP-based instance weighting, class weighting, or controlled undersampling) combined with interpretability is what actually improves real fraud-detection deployments, not just raw model capacity — one paper achieved "perfect recall for fraudulent instances" using SHAP-weighted XGBoost plus Anchor rules on financial statement fraud [^12].
- Reported production-grade benchmarks worth citing for calibration: GNN-GraphSAGE on IEEE-CIS (590,540 transactions) achieved AUC-ROC 0.9248/F1 0.60 [^14]; a GAT+RL framework on IEEE-CIS achieved AUROC 0.872, F1 0.839, with 33% fewer false positives than a GNN baseline [^10]. These give you realistic target ranges to compare your own held-out metrics against, rather than reporting an inflated number with no context.

## Chargeback evidence automation (specific to Razorpay's own example)

Razorpay explicitly lists "Chargeback evidence responder" as an example direction. While explicit chargeback-automation research is thinner in academic literature, the same principles apply as with any decision + evidence pipeline: gather transaction records, device/IP logs, delivery confirmation, communication history, and prior dispute outcomes, then generate a structured evidence packet with a confidence-scored recommendation — mirroring the SHAP/rule-based explainability approaches above applied to a specific dispute-resolution workflow rather than a binary fraud flag.

## Prioritized shortlist: what to actually add to Sentinel

| Addition | Effort | Payoff | Research grounding |
|---|---|---|---|
| Deterministic graph link-analysis (shared device/account clusters via NetworkX connected components) | Low-Medium | High — visual "wow" + maps directly to abuse-ring example | [^8][^6] |
| SHAP explanations on your gradient-boosted model | Low | High — regulatory-grade explainability | [^11][^14][^13] |
| Fast deterministic reason codes alongside SHAP | Low | Medium-High — shows latency/interpretability tradeoff awareness | [^15] |
| Rolling drift-monitor panel (distribution/precision over time windows) | Low-Medium | High — very few teams will think of this | [^16][^19] |
| Cost-sensitive threshold + class-imbalance handling | Low | High — makes metrics credible | [^12] |
| Benford as one "portfolio integrity" tab, gated by applicability check | Low | Medium — visual polish, correctly scoped | (prior turn) |
| GNN training from scratch | High | Low ROI in 5 days | [^4][^7] |
| Full adversarial training pipeline | High | Low ROI in 5 days | [^18] |

## Bottom line

The strongest positioning is: *"Sentinel fuses five complementary signal layers — rules, statistical/distribution checks (including a properly-gated Benford module), a supervised cost-sensitive classifier with SHAP explainability, a lightweight graph link-analysis layer for abuse rings, and a drift-monitoring panel — because no single technique is sufficient against adaptive, non-stationary fraud."* This directly mirrors how production and academic fraud systems are actually built [^1][^16][^3], turns Benford into one honest instrument among several, and gives you multiple genuinely differentiated, feasible things to demo instead of one gimmick.

---

## References

1. [Synthetic Identity Fraud Detection: Signals and Methods](https://bureau.id/resources/blog/synthetic-identity-fraud-detection) - See how synthetic identity fraud detection uses identity, device, graph, and behavior signals to cat...

2. [Synthetic Identity Fraud: Actionable Strategies for Detection ...](https://www.linkedin.com/pulse/synthetic-identity-fraud-actionable-strategies-detection-rahul-kumar-kvu1e) - The Challenge Synthetic identity refers to a fictitious identity created by combining real and imagi...

3. [How to Detect and Prevent Synthetic Identity Fraud in 2025](https://www.businessscreen.com/resources/synthetic-fraud-red-flags) - Discover what synthetic identity fraud is, how it works, and how to detect it. Learn to prevent synt...

4. [Graph Neural Networks for Financial Fraud Detection: A Review](https://arxiv.org/abs/2411.05815) - The landscape of financial transactions has grown increasingly complex due to the expansion of globa...

5. [Financial fraud detection using graph neural networks: A systematic ...](https://www.sciencedirect.com/science/article/abs/pii/S0957417423026581)

6. [Data Preprocessing And...](https://aws.amazon.com/blogs/machine-learning/detect-financial-transaction-fraud-using-a-graph-neural-network-with-amazon-sagemaker/) - Fraud plagues many online businesses and costs them billions of dollars each year. Financial fraud, ...

7. [detectGNN: Harnessing Graph Neural Networks for Enhanced ...](https://arxiv.org/pdf/2503.22681.pdf)

8. [5. What The Data Showed](https://natashagluons.medium.com/building-a-fraud-detection-model-using-graph-neural-networks-gnns-d3c62b7c38e9) - Understanding structured network of fraudulent organizations

9. [FraudGNN-RL: A Graph Neural Network With ...](https://www.computer.org/csdl/journal/oj/2025/01/10892045/24rmDEnklJS) - As financial systems become increasingly complex and interconnected, traditional fraud detection met...

10. [Reinforcement learning with graph neural network (RL-GNN ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC12672665/) - The research work introduces a new framework which optimizes reinforcement learning with graph neura...

11. [Explaining Fraud Detection With Ai: A Shap And Clustering ...](https://www.ijcrt.org/papers/IJCRT2504222.pdf)

12. [SHAP-Instance Weighted and Anchor Explainable AI](https://ijournalse.org/index.php/ESJ/article/view/2653) - This research aims to enhance financial fraud detection by integrating SHAP-Instance Weighting and A...

13. [[PDF] Explainable AI (XAI) Analysis Using SHAP for Credit Card Fraud](https://scriptaintelektual.com/scripta-technica/article/download/602/474)

14. [Shapley Value-Guided Adaptive Ensemble Learning for ...](https://arxiv.org/abs/2604.14231) - Financial crime costs U.S. institutions over $32 billion each year. Although AI tools for fraud dete...

15. [Explainable AI in Production: A Neuro-Symbolic Model for Real-Time Fraud Detection](https://towardsdatascience.com/explainable-ai-in-production-a-neuro-symbolic-model-for-real-time-fraud-detection/) - SHAP needs 30 ms to explain a fraud prediction. That explanation is stochastic, runs after the decis...

16. [Robust AI for Financial Fraud Detection in the GCC: A Hybrid ... - MDPI](https://www.mdpi.com/0718-1876/20/2/121) - Experiments illustrate significant gains in fraud recall (from 35% to 85%), adversarial robustness (...

17. [Adversarial Learning in Real-World Fraud Detection - arXiv](https://arxiv.org/html/2307.01390) - Credit card fraud detection and concept-drift adaptation ... Adversarial concept drift detection und...

18. [A Fraud Detection System Robust to Adversarial ...](https://fenix.tecnico.ulisboa.pt/downloadFile/1126295043840783/98773-Tiago-Melo-dissertacao.pdf)

19. [Adaptive Fraud Detection Under Concept Drift: Risks and ...](https://ajdsa-journal.org/index.php/ajdsa/article/view/77) - This study has examined how concept drift affects the performance and reliability of artificial inte...

20. [[Literature Review] Data-Centric Dual-Layer Adversarial ...](https://www.themoonlight.io/en/review/sourced/data-centric-dual-layer-adversarial-learning-for-fraud-detection-under-label-delay-and-concept-drift) - The paper **"Data-Centric Dual-Layer Adversarial Learning for Fraud Detection under Label Delay and ...

21. [Toolkit Module 4: Detecting a Synthetic Identity - FedPayments Improvement](https://fedpaymentsimprovement.org/synthetic-identity-fraud-mitigation-toolkit/detecting-a-synthetic-identity/)

22. [Synthetic Identity Fraud: A Practical Guide - businessscreen.com](https://www.businessscreen.com/resources/synthetic-identity-fraud-a-practical-guide) - Learn how to detect and prevent synthetic identity fraud. Discover how BusinessScreen.com delivers i...

23. [Synthetic identity fraud detection: How to identify fake identities](https://www.gbg.com/en-us/blog/synthetic-identity-fraud-detection/) - Discover how to detect synthetic identities in 2026, examples of synthetic identity fraud in banking...

24. [Synthetic identity fraud: How to detect and prevent it - Plaid](https://plaid.com/resources/fraud/synthetic-identity-fraud/) - Fraud detection tools, like device fingerprinting, help identify patterns across these manufactured ...

