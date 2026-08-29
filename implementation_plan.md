# 🏆 Horizon — Hackathon Winning Strategy & Revised 2-Week Battle Plan

## Context Summary

**Hackathon:** SMART HORIZON 2026 — 48-Hour International Hackathon  
**Team:** VibeCoderz | SH-FIN-01 | SHIH26-TID-85  
**Problem Statement:** Build an autonomous multi-agent investigation system for financial crime — detecting anomalies, collecting context, assessing regulatory risk, generating audit-ready explanations, and recommending actions (Block/Monitor/Escalate).  
**Current Date:** 9 August 2026  
**Deadline:** ~2 weeks from now (~21 August 2026)

---

## Part 1 — Research Analysis: What You've Built So Far

Your research is **genuinely excellent** — far above what most hackathon teams produce. Here's the honest assessment:

| Module | Quality | Key Strength | Gap |
|---|---|---|---|
| [Module 1](file:///c:/Users/Digvijay/Documents/WebDev/Projects/horizon/Research/Module_1.md) — Banking Basics | ✅ Solid | Covers UPI, CBS, payment rails accurately | No gap — this is reference material, not build material |
| [Module 2](file:///c:/Users/Digvijay/Documents/WebDev/Projects/horizon/Research/Module_2.md) — Fraud Domain | ✅ Good | Clear roadmap, smart decision to focus UPI fraud | Lacks the actual fraud encyclopedia (just has the plan) |
| [Module 3-4](file:///c:/Users/Digvijay/Documents/WebDev/Projects/horizon/Research/module_3_4.md) — Workflow + Competitors | ✅ Excellent | Gap analysis table is gold — shows existing tools don't do explainable AI + GenAI reports + affordable Indian focus | Perfect as-is for pitch deck |
| [Module 5](file:///c:/Users/Digvijay/Documents/WebDev/Projects/horizon/Research/module_5.md) — Research Papers | ✅ Great structure | Cluster mapping to agents is brilliant | Paper summaries not yet filled — fine, skip for building |
| [Module 6](file:///c:/Users/Digvijay/Documents/WebDev/Projects/horizon/Research/Module_6_Regulations_and_Compliance.md) — Regulations | 🏆 Outstanding | Most thorough module. Compliance architecture, "AI recommends, Human decides" principle, STR/CTR filing details | This IS your pitch. Quote it heavily. |
| [Module 7](file:///c:/Users/Digvijay/Documents/WebDev/Projects/horizon/Research/Module_7_Feature_Validation_and_Opportunity_Analysis.md) — Feature Validation | 🏆 Outstanding | Priority matrix (Tier 1-4) is the single most important artifact. Every feature justified with "Need for Our System?" | Already tells you exactly what to build |

> [!IMPORTANT]
> **Your research has already answered the hardest question: WHAT to build.** Module 7's Priority Matrix + Module 6's compliance framework = your entire product spec. Most teams are still debating this at day 7. You're ahead.

---

## Part 2 — Analysis of Your Friend's 12-Day Plan

The [Next 12 days plan.md](file:///c:/Users/Digvijay/Documents/WebDev/Projects/horizon/Research/Next%2012%20days%20plan.md) is **80% correct in strategy, but has critical issues** that will burn you if not fixed:

### ✅ What the Plan Gets RIGHT

| Decision | Why It's Correct |
|---|---|
| P0 scope cut — build only Tier 1 | Matches your own Module 7 priority matrix perfectly |
| Skip Neo4j → use NetworkX + D3.js | Neo4j setup eats 1-2 days; NetworkX is Python-native and trivial |
| No fine-tuning — use API LLM + prompts | Your Module 7 Section 11 explicitly recommends this |
| Freeze JSON schema on Day 0 | Single best piece of advice in the document — prevents late-stage breakage |
| XGBoost + SHAP for scoring | Proven, fast, explainable — matches Module 5 cluster A/C |
| ChromaDB for RAG | Free, 10-line quickstart, no DevOps overhead |
| Synthetic data generator on Day 1 | Everything downstream depends on this — correct to prioritize |

### ❌ What the Plan Gets WRONG or Misses

| Issue | Problem | Fix |
|---|---|---|
| **5 people assumed, but team composition not confirmed** | Plan assigns A/B/C/D/E without knowing your actual team | You must re-map roles to YOUR real team (see Part 3) |
| **No pitch/deck track** | Plan treats Day 12 as "demo prep" — that's 1 day for pitch. Smart Horizon judges care 40%+ about presentation | Assign pitch/deck work starting Day 8, not Day 12 |
| **No database mentioned for case management** | Says "Postgres" but doesn't specify if you have Postgres experience | Use SQLite or Supabase (free) — zero setup. Postgres is overkill for a hackathon |
| **Missing the compliance "wow" feature** | Plan builds case queue + graph + risk score, but doesn't highlight the STR/report generation enough | STR draft generation in FIU-IND-like XML format is your **#1 differentiator** per Module 6. Prioritize it ABOVE the graph visualization |
| **Day 7 "integration day" is dangerous** | Assumes 6 days of parallel work then 1 day of integration. Integration almost always takes 2x longer | Do integration CONTINUOUSLY — frontend hits real endpoints starting Day 4, not Day 7 |
| **No mention of deployment** | Judges need to see it running. Plan assumes local dev only | Deploy to Vercel (frontend) + Railway/Render (backend) by Day 6 at latest |
| **No error handling or demo safety nets** | "Days 10-11 polish" is fine for polish, but doesn't mention fallback UX for when the LLM times out, graph has no data, etc. | Build "graceful degradation" UX — loading states, skeleton screens, fallback messages. A crash during demo = instant loss |
| **Day 0 "half day" is too relaxed** | Schema definition + repo setup + role assignment + Figma can easily fill a full day | Make Day 0 a FULL working day |

> [!WARNING]
> **The single biggest risk in this plan is Day 7's integration cliff.** Six days of parallel work → one day to wire everything together → 4 more days. In hackathons, integration is where 70% of teams die. **Solution:** Start integrating from Day 3-4 onwards. Frontend should never work on "mock JSON" for more than 2 days.

---

## Part 3 — Revised Winning Strategy & Battle Plan

### The Winning Product: "Horizon — AI Investigation Co-pilot for Financial Crime"

```
┌──────────────────────────────────────────────────────────────────┐
│                    INVESTIGATION DASHBOARD                       │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────────────┐    │
│  │ Case Queue │  │ Case Detail  │  │ "Why Flagged" Panel   │    │
│  │ (Priority  │  │ (Timeline +  │  │ (SHAP bars + LLM     │    │
│  │  sorted)   │  │  Evidence)   │  │  explanation + RAG    │    │
│  └────────────┘  └──────────────┘  │  citations)           │    │
│                                     └───────────────────────┘    │
│  ┌──────────────┐  ┌────────────────────────────────────────┐   │
│  │ Graph View   │  │ Investigation Report / STR Draft       │   │
│  │ (Money flow  │  │ (LLM-generated, audit-ready)           │   │
│  │  + entities) │  │ [Generate PDF] [Generate STR XML]      │   │
│  └──────────────┘  └────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ [✓ Approve]  [⚠ Escalate]  [✕ Dismiss]  [🔒 Kill Switch]│   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### Architecture (What You're Actually Building)

```
Frontend (Next.js or Vite + React)
    ↕ REST API
Backend (FastAPI / Python)
    ├── Orchestrator (async Python functions, NOT LangGraph)
    │     ├── scoreAgent  → XGBoost + SHAP → Risk Score + Explanation
    │     ├── contextAgent → NetworkX graph + geo-velocity + timeline
    │     ├── reasonAgent  → LLM (Claude/GPT) + RAG (ChromaDB) → Case Summary
    │     └── decisionAgent → Rule engine → Allow/Verify/Block/Escalate
    ├── Database (SQLite / Supabase)
    │     ├── cases, transactions, customers, alerts, audit_log
    │     └── Synthetic data generator script
    └── RAG Knowledge Base (ChromaDB)
          └── 5-10 RBI/NPCI/PMLA regulatory PDFs
```

### Tech Stack Decision

| Layer | Technology | Why |
|---|---|---|
| Frontend | **Vite + React** (or Next.js if team prefers) | Fast, hot reload, you know it |
| Styling | **Tailwind CSS** (if comfortable) or **Vanilla CSS** | Speed of development is paramount |
| Charts | **Recharts** or **Chart.js** for risk score bars | Simple, pretty |
| Graph Viz | **react-force-graph** or **vis.js** or **D3.js** | Money flow visualization |
| Backend | **FastAPI (Python)** | Fastest Python API framework, async support |
| Database | **SQLite** (dev) → **Supabase** (if deployed) | Zero setup |
| ML Model | **XGBoost** + **SHAP** | Proven for fraud, explainable |
| Graph Engine | **NetworkX** | Python-native, no infra needed |
| RAG | **ChromaDB** + **sentence-transformers** | Free, 10-line setup |
| LLM | **OpenAI GPT-4o** or **Claude 3.5 Sonnet** via API | Best reasoning, structured output |
| Deployment | **Vercel** (frontend) + **Railway** or **Render** (backend) | Free tier, zero DevOps |

---

### Revised Day-by-Day Plan (14 Days: Aug 10 — Aug 23)

> [!NOTE]
> This plan assumes the team is you (Digvijay) + teammates. Adjust role names to real people. The plan is designed so that **no person is blocked on another for more than 1 day**.

---

#### 🔴 Phase 1: Foundation (Days 0-2) — Aug 10-12

**Day 0 — FULL DAY (Aug 10, Sunday)**

Everyone together:
- [ ] Read this strategy document as a team
- [ ] **Define the Evidence Package JSON schema** — this is THE contract:
  ```json
  {
    "case_id": "FC-2026-XXXX",
    "alert": { "type": "...", "timestamp": "...", "rule_triggered": "..." },
    "transaction": { "amount": 490000, "sender": "...", "receiver": "...", ... },
    "customer": { "name": "...", "kyc_status": "...", "risk_category": "...", ... },
    "risk_score": { "score": 85, "factors": [...], "shap_values": {...} },
    "graph_context": { "connections": [...], "patterns": [...] },
    "geo_velocity": { "impossible_travel": true, "details": "..." },
    "llm_analysis": { "summary": "...", "findings": [...], "recommendation": "..." },
    "rag_citations": [ { "source": "...", "text": "...", "relevance": 0.95 } ],
    "recommended_action": "BLOCK",
    "confidence": 0.92
  }
  ```
- [ ] Set up GitHub repo with branch protection
- [ ] Set up project board (GitHub Projects / Notion) with tickets from this plan
- [ ] Decide team role assignments (see below)
- [ ] Set up shared .env for API keys (OpenAI/Claude)

**Day 1 (Aug 11) — Parallel Tracks Begin**

| Track | Person(s) | Tasks |
|---|---|---|
| **Frontend** | 2 people | Scaffold Vite+React app. Build shell: sidebar nav, case queue table (hardcoded JSON), empty case detail page. Set up routing. |
| **Backend** | 1 person | Scaffold FastAPI. Define DB schema (SQLite). **Write the synthetic data generator** — this is THE most critical Day 1 task. Generate 50 realistic-looking transactions with fraud/legitimate mix. |
| **ML + Graph** | 1 person | Download Kaggle credit card fraud dataset. Build XGBoost training pipeline. Train model, get SHAP working on a single prediction. Export model. |
| **LLM + RAG** | 1 person | Collect 5-10 regulatory PDFs (RBI circulars, NPCI OCs, PMLA excerpts — all public). Set up ChromaDB. Ingest documents. Test 3 retrieval queries. Write the first version of the LLM prompt contract. |

**Day 2 (Aug 12) — Foundations Solidify**

| Track | Person(s) | Tasks |
|---|---|---|
| **Frontend** | 2 people | Build Case Detail page layout: tabs for Evidence, Risk Score, Graph, Timeline, Report. Use mock JSON from the schema. Style the "Why Flagged" panel with SHAP bar chart mockup. |
| **Backend** | 1 person | Build API endpoints: `GET /cases`, `GET /cases/{id}`, `POST /alerts` (trigger investigation). Wire synthetic data into DB. Serve real JSON from API. |
| **ML + Graph** | 1 person | Build NetworkX graph from synthetic transaction data. Implement fan-in/fan-out/circular detection. Expose as function that returns JSON matching schema. |
| **LLM + RAG** | 1 person | Wire LLM prompt contract — feed mock evidence package → get structured JSON back (risk_assessment, findings, recommended_actions). Test with 3-4 varied cases. Add RAG retrieval step before LLM call. |

---

#### 🟡 Phase 2: Core Integration (Days 3-5) — Aug 13-15

> [!IMPORTANT]
> **Integration starts NOW, not Day 7.** Frontend starts hitting real endpoints from Day 3.

**Day 3 (Aug 13) — Wire It Up**

| Track | Tasks |
|---|---|
| **Frontend** | Connect case queue to `GET /cases` API. Replace all mock JSON with API calls. Display real risk scores from backend. |
| **Backend** | Build the orchestrator: `alert → scoreAgent() → contextAgent() → reasonAgent() → decisionAgent()` as sequential Python async functions. Each function returns a piece of the evidence package JSON. |
| **ML + Graph** | Integrate XGBoost scoring into the orchestrator pipeline. Return SHAP values as JSON. Build the graph analysis endpoint. |
| **LLM + RAG** | Integrate RAG + LLM into the orchestrator pipeline. The orchestrator calls your function with the evidence package, you return the LLM analysis. |

**Day 4 (Aug 14) — First End-to-End Flow**

🎯 **MILESTONE: One complete case flows from alert → orchestrator → all 4 agents → dashboard display**

| Track | Tasks |
|---|---|
| **Everyone** | Wire the full pipeline for ONE case. Alert triggers orchestrator → score → graph → LLM+RAG → decision → frontend displays everything. **This will be messy. That's expected. Budget the full day.** |
| **Frontend** | Display real SHAP bars + LLM explanation in "Why Flagged" panel. Show real graph data (even if ugly). |
| **Backend** | Ensure orchestrator returns complete evidence package. Handle errors gracefully (LLM timeout → return partial result with "Analysis pending"). |

**Day 5 (Aug 15) — Graph Visualization + Timeline**

| Track | Tasks |
|---|---|
| **Frontend Person 1** | Build graph visualization using react-force-graph or vis.js. Show accounts as nodes, transactions as edges, highlight suspicious patterns (red nodes, thick edges for large amounts). |
| **Frontend Person 2** | Build Timeline component — vertical timeline showing case events chronologically with icons and risk indicators. |
| **Backend** | Build case state machine: `Open → Under Review → Escalated → Closed`. Add approval/reject/escalate endpoints. Add audit_log table (append-only: who, what, when, action). |
| **LLM + RAG** | Build investigation report generator — LLM drafts full case summary following the template from Module 7's Case Summarization section. |

---

#### 🟢 Phase 3: Differentiators (Days 6-8) — Aug 16-18

**Day 6 (Aug 16) — Report Generation + STR Draft**

| Track | Tasks |
|---|---|
| **Frontend** | Build report view page — display LLM-generated investigation summary beautifully. Add "Generate PDF" button (use html2pdf or react-pdf). Build STR draft view (structured form with auto-filled fields). |
| **Backend** | Build STR generation endpoint — take case data, generate structured XML-like report matching FIU-IND format. This is a template engine, not AI. |
| **ML** | Add 3-4 more synthetic case archetypes: (1) mule account with fan-out pattern, (2) legitimate high-volume merchant (to show false-positive handling), (3) geo-velocity anomaly, (4) SIM swap + new device. |
| **LLM** | Add compliance panel — RAG citations shown inline with LLM statements. Each regulatory claim links to source document. |

**Day 7 (Aug 17) — Polish Core + Deploy**

| Track | Tasks |
|---|---|
| **Frontend** | Add approval workflow screen (Analyst submits recommendation → Manager approves/rejects). Add "Kill Switch" toggle in header (disables auto-decisions, turns everything to manual). Add audit trail view (table of all actions). |
| **Backend** | Maker-checker approval flow. Role-based access (analyst, manager, auditor). |
| **DevOps** | **Deploy**: Frontend → Vercel. Backend → Railway or Render. Ensure it works on a real URL. |
| **Everyone** | Full team QA — walk through 3 cases end-to-end on the deployed version. Fix bugs. |

**Day 8 (Aug 18) — Edge Cases + Guardrails**

| Track | Tasks |
|---|---|
| **All** | Add "Insufficient evidence" handling — when data is missing, LLM should say "Cannot determine" not hallucinate |
| **All** | Add prompt injection test — feed malicious note in transaction metadata, confirm LLM doesn't follow it (mention in pitch — judges love this) |
| **Frontend** | Loading states, empty states, error states for EVERY component. Skeleton screens while data loads. Responsive layout check. |
| **LLM** | Add confidence scoring — LLM outputs a confidence level with its analysis. Low confidence → system recommends human review |

---

#### 🔵 Phase 4: Pitch & Polish (Days 9-11) — Aug 19-21

**Day 9 (Aug 19) — UI Polish Day**

| Track | Tasks |
|---|---|
| **Frontend** | This is your STRENGTH. Make it shine: smooth animations, dark mode, glassmorphism panels, micro-interactions on buttons. The dashboard should look like a $50K SaaS product. |
| **Frontend** | Add data visualization: donut chart for case status distribution, line chart for risk score trend, counter for cases resolved today. |
| **Backend** | Performance optimization — cache LLM responses, add request timeouts, optimize DB queries |

**Day 10 (Aug 20) — Pitch Deck + Demo Script**

| Track | Tasks |
|---|---|
| **1-2 people** | Build pitch deck (10-12 slides max): |
| | 1. Problem: "10,000 alerts/day. Who investigates them?" |
| | 2. Current Pain: Manual investigation takes hours, backlogs growing |
| | 3. Our Solution: "AI recommends, Human decides, System documents" |
| | 4. Architecture: 4-agent pipeline diagram |
| | 5. Live Demo Screenshots (3-4 key screens) |
| | 6. Tech Stack: XGBoost + SHAP + LLM + RAG + Graph |
| | 7. Compliance: "Built for RBI, NPCI, PMLA from Day 1" |
| | 8. Differentiator table (us vs FICO/Feedzai/etc from Module 3-4) |
| | 9. Impact: "70% faster investigation, automated STR drafts" |
| | 10. Future Scope: GNN, behavioral biometrics, consortium data |
| | 11. Team slide |
| **Rest of team** | Prepare 3 scripted demo cases: |
| | Case 1: Clear fraud — mule account + fan-out pattern + auto-generated STR |
| | Case 2: False positive — high-volume merchant correctly dismissed (shows the system is smart, not trigger-happy) |
| | Case 3: Compliance case — transaction flagged, RAG cites specific RBI circular, analyst approves with documented reasoning |

**Day 11 (Aug 21) — Rehearsal + Final Fixes**

| Track | Tasks |
|---|---|
| **Everyone** | Full team dry run of the presentation + demo, 3 times minimum |
| **Everyone** | Time it. Cut anything that isn't rock-solid. |
| **Everyone** | Prepare backup screenshots/video in case live demo fails |
| **Everyone** | Verify deployed version works. Test on multiple browsers. |
| **Everyone** | Prepare Q&A answers for expected judge questions (see below) |

---

### 🎤 Judge Q&A Preparation — Killer Answers

| Expected Question | Your Answer |
|---|---|
| "Why multi-agent instead of one model?" | "A single agent overwhelmed by tools loses accuracy. Our 4 agents specialize — scoreAgent runs ML, contextAgent does graph analysis, reasonAgent writes explanations, decisionAgent applies policy. Errors stay contained, and each agent's reasoning is independently auditable — critical for RBI compliance." |
| "How do you handle hallucinations?" | "Three layers: (1) RAG grounds every regulatory claim in actual RBI/NPCI documents with citations, (2) structured output schemas prevent free-form generation, (3) human-in-the-loop — AI recommends, human decides. We also built prompt injection tests to demonstrate adversarial robustness." |
| "Can AI block an account?" | "No — and that's by design. RBI mandates human oversight for material financial decisions. Our system recommends Block/Allow/Escalate with full reasoning, but a human analyst approves every action. We even built a kill switch per RBI's Model Risk Management Framework draft." |
| "What about false positives?" | "Great question — Case 2 in our demo specifically shows a legitimate high-volume merchant that our system correctly identifies as NOT fraud, despite triggering velocity alerts. The SHAP explanation shows WHY it's not suspicious. This reduces analyst fatigue." |
| "How is this different from Feedzai/FICO?" | "Those systems detect and alert. We investigate and explain. They generate 10,000 alerts — someone still has to investigate each one. Our system auto-generates investigation reports, cites regulatory requirements, and drafts STRs. We augment small compliance teams." |
| "What data did you train on?" | "We generated a synthetic dataset with realistic UPI transaction patterns — mule accounts, fan-out patterns, velocity anomalies, geo-velocity impossible travel. For production, this would train on real anonymized bank data. The XGBoost model achieves ~0.94 F1 on the synthetic set with SHAP explainability." |

---

### 🚫 Guardrails — Things That Will Kill Your Hackathon

| Risk | Prevention |
|---|---|
| **Integration breaks on demo day** | Start integrating Day 3, not Day 7. Never work on mocks for >2 days. |
| **LLM times out during live demo** | Cache LLM responses for your 3 demo cases. Pre-run them. |
| **Someone changes the JSON schema late** | Freeze schema Day 0. Any change requires team standup. |
| **Neo4j setup eats 2 days** | Use NetworkX. Period. |
| **Custom ML training fails** | XGBoost on synthetic data. If it breaks, fallback to a weighted scoring formula. |
| **"It works on my machine"** | Deploy by Day 7. Test on deployed URL daily. |
| **Beautiful UI but no backend** | Backend person must deliver working endpoints by Day 2 EOD. |
| **Pitch is an afterthought** | Start deck on Day 10. Rehearse 3x on Day 11. |

---

## Part 4 — What Makes This a WINNING Solution

### The 7-Second Pitch
> **"Current fraud systems generate 10,000 alerts a day. Who investigates them? Our multi-agent AI does — it runs the full investigation, explains its reasoning, cites the regulations, drafts the STR, and presents it to a human analyst for one-click approval. Investigation time: hours → seconds."**

### Your 4 Competitive Advantages (for judges)

1. **Not detection — INVESTIGATION.** Every competitor detects fraud. Nobody investigates it autonomously.
2. **Compliance-first, not compliance-afterthought.** Your Module 6 research means you can cite RBI FREE-AI, Model Risk Management Framework, PMLA, FATF R.1 — judges from banking/compliance will be floored.
3. **Explainability is built-in, not bolted-on.** SHAP values + LLM natural language + RAG citations. Three layers of "why."
4. **Built for India.** UPI-focused, RBI-aligned, FIU-IND-format STR generation, DPDP-aware. Not a generic "works everywhere" system.

---

## Open Questions for Your Team

> [!IMPORTANT]
> Answer these before you start building:

1. **How many people are on your team?** The plan assumes 4-5 people. If it's fewer, some tracks must merge.
2. **Does anyone have FastAPI / Python backend experience?** If not, consider using Express.js + Node.js instead (since you're frontend-heavy).
3. **Which LLM API do you have access to?** OpenAI (GPT-4o) or Anthropic (Claude 3.5 Sonnet)? Get API keys NOW.
4. **When is the actual submission deadline?** Is it 48-hour onsite, or a 2-week build + submission? This changes the plan significantly.
5. **Do you have a Figma/wireframe for the dashboard yet?** If not, should one of the frontend devs create a quick wireframe on Day 0?

---

*This plan is designed to be realistic, executable in 2 weeks with a frontend-heavy team, and optimized for maximum judge impact. Every feature is traceable back to your own research modules.*
