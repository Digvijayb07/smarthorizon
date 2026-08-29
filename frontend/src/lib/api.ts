/**
 * API Service Layer
 * =================
 * Centralizes all communication between the React frontend and the
 * FastAPI backend at http://localhost:8000/api.
 *
 * Every function returns typed data matching our investigation types.
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ── Generic fetch helper ─────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

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
  // Joined data from get_case
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
  fraud_probability: number;
  recommended_action: string;
  shap_contributions: Record<string, number>;
  top_features: Array<{ feature: string; contribution: number }>;
}

export interface InvestigationResponse {
  case_id: string;
  transaction_id: string;
  risk_score: number;
  risk_band: string;
  recommended_action: string;
  investigation_report: string;
  str_required: boolean;
  str_draft: string | null;
  agents: {
    scoreAgent: unknown;
    contextAgent: unknown;
    reasonAgent: unknown;
    decisionAgent: unknown;
  };
}

export interface AuditLogEntry {
  id: number;
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

/** Submit analyst decision */
export function submitDecision(
  caseId: string,
  decision: string,
  analystId: string,
  notes?: string,
): Promise<DecisionResponse> {
  return apiFetch(`/api/cases/${encodeURIComponent(caseId)}/decision`, {
    method: "POST",
    body: JSON.stringify({
      analyst_id: analystId,
      decision,
      notes: notes ?? "",
    }),
  });
}

/** Score a transaction */
export function scoreTransaction(transactionId: string): Promise<ScoreResponse> {
  return apiFetch(`/api/score/${encodeURIComponent(transactionId)}`);
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
  const path = caseId ? `/api/audit/?case_id=${encodeURIComponent(caseId)}` : "/api/audit/";
  const data = await apiFetch<AuditLogResponse | AuditLogEntry[]>(path);
  if (Array.isArray(data)) return data;
  if (data && Array.isArray((data as AuditLogResponse).entries)) return (data as AuditLogResponse).entries;
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
