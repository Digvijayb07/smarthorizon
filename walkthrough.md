# 🚀 Safe Flow — Merged Platform Walkthrough

## Overview

We have merged the best of both repositories into a unified, demo-ready autonomous financial crime investigation platform:

- **Frontend (from `horizon2`)**: Production-grade React 19 + TanStack Router + Tailwind v4 + shadcn/ui (46 components) + Role-Based Access Control (Investigator, Manager, Administrator) + 19-section landing page.
- **Backend & ML (from `horizon`)**: FastAPI backend on port 8000 with XGBoost + SHAP explainability model trained on 205k rows, multi-agent orchestrator (`scoreAgent`, `contextAgent`, `reasonAgent`, `decisionAgent`) powered by Gemini 3.7 Flash, SQLite persistent database with audit trail, and FIU-IND / PMLA compliance reporting.

---

## 🔗 Integrated Architecture

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

## 🛠️ Key Milestones Completed

### 1. Unified Project Structure
- `frontend/`: Adopted the full TypeScript codebase from `horizon2`.
- `backend/`: Kept our operational FastAPI backend with model serving, database, and agents.
- `backend/configs/`: Imported `thresholds.json` and `features.json` from `smarthoriagent/configs/`.

### 2. Live API Service Layer (`frontend/src/lib/api.ts`)
- Configured type-safe API client communicating with `http://localhost:8000`.
- Typed interfaces for `BackendCase`, `ScoreResponse`, `InvestigationResponse`, `AuditLogEntry`.

### 3. Integrated Pages & Components
- **Case Queue (`/dashboard/cases`)**: Live query from `GET /api/cases/` with risk band filtering, search, and real-time backend status indicators.
- **Case Workspace (`/dashboard/cases/$caseId`)**:
  - Top header with case risk score, status, and **"Run AI Investigation"** button.
  - Interactive **AgentStatus** pipeline visualization (`orchestrator` → `data` → `risk` → `reason`).
  - **AI Investigation Report** powered by Gemini with full transaction breakdown and regulatory references.
  - **FIU-IND Suspicious Transaction Report (STR)** draft viewer with one-click copy.
  - **Analyst Decision & Maker-Checker** actions (*Block & Report*, *Flag for Monitoring*, *Dismiss*, *Escalate*) that record immediately to the backend SQLite `audit_log`.
- **System Audit Trail (`/dashboard/audit` & `/dashboard/audit-logs`)**: Live, immutable audit log table displaying all actor actions, timestamps, and target cases.
- **Reports Repository (`/dashboard/reports`)**: Live case reports with export capabilities and direct links to workspace investigation packages.
- **Dashboard Stats (`/dashboard`)**: Wired metric cards to `GET /api/cases/stats/summary`.

---

## 🧪 Verification & End-to-End Test

| Action | Endpoint / Page | Status |
|---|---|---|
| **Frontend Dev Server** | `http://localhost:8080` | ✅ Running |
| **Backend API Server** | `http://localhost:8000` | ✅ Running (`/health` OK) |
| **List Cases** | `GET /api/cases/?limit=50` | ✅ 200 OK |
| **Get Case Details** | `GET /api/cases/FC-20260815-83D0B1` | ✅ 200 OK |
| **Run Multi-Agent Investigation** | `POST /api/investigate/FC-20260815-83D0B1` | ✅ 200 OK (Score 99.8, Action BLOCK) |
| **Submit Analyst Decision** | `POST /api/cases/FC-20260815-83D0B1/decision` | ✅ 200 OK (Committed to SQLite) |
| **Audit Log Trail** | `GET /api/audit/` | ✅ 200 OK (Logged with timestamp) |

---

## 🚀 Running the Project

1. **Backend**:
   ```bash
   cd backend
   python -m uvicorn main:app --port 8000
   ```
2. **Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   Open `http://localhost:8080` in your browser.
