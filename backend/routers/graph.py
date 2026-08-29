"""
Graph Agent Router — /api/graph
================================
Two endpoints:

  GET  /api/graph/{case_id}       — Fetches case transactions from DB and builds a
                                    money-flow graph.  Returns nodes + links for the
                                    frontend.  Detects FAN_OUT / FAN_IN patterns.

  POST /api/graph/analyze         — Accepts a validated list of TransactionRecord
                                    objects (via Pydantic schemas from agents/graph_agent)
                                    and returns a clean graph summary.  Used for ad-hoc
                                    analysis without needing a persisted case.

The core graph-building logic lives in:
  backend/agents/graph_agent/builder.py  ← NetworkX DiGraph construction
  backend/agents/graph_agent/service.py  ← analyze_transactions() entry point
  backend/agents/graph_agent/schemas.py  ← TransactionRecord + GraphAnalysisResult
"""
import sqlite3
from typing import Any

import networkx as nx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import get_db
from agents.graph_agent.schemas import TransactionRecord
from agents.graph_agent.service import analyze_transactions

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas for the POST /analyze endpoint
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    transactions: list[TransactionRecord]


# ---------------------------------------------------------------------------
# POST /api/graph/analyze  — validated ad-hoc graph analysis
# ---------------------------------------------------------------------------

@router.post("/analyze")
async def analyze_transaction_graph(body: AnalyzeRequest):
    """
    Accept a list of raw transactions, build a directed graph, and return
    a validated summary (nodes, connections, counts).

    Uses the Pydantic-validated service layer (agents/graph_agent/service.py)
    contributed by the graph-agent branch.
    """
    try:
        result = analyze_transactions(
            [t.model_dump() for t in body.transactions]
        )
        return result
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# GET /api/graph/{case_id}  — case-based graph from DB
# ---------------------------------------------------------------------------

@router.get("/{case_id}")
async def get_transaction_graph(
    case_id: str,
    depth: int = 2,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    """
    Build a money-flow graph for a persisted case.
    Returns nodes (accounts) and edges (transactions) for D3 / react-force-graph.
    Detects FAN_OUT and FAN_IN patterns.
    """
    case = conn.execute(
        "SELECT * FROM cases WHERE case_id = ?", (case_id,)
    ).fetchone()
    if not case:
        raise HTTPException(404, detail=f"Case {case_id} not found")

    txn = conn.execute(
        "SELECT * FROM transactions WHERE transaction_id = ?",
        (dict(case)["transaction_id"],),
    ).fetchone()
    if not txn:
        return {"case_id": case_id, "nodes": [], "links": [], "patterns": []}

    txn_dict = dict(txn)
    G = nx.DiGraph()

    sender_id   = txn_dict.get("sender_account") or txn_dict.get("sender_id", "UNKNOWN")
    receiver_id = txn_dict.get("receiver_account") or txn_dict.get("receiver_id", "UNKNOWN")

    G.add_node(sender_id,   label=sender_id,   type="sender",   risk="HIGH")
    G.add_node(receiver_id, label=receiver_id, type="receiver", risk="UNKNOWN")
    G.add_edge(
        sender_id,
        receiver_id,
        amount=txn_dict.get("amount"),
        transaction_id=txn_dict.get("transaction_id"),
        channel=txn_dict.get("channel", "UPI"),
    )

    # Pattern detection
    patterns: list[dict[str, Any]] = []
    if G.out_degree(sender_id) > 3:
        patterns.append({"type": "FAN_OUT", "node": sender_id, "degree": G.out_degree(sender_id)})
    if G.in_degree(receiver_id) > 3:
        patterns.append({"type": "FAN_IN",  "node": receiver_id, "degree": G.in_degree(receiver_id)})

    nodes = [{"id": n, **G.nodes[n]} for n in G.nodes]
    links = [{"source": u, "target": v, **G.edges[u, v]} for u, v in G.edges]

    return {
        "case_id":  case_id,
        "nodes":    nodes,
        "links":    links,
        "patterns": patterns,
    }
