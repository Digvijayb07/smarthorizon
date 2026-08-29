Good - that changes the plan a lot. With 1-2 weeks and a team that's frontend-heavy but backend/ML-light, the winning strategy isn't "build everything in the document" - it's **cut aggressively to the P0 list your own research already identified**, lean hard into your frontend strength for the demo, and de-risk the ML/backend side by using the simplest possible implementation of each piece (pretrained/off-the-shelf tools, not custom training).

Here's the full plan.

**1\. Lock the MVP scope first (don't skip this)**

Your document already tells you what to build (Section 24 / Table 15). Treat everything else as "explain in the doc, don't build."

**Build (P0 only):**

- Case queue + case detail dashboard (your strength - make this shine)
- Orchestrator that calls 3 "agents" (really: sequenced/parallel functions, not a fancy framework)
- One trained risk model (XGBoost on synthetic data) + SHAP explanation
- A simple transaction graph (NetworkX backend + D3.js/vis.js frontend - skip Neo4j)
- RAG over 5-10 regulatory PDFs (RBI/NPCI/PMLA circulars) using ChromaDB
- One shared LLM via API (Claude or GPT) for investigation reasoning + report drafting
- Audit trail (just an append-only table, not a fancy immutable log)
- Human approve/reject/escalate action

**Explicitly do NOT build** (mention as "future work" in your pitch - this is exactly what your doc's Table 15 "Future" row says):

- GNN, real device fingerprinting, real behavioral analytics, LoRA fine-tuning, consortium data, Neo4j cluster, real bank integrations.

**Simplify given weak backend/ML:**

- No custom orchestration framework (LangGraph) - just Python functions called in sequence/parallel with asyncio.
- No fine-tuning anything. One API-based LLM, controlled entirely through the prompt contract already in your doc (Section 9) - that's your differentiator, and it's just prompt engineering.
- ML model = XGBoost trained on a synthetic dataset you generate yourselves (a script, ~30 min of work), not real bank data.
- RAG = ChromaDB + sentence-transformers - both have 10-line quickstarts.

**2\. Role assignment (5 people, frontend-heavy)**

| **Person** | **Track**                                                                    | **Why**                                                            |
| ---------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| A + B      | **Frontend** - dashboard, case queue, evidence view, "Why Flagged" panel     | Your strongest area - this is what judges see most                 |
| C          | **Backend/API** - FastAPI, mock data generator, DB schema, orchestrator glue | Backend, but this part is mostly plumbing, not ML                  |
| D          | **ML + Graph** - XGBoost + SHAP, synthetic dataset, NetworkX graph logic     | The "weak" area - give them the most runway and pair-program early |
| E          | **LLM + RAG + Reports** - prompt contract, RAG pipeline, report generation   | Mostly prompt engineering + API calls, very learnable in days      |

Person C and D should sit together for the first 3 days - the API layer and the ML layer are tightly coupled (schema of the "evidence package" JSON).

**3\. Day-by-day plan (assuming ~12 working days)**

**Day 0 (kickoff, half day)**

- Everyone reads the architecture doc together, agrees on the P0 cut above.
- Define the **evidence package JSON schema** as a team (this is the contract everything else plugs into - matches your doc's Section 9 output format). This single artifact prevents integration hell later.
- Set up shared GitHub repo, project board with the P0 list as tickets, Figma/wireframe doc.

**Days 1-2 - Foundations (parallel)**

- A+B: Wireframe + build the shell UI (routing, case queue table, empty case detail page) with mock JSON.
- C: FastAPI skeleton, Postgres schema (cases, transactions, customers, alerts), synthetic data generator script (this is critical - everything downstream depends on realistic fake data).
- D: Learn/build XGBoost pipeline on a public fraud dataset (e.g., Kaggle credit card fraud, or IEEE-CIS) as a training exercise; start designing feature engineering for your synthetic schema.
- E: Collect 5-10 real regulatory PDFs (RBI circulars, PMLA excerpts, NPCI guidelines - publicly available), set up ChromaDB, get basic retrieval working on 3 sample questions.

**Days 3-4 - Core logic**

- C+D: Build the risk scoring endpoint - feed synthetic transaction → XGBoost → score 0-100 + SHAP values, return as JSON matching the evidence schema.
- C: Build the transaction graph builder (NetworkX: fan-in/fan-out/circular-flow detection on synthetic data) and expose as an API.
- E: Wire the LLM prompt contract (Section 9 of your doc) - feed it a mock evidence package, get back structured JSON (risk_assessment, findings, recommended_actions, etc). Test with 3-4 varied fake cases until output is reliable.
- A+B: Build case detail page sections (Evidence tab, Risk Score tab) against the schema, still on mock data.

**Days 5-6 - Orchestration + Graph UI**

- C: Write the orchestrator - given an alert, call risk-scoring, graph, RAG, and LLM steps (sequential is fine; parallel with asyncio.gather if time allows), assemble the final evidence package, save case to DB.
- B: Graph visualization (D3.js or vis.js) rendering the NetworkX output - money flow between accounts, highlight suspicious patterns.
- A: "Why Flagged" panel - SHAP bars + LLM's natural-language explanation side by side (this is a big differentiator, invest real polish here).
- E: Compliance panel - RAG citations shown next to LLM's regulatory statements.

**Day 7 - First end-to-end integration checkpoint**

- Whole team: wire frontend to real backend endpoints (not mocks) for one full case flow: alert → orchestrator → evidence → LLM → dashboard. Expect this day to be messy - budget it as integration-only, no new features.

**Days 8-9 - Case lifecycle + reports (Tier 1/P1 stretch)**

- C: Case state machine (Open → Review → Escalate → Close), maker-checker approval flow, audit log table.
- E: Report generation - LLM drafts narrative, template fills structured fields (Investigation Summary + a simple STR draft).
- A+B: Approval screen, audit trail view, timeline view.
- D: Tune risk thresholds, add 2-3 more synthetic case archetypes (mule account, geo-velocity anomaly, legitimate high-volume customer) so the demo has variety.

**Days 10-11 - Guardrails, polish, edge cases**

- Add the "Insufficient evidence" and no-hallucination checks from your prompt contract - test by feeding a case with missing data.
- Add a basic prompt-injection test (feed a malicious note in transaction metadata, confirm the LLM doesn't follow it) - this maps directly to your doc's Section 23 and is a great judge talking point.
- UI polish pass: loading states, empty states, consistent styling - since design is your strength, this is where you differentiate.
- Write the "kill switch" toggle (even if it just disables the approve button) - cheap to build, checks a box judges look for.

**Day 12 - Demo prep & rehearsal**

- Prepare 2-3 scripted demo cases showing different outcomes (clear fraud with graph pattern, false-positive correctly dismissed, compliance-flagged case with RAG citation).
- Write the pitch: lead with "AI recommends, human decides" principle, show the architecture diagram, walk through one full case live.
- Full team dry run, time it, cut anything that isn't rock-solid.

**4\. Guardrails against the biggest hackathon risks for your team**

- **Don't attempt Neo4j** unless someone already knows it - NetworkX + a JS graph library gets you 90% of the visual impact with a fraction of the setup pain.
- **Don't fine-tune anything.** Your own doc says this explicitly (Section 7) - one API LLM + good prompts is not a compromise, it's the recommended approach.
- **Generate synthetic data early (Day 1)**, not later - every other team is blocked on it.
- **Freeze the evidence-package JSON schema on Day 0** and don't change it without a team conversation - this is the #1 source of late-stage integration breakage in multi-person hackathons.
- Since backend/ML is the thin part of the team, it's fine to lean on Claude Code or similar to accelerate the FastAPI/XGBoost/ChromaDB boilerplate - those parts are well-trodden and fast to generate correctly, freeing D and C's time for the harder integration logic.

If it'd help, I can generate the synthe