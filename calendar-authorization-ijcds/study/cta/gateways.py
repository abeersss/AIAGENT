"""Tool gateways. The agent reaches the calendar only through `Gateway.call`.

G0  none                no authorization
G1  allowlist           tool-name allowlist (per task)
G2  precheck            argument-level + object-version check, then write (separate txns)
G2b precheck_recheck    G2 plus a second check immediately before the write
G3  committime          same policy, checked inside the write transaction (atomic)
A1  committime_noversion   G3 without version binding           (ablation)
A2  committime_diffscope   G3 with field-scoped guard instead of object version (ablation)

`window_hook(gap, ctx)` is called at each point where another actor's commit could be
interleaved. The experiment controller uses it to inject revocations and concurrent
edits deterministically. `gap` is one of:
  "check_write"    after the (first) authorization check, before the write
  "recheck_write"  after G2b's recheck, before the write
  "pre_txn"        at the same logical position for gateways with no separate check
  "after_commit"   after the write has committed
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

from .policy import WRITE_TOOLS, args_allowed, target_of

GUARDED_FIELDS = {
    "reschedule_calendar_event": ["start_time", "end_time", "status", "participants"],
    "add_calendar_event_participants": ["participants", "status"],
    "cancel_calendar_event": ["status", "start_time"],
}

class MirrorRejected(Exception):
    pass


DENY_REASONS = ("not_allowlisted", "not_approved", "approval_revoked", "version_mismatch",
                "guard_mismatch", "event_not_found")


@dataclass
class Denial:
    reason: str
    detail: str
    action: str
    event_id: str | None
    current_version: int | None = None

    def as_tool_result(self) -> str:
        """Structured reason returned to the agent so it can ask for renewed approval."""
        return json.dumps({"status": "denied", "reason": self.reason, "detail": self.detail,
                           "action": self.action, "event_id": self.event_id,
                           "current_version": self.current_version,
                           "next_step": "request renewed approval from the user" if self.reason in
                           ("approval_revoked", "version_mismatch", "guard_mismatch") else "do not retry"})


@dataclass
class CallRecord:
    action: str
    args: dict
    outcome: str                      # committed | denied | error | passthrough
    reason: str | None = None
    seq: int | None = None
    gateway_ms: float = 0.0           # authorization + store transaction, excluding hooks and mirroring
    tool_ms: float = 0.0              # whole call incl. mirroring into the benchmark env
    approval_id: int | None = None


def _event_fields(row) -> dict:
    return {k: row.data.get(k) for k in ("start_time", "end_time", "status", "participants")}


class Gateway:
    name = "base"
    authorizes = True

    def __init__(self, store, runtime, env, user, allowlist=None, window_hook=None):
        self.store, self.runtime, self.env, self.user = store, runtime, env, user
        self.allowlist = set(allowlist or [])
        self.window_hook = window_hook or (lambda gap, ctx: None)
        self.records: list[CallRecord] = []
        self.account_email = env.calendar.account_email
        self._hook_s = 0.0

    # -- helpers ---------------------------------------------------------------------
    def _hook(self, gap, ctx):
        t = time.perf_counter()
        self.window_hook(gap, ctx)
        self._hook_s += time.perf_counter() - t

    def _find(self, c, action, args, check_version: str):
        """Return (approval, None) or (None, Denial). check_version: object | field | none."""
        tgt = target_of(action, args)
        row = None
        if tgt is not None:
            row = self.store.get_event(tgt, c)
            if row is None:
                return None, Denial("event_not_found", f"event {tgt} does not exist", action, tgt)
        cands = [a for a in self.store.approvals(c)
                 if a["user"] == self.user and a["action"] == action and a["event_id"] == tgt]
        admitted = [a for a in cands if args_allowed(a["constraints"], args)[0]]
        if not admitted:
            detail = args_allowed(cands[0]["constraints"], args)[1] if cands else "no approval for this action/target"
            return None, Denial("not_approved", detail, action, tgt, row.version if row else None)
        active = [a for a in admitted if a["status"] == "active"]
        if not active:
            return None, Denial("approval_revoked", "the approval was revoked", action, tgt, row.version if row else None)
        a = active[-1]
        if row is not None and check_version == "object" and a["expected_version"] is not None \
                and a["expected_version"] != row.version:
            return None, Denial("version_mismatch",
                                f"approved version {a['expected_version']}, current version {row.version}",
                                action, tgt, row.version)
        if row is not None and check_version == "field":
            guard = a["constraints"].get("guard", {})
            cur = _event_fields(row)
            changed = [k for k, v in guard.items() if cur.get(k) != v]
            if changed:
                return None, Denial("guard_mismatch", f"approved fields changed: {changed}", action, tgt, row.version)
        return a, None

    def _apply(self, c, action, args, approval_id):
        """Inside an open transaction: write the store, then apply the same call to the
        benchmark environment. If the benchmark rejects the call, raise so the store
        transaction rolls back and both stay consistent. Mirror time is excluded from
        gateway_ms."""
        info = self.store.apply_write(c, action, args, self.account_email, approval_id, self.name)
        t = time.perf_counter()
        res, err = self.runtime.run_function(self.env, action, args)
        self._mirror_s += time.perf_counter() - t
        if err:
            raise MirrorRejected(err)
        info["result"] = res
        return info

    def _commit(self, action, args, approval_id):
        with self.store.txn() as c:
            return self._apply(c, action, args, approval_id)

    # -- entry point -----------------------------------------------------------------
    def call(self, action: str, args: dict):
        t0 = time.perf_counter()
        self._hook_s = 0.0
        self._mirror_s = 0.0
        if action not in WRITE_TOOLS:
            res, err = self.runtime.run_function(self.env, action, args)
            self.records.append(CallRecord(action, args, "passthrough", tool_ms=(time.perf_counter() - t0) * 1e3))
            return res, err
        ctx = {"action": action, "args": args}
        try:
            out = self._write(action, args, ctx)
        except Exception as e:      # malformed arguments, unknown event, benchmark rejection
            rec = CallRecord(action, args, "error", reason=type(e).__name__)
            rec.tool_ms = (time.perf_counter() - t0 - self._hook_s) * 1e3
            self.records.append(rec)
            return None, f"{type(e).__name__}: {e}"
        rec, result, err = out
        rec.tool_ms = (time.perf_counter() - t0 - self._hook_s) * 1e3
        self.records.append(rec)
        if rec.outcome == "committed":
            self._hook("after_commit", ctx)
        return result, err

    def _write(self, action, args, ctx):
        raise NotImplementedError

    def _denied(self, action, args, d: Denial, g_ms):
        return CallRecord(action, args, "denied", reason=d.reason, gateway_ms=g_ms), d.as_tool_result(), None

    def _done(self, action, args, info, approval_id, g_ms):
        g_ms -= self._mirror_s * 1e3
        return CallRecord(action, args, "committed", seq=info["seq"], gateway_ms=g_ms,
                          approval_id=approval_id), info["result"], None


class NoAuth(Gateway):
    name = "G0_none"

    def _write(self, action, args, ctx):
        self._hook("pre_txn", ctx)
        t = time.perf_counter()
        info = self._commit(action, args, None)
        return self._done(action, args, info, None, (time.perf_counter() - t) * 1e3)


class Allowlist(Gateway):
    name = "G1_allowlist"

    def _write(self, action, args, ctx):
        t = time.perf_counter()
        if action not in self.allowlist:
            d = Denial("not_allowlisted", f"tool {action} not allowlisted for this task", action,
                       target_of(action, args))
            return self._denied(action, args, d, (time.perf_counter() - t) * 1e3)
        g1 = time.perf_counter() - t
        self._hook("pre_txn", ctx)
        t = time.perf_counter()
        info = self._commit(action, args, None)
        return self._done(action, args, info, None, (g1 + time.perf_counter() - t) * 1e3)


class PreCheck(Gateway):
    """Check in its own read transaction, then write in a second transaction."""
    name = "G2_precheck"
    rechecks = 0
    version_mode = "object"

    def _write(self, action, args, ctx):
        t = time.perf_counter()
        with self.store.txn() as c:
            a, d = self._find(c, action, args, self.version_mode)
            if d:
                self.store.log_denial(c, action, args, d.event_id, d.reason, self.name, d.current_version)
        g = time.perf_counter() - t
        if d:
            return self._denied(action, args, d, g * 1e3)
        self._hook("check_write", ctx)
        for _ in range(self.rechecks):
            t = time.perf_counter()
            with self.store.txn() as c:
                a, d = self._find(c, action, args, self.version_mode)
                if d:
                    self.store.log_denial(c, action, args, d.event_id, d.reason, self.name, d.current_version)
            g += time.perf_counter() - t
            if d:
                return self._denied(action, args, d, g * 1e3)
            self._hook("recheck_write", ctx)
        t = time.perf_counter()
        info = self._commit(action, args, a["approval_id"])
        g += time.perf_counter() - t
        return self._done(action, args, info, a["approval_id"], g * 1e3)


class PreCheckRecheck(PreCheck):
    name = "G2b_precheck_recheck"
    rechecks = 1


class CommitTime(Gateway):
    """Approval, version/guard and arguments are checked inside the write transaction.
    BEGIN IMMEDIATE serializes this transaction with revocations and concurrent edits:
    whichever acquires SQLite's write lock first commits first (linearization point)."""
    name = "G3_committime"
    version_mode = "object"

    def _write(self, action, args, ctx):
        self._hook("pre_txn", ctx)
        t = time.perf_counter()
        with self.store.txn() as c:
            a, d = self._find(c, action, args, self.version_mode)
            if d is None:
                info = self._apply(c, action, args, a["approval_id"])
            else:
                self.store.log_denial(c, action, args, d.event_id, d.reason, self.name, d.current_version)
        g = (time.perf_counter() - t) * 1e3
        if d:
            return self._denied(action, args, d, g)
        return self._done(action, args, info, a["approval_id"], g)


class CommitTimeNoVersion(CommitTime):
    name = "A1_committime_noversion"
    version_mode = "none"


class CommitTimeDiffScope(CommitTime):
    name = "A2_committime_diffscope"
    version_mode = "field"


class PreCheckDiffScope(PreCheck):
    """Secondary control: the field-scoped policy checked BEFORE the write, in its own txn."""
    name = "T1_precheck_fieldscope"
    version_mode = "field"


GATEWAYS = {g.name: g for g in (NoAuth, Allowlist, PreCheck, PreCheckRecheck, CommitTime,
                                 CommitTimeNoVersion, CommitTimeDiffScope, PreCheckDiffScope)}
