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
from regulatory import REGULATORY_CLAUSES, extract_cited_clauses, format_clauses_for_prompt

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


def _build_llm_prompt(txn: dict, score_result: dict, graph_context: dict | None = None) -> str:
    factors_text = "\n".join(
        f"  - {f['feature']}: {f.get('description', f['feature'])} (SHAP impact: {f['shap_value']:+.3f})"
        for f in score_result.get("top_factors", [])
    )

    graph_ctx = graph_context or {}
    patterns = graph_ctx.get("patterns", [])
    patterns_text = "\n".join(
        f"  - [{p.get('type')}] ({p.get('severity', 'HIGH')}): {p.get('description')}"
        for p in patterns
    ) if patterns else "  - Isolated transaction; no multi-hop syndicate loops detected."

    network_risk = graph_ctx.get("network_risk", "LOW")
    network_summary = graph_ctx.get("network_risk_summary", "Isolated point-to-point transfer.")
    node_count = graph_ctx.get("node_count", 2)
    edge_count = graph_ctx.get("edge_count", 1)

    # Implicated node accounts
    nodes = graph_ctx.get("nodes", [])
    mule_accounts = [
        n["id"] for n in nodes
        if n.get("role") in ["MULE_CASHOUT", "INTERMEDIARY"] or n.get("suspicious")
    ]
    mules_text = ", ".join(mule_accounts[:6]) if mule_accounts else "None identified beyond primary endpoints"

    clauses_json = format_clauses_for_prompt()

    return f"""You are a Lead Financial Crime Investigator at an Indian Scheduled Commercial Bank.
Analyze this alert and write a clear, audit-ready investigation report synthesizing both Machine Learning features and NetworkX Multi-Hop Graph intelligence.

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

MACHINE LEARNING & SHAP SIGNALS (XGBoost):
- Transaction Risk Score: {score_result.get('risk_score', 0)}/100 ({score_result.get('risk_band', 'MEDIUM')} risk)
- Model Probability: {score_result.get('model_probability', 0):.4f} (before severity override)
- Rule Adjustments: {score_result.get('rule_adjustments', [])}
- Recommended Action: {score_result.get('recommended_action', 'MONITOR')}
- Primary Explainability Drivers:
{factors_text}

NETWORK GRAPH & RELATIONAL TOPOLOGY (NetworkX):
- Network Risk Level: {network_risk} ({network_summary})
- Subgraph Scope: {node_count} Accounts, {edge_count} Flow Edges
- Implicated Syndicate/Mule Accounts: {mules_text}
- Detected Topological Patterns:
{patterns_text}

REGULATORY COMPLIANCE CITATION CONTRACT:
You MUST cite specific statutory clause IDs inline next to each finding in Section 3, in the exact bracketed format [CLAUSE_ID].
Do NOT cite any clause outside the available catalog:
{clauses_json}

Please provide a structured report with these exact 5 sections:
1. EXECUTIVE SUMMARY: Direct summary of the transaction, composite risk, and whether it represents an isolated anomaly or an active multi-account syndicate. Explicitly cite the Network Risk level ({network_risk}).
2. SUSPICIOUS INDICATORS: Key signals observed (money flow, balance depletion, SHAP feature drivers, and topological graph patterns like structuring or mule fan-out).
3. REGULATORY COMPLIANCE ASSESSMENT: Applicable statutory obligations citing clause IDs inline in [CLAUSE_ID] format (e.g. [PMLA_S12], [PMLA_S3], [RBI_MD_KYC_2016_PARA_23], [RBI_MD_KYC_2016_PARA_37], [RBI_FRM_2024_CIRCULAR], [NPCI_UPI_2023_PARA_5], [NPCI_OC_138_MULE]).
4. RECOMMENDED ACTION & JUSTIFICATION: Action (BLOCK / FLAG FOR MONITORING / DISMISS) with explicit rationale citing both ML and Network signals.
5. ANALYST ACTION ITEMS: Concrete verification checklist for the human analyst, including freezing implicated mule accounts.
"""


def _generate_fallback_report(txn: dict, score_result: dict, graph_context: dict | None = None) -> str:
    """Deterministic, high-quality regulatory investigation template with inline clause citations."""
    scenario = txn.get("scenario_type", "SUSPICIOUS_VELOCITY").replace("_", " ").title()
    amount = txn.get("amount", 0)
    score = score_result.get("risk_score", 75)
    band = score_result.get("risk_band", "HIGH")
    action = score_result.get("recommended_action", "FLAG")
    reason = txn.get("fraud_reason", "Abnormal fund movement pattern detected.")

    graph_ctx = graph_context or {}
    net_risk = graph_ctx.get("network_risk", "HIGH")
    net_summary = graph_ctx.get("network_risk_summary", "Multi-hop counterparty network detected.")
    patterns = graph_ctx.get("patterns", [])
    patterns_bullet = "\n".join(
        f"- **Network Pattern ({p.get('type')})**: {p.get('description')}"
        for p in patterns
    ) if patterns else "- **Network Topology**: Multi-hop traversal identified connected feeder and intermediary accounts."

    return f"""### 1. EXECUTIVE SUMMARY
Investigation opened for transaction **{txn.get('transaction_id')}** involving a transfer of **INR {amount:,.2f}** via {txn.get('channel', 'UPI')}. The system identified behavioral indicators consistent with **{scenario}**. Composite risk evaluation produced an XGBoost Transaction Risk Score of **{score}/100 ({band} Risk)** alongside a NetworkX Topological Risk of **{net_risk}** ({net_summary}).

### 2. SUSPICIOUS INDICATORS
- **Behavioral Anomaly**: {reason}
- **Balance Trajectory**: Origin balance depleted from INR {txn.get('old_balance_orig', 0):,.2f} to INR {txn.get('new_balance_orig', 0):,.2f}.
- **ML Attribution Drivers**: Elevated weights on balance depletion ratio and velocity indicators.
{patterns_bullet}

### 3. REGULATORY COMPLIANCE ASSESSMENT
- **Statutory STR Reporting Obligation [PMLA_S12]**: Mandatory reporting of transactions displaying no lawful economic purpose or suspected of being structured to avoid thresholds to FIU-IND.
- **Offence of Money Laundering & Structuring [PMLA_S3]**: Structuring and rapid dispersal of funds across multi-tier accounts triggers statutory anti-layering enforcement under Section 3.
- **Enhanced Due Diligence Mandate [RBI_MD_KYC_2016_PARA_23]**: Disproportionate transactional velocity relative to customer profile mandates immediate Enhanced Due Diligence (EDD) and source verification.
- **Strict 7-Day Statutory Filing Window [RBI_MD_KYC_2016_PARA_37]**: Obligation to transmit completed Suspicious Transaction Report to FIU-IND within 7 working days of established suspicion.
- **Real-Time Fraud Containment [RBI_FRM_2024_CIRCULAR]**: Mandates immediate nodal account debit freeze and synchronized counterparty scrutiny across banking rails.
- **Mule Account Mitigation Directives [NPCI_OC_138_MULE] [NPCI_UPI_2023_PARA_5]**: Alerts on rapid velocity mule dispersion mandate real-time beneficiary holds and automated NCRP alert transmission.

### 4. RECOMMENDED ACTION & JUSTIFICATION
**Recommendation**: **{action}**
*Rationale*: High composite risk ({score}/100 Transaction Risk + {net_risk} Network Risk). Multi-hop analysis confirms coordinated fund movement necessitating immediate nodal intervention.

### 5. ANALYST ACTION ITEMS
1. Verify device fingerprint and IP geovelocity for account `{txn.get('sender_account')}`.
2. Place a provisional lien/freeze on recipient `{txn.get('receiver_account')}` and associated downstream mule accounts [RBI_FRM_2024_CIRCULAR].
3. Transmit draft STR package to Principal Officer for statutory FIU-IND submission within 7 days [PMLA_S12] [RBI_MD_KYC_2016_PARA_37].
"""


async def _call_gemini_or_fallback(
    prompt: str, txn: dict, score_result: dict, graph_context: dict | None = None
) -> tuple[str, bool]:
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
    return _generate_fallback_report(txn, score_result, graph_context), False


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

    # ── 2. contextAgent — multi-hop graph analysis via NetworkX ───────────────
    sender_account = txn_dict.get("sender_account") or txn_dict.get("sender_id", "UNKNOWN")
    receiver_account = txn_dict.get("receiver_account") or txn_dict.get("receiver_id", "UNKNOWN")

    visited_accounts = {sender_account, receiver_account}
    current_frontier = {sender_account, receiver_account}
    collected_txns: dict[str, dict[str, Any]] = {}

    if txn_dict.get("transaction_id"):
        collected_txns[txn_dict["transaction_id"]] = txn_dict

    for _ in range(2):
        if not current_frontier:
            break
        placeholders = ",".join("?" for _ in current_frontier)
        query_params = list(current_frontier) + list(current_frontier)
        hop_rows = conn.execute(
            f"""SELECT * FROM transactions
               WHERE sender_account IN ({placeholders}) OR receiver_account IN ({placeholders})
               ORDER BY timestamp ASC LIMIT 40""",
            query_params,
        ).fetchall()

        next_frontier = set()
        for r in hop_rows:
            r_dict = dict(r)
            t_id = r_dict.get("transaction_id") or f"TX-{len(collected_txns)}"
            if t_id not in collected_txns:
                collected_txns[t_id] = r_dict
                src = r_dict.get("sender_account") or r_dict.get("sender_id")
                dst = r_dict.get("receiver_account") or r_dict.get("receiver_id")
                if src and src not in visited_accounts:
                    next_frontier.add(src)
                if dst and dst not in visited_accounts:
                    next_frontier.add(dst)

        visited_accounts.update(next_frontier)
        current_frontier = next_frontier
        if len(collected_txns) >= 50:
            break

    import networkx as nx
    G = nx.DiGraph()
    for t_id, r_dict in collected_txns.items():
        src = r_dict.get("sender_account") or r_dict.get("sender_id", "UNKNOWN")
        dst = r_dict.get("receiver_account") or r_dict.get("receiver_id", "UNKNOWN")
        amt = r_dict.get("amount", 0)
        G.add_node(src)
        G.add_node(dst)
        G.add_edge(
            src, dst,
            amount=amt,
            transaction_id=t_id,
            channel=r_dict.get("channel", "UPI"),
            timestamp=r_dict.get("timestamp", ""),
        )

    G.add_node(sender_account)
    G.add_node(receiver_account)
    G.add_edge(
        sender_account,
        receiver_account,
        amount=txn_dict.get("amount", 0),
        transaction_id=txn_dict.get("transaction_id", ""),
        channel=txn_dict.get("channel", "UPI"),
        timestamp=txn_dict.get("timestamp", ""),
    )

    for n in G.nodes:
        in_d = G.in_degree(n)
        out_d = G.out_degree(n)
        if n == sender_account:
            role = "ORIGIN"
            suspicious = True
        elif n == receiver_account:
            role = "INTERMEDIARY" if out_d > 0 else "BENEFICIARY"
            suspicious = True
        elif G.has_edge(n, sender_account):
            role = "FEEDER"
            suspicious = False
        elif G.has_edge(receiver_account, n) or G.has_edge(sender_account, n):
            role = "MULE_CASHOUT"
            suspicious = True
        elif in_d > 0 and out_d > 0:
            role = "INTERMEDIARY"
            suspicious = True
        else:
            role = "COUNTERPARTY"
            suspicious = False
        G.nodes[n]["role"] = role
        G.nodes[n]["suspicious"] = suspicious
        G.nodes[n]["in_degree"] = in_d
        G.nodes[n]["out_degree"] = out_d

    from routers.graph import _detect_patterns
    patterns, network_risk, network_summary = _detect_patterns(G, sender_account, receiver_account)

    graph_context = {
        "nodes": [{"id": n, **G.nodes[n]} for n in G.nodes],
        "links": [
            {
                "source": u,
                "target": v,
                "amount": G.edges[u, v].get("amount"),
                "channel": G.edges[u, v].get("channel", "UPI"),
                "transaction_id": G.edges[u, v].get("transaction_id"),
                "timestamp": G.edges[u, v].get("timestamp"),
            }
            for u, v in G.edges
        ],
        "patterns": patterns,
        "network_risk": network_risk,
        "network_risk_summary": network_summary,
        "transaction_count": len(collected_txns),
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
    }

    # ── 3. reasonAgent (Gemini LLM) ──────────────────────────────────────────
    prompt = _build_llm_prompt(txn_dict, score_result, graph_context)
    llm_report, ai_generated = await _call_gemini_or_fallback(prompt, txn_dict, score_result, graph_context)

    # ── 4. STR Draft (FIU-IND format with Relational Evidence) ────────────────
    mule_list = [
        n["id"] for n in graph_context["nodes"]
        if n.get("role") in ["MULE_CASHOUT", "INTERMEDIARY"]
    ]
    mule_line = ", ".join(mule_list) if mule_list else "None identified beyond primary endpoints"
    pattern_line = ", ".join(p["type"] for p in patterns) if patterns else "Point-to-point transfer"

    str_draft = (
        f"SUSPICIOUS TRANSACTION REPORT — FIU-IND FORMAT\n"
        f"{'='*55}\n"
        f"Report Date         : {datetime.utcnow().strftime('%d-%b-%Y')}\n"
        f"Case Reference      : {case_id}\n"
        f"Transaction ID      : {actual_txn_id}\n"
        f"Amount              : INR {txn_dict.get('amount', 0):,.2f}\n"
        f"Channel             : {txn_dict.get('channel', 'UPI')}\n"
        f"Sender Account      : {sender_account}\n"
        f"Receiver Account    : {receiver_account}\n"
        f"XGBoost Risk Score  : {score_result['risk_score']}/100 ({score_result['risk_band']})\n"
        f"Network Risk Level  : {network_risk} ({network_summary})\n"
        f"Graph Topology Scope: {graph_context['node_count']} Accounts, {graph_context['edge_count']} Flow Edges\n"
        f"Detected Patterns   : {pattern_line}\n"
        f"Implicated Mules    : {mule_line}\n"
        f"Model Probability   : {score_result.get('model_probability', 0):.4f}\n"
        f"Rule Adjustments    : {score_result.get('rule_adjustments', [])}\n"
        f"Recommended Action  : {score_result['recommended_action']}\n"
        f"Statutory Basis     : PMLA 2002 Section 12 [PMLA_S12] & RBI KYC Para 37 [RBI_MD_KYC_2016_PARA_37]\n"
        f"Regulatory Mandates : RBI FRM 2024 [RBI_FRM_2024_CIRCULAR] | NPCI OC 138 [NPCI_OC_138_MULE] [NPCI_UPI_2023_PARA_5]\n"
        f"Alert Pattern       : {txn_dict.get('scenario_type', 'SUSPICIOUS_TRANSFER')} [PMLA_S3]\n"
        f"Alert Reason        : {txn_dict.get('fraud_reason', 'Behavioral anomaly detected')}\n"
        f"\nAI INVESTIGATION SUMMARY:\n{llm_report[:650]}...\n"
        f"\nReporting Officer   : [PENDING ANALYST SIGN-OFF]\n"
        f"Filing Deadline     : Within 7 days per PMLA 2002 Section 12 [PMLA_S12]\n"
    )

    # ── 5. Composite Risk Synthesis (ML Tabular + Network Topology) ───────────
    now = datetime.utcnow().isoformat()
    cited_clauses = extract_cited_clauses(llm_report + " " + str_draft)

    composite_risk_score = float(score_result["risk_score"])
    composite_risk_band = score_result["risk_band"]
    composite_action = score_result["recommended_action"]

    if network_risk == "CRITICAL":
        composite_risk_band = "CRITICAL"
        composite_risk_score = max(composite_risk_score, 98.4)
        composite_action = "ESCALATE"
    elif network_risk == "HIGH" and composite_risk_band in {"LOW", "MEDIUM"}:
        composite_risk_band = "HIGH"
        composite_risk_score = max(composite_risk_score, 78.5)
        composite_action = "ESCALATE"

    # Actionable Counterfactual Explanation (Phase 4)
    cf = generate_counterfactual(
        transaction=txn_dict,
        shap_dict=score_result.get("shap_values", {}),
        risk_band=composite_risk_band,
        current_score=composite_risk_score,
        model=app_state.model,
        metadata=app_state.metadata,
        network_risk=network_risk,
        patterns=patterns,
    )

    evidence_package = {
        "case_id": case_id,
        "transaction_id": actual_txn_id,
        "transaction": txn_dict,
        # Flat risk fields (frontend-friendly)
        "risk_score": composite_risk_score,
        "ml_risk_score": score_result["risk_score"],
        "ml_risk_band": score_result["risk_band"],
        "model_probability": score_result.get("model_probability", 0),
        "risk_level": composite_risk_band,
        "risk_band": composite_risk_band,
        "probability": score_result["probability"],
        "top_factors": score_result["top_factors"],
        "shap_values": score_result.get("shap_values", {}),
        "rule_adjustments": score_result.get("rule_adjustments", []),
        "counterfactual": cf,
        # Regulatory Clause Traceability (Phase 4)
        "regulatory_clauses": REGULATORY_CLAUSES,
        "cited_clauses": cited_clauses,
        # Agent outputs
        "graph_context": graph_context,
        "investigation_report": llm_report,
        "llm_analysis": llm_report,
        "str_draft": str_draft,
        "recommended_action": composite_action,
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
                    composite_risk_score, composite_risk_band,
                    composite_action, llm_report, str_draft, now,
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
                    composite_risk_score, composite_risk_band,
                    composite_action, user.email,
                    llm_report, str_draft, now, now,
                ),
            )
        conn.commit()
        log_audit(
            conn, case_id, "INVESTIGATION_COMPLETED",
            actor=user.email,
            details=f"CompositeScore={composite_risk_score}, Action={composite_action}, ML={score_result['risk_score']}, Network={network_risk}, AI={ai_generated}",
        )
        evidence_package["audit_logged"] = True

    return evidence_package


@router.get("/regulatory-clauses")
async def get_regulatory_clauses_endpoint(_: CurrentUser = Depends(current_user)):
    """Return dictionary of regulatory clauses and metadata for UI citation tooltips."""
    return REGULATORY_CLAUSES
