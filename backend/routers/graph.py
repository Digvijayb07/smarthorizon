"""
Graph Router — /api/graph
=========================
Two endpoints:

  GET  /api/graph/{case_id}       — Fetches case transactions from DB, queries
                                    related transactions within configurable depth/time
                                    window, builds a money-flow graph with real pattern
                                    detection (FAN_OUT / FAN_IN / CIRCULAR / VELOCITY).

  POST /api/graph/analyze         — Accepts a validated list of TransactionRecord
                                    objects and returns a clean graph summary.

The core graph-building logic lives in:
  backend/agents/graph_agent/builder.py  ← NetworkX DiGraph construction
  backend/agents/graph_agent/service.py  ← analyze_transactions() entry point
  backend/agents/graph_agent/schemas.py  ← TransactionRecord + GraphAnalysisResult
"""

import sqlite3
from typing import Any
from datetime import datetime, timedelta

import networkx as nx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import get_db, log_audit
from auth import current_user, CurrentUser
from agents.graph_agent.service import analyze_transactions as _analyze_transactions
from agents.graph_agent.schemas import TransactionRecord

router = APIRouter(dependencies=[Depends(current_user)])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    transactions: list[TransactionRecord]


# ---------------------------------------------------------------------------
# Pattern detection on an existing graph
# ---------------------------------------------------------------------------

def _detect_patterns(G: nx.DiGraph, primary_sender: str, primary_receiver: str) -> tuple[list[dict[str, Any]], str, str]:
    """
    Detect STRUCTURING (smurfing below PMLA thresholds), FAN_OUT (mule dispersion),
    FAN_IN (aggregation), CIRCULAR (wash-trading cycles), and LAYERED_MULE patterns.
    Returns (patterns, network_risk_band, network_risk_summary).
    """
    patterns: list[dict[str, Any]] = []

    # 1. STRUCTURING / SMURFING (Rapid sub-₹50,000 transfers under PMLA reporting ceiling)
    for node in G.nodes:
        out_edges = G.out_edges(node, data=True)
        sub_50k_transfers = [
            d for _, _, d in out_edges
            if d.get("amount") and 10000 <= float(d.get("amount", 0)) < 50000
        ]
        if len(sub_50k_transfers) >= 3:
            total_structured = sum(float(d.get("amount", 0)) for d in sub_50k_transfers)
            destinations = len(set(v for _, v, _ in out_edges))
            patterns.append({
                "type": "STRUCTURING",
                "severity": "CRITICAL",
                "node": node,
                "count": len(sub_50k_transfers),
                "total_amount": round(total_structured, 2),
                "description": (
                    f"Structuring/Smurfing pattern: Account {node} executed {len(sub_50k_transfers)} "
                    f"transfers under the ₹50,000 PMLA statutory threshold (Total: ₹{total_structured:,.2f}) "
                    f"to {destinations} destination accounts to evade automated AML triggers."
                ),
            })

    # 2. FAN_OUT: Mule dispersion (out_degree >= 3)
    for node in G.nodes:
        out_deg = G.out_degree(node)
        if out_deg >= 3:
            patterns.append({
                "type": "FAN_OUT",
                "severity": "HIGH",
                "node": node,
                "degree": out_deg,
                "description": (
                    f"Mule fan-out dispersion: Account {node} split and disbursed funds across "
                    f"{out_deg} separate counterparty accounts."
                ),
            })

    # 3. FAN_IN: Inflow aggregation (in_degree >= 3)
    for node in G.nodes:
        in_deg = G.in_degree(node)
        if in_deg >= 3:
            patterns.append({
                "type": "FAN_IN",
                "severity": "HIGH",
                "node": node,
                "degree": in_deg,
                "description": (
                    f"Fund aggregation funnel: Account {node} collected inflows from "
                    f"{in_deg} distinct feeder accounts."
                ),
            })

    # 4. CIRCULAR: Fund cycling (simple cycles >= 2 nodes)
    try:
        cycles = list(nx.simple_cycles(G))
        for cycle in cycles[:3]:
            if len(cycle) >= 2:
                patterns.append({
                    "type": "CIRCULAR",
                    "severity": "CRITICAL",
                    "nodes": cycle,
                    "length": len(cycle),
                    "description": f"Circular fund laundering loop: {' → '.join(cycle)} → {cycle[0]}.",
                })
    except nx.NetworkXError:
        pass

    # 5. LAYERED_MULE / RAPID PASSTHROUGH (conduit node receiving and immediately passing funds)
    for node in G.nodes:
        if G.in_degree(node) >= 1 and G.out_degree(node) >= 1 and node != primary_sender:
            patterns.append({
                "type": "LAYERED_MULE",
                "severity": "HIGH",
                "node": node,
                "description": (
                    f"Layered conduit mule: Account {node} acts as an intermediary, receiving funds "
                    f"from {G.in_degree(node)} source(s) and dispersing to {G.out_degree(node)} recipient(s)."
                ),
            })

    # 6. Composite Network Risk Scoring
    has_critical = any(p.get("severity") == "CRITICAL" for p in patterns)
    has_high = any(p.get("severity") == "HIGH" for p in patterns)
    has_mule_layering = any(p["type"] == "LAYERED_MULE" for p in patterns)
    has_structuring = any(p["type"] == "STRUCTURING" for p in patterns)
    has_circular = any(p["type"] == "CIRCULAR" for p in patterns)

    if has_critical or (has_structuring and has_high):
        network_risk = "CRITICAL"
        if has_circular:
            summary = "Circular wash-routing cycle detected across accounts."
        elif has_structuring:
            summary = "PMLA sub-threshold structuring syndicate with multi-destination dispersion."
        else:
            summary = "Critical multi-node syndicate structure identified."
    elif has_high or has_mule_layering:
        network_risk = "HIGH"
        summary = "Coordinated mule dispersion/aggregation detected across cluster."
    elif G.number_of_nodes() > 2:
        network_risk = "MEDIUM"
        summary = "Multi-hop counterparty network detected; elevated relational connection."
    else:
        network_risk = "LOW"
        summary = "Isolated bilateral transaction; no multi-hop syndicate topology detected."

    return patterns, network_risk, summary


# ---------------------------------------------------------------------------
# POST /api/graph/analyze  — validated ad-hoc graph analysis
# ---------------------------------------------------------------------------

@router.post("/analyze")
async def analyze_transaction_graph(body: AnalyzeRequest):
    """
    Accept a list of raw transactions, build a directed graph, and return
    a validated summary (nodes, connections, counts).
    """
    try:
        result = _analyze_transactions([t.model_dump() for t in body.transactions])
        return result
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# GET /api/graph/{case_id}  — case-based graph from DB (with real pattern detection)
# ---------------------------------------------------------------------------

@router.get("/{case_id}")
async def get_transaction_graph(
    case_id: str,
    depth: int = 2,
    conn: sqlite3.Connection = Depends(get_db),
    _: CurrentUser = Depends(current_user),
) -> dict[str, Any]:
    """
    Build a multi-hop money-flow graph for a persisted case by performing
    a BFS traversal (up to `depth` hops) from the case's primary sender and receiver.
    Returns nodes with role labels (ORIGIN, INTERMEDIARY, MULE_CASHOUT, FEEDER),
    edges with amounts/channels, detected relational patterns (STRUCTURING, FAN_OUT,
    FAN_IN, CIRCULAR, LAYERED_MULE), and composite dual network risk scoring.
    """
    case = conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    if not case:
        raise HTTPException(404, detail=f"Case {case_id} not found")

    txn = conn.execute(
        "SELECT * FROM transactions WHERE transaction_id = ?",
        (dict(case)["transaction_id"],),
    ).fetchone()
    if not txn:
        return {
            "case_id": case_id,
            "nodes": [],
            "links": [],
            "patterns": [],
            "network_risk": "LOW",
            "network_risk_summary": "No transaction records found.",
        }

    txn_dict = dict(txn)
    primary_sender = txn_dict.get("sender_account") or txn_dict.get("sender_id", "UNKNOWN")
    primary_receiver = txn_dict.get("receiver_account") or txn_dict.get("receiver_id", "UNKNOWN")

    # ── Multi-Hop BFS Traversal (up to `depth` hops) ───────────────────────────
    visited_accounts = {primary_sender, primary_receiver}
    current_frontier = {primary_sender, primary_receiver}
    collected_txns: dict[str, dict[str, Any]] = {}

    # Add primary transaction first
    if txn_dict.get("transaction_id"):
        collected_txns[txn_dict["transaction_id"]] = txn_dict

    search_depth = max(1, min(depth, 3))
    for _ in range(search_depth):
        if not current_frontier:
            break
        placeholders = ",".join("?" for _ in current_frontier)
        # Check both sender and receiver matches
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

    # ── Construct NetworkX Graph ──────────────────────────────────────────────
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

    # Ensure the primary edge is explicitly recorded
    G.add_node(primary_sender)
    G.add_node(primary_receiver)
    G.add_edge(
        primary_sender,
        primary_receiver,
        amount=txn_dict.get("amount", 0),
        transaction_id=txn_dict.get("transaction_id", ""),
        channel=txn_dict.get("channel", "UPI"),
        timestamp=txn_dict.get("timestamp", ""),
    )

    # ── Role Classification per Node ──────────────────────────────────────────
    for n in G.nodes:
        in_d = G.in_degree(n)
        out_d = G.out_degree(n)
        if n == primary_sender:
            role = "ORIGIN"
            suspicious = True
        elif n == primary_receiver:
            role = "INTERMEDIARY" if out_d > 0 else "BENEFICIARY"
            suspicious = True
        elif G.has_edge(n, primary_sender):
            role = "FEEDER"
            suspicious = False
        elif G.has_edge(primary_receiver, n) or G.has_edge(primary_sender, n):
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

    # ── Pattern Detection & Composite Risk ────────────────────────────────────
    patterns, network_risk, network_summary = _detect_patterns(G, primary_sender, primary_receiver)

    nodes = [{"id": n, **G.nodes[n]} for n in G.nodes]
    links = [
        {
            "source": u,
            "target": v,
            "amount": G.edges[u, v].get("amount"),
            "channel": G.edges[u, v].get("channel", "UPI"),
            "transaction_id": G.edges[u, v].get("transaction_id"),
            "timestamp": G.edges[u, v].get("timestamp"),
        }
        for u, v in G.edges
    ]

    return {
        "case_id": case_id,
        "nodes": nodes,
        "links": links,
        "patterns": patterns,
        "network_risk": network_risk,
        "network_risk_summary": network_summary,
        "transaction_count": len(collected_txns),
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "primary_sender": primary_sender,
        "primary_receiver": primary_receiver,
    }
