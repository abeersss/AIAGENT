"""Transactional calendar event store (SQLite) with approvals and a global commit log.

Every state change (event write, approval grant, approval revocation, benign concurrent
edit) is appended to `log` inside the same transaction that makes the change, so the
log's `seq` column is the commit order. The independent outcome oracle (oracle.py) reads
only this log and the approvals table; it never trusts a gateway's own verdict.
"""
from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
    approval_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    action TEXT NOT NULL,
    event_id TEXT,                 -- NULL for create
    constraints TEXT NOT NULL,     -- JSON, see policy.py
    expected_version INTEGER,      -- NULL = not version-bound (create)
    status TEXT NOT NULL,          -- active | revoked
    granted_seq INTEGER NOT NULL,
    revoked_seq INTEGER
);
CREATE TABLE IF NOT EXISTS log (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,            -- write | grant | revoke | benign_edit
    actor TEXT NOT NULL,
    action TEXT,
    event_id TEXT,
    args TEXT,
    approval_id INTEGER,
    version_before INTEGER,
    version_after INTEGER,
    gateway TEXT,
    reason TEXT,                   -- denial reason (kind = deny)
    data_before TEXT,              -- full event row before the change / at the denied attempt
    data_after TEXT,               -- full event row after the change
    ts REAL NOT NULL
);
"""

TIME_FMT = "%Y-%m-%d %H:%M"


def _dt(s: str) -> datetime:
    return datetime.strptime(s, TIME_FMT)


def _iso(d: datetime) -> str:
    return d.isoformat()


@dataclass
class EventRow:
    id: str
    version: int
    data: dict


class EventStore:
    """One SQLite database file; open several connections for concurrency tests."""

    def __init__(self, path: str, timeout: float = 30.0):
        self.path = path
        self.conn = sqlite3.connect(path, timeout=timeout, isolation_level=None, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=DELETE")
        self.conn.executescript(SCHEMA)

    def other_connection(self) -> "EventStore":
        return EventStore(self.path)

    # -- transactions ---------------------------------------------------------------
    @contextmanager
    def txn(self):
        """BEGIN IMMEDIATE takes SQLite's RESERVED lock up front, so two write
        transactions are serialized: whichever acquires the lock first commits first."""
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield self.conn
            self.conn.execute("COMMIT")
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise

    def _log(self, c, kind, actor, action=None, event_id=None, args=None, approval_id=None,
             vb=None, va=None, gateway=None, reason=None, before=None, after=None) -> int:
        cur = c.execute(
            "INSERT INTO log(kind, actor, action, event_id, args, approval_id, version_before, version_after,"
            " gateway, reason, data_before, data_after, ts) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (kind, actor, action, event_id, json.dumps(args) if args is not None else None, approval_id,
             vb, va, gateway, reason, json.dumps(before) if before is not None else None,
             json.dumps(after) if after is not None else None, time.time()))
        return cur.lastrowid

    def log_denial(self, c, action, args, event_id, reason, gateway, version=None):
        row = self.get_event(event_id, c) if event_id is not None else None
        return self._log(c, "deny", "agent", action, event_id, args, None, version, None, gateway, reason,
                         before=row.data if row else None)

    # -- loading -------------------------------------------------------------------
    def load_events(self, calendar) -> None:
        with self.txn() as c:
            for ev in calendar.events.values():
                c.execute("INSERT INTO events(id, version, data) VALUES (?,?,?)",
                          (ev.id_, 1, ev.model_dump_json()))

    # -- reads ---------------------------------------------------------------------
    def get_event(self, event_id: str, c=None) -> EventRow | None:
        c = c or self.conn
        r = c.execute("SELECT id, version, data FROM events WHERE id=?", (event_id,)).fetchone()
        return EventRow(r[0], r[1], json.loads(r[2])) if r else None

    def next_event_id(self, c) -> str:
        r = c.execute("SELECT MAX(CAST(id AS INTEGER)) FROM events").fetchone()
        return str((r[0] or 0) + 1)

    def approvals(self, c=None) -> list[dict]:
        c = c or self.conn
        cols = ["approval_id", "user", "action", "event_id", "constraints", "expected_version", "status",
                "granted_seq", "revoked_seq"]
        out = []
        for r in c.execute(f"SELECT {', '.join(cols)} FROM approvals ORDER BY approval_id"):
            d = dict(zip(cols, r))
            d["constraints"] = json.loads(d["constraints"])
            snap = c.execute("SELECT data_before FROM log WHERE seq=?", (d["granted_seq"],)).fetchone()
            d["snapshot"] = json.loads(snap[0]) if snap and snap[0] else None
            out.append(d)
        return out

    def log_rows(self) -> list[dict]:
        cols = ["seq", "kind", "actor", "action", "event_id", "args", "approval_id", "version_before",
                "version_after", "gateway", "reason", "data_before", "data_after", "ts"]
        out = []
        for r in self.conn.execute(f"SELECT {', '.join(cols)} FROM log ORDER BY seq"):
            d = dict(zip(cols, r))
            for k in ("args", "data_before", "data_after"):
                d[k] = json.loads(d[k]) if d[k] else None
            out.append(d)
        return out

    # -- approvals (trusted fixture only) ------------------------------------------
    def grant(self, user, action, event_id, constraints, expected_version) -> int:
        with self.txn() as c:
            row = self.get_event(event_id, c) if event_id is not None else None
            seq = self._log(c, "grant", "fixture", action, event_id, constraints, vb=expected_version,
                            before=row.data if row else None)
            cur = c.execute(
                "INSERT INTO approvals(user, action, event_id, constraints, expected_version, status, granted_seq)"
                " VALUES (?,?,?,?,?, 'active', ?)",
                (user, action, event_id, json.dumps(constraints), expected_version, seq))
            aid = cur.lastrowid
            c.execute("UPDATE log SET approval_id=? WHERE seq=?", (aid, seq))
            return aid

    def revoke(self, approval_id: int) -> int:
        with self.txn() as c:
            seq = self._log(c, "revoke", "fixture", approval_id=approval_id)
            c.execute("UPDATE approvals SET status='revoked', revoked_seq=? WHERE approval_id=? AND status='active'",
                      (seq, approval_id))
            return seq

    # -- benign concurrent edit (another user / device) ------------------------------
    def benign_edit(self, event_id: str, note: str) -> tuple[int, int]:
        with self.txn() as c:
            row = self.get_event(event_id, c)
            before = json.loads(json.dumps(row.data))
            data = row.data
            data["description"] = (data.get("description") or "") + note
            c.execute("UPDATE events SET version=?, data=? WHERE id=?", (row.version + 1, json.dumps(data), event_id))
            seq = self._log(c, "benign_edit", "other_user", "edit_description", event_id, {"append": note},
                            vb=row.version, va=row.version + 1, before=before, after=data)
            return seq, row.version + 1

    def related_edit(self, event_id: str, kind: str) -> tuple[int, int, dict]:
        """A conflicting concurrent change by another user: 'move' shifts the event by one
        day; 'cancel' cancels it. Both touch fields the agent's approval depends on."""
        with self.txn() as c:
            row = self.get_event(event_id, c)
            before = json.loads(json.dumps(row.data))
            data = row.data
            if kind == "move":
                s0, e0 = datetime.fromisoformat(data["start_time"]), datetime.fromisoformat(data["end_time"])
                data["start_time"], data["end_time"] = _iso(s0 + timedelta(days=1)), _iso(e0 + timedelta(days=1))
            elif kind == "cancel":
                data["status"] = "canceled"
            elif kind.startswith("add_attendee:"):
                data["participants"] = list(data["participants"]) + [kind.split(":", 1)[1]]
            else:
                raise ValueError(kind)
            c.execute("UPDATE events SET version=?, data=? WHERE id=?", (row.version + 1, json.dumps(data), event_id))
            seq = self._log(c, "benign_edit", "other_user", "related_edit", event_id, {"kind": kind},
                            vb=row.version, va=row.version + 1, before=before, after=data)
            return seq, row.version + 1, data

    # -- mutation semantics (mirror AgentDojo's Calendar) ----------------------------
    def apply_write(self, c, action: str, args: dict, account_email: str, approval_id, gateway: str) -> dict:
        """Apply one calendar mutation inside an open transaction `c`; returns a log dict."""
        if action == "create_calendar_event":
            eid = self.next_event_id(c)
            participants = list(set(list(args.get("participants") or []) + [account_email]))
            data = {"id_": eid, "title": args["title"], "description": args.get("description", ""),
                    "start_time": _iso(_dt(args["start_time"])), "end_time": _iso(_dt(args["end_time"])),
                    "location": args.get("location"), "participants": participants, "all_day": False,
                    "status": "confirmed"}
            c.execute("INSERT INTO events(id, version, data) VALUES (?,?,?)", (eid, 1, json.dumps(data)))
            vb, va = None, 1
            before = None
        else:
            eid = str(args["event_id"])
            row = self.get_event(eid, c)
            if row is None:
                raise KeyError(f"event {eid} not found")
            before = json.loads(json.dumps(row.data))
            data = row.data          # patch: start from the CURRENT stored row
            if action == "reschedule_calendar_event":
                old_s, old_e = datetime.fromisoformat(data["start_time"]), datetime.fromisoformat(data["end_time"])
                ns = _dt(args["new_start_time"])
                ne = _dt(args["new_end_time"]) if args.get("new_end_time") else ns + (old_e - old_s)
                data["start_time"], data["end_time"] = _iso(ns), _iso(ne)
            elif action == "add_calendar_event_participants":
                data["participants"] = list(data["participants"]) + list(args["participants"])
            elif action == "cancel_calendar_event":
                data["status"] = "canceled"
            else:
                raise ValueError(action)
            vb, va = row.version, row.version + 1
            c.execute("UPDATE events SET version=?, data=? WHERE id=?", (va, json.dumps(data), eid))
        seq = self._log(c, "write", "agent", action, eid, args, approval_id, vb, va, gateway,
                        before=before, after=data)
        return {"seq": seq, "event_id": eid, "version_before": vb, "version_after": va}
