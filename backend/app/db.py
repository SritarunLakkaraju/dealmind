"""SQLite store for structured data the UI renders (deals, timeline, commitments, outcomes).

Hindsight holds the *memory*; this holds the *records*.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS deals (
    id TEXT PRIMARY KEY, name TEXT, company TEXT, industry TEXT, amount REAL,
    stage TEXT, status TEXT DEFAULT 'open', primary_competitor TEXT, persona TEXT,
    next_meeting TEXT, owner TEXT, created_at TEXT, closed_at TEXT, close_reason TEXT,
    description TEXT
);
CREATE TABLE IF NOT EXISTS stakeholders (
    id INTEGER PRIMARY KEY AUTOINCREMENT, deal_id TEXT, name TEXT, role TEXT,
    stance TEXT, concerns TEXT, updated_at TEXT, UNIQUE(deal_id, name)
);
CREATE TABLE IF NOT EXISTS interactions (
    id TEXT PRIMARY KEY, deal_id TEXT, type TEXT, title TEXT, date TEXT,
    participants TEXT, content TEXT, extraction TEXT, retained INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS commitments (
    id INTEGER PRIMARY KEY AUTOINCREMENT, deal_id TEXT, interaction_id TEXT, owner TEXT,
    who TEXT, what TEXT, due_date TEXT, done INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS suggestions (
    id TEXT PRIMARY KEY, deal_id TEXT, objection TEXT, category TEXT, tactic TEXT,
    response TEXT, created_at TEXT, outcome TEXT
);
CREATE TABLE IF NOT EXISTS tactic_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT, deal_id TEXT, deal_name TEXT, category TEXT,
    persona TEXT, competitor TEXT, tactic TEXT, worked INTEGER, note TEXT, date TEXT
);
CREATE TABLE IF NOT EXISTS briefs (
    deal_id TEXT, memory INTEGER, payload TEXT, created_at TEXT, PRIMARY KEY (deal_id, memory)
);
CREATE TABLE IF NOT EXISTS postmortems (
    deal_id TEXT PRIMARY KEY, result TEXT, text TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS pending_retains (
    id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT, created_at TEXT
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _connect() -> sqlite3.Connection:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def tx() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with tx() as c:
        c.executescript(SCHEMA)


def rows(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    with tx() as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]


def row(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    found = rows(sql, params)
    return found[0] if found else None


def execute(sql: str, params: tuple = ()) -> int:
    with tx() as c:
        cur = c.execute(sql, params)
        return cur.lastrowid or 0


# ---------- convenience helpers ----------

def get_deal(deal_id: str) -> dict | None:
    return row("SELECT * FROM deals WHERE id=?", (deal_id,))


def upsert_stakeholder(deal_id: str, name: str, role: str, stance: str, concerns: list[str]) -> None:
    # Match "Priya" to "Priya Menon" so partial names don't create duplicate people.
    candidates = rows("SELECT * FROM stakeholders WHERE deal_id=?", (deal_id,))
    key = name.strip().lower()
    existing = next((c for c in candidates if c["name"].lower() == key), None) or next(
        (c for c in candidates if c["name"].lower().startswith(key + " ") or key.startswith(c["name"].lower() + " ")), None
    )
    if existing:
        merged = list(dict.fromkeys(json.loads(existing["concerns"] or "[]") + concerns))[-6:]
        execute(
            "UPDATE stakeholders SET role=?, stance=?, concerns=?, updated_at=? WHERE id=?",
            (existing["role"] or role, stance or existing["stance"], json.dumps(merged), now_iso(), existing["id"]),
        )
    else:
        execute(
            "INSERT INTO stakeholders (deal_id, name, role, stance, concerns, updated_at) VALUES (?,?,?,?,?,?)",
            (deal_id, name, role, stance, json.dumps(concerns), now_iso()),
        )


def stakeholders_for(deal_id: str) -> list[dict]:
    out = rows("SELECT * FROM stakeholders WHERE deal_id=? ORDER BY id", (deal_id,))
    for s in out:
        s["concerns"] = json.loads(s["concerns"] or "[]")
    return out
