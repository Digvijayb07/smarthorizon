"""
Cases Router — /api/cases
==========================
CRUD for investigation cases.
Cases are created automatically when an alert fires,
and closed when an analyst makes a decision.
"""

import uuid
import sqlite3
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from database import get_db, log_audit, init_db

router = APIRouter()

# Initialize tables on import
init_db()


# ── Pydantic Models ────────────────────────────────────────────────────────────
class CaseCreate(BaseModel):
    transaction_id:    str
    risk_score:        float
    risk_band:         str
    recommended_action:str
    investigation_data:Optional[dict] = None   # full evidence package JSON


class CaseDecision(BaseModel):
    analyst_id:     str
    decision:       str   # APPROVE_BLOCK | APPROVE_FLAG | DISMISS | ESCALATE
    notes:          Optional[str] = ""


class CaseUpdate(BaseModel):
    status:              Optional[str] = None
    investigation_report:Optional[str] = None
    str_draft:           Optional[str] = None


# ── Helper ────────────────────────────────────────────────────────────────────
def row_to_dict(row) -> dict:
    return dict(row) if row else None


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/")
async def list_cases(
    status: Optional[str] = None,
    risk_band: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    conn: sqlite3.Connection = Depends(get_db)
):
    """List all cases with optional filters. Used by the Case Queue dashboard."""
    query  = "SELECT * FROM cases"
    params = []
    wheres = []

    if status:
        wheres.append("status = ?")
        params.append(status)
    if risk_band:
        wheres.append("risk_band = ?")
        params.append(risk_band)

    if wheres:
        query += " WHERE " + " AND ".join(wheres)

    query += " ORDER BY opened_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]

    return {
        "cases":  [row_to_dict(r) for r in rows],
        "total":  total,
        "limit":  limit,
        "offset": offset,
    }


@router.post("/", status_code=201)
async def create_case(
    body: CaseCreate,
    conn: sqlite3.Connection = Depends(get_db)
):
    """Create a new investigation case from an alert."""
    case_id = f"FC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    now     = datetime.utcnow().isoformat()

    conn.execute("""
        INSERT INTO cases
          (case_id, transaction_id, status, risk_score, risk_band,
           recommended_action, opened_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        case_id, body.transaction_id, "OPEN",
        body.risk_score, body.risk_band, body.recommended_action,
        now, now
    ))
    conn.commit()

    log_audit(conn, case_id, "CASE_OPENED",
              details=f"risk_score={body.risk_score}, band={body.risk_band}")

    return {"case_id": case_id, "status": "OPEN", "opened_at": now}


@router.get("/{case_id}")
async def get_case(
    case_id: str,
    conn: sqlite3.Connection = Depends(get_db)
):
    """Get full case details including linked transaction."""
    case = conn.execute(
        "SELECT * FROM cases WHERE case_id = ?", (case_id,)
    ).fetchone()

    if not case:
        raise HTTPException(404, f"Case {case_id} not found")

    case_dict = row_to_dict(case)

    # Attach transaction data
    txn = conn.execute(
        "SELECT * FROM transactions WHERE transaction_id = ?",
        (case_dict["transaction_id"],)
    ).fetchone()
    case_dict["transaction"] = row_to_dict(txn)

    # Attach sender customer
    if txn and txn["sender_id"]:
        sender = conn.execute(
            "SELECT * FROM customers WHERE customer_id = ?",
            (txn["sender_id"],)
        ).fetchone()
        case_dict["sender"] = row_to_dict(sender)

    # Attach receiver customer
    if txn and txn["receiver_id"]:
        receiver = conn.execute(
            "SELECT * FROM customers WHERE customer_id = ?",
            (txn["receiver_id"],)
        ).fetchone()
        case_dict["receiver"] = row_to_dict(receiver)

    return case_dict


@router.post("/{case_id}/decision")
async def submit_decision(
    case_id: str,
    body: CaseDecision,
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Analyst submits a decision on a case.
    This is the human-in-the-loop step — AI recommends, human decides.
    """
    case = conn.execute(
        "SELECT * FROM cases WHERE case_id = ?", (case_id,)
    ).fetchone()
    if not case:
        raise HTTPException(404, f"Case {case_id} not found")

    valid_decisions = {"APPROVE_BLOCK", "APPROVE_FLAG", "DISMISS", "ESCALATE"}
    if body.decision not in valid_decisions:
        raise HTTPException(400, f"Invalid decision. Must be one of: {valid_decisions}")

    now    = datetime.utcnow().isoformat()
    status = {
        "APPROVE_BLOCK": "CLOSED",
        "APPROVE_FLAG":  "MONITORING",
        "DISMISS":       "CLOSED",
        "ESCALATE":      "ESCALATED",
    }[body.decision]

    conn.execute("""
        UPDATE cases
        SET analyst_id=?, analyst_decision=?, analyst_notes=?,
            status=?, updated_at=?, closed_at=?
        WHERE case_id=?
    """, (
        body.analyst_id, body.decision, body.notes,
        status, now, now if status == "CLOSED" else None,
        case_id
    ))
    conn.commit()

    log_audit(conn, case_id, "ANALYST_DECISION",
              actor=body.analyst_id,
              details=f"decision={body.decision}, notes={body.notes}")

    return {
        "case_id":  case_id,
        "decision": body.decision,
        "status":   status,
        "decided_at": now,
    }


@router.patch("/{case_id}")
async def update_case(
    case_id: str,
    body: CaseUpdate,
    conn: sqlite3.Connection = Depends(get_db)
):
    """Update case fields (report, STR draft, status)."""
    updates = []
    params  = []

    if body.status:
        updates.append("status = ?");              params.append(body.status)
    if body.investigation_report:
        updates.append("investigation_report = ?"); params.append(body.investigation_report)
    if body.str_draft:
        updates.append("str_draft = ?");           params.append(body.str_draft)

    if not updates:
        raise HTTPException(400, "No fields to update")

    updates.append("updated_at = ?"); params.append(datetime.utcnow().isoformat())
    params.append(case_id)

    conn.execute(f"UPDATE cases SET {', '.join(updates)} WHERE case_id = ?", params)
    conn.commit()

    return {"case_id": case_id, "updated": True}


@router.get("/stats/summary")
async def case_stats(conn: sqlite3.Connection = Depends(get_db)):
    """Dashboard stats — case counts by status and risk band."""
    by_status = conn.execute("""
        SELECT status, COUNT(*) as count FROM cases GROUP BY status
    """).fetchall()
    by_band = conn.execute("""
        SELECT risk_band, COUNT(*) as count FROM cases GROUP BY risk_band
    """).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]

    return {
        "total":    total,
        "by_status":[dict(r) for r in by_status],
        "by_band":  [dict(r) for r in by_band],
    }
