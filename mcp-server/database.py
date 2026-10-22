"""SQLite persistence for Warranty Vault.

The database is the source of truth: expiry dates and statuses are always
calculated here, never by the language model.
"""
import calendar
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path(os.getenv("WARRANTY_DB", Path(__file__).parent / "warranty.db"))
EXPIRING_SOON_DAYS = int(os.getenv("EXPIRING_SOON_DAYS", "30"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL DEFAULT 'demo',
    product_name TEXT NOT NULL,
    brand TEXT,
    category TEXT,
    purchase_date TEXT NOT NULL,
    purchase_price REAL CHECK (purchase_price IS NULL OR purchase_price >= 0),
    currency TEXT NOT NULL DEFAULT 'USD',
    warranty_duration_months INTEGER CHECK (warranty_duration_months IS NULL OR warranty_duration_months > 0),
    warranty_expiry_date TEXT,
    receipt_path TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    issue_description TEXT NOT NULL,
    draft_subject TEXT NOT NULL,
    draft_body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_purchases_expiry ON purchases(warranty_expiry_date);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # enforce FK constraints
    conn.executescript(SCHEMA)  # idempotent; recreates tables if the file was removed
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def today() -> date:
    return date.today()


def add_months(start: date, months: int) -> date:
    """Calendar-safe month addition (Jan 31 + 1 month -> Feb 28/29)."""
    idx = start.month - 1 + months
    year, month = start.year + idx // 12, idx % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def warranty_status(expiry: Optional[str], ref: Optional[date] = None) -> dict:
    """Return status (active / expiring_soon / expired / unknown) and days remaining."""
    if not expiry:
        return {"status": "unknown", "days_remaining": None}
    ref = ref or today()
    days = (parse_date(expiry) - ref).days
    if days < 0:
        status = "expired"
    elif days <= EXPIRING_SOON_DAYS:
        status = "expiring_soon"
    else:
        status = "active"
    return {"status": status, "days_remaining": days}


def row_to_purchase(row: sqlite3.Row) -> dict:
    d = dict(row)
    d.update(warranty_status(d.get("warranty_expiry_date")))
    return d


def iso_in(days: int) -> str:
    return (today() + timedelta(days=days)).isoformat()
