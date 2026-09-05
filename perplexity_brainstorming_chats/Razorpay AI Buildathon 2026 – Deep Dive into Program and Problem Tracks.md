# Razorpay AI Buildathon 2026 – Deep Dive into Program and Problem Tracks

## Overview of the Buildathon

The Razorpay AI Buildathon 2026 is a student-only hiring program used to recruit "AI Builder Interns" at Razorpay, structured as a build-first pathway rather than a traditional hackathon with prizes. Applicants pick one AI problem track, build a working project, and submit a public GitHub repo, a 5‑minute pitch video, and an architecture walkthrough; shortlisted builders go straight to a technical panel interview with no aptitude test or group discussion.[^1][^2][^3][^4][^5]

The internship offered through the Buildathon is based in Bangalore, in-person, with a stipend of ₹75,000 per month for 6 or 12 months starting around September 2026. The program is explicitly marketed as "Build. Show. Get hired." and emphasises that "your code speaks louder than your resume," signalling a focus on real engineering ability and AI judgment rather than CGPA or pedigree.[^2][^3][^6][^7][^5][^1]

## Eligibility and Target Audience

The Buildathon is restricted to currently enrolled students, typically in technical programs such as B.Tech, M.Tech, BCA, MCA or equivalent computer science or engineering degrees. Communication from Razorpay and community posts highlight eligible graduation batches like 2027–2029, reinforcing that this is not a lateral hiring channel for experienced professionals but a student pipeline.[^3][^8]

There is no explicit CGPA cutoff or college‑tier filter; instead, selection is based entirely on the quality of the submitted AI build and the candidate’s ability to explain and defend it during the panel interview. This makes the program appealing to strong builders from non‑Tier‑1 backgrounds who may be filtered out of traditional internship hiring by resume screens.[^2][^3]

## Timeline and Deadlines

Applications for Razorpay AI Buildathon 2026 are live as of August 2026, with the official application deadline clearly stated as 5 September 2026 across Razorpay’s materials and multiple third‑party explainers. After the deadline, Razorpay screens projects on a rolling basis through September, shortlisting candidates whose builds show strong signal for direct panel interviews.[^9][^4][^7][^3][^2]

The AI Builder Internship is planned to commence from September 2026 at Razorpay’s Bangalore office, with selected interns joining for either a 6‑month or 12‑month term depending on their choice and Razorpay’s needs. Applicants are advised in community content and videos to submit well before the deadline to avoid last‑minute rush and to allow sufficient time to refine their build and documentation.[^10][^11][^4][^3][^2]

## Application Flow and Submission Requirements

The application process follows a clear four‑step flow described in Razorpay’s official page and amplified by community posts: pick a track, build something real, show your work (repo, video, architecture), and if the project has signal, Razorpay calls you in for a panel. Instead of long forms or online assessments, the core of the application is the working AI project and its accompanying artefacts.[^5][^1]

The application form itself asks for 12 specific items: basic personal and academic details (name, college, graduation year), in‑person availability from September, choice of 6 or 12 months, and a resume file; then project details including chosen track, project name, problem it solves, public GitHub repo URL, a 5‑minute pitch video link (can be unlisted), and a description of what broke and how the applicant recovered. These requirements emphasise both build quality and resilience under failure rather than just polished demos.[^1]

### What Razorpay Reads Instead of Your Resume

Razorpay’s own messaging contrasts a conventional resume (CGPA, buzzword skills, generic soft skills claims) with the "proof" it actually cares about: a repo that runs, a 5‑minute video of the project working, and an honest account of what broke at 2 AM and how the candidate fixed it. This framing is reinforced in third‑party explainers and social posts that stress that your project is effectively your first interview, and that reliable engineering plus thoughtful AI use matter more than credentials.[^4][^10][^1]

## Selection Criteria and Evaluation Philosophy

Razorpay and community decoders highlight four core evaluation axes: problem taste, build quality, AI judgment, and failure recovery. Problem taste refers to whether the candidate chose a problem that actually matters in a real payments or fintech context, rather than a trivial toy example or generic chat interface.[^4][^1]

Build quality focuses on whether the system runs reliably, is reasonably structured, and appears trustworthy enough that someone would rely on it in a production‑adjacent scenario, even if it’s still a prototype. AI judgment covers whether AI and ML tools are used in the right places (e.g., risk scoring, anomaly detection, text understanding, decision support) rather than sprinkled everywhere; it also includes knowing when not to use a heavy model and instead rely on simpler rules or heuristics.[^10][^2][^4]

Failure recovery assesses how the system behaves when things go wrong: handling degraded APIs, payment failures, model errors, data issues, or user edge cases gracefully rather than crashing. Razorpay explicitly asks candidates to describe "what broke and how you got out," signalling that it values robustness and debugging ability.[^1][^4]

## Distinction from Typical Hackathons

Although branded as a "Buildathon," Razorpay’s program differs from conventional hackathons in several important ways: the outcome is an AI Builder Internship rather than cash prizes or swag; judging is based on architecture, code quality, and real build behaviour instead of only demo‑day performance; and there is no resume screening or aptitude test involved.[^3][^2]

The Buildathon is positioned explicitly as a hiring funnel, not a one‑off event, and it leads into a 6‑ or 12‑month paid role for shortlisted candidates. Applicants are expected to ship functional code, measure their system’s impact (e.g., recovered revenue, precision/recall for risk models), and explain their design choices in depth, which pushes the format closer to a practical technical interview spread over weeks rather than a weekend hack.[^8][^2][^3]

## Summary of the Five Tracks

Razorpay’s official page defines five tracks, each aligned with real problems in payments, risk and finance operations, plus an open track for other ideas. Community breakdowns mirror this structure and provide additional interpretation of what each track implies.[^5][^1]

| Track | Core Theme | Primary Objective |
|-------|-----------|-------------------|
| AI Growth & Agentic Commerce | AI agents for commerce and growth | Grow merchant revenue and enable agent-to-agent commerce workflows[^1][^2] |
| AI Risk Manager | Fraud and loss prevention | Detect and mitigate fraud, abuse, returns and chargebacks with measurable performance[^1][^2] |
| AI Revenue Recovery | Revenue leakage and recovery | Identify at-risk or lost revenue (failed payments, abandonment, overdue receivables) and execute recovery workflows[^1][^2] |
| AI Finance Controller | Finance operations and control | Automate reconciliation, settlement, forecasting and cash‑position loops over batch data[^1][^3] |
| Open Track | Any meaningful AI build | Solve a real problem with a robust AI‑native product outside the above domains[^1][^2] |

Each track comes with an explicit "bar" stating expectations: explainable and bounded money actions with audit trails for growth/commerce; honest metrics and strictly defensive posture for risk; measured money recovered and compliant escalation for revenue recovery; throughput plus accuracy and exception handling for finance controller; and real value creation with reliable execution for open track.[^5][^1]

## Track 01 – AI Growth & Agentic Commerce

The AI Growth & Agentic Commerce track focuses on using AI agents to grow merchant revenue and make merchants "sellable" to AI buyers. Builders are asked to use Razorpay’s test‑mode APIs to create agents that either drive revenue growth for a merchant or enable an AI buyer to complete transactions end‑to‑end.[^3][^1][^5]

Razorpay contextualises this track with references to NPCI’s UAP and global protocol races like ACP, AP2 and x402, framing agent‑to‑agent commerce as a key open problem for 2026. Example directions include conversational in‑app checkout, agent‑readable catalogs, upsell and cross‑sell agents, and campaign orchestrators. The bar for this track is that every money‑related action must be explainable, bounded and gated, with a visible audit trail and at least one failure case handled gracefully.[^1]

### Deep Problem Themes in Agentic Commerce

At a deeper level, the problem theme revolves around autonomous or semi‑autonomous agents interacting over payments APIs to execute commerce flows that traditionally require manual intervention. Key challenges include stateful orchestration of multiple steps (catalog discovery, pricing, payment initiation, error handling), safe delegation of money actions to agents, and interoperability between AI buyers and merchant systems.[^2][^4]

An agent‑readable catalog implies structured, machine‑consumable product and pricing data that can be navigated by agents, possibly with embeddings or schemas for semantic search. Upsell/cross‑sell agents introduce personalization, requiring models that understand merchant context, buyer behaviour and constraints to suggest additional products or higher‑margin options without harming conversion.[^2][^1]

Campaign orchestrators are essentially AI systems that design, execute and monitor marketing or discount campaigns using payments and engagement signals, raising themes around multi‑armed bandits, uplift modeling, and budget‑aware optimization. Safety and compliance add a risk layer: agents must not initiate unbounded charges or unauthorized actions, and they must log all steps for audit and rollback.[^4][^2]

## Track 02 – AI Risk Manager

The AI Risk Manager track aims to "stop the merchant losing money to fraud, returns and chargebacks" by building detectors, verifiers or auto‑responders targeting a specific class of loss. Participants must ship a working system with measured precision and recall on a held‑out test set, along with honest accounting of false‑positive costs.[^10][^5][^1]

Example build directions include a chargeback evidence responder (assembling and submitting evidence to payment networks), a return‑risk scorer (predicting likelihood of abusive returns), a fraud‑spike detector (detecting sudden anomalies), or an abuse‑ring sentinel (identifying coordinated fraud rings). Razorpay explicitly emphasizes that the track is strictly defense‑only; any offense‑capable system (e.g. tools that help commit fraud) is disqualified.[^5][^1]

### Deep Problem Themes in Risk Management

This track’s underlying themes align with financial risk analytics and fraud detection: anomaly detection over transaction streams, supervised classification for fraud labels, and temporal patterns for spikes or coordinated attacks. Precision/recall trade‑offs matter greatly because false positives can block legitimate customers or create friction that harms revenue, while false negatives let fraud slip through.[^4][^2]

Candidates are expected to design data pipelines for risk signals (transaction features, device fingerprints, behavioural patterns), choose appropriate models (from gradient boosting and deep learning to simpler rules), and evaluate performance on held‑out data. Honest metrics mean explicitly stating thresholds, confusion matrices and the business cost of wrong decisions rather than cherry‑picking impressive numbers.[^3][^2]

Auto‑responders introduce workflow automation: generating evidence packages for chargebacks, triggering additional verification (OTP, KYC checks), or temporarily throttling risky segments. Abuse‑ring detection involves graph‑based reasoning or community detection over entities like cards, devices, IPs and merchants to catch clusters indicative of collusion.[^1][^4]

## Track 03 – AI Revenue Recovery

The AI Revenue Recovery track targets "revenue that’s slipping away" across payment failures, checkout abandonment, failed subscriptions and overdue invoices. Builders must create agents that detect revenue at risk, diagnose the root cause, choose an appropriate intervention, and execute a bounded recovery workflow, then show measured money recovered across a batch with compliant escalation and stopping rules.[^5][^1]

Example directions cited include payment degradation → root cause → recovery action, checkout drop‑off recovery, failed‑subscription recovery, B2B receivables chasers, mandate retry sequencers, Hinglish voice‑based recovery flows, and promise‑to‑pay trackers. The emphasis is on closing the loop: not just flagging a problem, but driving remedial actions and tracking recovery outcomes.[^1]

### Deep Problem Themes in Revenue Recovery

The core theme here is lifecycle revenue management: understanding how and why money fails to move through the pipe and designing AI‑informed interventions to salvage it. For payment degradation (e.g., rising failure rates due to network issues or PG problems), the agent must monitor metrics, identify patterns, attribute causes, and suggest or execute mitigations like route changes, retries or fallback flows.[^2][^4]

Checkout abandonment recovery involves behavioral analytics and messaging: tracking where users drop off, segmenting them, and triggering nudges (emails, SMS, in‑app prompts) with offers or reminders at the right time, possibly personalized via models. Subscription recovery is about retry strategies, card updater flows, and communication sequences to prevent churn; B2B receivables chasers add workflow logic around invoice reminders, escalation paths, and promise‑tracking.[^10][^1]

Mandate retry sequencing touches recurring payments and auto‑debit mandates, requiring careful handling of bank rules, retry windows and customer consent. Hinglish voice recovery references conversational AI for Indian users, where speech or voicebots in mixed Hindi‑English can reach customers; this introduces ASR, NLU and compliance issues around what agents can say and promise.[^1]

## Track 04 – AI Finance Controller

The AI Finance Controller track is about "running the books and the cash position" by closing one finance‑ops loop over a batch of synthetic data and reporting match rate plus unresolved exceptions. Builders should focus on tasks like multi‑source reconciliation, settlement Q&A, forward cash forecasting, or tax line matching.[^3][^5][^1]

Razorpay notes that 2026 "builder consensus" is that verification capacity, not generation speed, is the bottleneck; reconciliation, settlement and forecasting remain largely manual, making this a ripe area for AI augmentation. The bar combines throughput, measured accuracy and an honest exception list, emphasizing that cherry‑picked perfect matches do not prove system utility.[^1]

### Deep Problem Themes in Finance Ops and Reconciliation

Finance-controller problems revolve around matching and validating records across heterogeneous systems: payment gateways, bank statements, internal ledgers, tax records and external invoices. Multi‑source reconciliation requires entity matching, tolerance for minor discrepancies, and rule‑based or learned logic to decide which mismatches can be auto‑resolved versus escalated.[^2][^3]

Settlement Q&A agents act as copilots for finance teams, answering questions about which payments settled, why a settlement amount differs from expectations, or which fees were applied, using structured and semi‑structured data. Forward cash forecasting is a time‑series and scenario modeling problem, predicting cash inflows and outflows based on historical patterns, known invoices and subscription schedules.[^4][^3]

Tax‑line matching maps transactions to correct tax lines or categories, potentially automating GST/other tax reporting preparation. Exception lists are crucial: the system must surface the cases it cannot confidently resolve, with reasons, so human controllers can review them; this is part of building trustworthy AI support in finance.[^3][^1]

## Track 05 – Open Track

The Open Track allows builders to "build what you believe should exist" so long as it solves a real problem, uses AI meaningfully, and demonstrates a working product that creates measurable value. Razorpay clarifies that open does not mean easier: the same bar for execution quality, reliability and depth applies as in the other tracks.[^2][^1]

Community posts describe this as an opportunity for AI‑native fintech products or systems that fall outside the predefined domains, such as novel AI tools for merchant analytics, customer support, compliance automation or entirely new workflows adjacent to Razorpay’s ecosystem. The track rewards candidates who deeply understand a problem space and can show evidence that their solution improves metrics that matter (e.g., time saved, error reduction, conversion improvement).[^7][^2]

## Practical Strategy and Advice from Community Content

Multiple YouTube explainers and social posts offer practical advice on how to approach the Buildathon: pick one track that aligns with your strengths instead of trying to cover all; avoid generic ChatGPT wrappers, focusing instead on specific, high‑signal problems; and treat the project as a product, not just a college assignment.[^11][^10][^4]

They recommend building something that actually runs end‑to‑end, with proper documentation, logging and error handling, and then recording a pitch video that explains the problem, shows the system working, and summarizes architecture and metrics rather than only UI flows. Candidates are also encouraged to quantify their system’s impact (revenue recovered, fraud reduction, time saved) and to openly discuss limitations and failure modes, which aligns with Razorpay’s emphasis on honest metrics and exception handling.[^10][^4][^3][^2]

Finally, community guidance highlights that this Buildathon is a strong opportunity for students serious about AI, ML, agents or fintech, especially those frustrated with DSA‑heavy hiring pipelines; by investing in a high‑quality build, they can showcase practical ability and potentially convert directly into a high‑stipend AI internship.[^8][^4][^2]

---

## References

1. [Razorpay AI Buildathon — Build. Show. Get hired.](https://razorpay.com/buildathon/) - # Razorpay AI Buildathon — Build. Show. Get hired.

Think you can build real AI? Prove it. A student...

2. [Razorpay AI Buildathon 2026: Tracks, Eligibility, Stipend & ...](https://velonx.in/blog/razorpay-ai-buildathon-2026-tracks-eligibility-stipend-selection-process) - Most internship hiring still starts with a resume screen, an aptitude test, and a group discussion r...

3. [Razorpay AI Buildathon 2026 - 75000 Stipend Internship for Students](https://cloudsutra.in/blogs/razorpay-ai-buildathon-2026-75000-stipend-internship-for-students) - Razorpay AI Buildathon 2026 offers students a ₹75,000/month AI Builder Internship with no resume scr...

4. [Razorpay Is Hiring AI Builders 🔥 ₹75K/Month | No Aptitude Test or GD | Razorpay Buildathon 2026](https://www.youtube.com/watch?v=AWKvY-KjL9k) - Tired of the same DSA → OA → Interview → Rejection cycle?

Razorpay is giving students a VERY differ...

5. [Build. Show. Get hired. | Dr. S Chand Rakesh Roshan, Ph.D.](https://www.linkedin.com/posts/schandrakeshroshan_razorpay-ai-buildathon-build-show-get-activity-7496419284542423040-hqSD) - AI Builder Internship - Buildathon - Razorpay- Bamgalore, India :: Build. Show. Get hired. Think you...

6. [Ashinee Kesanam - Razorpay AI Buildathon 2026 - LinkedIn](https://www.linkedin.com/posts/ashinee20_razorpay-ai-buildathon-2026-build-show-activity-7496914271059144704-ukJE) - Razorpay AI Buildathon 2026 - Build. Show. Get Hired. Razorpay is inviting students to build real-wo...

7. [Bharathi G's Post - LinkedIn](https://www.linkedin.com/posts/cloudsutra_razorpay-razorpaybuildathon-aibuildathon-activity-7497187001977319424-KAf2) - 🚀 Razorpay AI Buildathon 2026 — ₹75,000/month AI Builder Internship! If you're a student interested ...

8. [ApplyNest's Post](https://www.linkedin.com/posts/applynest_razorpay-razorpaybuildathon-aiinternship-activity-7496873800744198144-72ha) - 🚀 Razorpay AI Buildathon 2026 — ₹75,000/month AI Internship Opportunity! If you're a student interes...

9. [Razorpay AI Buildathon 2026: Build Real ...](https://www.instagram.com/p/DcVQee_n-UL/) - 0 likes, 0 comments - trueline_research on August 21, 2026: "𝐑𝐚𝐳𝐨𝐫𝐩𝐚𝐲 𝐀𝐈 𝐁𝐮𝐢𝐥𝐝𝐚𝐭𝐡𝐨𝐧 𝟐𝟎𝟐𝟔: 𝐁𝐮𝐢𝐥𝐝 𝐑𝐞𝐚𝐥...

10. [Razorpay AI Buildathon 2026 🔥 ₹75,000/Month AI Internship | Students Can Get Hired!](https://www.youtube.com/watch?v=mmENFZNA8qE) - 🚨 Razorpay is looking for AI Builders! 🤖🔥

Razorpay AI Buildathon 2026 is a student-focused opportun...

11. [Razorpay AI Buildathon 2026 || ₹75K/Month AI Internship || Student Program || Apply Now!](https://www.youtube.com/watch?v=l_AbZCdrBpY) - Razorpay AI Buildathon 2026 || ₹75K/Month AI Internship || Student Program || Apply Now!

Razorpay A...

