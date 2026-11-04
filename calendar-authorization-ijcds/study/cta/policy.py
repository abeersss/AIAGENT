"""Argument-level approval policy, shared by the pre-check gateway, the commit-time
gateway and the outcome oracle, so the two enforced gateways differ ONLY in when and
how the same policy is enforced.

Constraint vocabulary (JSON):
  equals:   {arg: value}            argument must equal value (after normalisation)
  one_of:   {arg: [values]}         argument must be one of values (None = omitted)
  subset:   {arg: [values]}         list argument must be a subset of values
"""
from __future__ import annotations

WRITE_TOOLS = {"create_calendar_event", "reschedule_calendar_event",
               "add_calendar_event_participants", "cancel_calendar_event"}


def _norm(v):
    if isinstance(v, str):
        return v.strip().lower()
    return v


def args_allowed(constraints: dict, args: dict) -> tuple[bool, str]:
    for k, v in constraints.get("equals", {}).items():
        if _norm(args.get(k)) != _norm(v):
            return False, f"argument '{k}'={args.get(k)!r} not approved (expected {v!r})"
    for k, vals in constraints.get("one_of", {}).items():
        if _norm(args.get(k)) not in [_norm(x) for x in vals]:
            return False, f"argument '{k}'={args.get(k)!r} not in approved values {vals!r}"
    for k, vals in constraints.get("subset", {}).items():
        got = {_norm(x) for x in (args.get(k) or [])}
        allowed = {_norm(x) for x in vals}
        if not got <= allowed:
            return False, f"argument '{k}' contains unapproved values {sorted(got - allowed)!r}"
    return True, ""


def target_of(action: str, args: dict) -> str | None:
    return None if action == "create_calendar_event" else str(args.get("event_id"))


def matching_approvals(approvals: list[dict], user: str, action: str, args: dict) -> list[dict]:
    """Approvals for this user/action/target whose argument constraints admit `args`."""
    tgt = target_of(action, args)
    out = []
    for a in approvals:
        if a["user"] != user or a["action"] != action or a["event_id"] != tgt:
            continue
        ok, _ = args_allowed(a["constraints"], args)
        if ok:
            out.append(a)
    return out
