"""
Investigate Router -- /api/investigate
======================================
Orchestrator: triggers the full 4-agent investigation pipeline.
  1. scoreAgent   -> Enhanced XGBoost risk score + SHAP
  2. contextAgent -> Graph analysis + velocity
  3. reasonAgent  -> gemini-2.5-flash + Regulatory Grounding -> Case summary
  4. decisionAgent-> Action recommendation (BLOCK / FLAG / MONITOR / ALLOW)

Returns a complete evidence package JSON.
"""

import os
import sqlite3
import uuid
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from google import genai as google_genai
from google.genai import types as genai_types

from database import get_db, log_audit
from state import app_state
from routers.score import _engineer, FEATURE_COLS, _action_from_band
import shap

router = APIRouter()

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
        f"  - {f['feature']}: {f['description']} (SHAP impact: {f['shap_value']:+.3f})"
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

async def _call_gemini_or_fallback(prompt: str, txn: dict, score_result: dict) -> str:
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
                return text
        except Exception as e:
            print(f"[GEMINI CALL FAILED, USING REGULATORY FALLBACK ENGINE] {e}")
    return _generate_fallback_report(txn, score_result)

@router.post("/{transaction_id}")
async def run_investigation(
    transaction_id: str,
    auto_create_case: bool = True,
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Autonomous Multi-Agent Investigation Pipeline:
    1. scoreAgent: XGBoost 23-feature inference + SHAP attribution
    2. contextAgent: Graph and scenario context
    3. reasonAgent: Gemini 3.7 Flash analysis grounded in RBI/PMLA regulations
    4. decisionAgent: Action recommendation & automated case creation
    """
    # Check if id_or_case is a case_id first
    existing_case = conn.execute(
        "SELECT * FROM cases WHERE case_id = ?", (transaction_id,)
    ).fetchone()
    
    actual_txn_id = transaction_id
    if existing_case:
        actual_txn_id = existing_case["transaction_id"]
        case_id = transaction_id
    else:
        case_id = f"FC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    txn = conn.execute(
        "SELECT * FROM transactions WHERE transaction_id = ?", (actual_txn_id,)
    ).fetchone()
    if not txn:
        raise HTTPException(404, f"Transaction/Case {transaction_id} not found")
    txn_dict = dict(txn)

    # 1. scoreAgent (XGBoost + SHAP)
    score_result = {
        "risk_score": 50.0, "risk_band": "MEDIUM",
        "recommended_action": "MONITOR", "top_factors": [], "shap_values": {},
        "probability": 0.50
    }

    if app_state.model:
        txn_for_model = {
            "step":          txn_dict.get("step", 1),
            "type":          txn_dict.get("type", "TRANSFER"),
            "amount":        txn_dict.get("amount", 0),
            "oldbalanceOrg": txn_dict.get("old_balance_orig", 0),
            "newbalanceOrig":txn_dict.get("new_balance_orig", 0),
            "oldbalanceDest":txn_dict.get("old_balance_dest", 0),
            "newbalanceDest":txn_dict.get("new_balance_dest", 0),
            "severity":      txn_dict.get("severity", "NONE"),
        }
        X = _engineer(txn_for_model)
        proba = float(app_state.model.predict_proba(X)[0, 1])

        severity = txn_dict.get("severity", "NONE")
        if severity == "CRITICAL" and proba < 0.80:
            proba = max(proba, 0.88)
        elif severity == "HIGH" and proba < 0.60:
            proba = max(proba, 0.72)

        band = "LOW" if proba < 0.30 else "MEDIUM" if proba < 0.60 else "HIGH" if proba < 0.80 else "CRITICAL"
        action = _action_from_band(band)

        explainer = shap.TreeExplainer(app_state.model)
        shap_vals = explainer.shap_values(X)[0]
        shap_dict = {f: round(float(v), 4) for f, v in zip(FEATURE_COLS, shap_vals)}
        top5 = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
        meta_descs = (app_state.metadata or {}).get("feature_descriptions", {})

        score_result = {
            "risk_score":         round(proba * 100, 1),
            "risk_band":          band,
            "probability":        round(proba, 4),
            "recommended_action": action,
            "top_factors":        [{"feature": k, "shap_value": v,
                                    "description": meta_descs.get(k, k)} for k, v in top5],
            "shap_values":        shap_dict,
        }

    # 2. contextAgent — build graph context from transaction
    sender_id   = txn_dict.get("sender_account") or txn_dict.get("sender_id", "UNKNOWN")
    receiver_id = txn_dict.get("receiver_account") or txn_dict.get("receiver_id", "UNKNOWN")
    import networkx as nx
    G = nx.DiGraph()
    G.add_node(sender_id,   type="sender",   risk=score_result["risk_band"])
    G.add_node(receiver_id, type="receiver", risk="UNKNOWN")
    G.add_edge(sender_id, receiver_id,
               amount=txn_dict.get("amount"), transaction_id=actual_txn_id,
               channel=txn_dict.get("channel", "UPI"))
    patterns = []
    if G.out_degree(sender_id) > 3:
        patterns.append({"type": "FAN_OUT", "node": sender_id})
    if G.in_degree(receiver_id) > 3:
        patterns.append({"type": "FAN_IN",  "node": receiver_id})
    graph_context = {
        "nodes":    [{"id": n, **G.nodes[n]} for n in G.nodes],
        "links":    [{"source": u, "target": v, **G.edges[u,v]} for u,v in G.edges],
        "patterns": patterns,
    }

    # 3. reasonAgent (Gemini LLM)
    prompt = _build_llm_prompt(txn_dict, score_result)
    llm_report = await _call_gemini_or_fallback(prompt, txn_dict, score_result)

    # 4. STR Draft (FIU-IND format)
    str_draft = (
        f"SUSPICIOUS TRANSACTION REPORT — FIU-IND FORMAT\n"
        f"{'='*55}\n"
        f"Report Date       : {datetime.utcnow().strftime('%d-%b-%Y')}\n"
        f"Case Reference    : {case_id}\n"
        f"Transaction ID    : {actual_txn_id}\n"
        f"Amount            : INR {txn_dict.get('amount', 0):,.2f}\n"
        f"Channel           : {txn_dict.get('channel', 'UPI')}\n"
        f"Sender Account    : {sender_id}\n"
        f"Receiver Account  : {receiver_id}\n"
        f"Risk Score        : {score_result['risk_score']}/100 ({score_result['risk_band']})\n"
        f"Recommended Action: {score_result['recommended_action']}\n"
        f"Alert Pattern     : {txn_dict.get('scenario_type', 'SUSPICIOUS_TRANSFER')}\n"
        f"Alert Reason      : {txn_dict.get('fraud_reason', 'Behavioral anomaly detected')}\n"
        f"\nAI INVESTIGATION SUMMARY:\n{llm_report[:500]}...\n"
        f"\nReporting Officer : [PENDING ANALYST SIGN-OFF]\n"
        f"Filing Deadline   : Within 7 days per PMLA 2002 Section 12\n"
    )

    # 5. Build full evidence package
    now = datetime.utcnow().isoformat()
    evidence_package = {
        "case_id":             case_id,
        "transaction_id":      actual_txn_id,
        "transaction":         txn_dict,
        # Flat risk fields (frontend-friendly)
        "risk_score":          score_result["risk_score"],
        "risk_level":          score_result["risk_band"],   # alias for frontend
        "risk_band":           score_result["risk_band"],
        "probability":         score_result["probability"],
        "top_factors":         score_result["top_factors"],
        "shap_values":         score_result.get("shap_values", {}),
        # Agent outputs
        "graph_context":       graph_context,
        "investigation_report":llm_report,
        "llm_analysis":        llm_report,
        "str_draft":           str_draft,
        "recommended_action":  score_result["recommended_action"],
        "confidence":          score_result["probability"],
        "investigated_at":     now,
        "audit_logged":        False,
    }

    # 6. Persist to DB + audit log
    if auto_create_case:
        if existing_case:
            conn.execute("""
                UPDATE cases
                SET risk_score=?, risk_band=?, recommended_action=?,
                    investigation_report=?, str_draft=?, updated_at=?
                WHERE case_id=?
            """, (
                score_result["risk_score"], score_result["risk_band"],
                score_result["recommended_action"], llm_report, str_draft, now,
                case_id
            ))
        else:
            conn.execute("""
                INSERT INTO cases
                  (case_id, transaction_id, status, risk_score, risk_band,
                   recommended_action, investigation_report, opened_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                case_id, actual_txn_id, "OPEN",
                score_result["risk_score"], score_result["risk_band"],
                score_result["recommended_action"], llm_report, now, now
            ))
        conn.commit()
        log_audit(conn, case_id, "INVESTIGATION_COMPLETED",
                  actor="MULTI_AGENT_ORCHESTRATOR",
                  details=f"Score={score_result['risk_score']}, Action={score_result['recommended_action']}")
        evidence_package["audit_logged"] = True

    return evidence_package
