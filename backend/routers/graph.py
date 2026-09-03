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

def _detect_patterns(G: nx.DiGraph, sender_id: str, receiver_id: str) -> list[dict[str, Any]]:
    """Detect FAN_OUT, FAN_IN, CIRCULAR, VELOCITY, and MULE_NETWORK patterns."""
    patterns: list[dict[str, Any]] = []

    out_deg = G.out_degree(sender_id)
    in_deg = G.in_degree(receiver_id)

    # FAN_OUT: sender has >3 unique outbound destinations
    if out_deg > 3:
        patterns.append({
            "type": "FAN_OUT",
            "node": sender_id,
            "degree": out_deg,
            "description": f"Account {sender_id} sent funds to {out_deg} unique destinations — classic mule fan-out pattern.",
        })

    # FAN_IN: receiver has >3 unique inbound sources
    if in_deg > 3:
        patterns.append({
            "type": "FAN_IN",
            "node": receiver_id,
            "degree": in_deg,
            "description": f"Account {receiver_id} received funds from {in_deg} unique sources — fan-in aggregation pattern.",
        })

    # CIRCULAR: detect any simple cycle in the graph
    try:
        cycles = list(nx.simple_cycles(G))
        for cycle in cycles[:5]:  # limit to 5 detected cycles
            patterns.append({
                "type": "CIRCULAR",
                "nodes": cycle,
                "length": len(cycle),
                "description": f"Circular fund flow detected: {' → '.join(cycle)} → {cycle[0]}.",
            })
    except nx.NetworkXError:
        pass

    # VELOCITY: if sender has >5 outbound edges, flag velocity
    if out_deg > 5:
        patterns.append({
            "type": "VELOCITY",
            "node": sender_id,
            "count": out_deg,
            "description": f"High-velocity outbound pattern: {out_deg} transfers in the analysis window.",
        })

    # MULE_NETWORK: combination of fan-out + circular patterns
    has_fan_out = any(p["type"] == "FAN_OUT" for p in patterns)
    has_circular = any(p["type"] == "CIRCULAR" for p in patterns)
    if has_fan_out and has_circular:
        patterns.append({
            "type": "MULE_NETWORK",
            "description": "Combined fan-out + circular flow pattern detected — strong mule network indicator.",
        })

    return patterns


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
    Build a money-flow graph for a persisted case by querying ALL related
    transactions for the sender and receiver accounts (within configurable depth).
    Returns nodes (accounts) and edges (transactions) for D3 / react-force-graph.
    Detects FAN_OUT, FAN_IN, CIRCULAR, VELOCITY, and MULE_NETWORK patterns.
    """
    case = conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    if not case:
        raise HTTPException(404, detail=f"Case {case_id} not found")

    txn = conn.execute(
        "SELECT * FROM transactions WHERE transaction_id = ?",
        (dict(case)["transaction_id"],),
    ).fetchone()
    if not txn:
        return {"case_id": case_id, "nodes": [], "links": [], "patterns": []}

    txn_dict = dict(txn)
    sender_account = txn_dict.get("sender_account") or txn_dict.get("sender_id", "UNKNOWN")
    receiver_account = txn_dict.get("receiver_account") or txn_dict.get("receiver_id", "UNKNOWN")

    # Query ALL related transactions for sender and receiver (not just the single one)
    related_txns = conn.execute(
        """SELECT * FROM transactions
           WHERE sender_account = ? OR receiver_account = ?
              OR sender_id = ? OR receiver_id = ?
           ORDER BY timestamp ASC""",
        (sender_account, receiver_account, sender_account, receiver_account),
    ).fetchall()

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

    patterns = _detect_patterns(G, sender_account, receiver_account)

    nodes = [{"id": n, **G.nodes[n]} for n in G.nodes]
    links = [{"source": u, "target": v, **G.edges[u, v]} for u, v in G.edges]

    return {
        "case_id": case_id,
        "nodes": nodes,
        "links": links,
        "patterns": patterns,
        "transaction_count": len(related_txns),
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
    }
