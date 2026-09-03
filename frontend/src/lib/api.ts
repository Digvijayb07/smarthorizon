/**
 * API Service Layer
 * =================
 * Centralizes all communication between the React frontend and the
 * FastAPI backend at http://localhost:8000/api.
 *
 * Every function returns typed data matching our investigation types.
 * All requests include the JWT bearer token from the auth context.
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ── Auth token management ──────────────────────────────────────────────────

let _authToken: string | null = null;

export function setAuthToken(token: string | null) {
  _authToken = token;
  if (token) {
    sessionStorage.setItem("horizon-auth-token", token);
  } else {
    sessionStorage.removeItem("horizon-auth-token");
  }
}

export function getAuthToken(): string | null {
  if (_authToken) return _authToken;
  if (typeof window !== "undefined") {
    _authToken = sessionStorage.getItem("horizon-auth-token");
  }
  return _authToken;
}

// ── Generic fetch helper ─────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const token = getAuthToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options?.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    // Token expired or invalid — clear it
    setAuthToken(null);
    throw new Error("Session expired. Please sign in again.");
  }

  if (!res.ok) {
    const body = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${body}`);
  }

  return res.json() as Promise<T>;
}

// ── Types matching backend response shapes ───────────────────────────────────

export interface BackendCase {
  case_id: string;
  transaction_id: string;
  status: string;
  risk_score: number;
  risk_band: string;
  recommended_action: string;
  opened_at: string;
  updated_at: string;
  closed_at: string | null;
  analyst_id: string | null;
  analyst_decision: string | null;
  analyst_notes: string | null;
  investigation_report: string | null;
  str_draft: string | null;
  transaction?: BackendTransaction | null;
  sender?: BackendCustomer | null;
  receiver?: BackendCustomer | null;
}

export interface BackendTransaction {
  transaction_id: string;
  sender_id: string;
  receiver_id: string;
  amount: number;
  currency: string;
  type: string;
  channel: string;
  timestamp: string;
  sender_balance_before: number;
  sender_balance_after: number;
  receiver_balance_before: number;
  receiver_balance_after: number;
  is_flagged: number;
  flag_reason: string | null;
}

export interface BackendCustomer {
  customer_id: string;
  name: string;
  email: string;
  phone: string;
  account_type: string;
  kyc_status: string;
  risk_rating: string;
  created_at: string;
  pep_status: number;
  sanctions_hit: number;
}

export interface CaseListResponse {
  cases: BackendCase[];
  total: number;
  limit: number;
  offset: number;
}

export interface CaseStatsResponse {
  total: number;
  by_status: Array<{ status: string; count: number }>;
  by_band: Array<{ risk_band: string; count: number }>;
}

export interface ScoreResponse {
  transaction_id: string;
  risk_score: number;
  risk_band: string;
  model_probability: number;
  probability: number;
  recommended_action: string;
  top_factors: Array<{
    feature: string;
    shap_value: number;
    impact: string;
    description: string;
  }>;
  shap_values: Record<string, number>;
  rule_adjustments: string[];
  model_version: string;
}

export interface InvestigationResponse {
  case_id: string;
  transaction_id: string;
  risk_score: number;
  model_probability: number;
  risk_band: string;
  recommended_action: string;
  investigation_report: string;
  str_draft: string;
  ai_generated: boolean;
  reasoning_source: string;
  rule_adjustments: string[];
  graph_context: {
    nodes: Array<{ id: string; type?: string }>;
    links: Array<{
      source: string;
      target: string;
      amount: number;
      transaction_id: string;
    }>;
    patterns: Array<{ type: string; description?: string }>;
    node_count: number;
    edge_count: number;
  };
}

export interface AuditLogEntry {
  log_id: number;
  case_id: string;
  action: string;
  actor: string;
  timestamp: string;
  details: string;
}

export interface DecisionResponse {
  case_id: string;
  decision: string;
  status: string;
  decided_at: string;
}

// ── API Functions ────────────────────────────────────────────────────────────

/** Login and get auth token */
export async function login(
  email: string,
  password: string,
): Promise<{ access_token: string; user: { email: string; name: string; role: string } }> {
  const data = await apiFetch<{
    access_token: string;
    user: { email: string; name: string; role: string };
  }>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setAuthToken(data.access_token);
  return data;
}

/** List cases with optional filters */
export function listCases(params?: {
  status?: string;
  risk_band?: string;
  limit?: number;
  offset?: number;
}): Promise<CaseListResponse> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.risk_band) qs.set("risk_band", params.risk_band);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const query = qs.toString();
  return apiFetch(`/api/cases${query ? `?${query}` : ""}`);
}

/** Get single case by ID (includes transaction + customer data) */
export function getCase(caseId: string): Promise<BackendCase> {
  return apiFetch(`/api/cases/${encodeURIComponent(caseId)}`);
}

/** Dashboard stats */
export function getCaseStats(): Promise<CaseStatsResponse> {
  return apiFetch("/api/cases/stats/summary");
}

/** Submit analyst decision (analyst_id derived from server token) */
export function submitDecision(
  caseId: string,
  decision: string,
  notes?: string,
): Promise<DecisionResponse> {
  return apiFetch(`/api/cases/${encodeURIComponent(caseId)}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision, notes: notes ?? "" }),
  });
}

/** Score a transaction */
export function scoreTransaction(
  transactionId: string,
  amount: number,
): Promise<ScoreResponse> {
  return apiFetch("/api/score/analyze", {
    method: "POST",
    body: JSON.stringify({
      transaction_id: transactionId,
      amount,
    }),
  });
}

/** Run full investigation on a case */
export function runInvestigation(caseId: string): Promise<InvestigationResponse> {
  return apiFetch(`/api/investigate/${encodeURIComponent(caseId)}`, {
    method: "POST",
  });
}

export interface AuditLogResponse {
  entries: AuditLogEntry[];
  count: number;
}

/** Get audit log for a case */
export async function getAuditLog(caseId?: string): Promise<AuditLogEntry[]> {
  const path = caseId
    ? `/api/audit/?case_id=${encodeURIComponent(caseId)}`
    : "/api/audit/";
  const data = await apiFetch<AuditLogResponse | AuditLogEntry[]>(path);
  if (Array.isArray(data)) return data;
  if (data && Array.isArray((data as AuditLogResponse).entries))
    return (data as AuditLogResponse).entries;
  return [];
}

/** Get STR draft for a case */
export function getStrDraft(caseId: string): Promise<{ case_id: string; str_draft: string }> {
  return apiFetch(`/api/reports/str-draft/${encodeURIComponent(caseId)}`);
}

/** Health check */
export function healthCheck(): Promise<{ status: string; model: string }> {
  return apiFetch("/health");
}
