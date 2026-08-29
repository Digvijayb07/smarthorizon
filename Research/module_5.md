**SMART HORIZON 2026 — 48-HOUR INTERNATIONAL HACKATHON** 

Team VibeCoderz | SH-FIN-01 | SHIH26-TID-85 

# **MODULE 5** 

## **Research Papers & Technical Study** 

_A task guide for the team — what this module covers, why it matters for our Problem Statement, and exactly how it will be executed._ 

## **1. Our Problem Statement, in One Paragraph** 

SH-FIN-01 asks for a fraud-detection system for banks. Our solution — the "Digital Investigator" — is a Multi-Agent AI System (MAS) that doesn't just flag suspicious transactions like legacy systems do. It runs the flag through a 4-stage pipeline of specialised agents that investigate, explain, and decide — turning a raw anomaly score into a verdict a human auditor can trust. 

|**Stage**|**Agent**|**Job**|
|---|---|---|
|1. Detect|**scoreAgent**|Hybrid rules + ML anomaly scoring on incoming transactions|
|2. Investigate|**contextAgent**|Enriches the flagged case with device ID, location,<br>behavioural history|
|3. Explain|**reasonAgent**|Generative AI writes an audit-ready narrative of WHY it's<br>fraud|
|4. Decide|**decisionAgent**|Outputs Allow / Verify / Block, or escalates to a human<br>analyst|



_<mark>Why this matters: judges in the final round will not just ask "does it work?" — they will ask "why this algorithm, why this architecture, is there evidence it beats existing systems?" That evidence layer is what Module 5 builds.</mark>_ 

## **2. What Module 5 Actually Is** 

Module 5 is not a coding task. It is the research and justification layer underneath the whole pipeline. Every technical claim in our pitch deck — "70% faster," "massive reduction in false positives," "RBI-compliant explanations" — needs a real published paper backing it up. That's what this module produces. 

### **Objective (as assigned)** 

- Understand the academic work behind fraud detection, explainable AI, and multi-agent systems. 

- Turn 18 assigned topics into structured paper summaries + one comparison table. 

- Make sure every stage of our pipeline (scoreAgent → contextAgent → reasonAgent → decisionAgent) has published evidence behind it. 

### **Two Deliverables** 

- Paper Summaries — one structured writeup per topic/paper (template in Section 4). 

- Comparison Table — a single table rolling up all papers so the team can answer "why this method" in 10 seconds during Q&A. 

## **3. How the 18 Topics Map to Our Pipeline** 

The 18 topics look unrelated at first glance. They aren't — each one exists to justify one specific agent in our architecture. Grouping them this way is what makes the research useful instead of just an academic checklist. 

|**Cluster → Agent**|**Topics in this Cluster**|**Why it's needed**|
|---|---|---|
|**A. Detection → scoreAgent**|Fraud Detection (general)<br>Isolation Forest<br>Random Forest<br>XGBoost<br>Autoencoders<br>One-Class SVM<br>AML Detection|These are the actual scoring<br>algorithms — proves our hybrid<br>rules+ML approach is grounded in<br>published, benchmarked methods.|
|**B. Context → contextAgent**|Graph Neural Networks<br>Graph Fraud Detection<br>Behavior Analytics<br>Knowledge Graph|Justifies why enriching a flagged<br>transaction with<br>device/location/relationship data<br>catches fraud that a lone transaction<br>score misses.|
|**C. Explainability →**<br>**reasonAgent**|Explainable AI<br>SHAP<br>LIME<br>Counterfactual AI|Backs up our "RBI-compliant, audit-<br>ready explanation" claim —<br>regulators need interpretable<br>reasons, not a black-box score.|
|**D. Orchestration →**<br>**decisionAgent + system**|LLMs in Banking<br>Multi-Agent AI<br>RAG<br>Risk Scoring|Justifies the multi-agent architecture<br>itself and the final<br>Allow/Verify/Block decision logic<br>— proves it's not just a buzzword.|



## **4. The Per-Paper Template — Fill This for Every Paper** 

Keep each summary to roughly half a page. Judges skim — density beats volume. Use this exact structure for every paper so all 5 team members' outputs merge cleanly into one document later. 

|**Field**|**What to write**|
|---|---|
|**Problem**|What gap in fraud detection does this paper address?|
|**Dataset**|What did they test on? (e.g. IEEE-CIS Fraud, PaySim, European credit card<br>dataset, real bank data)|
|**Method**|The actual algorithm / architecture used|
|**Advantages**|Why it worked / what it improved on|
|**Disadvantages**|Limitations, failure modes, cost, data needs|
|**Future Scope**|What the authors themselves flag as unsolved|
|**Can we use?**|Your judgment — does this fit scoreAgent / contextAgent / reasonAgent /<br>decisionAgent, or not applicable to our system?|



**Worked Example** 

|**Field**|**Example — "Fraud Detection in Banking: A Deep Learning Approach with**<br>**Explainable AI"**|
|---|---|
|Problem|Black-box deep learning fraud models aren't trusted by bank compliance teams|
|Dataset|Public credit card transaction dataset (anonymised)|
|Method|Deep neural network classifier + SHAP for post-hoc explanation|
|Advantages|High accuracy AND per-transaction explanation of which features drove the flag|
|Disadvantages|SHAP is computationally expensive at real-time transaction volume|
|Future Scope|Authors suggest lighter-weight approximate SHAP for production speed|
|Can we use?|Yes — directly supports reasonAgent's audit-narrative generation|



## **5. Final Comparison Table — Format** 

Once all paper summaries are done, roll them into one master table. This is the single artifact most likely to get pulled up during judge Q&A, so keep it scannable. 

|**Paper / Method**|**Category**|**Accuracy / F1 (if**<br>**reported)**|**Explainable?**|**Real-time**<br>**capable?**|**Fits**<br>**Agent**|
|---|---|---|---|---|---|
|e.g. XGBoost fraud|Detection|~0.94 F1|Low (needs|Yes|score|
|model|||SHAP)|||



_<mark>Add one row</mark>_ _<u><mark>per paper. Keep entries to a few words — this table is a lookup reference, not a report.</mark></u>_ 

## **6. Step-by-Step Execution Plan** 

- Step 1 — Cluster the 18 topics into the 4 groups from Section 3 (already done for you above). 

- Step 2 — For each cluster, find 2–3 real papers. Start with the ones already cited in our own deck's References slide, since judges may already recognise them: 

   - "Fraud Detection in Banking: A Deep Learning Approach with Explainable AI" 

   - "A User-Centered Explainable AI Approach for Financial Fraud Detection" 

   - "Autonomous AI Agents for Real-Time Financial Transaction Monitoring..." 

- Step 3 — Add 1–2 more papers per topic beyond what's already cited — this is where you add value the deck doesn't already have. 

- Step 4 — Fill the per-paper template (Section 4) for every paper. Keep it to half a page each. 

- Step 5 — Roll everything into the master comparison table (Section 5). 

- Step 6 — Write one closing paragraph tying the research back to the Problem Statement — e.g. which methods justify scoreAgent + reasonAgent's design choices, and why. This is the sentence most likely to get quoted in the final defense. 

### **Suggested Order of Attack** 

- Cluster A (Detection) first — it's the most concrete and has the most existing literature. 

- Cluster C (Explainability) second — it's the most differentiating claim in our pitch. 

- Cluster B (Context/Graph) third. 

- Cluster D (Orchestration/LLM/Multi-Agent) last — newest area, fewer but more novel papers. 

## **7. Why This Matters to the Rest of the Team** 

Each teammate has a different module. This one feeds all of them: 

- Gives the dev team (backend/frontend) confidence their scoreAgent / contextAgent / reasonAgent / decisionAgent design choices are backed by real research, not guesswork. 

- Gives the team a ready answer bank for judge questions like "why this algorithm," "how do you avoid false positives," "is this proven anywhere." 

- Strengthens the Feasibility and Impact slides already in the deck — those claims (70% faster, RBI-compliant, reduced false positives) currently have no citation trail; this module builds that trail. 

