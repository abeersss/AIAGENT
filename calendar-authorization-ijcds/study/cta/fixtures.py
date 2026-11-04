"""Trusted approval fixture.

Approvals are derived ONLY from the benchmark's own task definitions (the user task's
ground-truth intended calendar change for the suite version in use). They never read
tool outputs, model messages or injected content.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from .policy import WRITE_TOOLS

FMT = "%Y-%m-%d %H:%M"
USER = "emma.johnson@bluesparrowtech.com"     # the Workspace suite's account owner


def intended_writes(suite, user_task_id: str, env) -> list[tuple[str, dict]]:
    ut = suite.user_tasks[user_task_id]
    return [(c.function, dict(c.args)) for c in ut.ground_truth(env.model_copy(deep=True))
            if c.function in WRITE_TOOLS]


def allowlist_for(suite, user_task_id: str, env) -> set[str]:
    return {f for f, _ in intended_writes(suite, user_task_id, env)}


def approval_specs(suite, user_task_id: str, env) -> list[dict]:
    """One approval per intended write: action, target, argument constraints, guard snapshot."""
    specs = []
    account = env.calendar.account_email
    for action, args in intended_writes(suite, user_task_id, env):
        if action == "create_calendar_event":
            cons = {"equals": {"start_time": args["start_time"]}}
            if args.get("end_time"):
                cons["equals"]["end_time"] = args["end_time"]
            cons["subset"] = {"participants": list(args.get("participants") or []) + [account]}
            specs.append({"action": action, "event_id": None, "constraints": cons, "versioned": False})
        elif action == "reschedule_calendar_event":
            ev = env.calendar.events[args["event_id"]]
            start = datetime.strptime(args["new_start_time"], FMT)
            dur_end = (start + (ev.end_time - ev.start_time)).strftime(FMT)
            ends = [None, dur_end] + ([args["new_end_time"]] if args.get("new_end_time") else [])
            cons = {"equals": {"event_id": args["event_id"], "new_start_time": args["new_start_time"]},
                    "one_of": {"new_end_time": sorted(set(ends), key=lambda x: x or "")}}
            specs.append({"action": action, "event_id": args["event_id"], "constraints": cons, "versioned": True})
        elif action == "add_calendar_event_participants":
            cons = {"equals": {"event_id": args["event_id"]},
                    "subset": {"participants": list(args["participants"])}}
            specs.append({"action": action, "event_id": args["event_id"], "constraints": cons, "versioned": True})
        elif action == "cancel_calendar_event":
            cons = {"equals": {"event_id": args["event_id"]}}
            specs.append({"action": action, "event_id": args["event_id"], "constraints": cons, "versioned": True})
    return specs


def grant_all(store, specs) -> list[int]:
    """Grant each approval, binding the expected version and the guarded-field snapshot
    of the target as stored at grant time."""
    from .gateways import GUARDED_FIELDS, _event_fields
    ids = []
    for s in specs:
        cons = dict(s["constraints"])
        ver = None
        if s["event_id"] is not None:
            row = store.get_event(s["event_id"])
            ver = row.version
            snap = _event_fields(row)
            cons["guard"] = {k: snap[k] for k in GUARDED_FIELDS[s["action"]]}
        ids.append(store.grant(USER, s["action"], s["event_id"], cons, ver))
    return ids


def renewal_decision(denial_reason: str, concurrent_change: str | None) -> bool:
    """Would the (simulated, trusted) user re-approve after a structured denial?
    - unrelated concurrent edit (description changed): yes, re-approve against the new version
    - related concurrent edit (event moved / canceled by someone else): no
    - revoked approval or never-approved action: no
    """
    if denial_reason in ("version_mismatch", "guard_mismatch"):
        return concurrent_change == "unrelated"
    return False
