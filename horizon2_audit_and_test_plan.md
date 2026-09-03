# Safe Flow / Horizon — Deep Audit & Test Plan
Repo: `horizon2-main.zip` · Reviewed against `walkthrough.md`

---

## 1. Executive Summary

**What it is:** A fraud/AML investigation platform. React 19 + TanStack Router frontend talks to a FastAPI backend that runs an XGBoost+SHAP fraud model, a 4-step "agent pipeline" (score → context/graph → Gemini reasoning → decision), persists to SQLite, and drafts FIU-IND/PMLA compliance reports.

**Overall risk posture:** This is demo-quality software, not production-ready. The two biggest issues are:

1. **There is no authentication or authorization anywhere in the backend.** Every endpoint — including submitting an analyst decision that closes a case, or triggering an "AI investigation" — is open to anyone who can reach port 8000. The "Role-Based Access Control (Investigator/Manager/Administrator)" advertised in `walkthrough.md` is a `sessionStorage` value the browser sets for itself (`RoleContext.tsx`) with **zero server-side enforcement**. Anyone can open devtools and set their own role, or just call the API directly and pass any `analyst_id` they like.
2. **The "contextAgent" graph/fan-out-fan-in detection is dead code.** Both `routers/investigate.py` and `routers/graph.py` build a graph from a *single transaction* (one sender node, one receiver node, one edge) and then check `out_degree > 3` / `in_degree > 3` — which can never be true on a 1-edge graph. So every investigation's `graph_context.patterns` is always `[]`, silently. This directly undercuts the core "money-flow / mule-network detection" pitch of the product.

Beyond those two, there's a real **training/serving skew** bug in the ML feature pipeline (percentile-based thresholds at train time vs. hardcoded absolute thresholds at inference time), a **duplicate-case creation bug** in the investigation orchestrator, and an **inconsistent score-override rule** duplicated with different magic numbers in two files.

---

## 2. Repository Architecture

```
horizon2-main/
├── walkthrough.md, readme.md, implementation_plan.md   (docs)
├── Research/                                            (planning docs, not code)
├── backend/                                             FastAPI, Python
│   ├── main.py            — app bootstrap, CORS, router registration, model load
│   ├── state.py            — global AppState (model, metadata) singleton
│   ├── database.py         — raw sqlite3, table DDL, get_db() dependency, log_audit()
│   ├── routers/
│   │   ├── cases.py         — CRUD for cases, analyst decision endpoint
│   │   ├── score.py          — scoreAgent: XGBoost + SHAP single-transaction scoring
│   │   ├── graph.py           — contextAgent: graph endpoints (DB-backed + ad-hoc)
│   │   ├── investigate.py      — orchestrator: 4-agent pipeline, Gemini call, STR draft
│   │   ├── reports.py           — STR draft / full report read endpoints
│   │   └── audit.py              — read-only audit log
│   ├── agents/graph_agent/       — separately-tested graph builder (NOT used by investigate.py)
│   ├── train_enhanced_model.py    — trains XGBoost model, writes fraud_model.pkl + metadata
│   ├── generate_data.py, load_data.py — synthetic data + DB seeding
│   ├── fraud_model.pkl, model_metadata.json — committed model artifacts
│   └── tests/                      — 6 unit tests, all for agents/graph_agent only
└── frontend/                       React 19 + TanStack Router + Tailwind + shadcn/ui
    └── src/
        ├── context/RoleContext.tsx  — client-only "RBAC" (sessionStorage)
        ├── lib/api.ts                 — typed fetch client to localhost:8000
        └── routes/dashboard/...        — cases, audit, reports, roles, etc.
```

**Module dependency notes:**
- `investigate.py` imports `_engineer`, `FEATURE_COLS`, `_action_from_band` from `score.py` — but then **re-implements** its own copy of the severity-override logic with different constants (see §6, bug B3), rather than truly sharing it.
- `agents/graph_agent/` (builder.py/service.py/schemas.py) is a clean, tested, Pydantic-validated graph module — but it is **only wired to `POST /api/graph/analyze`**, an endpoint the frontend/orchestrator never calls. The actual pipeline (`investigate.py`) and `GET /api/graph/{case_id}` reimplement graph-building inline, badly (see bug B1).
- No auth middleware, no dependency-injected "current user," no session model anywhere in `backend/`.
- Each request opens a fresh `sqlite3.connect()` (no pooling, no WAL mode configured) — fine for a demo, a real concurrency risk under load.

---

## 3. Functional Inventory

| Area | Endpoint / Component | Behavior |
|---|---|---|
| Scoring | `POST /api/score/analyze` | Runs XGBoost on a single submitted transaction, returns score/band/SHAP |
| Orchestration | `POST /api/investigate/{transaction_id_or_case_id}` | Runs score → graph → Gemini (or fallback) → persists case + audit log |
| Graph (ad-hoc) | `POST /api/graph/analyze` | Validated multi-transaction graph builder (unused by the app) |
| Graph (case) | `GET /api/graph/{case_id}` | Builds a 2-node graph from the case's single transaction |
| Case CRUD | `GET/POST /api/cases`, `GET/PATCH /api/cases/{id}` | List/create/update cases |
| Analyst decision | `POST /api/cases/{id}/decision` | Records BLOCK/FLAG/DISMISS/ESCALATE decision, free-text `analyst_id` |
| Stats | `GET /api/cases/stats/summary` | Dashboard counts by status/band |
| Reports | `GET /api/reports/{id}/str-draft`, `.../full-report` | Formats stored case data into STR / report JSON |
| Audit | `GET /api/audit/` | Read-only audit trail, filterable by case |
| Frontend RBAC | `RoleContext.tsx` | Client-selected role, persisted in `sessionStorage`, no server check |
| Model training | `train_enhanced_model.py` | Loads combined CSVs, engineers features, trains XGBoost, writes artifacts |

---

## 4. Existing Test Assessment

- `backend/tests/` contains **6 tests total**, all against `agents/graph_agent/service.py`.
- That module is **not used by the live application** — the orchestrator (`investigate.py`) and the case-graph endpoint (`graph.py::get_transaction_graph`) both have their own inline, untested graph-building code.
- **Zero tests exist** for: `score.py` (the actual scoring logic used everywhere), `investigate.py` (the entire orchestration pipeline), `cases.py` (CRUD + decision endpoint), `database.py`, `audit.py`, `reports.py`, or the training/serving feature parity.
- The loose top-level scripts (`test_pipeline.py`, `test_direct_investigate.py`, `test_gemini.py`, `test_scenarios_score.py`) are ad-hoc manual scripts, not `pytest`-discoverable assertions — they print output for a human to eyeball rather than asserting expected values. They provide **no regression protection**.
- **Net effect:** the test suite currently verifies a module the product doesn't ship with, while the actual scoring/orchestration path — the part you're most worried about — has no automated coverage at all.

---

## 5. Requirement vs. Implementation Gaps

| Requirement (from `walkthrough.md`) | Expected Behavior | Actual Behavior | Mismatch | Severity |
|---|---|---|---|---|
| "Role-Based Access Control (Investigator, Manager, Administrator)" | Server enforces who can view/decide cases based on role | Role lives only in browser `sessionStorage`; backend has no auth/role checks at all | **Complete** — RBAC is decorative | **P0** |
| "audit_log (immutable)" | Audit entries cannot be altered after the fact | No DB constraint, trigger, or API prevents modification; only the *router* happens to expose no write/delete methods. A direct DB write or a future endpoint would break "immutability" silently | Partial — enforced by omission, not by design | P2 |
| "contextAgent → Graph analysis + velocity" | Detects multi-transaction patterns (fan-out/fan-in, mule velocity) per case | Builds a graph from exactly one transaction; fan-out/fan-in checks (`degree > 3`) are structurally unreachable | **Complete** — feature is non-functional | **P0** |
| "Multi-Agent Reasoning ... Gemini 3.7 Flash" | LLM produces the investigation narrative | Code calls model string `"gemini-3.6-flash"` (`investigate.py:120`) — inconsistent with docs, and unverified whether that model id is valid in the `google-genai` SDK being used | Naming/version mismatch — could mean silent fallback-only operation in practice | P2 |
| "Run Multi-Agent Investigation ... 200 OK (Score 99.8, Action BLOCK)" (verification table) | Repeatable, deterministic pipeline run | Score can be arbitrarily forced via the `severity` field baked into the stored transaction (see B3) — the demoed "99.8" may reflect the override floor, not genuine model output | Verification table doesn't distinguish AI-driven vs. rule-forced scores | P2 |
| Case decision is "human-in-the-loop" | A specific accountable analyst reviews and decides | `analyst_id` is an unauthenticated free-text string the client sends; anyone can submit a decision as anyone | **Complete** — no real accountability | **P0** |

---

## 6. Suspected Bug / Hypothesis List

| ID | Location | Suspected Bug | Why Suspicious | Test Method | Status | Severity |
|----|----------|----------------|-----------------|--------------|--------|----------|
| B1 | `routers/investigate.py:210-229`, `routers/graph.py:92-113` | Fan-out/fan-in detection is unreachable dead code | Graph is built from a single txn → max degree is 1; `> 3` check can never fire | Call `/api/investigate/{txn}` on any txn tied to a sender with many known transactions in the `transactions` table; confirm `patterns` is always `[]` | **Confirmed by code inspection** | **P0** |
| B2 | `train_enhanced_model.py:93-96` vs `score.py:80-81` / `investigate.py` inline copy | Training/serving skew on `is_large_amount` / `is_very_large` | Training computes these as **90th/99th percentile of the training batch** (data-dependent, likely far below ₹200k/₹1M); serving hardcodes **absolute** ₹200,000 / ₹1,000,000 cutoffs. Also `type_encoded` NaN-fill differs: training fills with `5`, serving fills with `3` | Feed a transaction near ₹200k and near the true training percentile boundary through both `engineer_features()` (offline) and `_engineer()` (API) and diff the resulting feature vectors | **Confirmed by code inspection** | **P0 (silently degrades every SHAP explanation and every risk score)** |
| B3 | `score.py:119-122` vs `investigate.py:186-189` | Duplicated severity-override rule with **different magic numbers** in each file | `score.py`: CRITICAL floor 0.85, HIGH floor 0.68. `investigate.py`: CRITICAL floor 0.88, HIGH floor 0.72. Same transaction can get two different "risk scores" depending on which endpoint scored it | Score the same transaction via `POST /api/score/analyze` and via `POST /api/investigate/{id}`, compare `risk_score` | **Confirmed by code inspection** | P1 |
| B4 | `score.py` / `investigate.py` severity override | Client- and data-controlled `severity` field silently overrides the ML model's probability, but the SHAP explanation shown to the analyst is computed from the **pre-override** probability | `explainer.shap_values(X)` is called on the *original* model output, before the `proba = max(proba, 0.85)` override — so the "why" (top factors) can visibly disagree with the "what" (score/band shown), e.g. a MEDIUM-looking SHAP breakdown next to a CRITICAL/BLOCK verdict | Craft a txn where the model naturally predicts ~0.4 but `severity="CRITICAL"`; confirm score becomes 85+ while shap top_factors still reflect a 0.4-probability explanation | **Confirmed by code inspection** | P1 |
| B5 | `routers/investigate.py:146-161` | Duplicate case creation — no idempotency on `transaction_id` | Lookup only checks `WHERE case_id = ?` against the path param. If you call `/api/investigate/TXN123` twice, passing the **transaction_id** both times (not the returned case_id), it never matches an "existing_case" and creates a **second** case row for the same transaction, since `cases.transaction_id` has no `UNIQUE` constraint | Call the endpoint twice with the same raw transaction_id (not the case_id from the first response); check `SELECT COUNT(*) FROM cases WHERE transaction_id=?` | **Confirmed by code inspection** | P1 |
| B6 | `routers/cases.py:208-234` (`update_case`) | Silent no-op when clearing a field to empty string | `if body.status:` / `if body.investigation_report:` use truthiness, so passing `""` to intentionally blank a field is silently ignored instead of applied | PATCH a case with `{"investigation_report": ""}`, confirm DB value is unchanged instead of cleared | **Confirmed by code inspection** | P3 |
| B7 | `routers/cases.py:208-234` | No validation on `status` in `PATCH /cases/{id}` | Unlike the `/decision` endpoint (which whitelists 4 decisions), `PATCH` accepts any arbitrary string into `status`, producing states the rest of the UI/logic doesn't recognize (e.g. filters in `list_cases` by `status` would just silently return nothing) | `PATCH /api/cases/{id}` with `{"status": "banana"}`; confirm it's accepted and then confirm dashboard filters/queue break for that case | **Confirmed by code inspection** | P2 |
| B8 | `main.py:51-57` | CORS: `allow_origins=["*"]` + `allow_credentials=True` | This combination is invalid per the Fetch/CORS spec — browsers will reject credentialed cross-origin requests here — but it also signals nobody has thought through the actual origin allowlist; per `.env.example`, `CORS_ORIGINS` is meant to be configurable but is **never read** in `main.py` (the env var is dead/unused) | Attempt a credentialed cross-origin fetch from a non-listed origin; also grep confirms `CORS_ORIGINS` env var is never referenced in code | **Confirmed by code inspection** | P2 |
| B9 | Entire `backend/` | No authentication/authorization on any route | No auth dependency, no token check, no session — grep for auth/jwt/session/login returns nothing in `routers/`, `main.py`, `database.py` | Call any endpoint (e.g. `/api/cases/{id}/decision`) with no credentials from a fresh client; confirm 200 OK | **Confirmed by code inspection** | **P0** |
| B10 | `frontend/src/context/RoleContext.tsx` | Client-side-only role selection | Role stored in `sessionStorage`, defaulted to `investigator`, freely switchable via `setRole()`/devtools with zero backend correlation | In browser console: `sessionStorage.setItem('smart-horizon-role','administrator')`, reload; confirm admin-only UI appears with no server check | **Confirmed by code inspection** | **P0** (compounds B9) |
| B11 | `database.py` | No foreign keys / referential integrity | `cases.transaction_id`, `transactions.sender_id`/`receiver_id` are plain TEXT with no `FOREIGN KEY` constraints and SQLite's `PRAGMA foreign_keys` is never enabled | Create a case referencing a nonexistent `transaction_id`; confirm insert succeeds, then `GET /api/cases/{id}` returns `"transaction": null` rather than an error | Not yet reproduced live — needs execution | P2 |
| B12 | `routers/investigate.py:114-130` | LLM failure is swallowed silently, and the model name looks wrong | Any Gemini exception is caught and logged only to stdout; the analyst sees a competent-looking fallback report with no indication AI reasoning didn't actually run. Also uses model id `"gemini-3.6-flash"`, inconsistent with docs' "Gemini 3.7 Flash" and with `test_gemini.py` — worth confirming this model id is even valid against the installed `google-genai` SDK | Force `GEMINI_API_KEY` unset or invalid, call `/api/investigate/{id}`, confirm response looks identical in shape to a real AI response with no `"ai_generated": false` flag anywhere for the frontend to check | **Confirmed by code inspection**, need live run to confirm the model-id validity | P2 |
| B13 | `agents/graph_agent/service.py` vs the live pipeline | Two parallel, divergent graph implementations | The well-tested `analyze_transactions()` is dead relative to the app's actual flow; a future maintainer fixing "the graph agent" would likely edit the tested-but-unused module and see no effect in the product | Trace call sites of `analyze_transactions` vs. inline graph code in `investigate.py`/`graph.py` | **Confirmed by code inspection** | P2 |

---

## 7. Master Testing Strategy

Given the findings so far, effort should be weighted: **~50% security/authz, ~35% scoring-pipeline correctness, ~15% everything else** — this matches both what the code shows and what you flagged as your concern.

1. **Lock down the P0s first** (auth/RBAC, dead graph logic) — these aren't edge cases, they're "the advertised feature doesn't exist" or "there is no security boundary at all."
2. **Unit-test the feature engineering parity** between `train_enhanced_model.py::engineer_features` and `score.py::_engineer` — this is the fastest way to catch B2-style skew permanently (a single parametrized test comparing outputs on the same synthetic row would have caught this).
3. **Contract-test the two scoring entry points** (`/api/score/analyze` vs `/api/investigate/{id}`) against the same transaction to catch divergence like B3/B4.
4. **Integration-test the full orchestration** (`POST /api/investigate/{id}` twice, with a case_id and with a raw transaction_id) to catch idempotency bugs like B5.
5. **Add negative/security tests as first-class citizens**, not an afterthought — right now they don't exist at all.

---

## 8. Detailed Test Cases

### A. Unit — Feature Engineering Parity (highest priority)

**TC-U01**
- Priority: P0
- Area: `score.py::_engineer` vs `train_enhanced_model.py::engineer_features`
- Objective: Confirm `is_large_amount`/`is_very_large` boundaries match between train and serve
- Input: A synthetic transaction with `amount` = the training set's actual 90th percentile value (compute once from `drivematerial` data), and another at ₹200,000 exactly
- Steps: Run both feature functions on identical input rows; diff the two resulting feature vectors
- Expected: Identical feature values for every column
- Failure Indicator: `is_large_amount`/`is_very_large` disagree between the two implementations
- Bug Hypothesis: B2
- Code Location: `backend/score.py:80-81`, `backend/train_enhanced_model.py:93-96`
- Risk: Every deployed prediction is scored on features that don't match what the model was trained on — silent accuracy/explainability degradation with no error thrown

**TC-U02**
- Priority: P1
- Area: `_engineer` — unmapped `type` value
- Input: `{"type": "UNKNOWN_RAIL", ...}`
- Steps: Call `_engineer()` directly
- Expected/Actual: Serve-side defaults `type_encoded` to `3` (TRANSFER); train-side defaults to `5` (no such class existed in training) — divergent behavior for out-of-vocabulary types
- Bug Hypothesis: B2 (extension)
- Risk: An out-of-vocabulary transaction type is silently mis-scored as a TRANSFER (index 3) at serve time even though the model never saw a "5" class in training either, so this is doubly undefined

**TC-U03**
- Priority: P2
- Area: `_engineer` — division-by-near-zero
- Input: `oldbalanceOrg = -1.0` (adversarial/malformed input — no validation prevents negative balances)
- Expected: Reasonable handling or explicit rejection
- Actual: `amount / (oldbalanceOrg + 1.0)` → division by zero if `oldbalanceOrg == -1`, producing `inf`/`NaN` fed straight into XGBoost
- Risk: Unhandled `inf`/`NaN` reaching `model.predict_proba` — behavior of XGBoost on `NaN` inputs should be verified explicitly (it does have native NaN handling, but should be confirmed to fail safe, not silently return a plausible-looking but meaningless score)

### B. Contract Tests — Cross-Endpoint Scoring Consistency

**TC-C01**
- Priority: P0
- Area: `/api/score/analyze` vs `/api/investigate/{id}`
- Objective: Confirm the two independent severity-override implementations don't diverge
- Steps: Store a transaction with `severity="HIGH"` and a model-predicted probability near 0.5; score via `/api/score/analyze` directly, and separately trigger `/api/investigate/{txn_id}`
- Expected: Same `risk_score`
- Actual (predicted from code): `/score/analyze` floors to 0.68 → 68.0; `/investigate` floors to 0.72 → 72.0. **Different scores for the identical transaction depending on entry point.**
- Bug Hypothesis: B3
- Risk: Analysts see inconsistent scores for the same transaction depending on which UI path/report they're viewing; undermines trust in the "AI score"

**TC-C02**
- Priority: P1
- Area: SHAP explanation vs. displayed score after severity override
- Steps: Construct a transaction with `severity="CRITICAL"` and features that the model would otherwise score ~0.3-0.4 (LOW/MEDIUM); call `/api/investigate/{id}`
- Expected: `top_factors` (SHAP) should explain why the score is CRITICAL/BLOCK
- Actual: `top_factors` reflects the model's *original* ~0.35 probability breakdown — likely dominated by LOW-risk-consistent factors — displayed next to a CRITICAL/BLOCK verdict
- Bug Hypothesis: B4
- Risk: An investigator reading the "why" panel gets an explanation that doesn't match the actual decision — actively misleading in a regulated compliance workflow

### C. Integration — Orchestrator Idempotency

**TC-I01**
- Priority: P1
- Area: `POST /api/investigate/{transaction_id}`
- Objective: Confirm repeated investigation of the same transaction doesn't create duplicate cases
- Preconditions: A transaction `TXN-DUP-1` exists with no case yet
- Steps: 1) `POST /api/investigate/TXN-DUP-1` → note returned `case_id`. 2) `POST /api/investigate/TXN-DUP-1` again (same raw transaction id, not the case_id from step 1).
- Expected: Second call updates the same case
- Actual (predicted): Second call creates a **new** case row (new `case_id`), because lookup only checks `cases.case_id = transaction_id`, never `cases.transaction_id = transaction_id`
- Bug Hypothesis: B5
- Code Location: `investigate.py:145-161`
- Risk: Duplicate cases inflate dashboard stats, confuse analysts, and could cause double STR filings for one real-world transaction

**TC-I02**
- Priority: P2
- Area: `PATCH /api/cases/{id}` field clearing
- Steps: `PATCH` a case with `{"investigation_report": ""}`
- Expected: `investigation_report` cleared
- Actual: Unchanged, due to truthiness check
- Bug Hypothesis: B6

### D. Security / AuthZ

**TC-S01**
- Priority: P0
- Area: All endpoints
- Objective: Confirm there is no authentication barrier
- Steps: From an unauthenticated client (no cookies, no headers), call `POST /api/cases/{any_case_id}/decision` with `{"analyst_id": "anyone", "decision": "APPROVE_BLOCK", "notes": "test"}`
- Expected: 401/403
- Actual: 200 OK, decision recorded and audit-logged as if it were legitimate
- Bug Hypothesis: B9
- Risk: **Critical** — anyone with network access to port 8000 can close/approve/block/dismiss any fraud case, impersonating any analyst by name, with an immutable-looking audit trail that has no real identity verification behind it

**TC-S02**
- Priority: P0
- Area: Frontend role gating
- Steps: In browser devtools, run `sessionStorage.setItem('smart-horizon-role', 'administrator')` then reload
- Expected: Admin UI blocked unless authenticated as an admin
- Actual: Full "System Administration" UI unlocked instantly
- Bug Hypothesis: B10

**TC-S03**
- Priority: P2
- Area: CORS
- Steps: Send a credentialed fetch from a disallowed origin (e.g. `evil.example.com`) directly against the API (bypassing the browser CORS check by using a non-browser client, or check via curl `Origin` header reflection)
- Expected: Origin rejected per `CORS_ORIGINS` in `.env.example`
- Actual: `main.py` never reads `CORS_ORIGINS`; hardcodes `allow_origins=["*"]`
- Bug Hypothesis: B8

**TC-S04**
- Priority: P2
- Area: Input validation / injection surface
- Steps: Submit `analyst_notes` or `fraud_reason` containing HTML/script payloads; confirm they're stored raw and rendered later in the STR draft / dashboard without escaping
- Objective: Confirm whether the React frontend escapes this by default (likely yes, JSX auto-escapes) but flag if any `dangerouslySetInnerHTML` or raw string interpolation is used to render `investigation_report`/`str_draft` (LLM-controlled and user-controlled fields)
- Note: Not yet confirmed live — grep `dangerouslySetInnerHTML` across `frontend/src` before closing this out

### E. Business Logic — Graph/Context Agent

**TC-B01**
- Priority: P0
- Area: `investigate.py` contextAgent step, `graph.py::get_transaction_graph`
- Objective: Confirm fan-out/fan-in detection actually fires for a real mule pattern
- Preconditions: Seed the `transactions` table with one sender account making 5+ outbound transfers to different receivers (a textbook fan-out mule pattern)
- Steps: Call `/api/investigate/{one_of_those_txn_ids}`
- Expected: `graph_context.patterns` includes a `FAN_OUT` entry
- Actual: `patterns` is `[]`, because the graph is built from only the single transaction being investigated, never the sender's full transaction history
- Bug Hypothesis: B1
- Risk: **Critical for the product's core value proposition** — the platform cannot detect the exact pattern (fund fan-out through mule accounts) it advertises detecting

### F. Regression Suite (once fixes land)

- Re-run TC-U01/U02 whenever `FEATURE_COLS`, `_engineer`, or `engineer_features` change.
- Re-run TC-C01/C02 whenever the severity-override thresholds change in either file.
- Re-run TC-I01 whenever `investigate.py`'s case-lookup logic changes.
- Re-run TC-B01 whenever graph-building logic changes in either `investigate.py` or `graph.py`.
- Add a CI gate: fail the build if `score.py` and `train_enhanced_model.py` feature-threshold constants diverge (a simple constants-equality test would suffice).

---

## 9. Priority Matrix

**P0 — Critical**
- B1: Fan-out/fan-in detection is dead code (core feature doesn't work)
- B2: Training/serving feature skew (every score is subtly wrong)
- B9: Zero authentication on any backend endpoint
- B10: RBAC is client-side only / cosmetic

**P1 — High**
- B3: Duplicated severity-override logic with inconsistent constants across endpoints
- B4: SHAP explanation can contradict the displayed (overridden) score
- B5: Duplicate case creation on repeated investigation calls

**P2 — Medium**
- B6/B7: `PATCH /cases/{id}` field-clearing and status-validation gaps
- B8: Invalid/unused CORS configuration
- B11: No referential integrity in SQLite schema
- B12: Silent LLM-failure fallback with no "AI vs. fallback" flag surfaced to the analyst
- B13: Dead, well-tested graph module vs. live, untested inline graph code (maintenance trap)

**P3 — Low**
- Truthiness-based optional-field handling in a couple of PATCH endpoints (part of B6)

---

## 10. Bug Detection Checklist

- [ ] Confirmed: no `auth`/`jwt`/`session`/`login` logic anywhere in `backend/` (grep clean)
- [ ] Confirmed: `RoleContext.tsx` role is client-only, `sessionStorage`-backed
- [ ] Confirmed: fan-out/fan-in graph logic operates on single-transaction graphs in two places
- [ ] Confirmed: `is_large_amount`/`is_very_large` computed differently at train vs. serve time
- [ ] Confirmed: severity-override floors differ between `score.py` (0.85/0.68) and `investigate.py` (0.88/0.72)
- [ ] Confirmed: SHAP values computed pre-override, not post-override
- [ ] Confirmed: no `UNIQUE` constraint on `cases.transaction_id`; investigate.py only checks by `case_id`
- [ ] Confirmed: `CORS_ORIGINS` env var defined in `.env.example` but never read in `main.py`
- [ ] Confirmed: test suite (6 tests) only covers the unused `agents/graph_agent` module
- [ ] Not yet run live: TC-S01, TC-S04, TC-I01, TC-B01, TC-U01 (need the actual environment spun up — see §11)

---

## 11. Recommended Testing Order

1. **B1 (dead graph logic)** and **B9/B10 (no auth)** — confirm live with a running instance; these are the highest-impact, easiest-to-verify findings and should shape any remediation plan before touching anything else.
2. **B2 (train/serve skew)** — write the parity unit test first; it's cheap and will likely surface more divergences than just the two documented here.
3. **B3/B4 (score inconsistency + SHAP mismatch)** — verify via TC-C01/C02 once you have `GEMINI_API_KEY` or accept the fallback path.
4. **B5 (duplicate cases)** — quick to reproduce, meaningful data-integrity risk.
5. Everything else in the P2 bucket, roughly in the order listed.

---

## 12. Automation Opportunities

- **Backend:** `pytest` is already a dependency; add `httpx.AsyncClient` + FastAPI's `TestClient` for endpoint-level integration tests (TC-C01, TC-I01, TC-S01). Add `pytest-mock`/`responses` to simulate Gemini failures for TC-C02/B12 without live API calls.
- **Feature parity:** A single parametrized `pytest` module that imports both `_engineer` (score.py) and `engineer_features` (train_enhanced_model.py) on the same fixture rows would make B2 permanently regression-proof — this is the highest-leverage single test to add.
- **Security:** A lightweight test that asserts every router requires *some* dependency-injected auth check (even a placeholder) would catch B9-style regressions the moment auth is eventually added and someone forgets a route.
- **Frontend:** No test files were found under `frontend/src` at all — consider Vitest + React Testing Library for `RoleContext` and the case decision flow once server-side auth exists to test against.
- **CI:** None of this appears to run in CI currently (no `.github/workflows` found in the archive) — wiring `pytest` into CI would be a prerequisite for any of the above to have ongoing value.

---

## What I did *not* do
Per your instructions, I have not modified any code. Everything above is either confirmed directly from reading the source (marked "Confirmed by code inspection") or a concrete, reproducible test case to run against a live instance to confirm the predicted behavior (marked "Not yet reproduced live"). Let me know which of these you'd like me to actually go fix, starting with the P0s if you agree with the prioritization.
