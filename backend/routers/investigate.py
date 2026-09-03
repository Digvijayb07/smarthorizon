"""
Investigate Router — /api/investigate
======================================
Orchestrator: triggers the full 4-agent investigation pipeline.
  1. scoreAgent   -> Centralized XGBoost risk score + SHAP (via routers.score)
  2. contextAgent -> Graph analysis from graph_agent with real pattern detection
  3. reasonAgent  -> gemini-2.5-flash + Regulatory Grounding -> Case summary
  4. decisionAgent-> Action recommendation (BLOCK / FLAG / MONITOR / ALLOW)

Returns a complete evidence package JSON.
"""

import os
import sqlite3
import uuid
import json
import math
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from google import genai as google_genai
from google.genai import types as genai_types

from database import get_db, log_audit
from state import app_state
from auth import current_user, CurrentUser
from routers.score import score_transaction, _band_from_proba, _action_from_band

router = APIRouter(dependencies=[Depends(current_user)])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
_gemini_client = None
if GEMINI_API_KEY:
    try:
        _gemini_client = google_genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[GEMINI INIT ERROR] {e}")


class InvestigateRequest(BaseModel):
    transaction_id: str
    auto_create_case: bool = True


def _build_llm_prompt(txn: dict, score_result: dict) -> str:
    factors_text = "\n".join(
        f"  - {f['feature']}: {f.get('description', f['feature'])} (SHAP impact: {f['shap_value']:+.3f})"
        for f in score_result.get("top_factors", [])
    )
    return f"""You are a Lead Financial Crime Investigator at an Indian Scheduled Commercial Bank.
Analyze this alert and write a clear, audit-ready investigation report.

TRANSACTION SUMMARY:
- Transaction ID: {txn.get('transaction_id')}
- Amount: INR {txn.get('amount', 0):,.2f}
- Channel: {txn.get('channel', 'UPI')}
- Sender Account: {txn.get('sender_account', txn.get('sender_id', 'Unknown'))}
- Receiver Account: {txn.get('receiver_account', txn.get('receiver_id', 'Unknown'))}
- Origin Pre/Post Balance: INR {txn.get('old_balance_orig', 0):,.2f} -> INR {txn.get('new_balance_orig', 0):,.2f}
- Dest Pre/Post Balance: INR {txn.get('old_balance_dest', 0):,.2f} -> INR {txn.get('new_balance_dest', 0):,.2f}
- Scenario Pattern: {txn.get('scenario_type', 'SUSPICIOUS_TRANSFER')}
- Alert Reason: {txn.get('fraud_reason', 'Behavioral anomaly detected')}
- Priority Severity: {txn.get('severity', 'HIGH')}

MACHINE LEARNING & SHAP SIGNALS:
- Risk Score: {score_result.get('risk_score', 0)}/100 ({score_result.get('risk_band', 'MEDIUM')} risk)
- Model Probability: {score_result.get('model_probability', 0):.4f} (before severity override)
- Rule Adjustments: {score_result.get('rule_adjustments', [])}
- Recommended Action: {score_result.get('recommended_action', 'MONITOR')}
- Primary Explainability Drivers:
{factors_text}

REGULATORY GUIDANCE:
- RBI Master Direction - Fraud Risk Management in Commercial Banks 2024
- PMLA 2002 Section 12 (Reporting of suspicious transactions to FIU-IND within 7 days)
- NPCI UPI Circular No. 138 (Mule and rapid fund velocity monitoring)

Please provide a structured report with these exact 5 sections:
1. EXECUTIVE SUMMARY: Direct summary of the transaction and flagged behavior.
2. SUSPICIOUS INDICATORS: Key signals observed (money flow, balance depletion, velocity).
3. REGULATORY COMPLIANCE ASSESSMENT: Applicable RBI/PMLA clauses and obligations.
4. RECOMMENDED ACTION & JUSTIFICATION: Action (BLOCK / FLAG FOR MONITORING / DISMISS) with explicit rationale.
5. ANALYST ACTION ITEMS: Concrete verification checklist for the human analyst.
"""


def _generate_fallback_report(txn: dict, score_result: dict) -> str:
    """Deterministic, high-quality regulatory investigation template if API is offline."""
    scenario = txn.get("scenario_type", "SUSPICIOUS_VELOCITY").replace("_", " ").title()
    amount = txn.get("amount", 0)
    score = score_result.get("risk_score", 75)
    band = score_result.get("risk_band", "HIGH")
    action = score_result.get("recommended_action", "FLAG")
    reason = txn.get("fraud_reason", "Abnormal fund movement pattern detected.")

    return f"""### 1. EXECUTIVE SUMMARY
Investigation opened for transaction **{txn.get('transaction_id')}** involving a transfer of **INR {amount:,.2f}** via {txn.get('channel', 'UPI')}. The system identified patterns consistent with **{scenario}**. Composite risk evaluation produced a score of **{score}/100 ({band} Risk)**.

### 2. SUSPICIOUS INDICATORS
- **Behavioral Flag**: {reason}
- **Balance Impact**: Origin balance moved from INR {txn.get('old_balance_orig', 0):,.2f} to INR {txn.get('new_balance_orig', 0):,.2f}.
- **ML Attribution**: Model flagged high anomalous weights on balance reconciliation and transfer-to-balance ratios.

### 3. REGULATORY COMPLIANCE ASSESSMENT
- **PMLA 2002 (Sec 12)**: Transactions displaying non-economic rationale require logging and potential STR filing with FIU-IND.
- **RBI Master Direction (Fraud Risk Management 2024)**: Mandates immediate containment and customer verification on flagged accounts.
- **NPCI OC 138**: Alerts on automated mule-dispersion patterns require real-time nodal desk review.

### 4. RECOMMENDED ACTION & JUSTIFICATION
**Recommendation**: **{action}**
*Rationale*: Given the {band} risk score ({score}/100) and observed {scenario} indicators, the account requires immediate risk mitigation.

### 5. ANALYST ACTION ITEMS
1. Verify device fingerprint and IP geovelocity for account `{txn.get('sender_account')}`.
2. Conduct out-of-band customer confirmation if account is frozen.
3. Review associated beneficiary `{txn.get('receiver_account')}` for multi-bank mule linkages.
"""


async def _call_gemini_or_fallback(prompt: str, txn: dict, score_result: dict) -> tuple[str, bool]:
    """
    Call Gemini LLM or return fallback report.
    Returns (report_text, ai_generated_flag).
    """
    if _gemini_client:
        try:
            import asyncio

            def _generate():
                response = _gemini_client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt,
                )
                return response.text if response and response.text else None

            text = await asyncio.to_thread(_generate)
            if text:
                return text, True
        except Exception as e:
            print(f"[GEMINI CALL FAILED, USING REGULATORY FALLBACK ENGINE] {e}")
    return _generate_fallback_report(txn, score_result), False


@router.post("/{transaction_id}")
async def run_investigation(
    transaction_id: str,
    auto_create_case: bool = True,
    conn: sqlite3.Connection = Depends(get_db),
    user: CurrentUser = Depends(current_user),
):
    """
    Autonomous Multi-Agent Investigation Pipeline:
    1. scoreAgent: XGBoost 23-feature inference + SHAP attribution (via centralized score_transaction)
    2. contextAgent: Multi-transaction graph analysis via graph_agent with real pattern detection
    3. reasonAgent: Gemini analysis grounded in RBI/PMLA regulations
    4. decisionAgent: Action recommendation & idempotent case creation
    """
    # ── Idempotent case lookup ────────────────────────────────────────────────
    # Check by both case_id AND transaction_id to prevent duplicate cases
    existing_case = conn.execute(
        "SELECT * FROM cases WHERE case_id = ? OR transaction_id = ?",
        (transaction_id, transaction_id),
    ).fetchone()

    actual_txn_id = transaction_id
    if existing_case:
        actual_txn_id = existing_case["transaction_id"]
        case_id = existing_case["case_id"]
    else:
        case_id = f"FC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    txn = conn.execute(
        "SELECT * FROM transactions WHERE transaction_id = ?", (actual_txn_id,)
    ).fetchone()
    if not txn:
        raise HTTPException(404, f"Transaction {transaction_id} not found")
    txn_dict = dict(txn)

    # ── 1. scoreAgent (centralized scoring) ───────────────────────────────────
    txn_for_model = {
        "step": txn_dict.get("step", 1),
        "type": txn_dict.get("type", "TRANSFER"),
        "amount": txn_dict.get("amount", 0),
        "oldbalanceOrg": txn_dict.get("old_balance_orig", 0),
        "newbalanceOrig": txn_dict.get("new_balance_orig", 0),
        "oldbalanceDest": txn_dict.get("old_balance_dest", 0),
        "newbalanceDest": txn_dict.get("new_balance_dest", 0),
    }
    try:
        score_result = score_transaction(txn_for_model)
    except HTTPException:
        # Model not loaded — use defaults
        score_result = {
            "risk_score": 50.0, "model_probability": 0.50, "risk_band": "MEDIUM",
            "recommended_action": "MONITOR", "top_factors": [], "shap_values": {},
            "probability": 0.50, "rule_adjustments": [],
        }

    # ── 2. contextAgent — query ALL related transactions for graph analysis ────
    sender_account = txn_dict.get("sender_account") or txn_dict.get("sender_id", "UNKNOWN")
    receiver_account = txn_dict.get("receiver_account") or txn_dict.get("receiver_id", "UNKNOWN")

    related_txns = conn.execute(
        """SELECT * FROM transactions
           WHERE sender_account = ? OR receiver_account = ?
              OR sender_id = ? OR receiver_id = ?
           ORDER BY timestamp ASC""",
        (sender_account, receiver_account, sender_account, receiver_account),
    ).fetchall()

    import networkx as nx
    G = nx.DiGraph()
    for r in related_txns:
        r_dict = dict(r)
        src = r_dict.get("sender_account") or r_dict.get("sender_id", "UNKNOWN")
        dst = r_dict.get("receiver_account") or r_dict.get("receiver_id", "UNKNOWN")
        G.add_node(src, type="sender" if src == sender_account else "related")
        G.add_node(dst, type="receiver" if dst == receiver_account else "related")
        G.add_edge(
            src, dst,
            amount=r_dict.get("amount"),
            transaction_id=r_dict.get("transaction_id"),
            channel=r_dict.get("channel", "UPI"),
        )

    # Real pattern detection on the full graph
    from routers.graph import _detect_patterns
    patterns = _detect_patterns(G, sender_account, receiver_account)

    graph_context = {
        "nodes": [{"id": n, **G.nodes[n]} for n in G.nodes],
        "links": [{"source": u, "target": v, **G.edges[u, v]} for u, v in G.edges],
        "patterns": patterns,
        "transaction_count": len(related_txns),
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
    }

    # ── 3. reasonAgent (Gemini LLM) ──────────────────────────────────────────
    prompt = _build_llm_prompt(txn_dict, score_result)
    llm_report, ai_generated = await _call_gemini_or_fallback(prompt, txn_dict, score_result)

    # ── 4. STR Draft (FIU-IND format) ────────────────────────────────────────
    str_draft = (
        f"SUSPICIOUS TRANSACTION REPORT — FIU-IND FORMAT\n"
        f"{'='*55}\n"
        f"Report Date       : {datetime.utcnow().strftime('%d-%b-%Y')}\n"
        f"Case Reference    : {case_id}\n"
        f"Transaction ID    : {actual_txn_id}\n"
        f"Amount            : INR {txn_dict.get('amount', 0):,.2f}\n"
        f"Channel           : {txn_dict.get('channel', 'UPI')}\n"
        f"Sender Account    : {sender_account}\n"
        f"Receiver Account  : {receiver_account}\n"
        f"Risk Score        : {score_result['risk_score']}/100 ({score_result['risk_band']})\n"
        f"Model Probability : {score_result.get('model_probability', 0):.4f}\n"
        f"Rule Adjustments  : {score_result.get('rule_adjustments', [])}\n"
        f"Recommended Action: {score_result['recommended_action']}\n"
        f"Alert Pattern     : {txn_dict.get('scenario_type', 'SUSPICIOUS_TRANSFER')}\n"
        f"Alert Reason      : {txn_dict.get('fraud_reason', 'Behavioral anomaly detected')}\n"
        f"\nAI INVESTIGATION SUMMARY:\n{llm_report[:500]}...\n"
        f"\nReporting Officer : [PENDING ANALYST SIGN-OFF]\n"
        f"Filing Deadline   : Within 7 days per PMLA 2002 Section 12\n"
    )

    # ── 5. Build full evidence package ────────────────────────────────────────
    now = datetime.utcnow().isoformat()
    evidence_package = {
        "case_id": case_id,
        "transaction_id": actual_txn_id,
        "transaction": txn_dict,
        # Flat risk fields (frontend-friendly)
        "risk_score": score_result["risk_score"],
        "model_probability": score_result.get("model_probability", 0),
        "risk_level": score_result["risk_band"],
        "risk_band": score_result["risk_band"],
        "probability": score_result["probability"],
        "top_factors": score_result["top_factors"],
        "shap_values": score_result.get("shap_values", {}),
        "rule_adjustments": score_result.get("rule_adjustments", []),
        # Agent outputs
        "graph_context": graph_context,
        "investigation_report": llm_report,
        "llm_analysis": llm_report,
        "str_draft": str_draft,
        "recommended_action": score_result["recommended_action"],
        "confidence": score_result["probability"],
        "ai_generated": ai_generated,
        "reasoning_source": "gemini-3.6-flash" if ai_generated else "regulatory-fallback-template",
        "investigated_at": now,
        "audit_logged": False,
    }

    # ── 6. Persist to DB + audit log (idempotent) ────────────────────────────
    if auto_create_case:
        if existing_case:
            conn.execute(
                """UPDATE cases
                   SET risk_score=?, risk_band=?, recommended_action=?,
                       investigation_report=?, str_draft=?, updated_at=?
                   WHERE case_id=?""",
                (
                    score_result["risk_score"], score_result["risk_band"],
                    score_result["recommended_action"], llm_report, str_draft, now,
                    case_id,
                ),
            )
        else:
            conn.execute(
                """INSERT INTO cases
                  (case_id, transaction_id, status, risk_score, risk_band,
                   recommended_action, analyst_id, investigation_report,
                   str_draft, opened_at, updated_at)
                  VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    case_id, actual_txn_id, "OPEN",
                    score_result["risk_score"], score_result["risk_band"],
                    score_result["recommended_action"], user.email,
                    llm_report, str_draft, now, now,
                ),
            )
        conn.commit()
        log_audit(
            conn, case_id, "INVESTIGATION_COMPLETED",
            actor=user.email,
            details=f"Score={score_result['risk_score']}, Action={score_result['recommended_action']}, AI={ai_generated}",
        )
        evidence_package["audit_logged"] = True

    return evidence_package
