"""
SQLite persistence. 4 tables: leads, outreach_drafts, replies, conversions.
Simple functions, no ORM.
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from openclaw import config

log = logging.getLogger("openclaw.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id                  TEXT PRIMARY KEY,
    business_name       TEXT NOT NULL,
    owner_name          TEXT DEFAULT '',
    email               TEXT DEFAULT '',
    phone               TEXT DEFAULT '',
    category            TEXT DEFAULT '',
    metro               TEXT DEFAULT '',
    rating              REAL DEFAULT 0.0,
    review_count        INTEGER DEFAULT 0,
    has_website         INTEGER DEFAULT 0,
    website_url         TEXT DEFAULT '',
    gbp_link            TEXT DEFAULT '',
    source              TEXT DEFAULT '',
    qualification_score INTEGER DEFAULT 0,
    roi_estimate_monthly INTEGER DEFAULT 0,
    review_themes       TEXT DEFAULT '[]',
    last_review_date    TEXT DEFAULT '',
    review_excerpt      TEXT DEFAULT '',
    review_excerpt_author TEXT DEFAULT '',
    review_excerpt_date TEXT DEFAULT '',
    tier                TEXT DEFAULT '',
    preview_url         TEXT DEFAULT '',
    preview_path        TEXT DEFAULT '',
    lead_status         TEXT DEFAULT 'new',
    manual_override     INTEGER DEFAULT 0,
    human_notes         TEXT DEFAULT '',
    created_at          TEXT DEFAULT '',
    updated_at          TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(lead_status);

CREATE TABLE IF NOT EXISTS outreach_drafts (
    id              TEXT PRIMARY KEY,
    lead_id         TEXT REFERENCES leads(id),
    subject         TEXT DEFAULT '',
    body            TEXT DEFAULT '',
    followup_number INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'draft',
    scheduled_for   TEXT DEFAULT '',
    sent_at         TEXT DEFAULT '',
    message_id      TEXT DEFAULT '',
    error           TEXT DEFAULT '',
    created_at      TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_drafts_status ON outreach_drafts(status);
CREATE INDEX IF NOT EXISTS idx_drafts_lead ON outreach_drafts(lead_id);

CREATE TABLE IF NOT EXISTS replies (
    id              TEXT PRIMARY KEY,
    lead_id         TEXT REFERENCES leads(id),
    from_email      TEXT DEFAULT '',
    subject         TEXT DEFAULT '',
    in_reply_to     TEXT DEFAULT '',
    raw_body        TEXT DEFAULT '',
    reply_type      TEXT DEFAULT 'other',
    created_at      TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS conversions (
    id          TEXT PRIMARY KEY,
    lead_id     TEXT REFERENCES leads(id),
    deal_value  REAL DEFAULT 0.0,
    status      TEXT DEFAULT '',
    created_at  TEXT DEFAULT ''
);
"""


@contextmanager
def get_db():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as db:
        db.executescript(_SCHEMA)
    _ensure_columns()
    print(f"Database initialized at {config.DB_PATH}")


def _ensure_columns():
    """Lightweight migration: add columns if they don't exist yet."""
    migrations = [
        ("replies", "subject", "TEXT DEFAULT ''"),
        ("replies", "in_reply_to", "TEXT DEFAULT ''"),
        ("leads", "last_review_date", "TEXT DEFAULT ''"),
        ("leads", "review_excerpt", "TEXT DEFAULT ''"),
        ("leads", "review_excerpt_author", "TEXT DEFAULT ''"),
        ("leads", "review_excerpt_date", "TEXT DEFAULT ''"),
    ]
    with get_db() as db:
        for table, col, col_type in migrations:
            try:
                db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
                log.info("Added column %s.%s", table, col)
            except sqlite3.OperationalError:
                pass  # column already exists


def db_exists() -> bool:
    """Check if the database file exists."""
    from pathlib import Path
    return Path(config.DB_PATH).exists()


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------

def insert_lead(lead: dict):
    d = dict(lead)
    if isinstance(d.get("has_website"), bool):
        d["has_website"] = int(d["has_website"])
    if isinstance(d.get("manual_override"), bool):
        d["manual_override"] = int(d["manual_override"])
    if isinstance(d.get("review_themes"), list):
        d["review_themes"] = json.dumps(d["review_themes"])
    cols = ", ".join(d.keys())
    vals = ", ".join(["?"] * len(d))
    with get_db() as db:
        db.execute(f"INSERT OR IGNORE INTO leads ({cols}) VALUES ({vals})", list(d.values()))


def update_lead(lead_id: str, **kwargs):
    kwargs["updated_at"] = datetime.utcnow().isoformat()
    if "has_website" in kwargs and isinstance(kwargs["has_website"], bool):
        kwargs["has_website"] = int(kwargs["has_website"])
    if "manual_override" in kwargs and isinstance(kwargs["manual_override"], bool):
        kwargs["manual_override"] = int(kwargs["manual_override"])
    if "review_themes" in kwargs and isinstance(kwargs["review_themes"], list):
        kwargs["review_themes"] = json.dumps(kwargs["review_themes"])
    sets = ", ".join(f"{k}=?" for k in kwargs)
    with get_db() as db:
        db.execute(f"UPDATE leads SET {sets} WHERE id=?", list(kwargs.values()) + [lead_id])


def get_lead(lead_id: str) -> dict | None:
    with get_db() as db:
        row = db.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
        return _lead_row(row) if row else None


def get_leads_by_status(status: str, limit: int = 200) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM leads WHERE lead_status=? AND manual_override=0 "
            "ORDER BY qualification_score DESC LIMIT ?",
            (status, limit),
        ).fetchall()
        return [_lead_row(r) for r in rows]


def lead_exists(email: str = "", business_name: str = "", metro: str = "") -> bool:
    with get_db() as db:
        if email:
            if db.execute("SELECT 1 FROM leads WHERE email=?", (email,)).fetchone():
                return True
        if business_name and metro:
            if db.execute(
                "SELECT 1 FROM leads WHERE business_name=? AND metro=?",
                (business_name, metro),
            ).fetchone():
                return True
    return False


def count_leads_by_status() -> dict:
    with get_db() as db:
        rows = db.execute(
            "SELECT lead_status, COUNT(*) as cnt FROM leads GROUP BY lead_status"
        ).fetchall()
        return {r["lead_status"]: r["cnt"] for r in rows}


def _lead_row(row) -> dict:
    d = dict(row)
    d["has_website"] = bool(d.get("has_website", 0))
    d["manual_override"] = bool(d.get("manual_override", 0))
    try:
        d["review_themes"] = json.loads(d.get("review_themes", "[]"))
    except (json.JSONDecodeError, TypeError):
        d["review_themes"] = []
    return d


# ---------------------------------------------------------------------------
# Outreach Drafts
# ---------------------------------------------------------------------------

def insert_draft(draft: dict):
    d = dict(draft)
    cols = ", ".join(d.keys())
    vals = ", ".join(["?"] * len(d))
    with get_db() as db:
        db.execute(f"INSERT INTO outreach_drafts ({cols}) VALUES ({vals})", list(d.values()))


def get_drafts_by_status(status: str, limit: int = 100) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT d.*, l.business_name, l.owner_name, l.email, l.metro "
            "FROM outreach_drafts d JOIN leads l ON d.lead_id = l.id "
            "WHERE d.status=? ORDER BY d.created_at LIMIT ?",
            (status, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def update_draft(draft_id: str, **kwargs):
    sets = ", ".join(f"{k}=?" for k in kwargs)
    with get_db() as db:
        db.execute(
            f"UPDATE outreach_drafts SET {sets} WHERE id=?",
            list(kwargs.values()) + [draft_id],
        )


def get_draft(draft_id: str) -> dict | None:
    with get_db() as db:
        row = db.execute(
            "SELECT d.*, l.business_name, l.owner_name, l.email, l.metro "
            "FROM outreach_drafts d JOIN leads l ON d.lead_id = l.id "
            "WHERE d.id=?",
            (draft_id,),
        ).fetchone()
        return dict(row) if row else None


def count_drafts_by_status() -> dict:
    with get_db() as db:
        rows = db.execute(
            "SELECT status, COUNT(*) as cnt FROM outreach_drafts GROUP BY status"
        ).fetchall()
        return {r["status"]: r["cnt"] for r in rows}


def get_lead_draft_count(lead_id: str) -> int:
    with get_db() as db:
        row = db.execute(
            "SELECT COUNT(*) as cnt FROM outreach_drafts WHERE lead_id=?",
            (lead_id,),
        ).fetchone()
        return row["cnt"] if row else 0


def draft_exists(lead_id: str, followup_number: int) -> bool:
    """Check if a draft already exists for this lead + followup_number."""
    with get_db() as db:
        row = db.execute(
            "SELECT 1 FROM outreach_drafts "
            "WHERE lead_id=? AND followup_number=? AND status NOT IN ('cancelled', 'failed')",
            (lead_id, followup_number),
        ).fetchone()
        return row is not None


def get_sent_message_ids_for_lead(lead_id: str) -> list[str]:
    """Get all message_ids for sent drafts to a lead (for reply threading)."""
    with get_db() as db:
        rows = db.execute(
            "SELECT message_id FROM outreach_drafts "
            "WHERE lead_id=? AND status='sent' AND message_id != ''",
            (lead_id,),
        ).fetchall()
        return [r["message_id"] for r in rows]


# ---------------------------------------------------------------------------
# Replies
# ---------------------------------------------------------------------------

def insert_reply(reply: dict):
    d = dict(reply)
    cols = ", ".join(d.keys())
    vals = ", ".join(["?"] * len(d))
    with get_db() as db:
        db.execute(f"INSERT INTO replies ({cols}) VALUES ({vals})", list(d.values()))


def get_replies(limit: int = 50) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT r.*, l.business_name, l.owner_name, l.metro "
            "FROM replies r JOIN leads l ON r.lead_id = l.id "
            "ORDER BY r.created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_lead_id_by_email(email: str) -> str | None:
    with get_db() as db:
        row = db.execute("SELECT id FROM leads WHERE email=?", (email,)).fetchone()
        return row["id"] if row else None


def get_lead_id_by_message_thread(in_reply_to: str = "", references: str = "") -> str | None:
    """Match a reply to a lead via In-Reply-To or References headers."""
    if not in_reply_to and not references:
        return None
    with get_db() as db:
        # Check In-Reply-To first (most reliable)
        if in_reply_to:
            row = db.execute(
                "SELECT lead_id FROM outreach_drafts "
                "WHERE message_id=? AND status='sent' LIMIT 1",
                (in_reply_to.strip(),),
            ).fetchone()
            if row:
                return row["lead_id"]
        # Check References header (space-separated message IDs)
        if references:
            for ref in references.split():
                ref = ref.strip().strip("<>")
                if ref:
                    row = db.execute(
                        "SELECT lead_id FROM outreach_drafts "
                        "WHERE message_id=? AND status='sent' LIMIT 1",
                        (ref,),
                    ).fetchone()
                    if row:
                        return row["lead_id"]
    return None


# ---------------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------------

def insert_conversion(conv: dict):
    d = dict(conv)
    cols = ", ".join(d.keys())
    vals = ", ".join(["?"] * len(d))
    with get_db() as db:
        db.execute(f"INSERT INTO conversions ({cols}) VALUES ({vals})", list(d.values()))


def get_conversion_stats() -> dict:
    with get_db() as db:
        total = db.execute("SELECT COUNT(*) as c FROM conversions").fetchone()["c"]
        won = db.execute("SELECT COUNT(*) as c FROM conversions WHERE status='won'").fetchone()["c"]
        lost = db.execute("SELECT COUNT(*) as c FROM conversions WHERE status='lost'").fetchone()["c"]
        revenue = db.execute(
            "SELECT COALESCE(SUM(deal_value), 0) as t FROM conversions WHERE status='won'"
        ).fetchone()["t"]
        return {"total": total, "won": won, "lost": lost, "revenue": revenue}


# ---------------------------------------------------------------------------
# Aggregate stats
# ---------------------------------------------------------------------------

def get_reply_count() -> int:
    with get_db() as db:
        return db.execute("SELECT COUNT(*) as c FROM replies").fetchone()["c"]


def get_positive_reply_count() -> int:
    with get_db() as db:
        return db.execute(
            "SELECT COUNT(*) as c FROM replies WHERE reply_type='positive'"
        ).fetchone()["c"]


def get_total_roi_pipeline() -> int:
    """ROI estimate for active pipeline (qualified through sent)."""
    with get_db() as db:
        return db.execute(
            "SELECT COALESCE(SUM(roi_estimate_monthly), 0) as t "
            "FROM leads WHERE lead_status IN ('qualified', 'draft_ready', 'approved', 'sent')"
        ).fetchone()["t"]


def get_closed_revenue() -> float:
    """Sum of deal_value for WON conversions."""
    with get_db() as db:
        return db.execute(
            "SELECT COALESCE(SUM(deal_value), 0) as t FROM conversions WHERE status='won'"
        ).fetchone()["t"]
