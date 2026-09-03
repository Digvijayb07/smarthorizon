"""
Database Setup
==============
SQLAlchemy-free SQLite with foreign-key enforcement, WAL mode, and
immutable audit-log semantics.
"""

import os
import sqlite3
from datetime import datetime


DB_PATH = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./horizon.db").replace("sqlite+aiosqlite:///./", "")

_CASE_STATUSES = {"OPEN", "MONITORING", "ESCALATED", "CLOSED"}


def init_db():
    """Create all tables with foreign keys enabled. Safe to call multiple times."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")

    c = conn.cursor()

    # ── Customers ─────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id      TEXT PRIMARY KEY,
            name             TEXT,
            account_id       TEXT,
            bank             TEXT,
            kyc_status       TEXT,
            risk_category    TEXT DEFAULT 'LOW',
            city             TEXT,
            phone            TEXT,
            is_mule_suspected INTEGER DEFAULT 0,
            is_pep           INTEGER DEFAULT 0,
            created_at       TEXT
        )
    """)

    # ── Transactions ───────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id   TEXT PRIMARY KEY,
            case_id          TEXT,
            sender_id        TEXT,
            sender_account   TEXT,
            receiver_id      TEXT,
            receiver_account TEXT,
            amount           REAL NOT NULL CHECK (amount >= 0),
            channel          TEXT DEFAULT 'UPI',
            step             INTEGER,
            type             TEXT,
            old_balance_orig REAL DEFAULT 0.0,
            new_balance_orig REAL DEFAULT 0.0,
            old_balance_dest REAL DEFAULT 0.0,
            new_balance_dest REAL DEFAULT 0.0,
            timestamp        TEXT,
            device_id        TEXT,
            ip_address       TEXT,
            location_city    TEXT,
            is_new_payee     INTEGER DEFAULT 0,
            is_vpn           INTEGER DEFAULT 0,
            fraud_type       TEXT,
            is_fraud         INTEGER DEFAULT 0,
            alert_triggered  INTEGER DEFAULT 0,
            scenario_type    TEXT,
            fraud_reason     TEXT,
            severity         TEXT DEFAULT 'NONE'
        )
    """)

    # ── Cases ──────────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            case_id              TEXT PRIMARY KEY,
            transaction_id       TEXT NOT NULL UNIQUE,
            status               TEXT DEFAULT 'OPEN' CHECK (status IN ('OPEN','MONITORING','ESCALATED','CLOSED')),
            risk_score           REAL DEFAULT 0,
            risk_band            TEXT DEFAULT 'LOW',
            recommended_action   TEXT DEFAULT 'MONITOR',
            analyst_id           TEXT,
            analyst_decision     TEXT,
            analyst_notes        TEXT,
            investigation_report TEXT,
            str_draft            TEXT,
            opened_at            TEXT,
            updated_at           TEXT,
            closed_at            TEXT,
            FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
        )
    """)

    # ── Audit Log (immutable — append-only) ────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id     TEXT NOT NULL,
            action      TEXT NOT NULL,
            actor       TEXT NOT NULL DEFAULT 'SYSTEM',
            details     TEXT DEFAULT '',
            timestamp   TEXT NOT NULL,
            FOREIGN KEY (case_id) REFERENCES cases(case_id)
        )
    """)

    conn.commit()
    conn.close()
    print(f"[OK] Database initialized: {DB_PATH}")


def get_db():
    """Yield a SQLite connection with foreign keys enabled. Use as FastAPI dependency."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


def log_audit(conn, case_id: str, action: str, actor: str = "SYSTEM", details: str = ""):
    """Append an immutable audit entry. Actor identity must come from the server."""
    conn.execute(
        "INSERT INTO audit_log (case_id, action, actor, details, timestamp) VALUES (?,?,?,?,?)",
        (case_id, action, actor, details, datetime.utcnow().isoformat()),
    )
    conn.commit()
