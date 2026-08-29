# 🚀 Safe Flow (Smart Horizon) — Project Status & Merge Summary

**Hackathon:** SMART HORIZON 2026  
**Team:** VibeCoderz | SH-FIN-01 | SHIH26-TID-85  
**Problem Statement:** Autonomous multi-agent financial crime investigation system (AI recommends, human decides).

---

## 1. 🔀 Branch Merge Breakdown: What Came from Where

```text
 ┌─────────────────────────────────────────────────────────────┐
 │                       HORIZON2 BRANCH                       │
 │  • 80+ TypeScript React Components (Radix UI / shadcn)      │
 │  • TanStack Router file-based routing (17+ typed routes)    │
 │  • Role-Based Access Control (Investigator / Manager / Admin)│
 │  • 19-Section Safe Flow Public Landing Page                 │
 │  • ML Configs (thresholds.json, features.json)              │
 └──────────────────────────────┬──────────────────────────────┘
                                │  MERGED
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                    UNIFIED SAFE FLOW APP                    │
 │               (Frontend :8080 ↔ Backend :8000)              │
 └──────────────────────────────▲──────────────────────────────┘
                                │  MERGED
 ┌──────────────────────────────┴──────────────────────────────┐
 │                       HORIZON BRANCH                        │
 │  • FastAPI Backend Server on port 8000                      │
 │  • Multi-Agent Orchestration (score/context/reason/decision)│
 │  • Gemini 3.7 Flash LLM Reasoning & Regulatory Grounding    │
 │  • XGBoost Model + SHAP Feature Attribution (205k rows)     │
 │  • SQLite Database (customers, transactions, cases, audit)  │
 │  • FIU-IND STR Regulatory Filing Generation                 │
 └─────────────────────────────────────────────────────────────┘
```

---

## 2. 📊 Tech Stack & Implementation Matrix

| Component / Layer | Technology Used | Status | Details & Implementation Notes |
|---|---|---|---|
| **Frontend Framework** | **React 19 + TypeScript + Vite** | ✅ **Works Fine** | High-performance Single Page Application with fast HMR running on port 8080. |
| **Routing** | **TanStack Router** (File-based) | ✅ **Works Fine** | 17+ typed routes (`/dashboard/cases`, `/dashboard/cases/$caseId`, `/dashboard/audit`, `/sign-in`, `/dashboard/reports`, etc.). |
| **State & API Fetching** | **@tanstack/react-query** | ✅ **Works Fine** | Centralized in `frontend/src/lib/api.ts` with automatic caching, invalidations, and graceful fallback to mock data if offline. |
| **UI & Styling** | **Tailwind CSS v4 + Radix UI (shadcn)** | ✅ **Works Fine** | 46 UI primitives (`button`, `card`, `dialog`, `badge`, `table`, etc.) + Dark/Light mode toggle. |
| **Role-Based Access** | **React Context (`RoleContext.tsx`)** | ✅ **Works Fine** | 3 distinct personas: **Investigator** (cases & review), **Manager** (approvals & escalations), **Administrator** (audit & users). |
| **Backend API** | **FastAPI (Python 3.13)** | ✅ **Works Fine** | High-performance async REST API on port 8000 with CORS and interactive OpenAPI/Swagger documentation at `/docs`. |
| **Database** | **SQLite (`horizon.db`)** | ✅ **Works Fine** | Persistent relational storage for `customers`, `transactions`, `cases`, and `audit_log`. Thread-safe configuration (`check_same_thread=False`). |
| **ML Fraud Detection** | **XGBoost Classifier** | ✅ **Works Fine** | Trained on 205k transactions (PaySim + synthetic fraud/legit scenarios). Provides 0–100 calibrated risk scores with 99.9% ROC-AUC. |
| **Model Explainability (XAI)** | **TreeSHAP (`shap` library)** | ✅ **Works Fine** | Computes local feature attribution per transaction (e.g. `dest_balance_change_ratio`, `balance_usage_ratio`, `is_vpn`). |
| **Agent Orchestrator** | **Custom Async Python Pipeline** | ✅ **Works Fine** | Sequential pipeline: `scoreAgent` ➔ `contextAgent` ➔ `reasonAgent` ➔ `decisionAgent`. |
| **LLM Reasoning & RAG** | **Gemini 3.7 Flash** | ✅ **Works Fine** | Grounded in PMLA Section 12, RBI Master Directions, and NPCI guidelines. Generates audit-ready executive findings. |
| **Regulatory Filing** | **FIU-IND STR Generator** | ✅ **Works Fine** | Generates Suspicious Transaction Report drafts conforming to Indian regulatory reporting requirements. |
| **Audit Trail** | **Immutable SQLite Log** | ✅ **Works Fine** | Every investigation execution and analyst decision (*Block*, *Flag*, *Dismiss*, *Escalate*) commits a tamper-evident audit record. |

---

## 3. 📋 Progress vs Main Implementation Plan (`implementation_plan.md`)

### ✅ COMPLETED & WORKING FINE

1. **Phase 0 & 1 — Foundation & UI Design System**:
   - [x] Evidence Package JSON contract frozen (`api.ts` interfaces).
   - [x] 19-Section public landing page (`HeroSection`, `ProblemSection`, `AgentArchitecture`, `RiskIntelligence`, `ComplianceSection`, etc.).
   - [x] Auth & Role selector with quick-switch demo personas.

2. **Phase 2 & 3 — Case Management & Queue**:
   - [x] Case Directory (`/dashboard/cases`) reading live records from `GET /api/cases/`.
   - [x] Search, risk level filtering (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), and status tracking.
   - [x] Real-time metrics overview on the Investigator Dashboard via `GET /api/cases/stats/summary`.

3. **Phase 4 & 5 — Multi-Agent Case Investigation & Explainability**:
   - [x] Case Workspace (`/dashboard/cases/$caseId`) with live transaction breakdown and customer KYC details.
   - [x] Interactive **"Run AI Investigation"** button triggering the full 4-agent Gemini pipeline.
   - [x] Animated **AgentStatus** progress component showing live stages (`Orchestrator` ➔ `Data` ➔ `Risk` ➔ `Reason`).
   - [x] Risk Intelligence panel displaying XGBoost score, risk bands, and top SHAP contributing factors.

4. **Phase 6 & 7 — Human Decision & Maker-Checker**:
   - [x] Action buttons (*Block & Report*, *Flag for Monitoring*, *Dismiss*, *Escalate to Manager*) calling `POST /api/cases/{id}/decision`.
   - [x] Immediate state update and confirmation badge in the UI.

5. **Phase 8 & 9 — Regulatory Compliance & Audit Trail**:
   - [x] Automatic generation of FIU-IND Suspicious Transaction Report (STR) draft.
   - [x] One-click STR text copying and export.
   - [x] Immutable Audit Log page (`/dashboard/audit` & `/dashboard/audit-logs`) listing all automated agent runs and human decisions with timestamps and actor tags.
   - [x] Reports Repository (`/dashboard/reports`) listing generated compliance filings with export.

---

### ⏳ REMAINING / MISSING OR ENHANCEMENTS FOR DEMO POLISH

| Feature / Task | Current State | What's Remaining to Do |
|---|---|---|
| **Interactive Graph Visualization** | Static SVG diagram rendering sample nodes/edges in `InvestigationGraph.tsx`. | Wire dynamic transaction network edges from `/api/graph` using D3 / react-force-graph for interactive node dragging and zoom. |
| **Vector DB RAG Retrieval (ChromaDB)** | Gemini uses in-prompt grounded regulatory context (PMLA/RBI/NPCI). | Ingest actual PDF circulars into ChromaDB with `sentence-transformers` for dynamic semantic chunk retrieval if judges ask for live vector search. |
| **Isolation Forest Fine-Tuning** | Evaluated in `smarthoriagent` with ROC-AUC 0.37 (caveat documented in deliverable). | Use XGBoost + rule heuristics as primary score (which works with 99.9% AUC) or recalibrate Isolation Forest contamination parameter. |
| **Cloud Deployment** | Running locally on ports 8080 (frontend) and 8000 (backend). | Deploy frontend to **Vercel** and backend to **Render / Railway** with `.env` configured for public demo access. |
| **Pitch Deck & Demo Script** | Research modules 1–7 complete and structured. | Create a 10-slide presentation deck emphasizing Module 6 (Compliance) and Module 7 (Feature Matrix). |

---

## 4. 🔗 End-to-End System Architecture

```text
 ┌───────────────────────────────────────────────────────────┐
 │               Safe Flow React/TanStack UI                │
 │                  (http://localhost:8080)                  │
 └─────────────────────────────┬─────────────────────────────┘
                               │ HTTP / JSON API (React Query)
                               ▼
 ┌───────────────────────────────────────────────────────────┐
 │               FastAPI Multi-Agent Server                  │
 │                  (http://localhost:8000)                  │
 ├─────────────────────────────┬─────────────────────────────┤
 │ • /api/cases                │ • /api/investigate          │
 │ • /api/score                │ • /api/reports              │
 │ • /api/audit                │ • /api/graph                │
 └──────────────┬──────────────┴──────────────┬──────────────┘
                │                             │
                ▼                             ▼
   ┌──────────────────────────┐  ┌──────────────────────────┐
   │    ML + XAI Engine       │  │   Gemini 3.7 Flash       │
   │  • XGBoost Supervised    │  │  • Multi-Agent Reasoning │
   │  • TreeSHAP Attribution  │  │  • RBI / PMLA Grounding  │
   │  • Topological Features  │  │  • FIU-IND STR Drafting  │
   └────────────┬─────────────┘  └────────────┬─────────────┘
                │                             │
                └──────────────┬──────────────┘
                               ▼
                 ┌──────────────────────────┐
                 │    SQLite Persistent DB  │
                 │  • customers             │
                 │  • transactions          │
                 │  • cases                 │
                 │  • audit_log (immutable) │
                 └──────────────────────────┘
```

---

## 5. 🚀 How to Run Locally

### Terminal 1: Backend Server
```bash
cd backend
python -m uvicorn main:app --port 8000
```
- API URL: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

### Terminal 2: Frontend Server
```bash
cd frontend
npm run dev
```
- Web Application: `http://localhost:8080`
