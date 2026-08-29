"""
Horizon — Database Setup
========================
SQLAlchemy async models + table creation.
Run init_db() once on startup.
"""

import os
import sqlite3
from datetime import datetime


DB_PATH = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./horizon.db").replace("sqlite+aiosqlite:///./", "")


def init_db():
    """Create all tables if they don't exist. Safe to call multiple times."""
    conn = sqlite3.connect(DB_PATH)
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
            amount           REAL,
            channel          TEXT DEFAULT 'UPI',
            step             INTEGER,
            type             TEXT,
            old_balance_orig REAL,
            new_balance_orig REAL,
            old_balance_dest REAL,
            new_balance_dest REAL,
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
            transaction_id       TEXT,
            status               TEXT DEFAULT 'OPEN',
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
            closed_at            TEXT
        )
    """)

    # ── Audit Log ──────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id     TEXT,
            action      TEXT,
            actor       TEXT DEFAULT 'SYSTEM',
            details     TEXT,
            timestamp   TEXT
        )
    """)

    conn.commit()
    conn.close()
    print(f"[OK] Database initialized: {DB_PATH}")


def get_db():
    """Yield a SQLite connection. Use as dependency in FastAPI routes."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row   # rows behave like dicts
    try:
        yield conn
    finally:
        conn.close()


def log_audit(conn, case_id: str, action: str, actor: str = "SYSTEM", details: str = ""):
    """Append an immutable audit entry."""
    conn.execute(
        "INSERT INTO audit_log (case_id, action, actor, details, timestamp) VALUES (?,?,?,?,?)",
        (case_id, action, actor, details, datetime.utcnow().isoformat())
    )
    conn.commit()
