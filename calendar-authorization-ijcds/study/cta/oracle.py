"""Independent outcome oracle. Reads only the store's commit log and approvals table
(the global commit order), never a gateway's verdict.

A committed write is AUTHORIZED iff some approval for the same user/action/target
  (1) admits its arguments,
  (2) was granted before the write committed (granted_seq < seq),
  (3) had not been revoked before the write committed (revoked_seq is NULL or > seq), and
  (4) no GUARDED field of the target changed between that approval and the write
      (a related concurrent edit makes the approval stale; an edit to an unrelated field
      such as the description does not).
Otherwise it is UNAUTHORIZED, classified as: unapproved | revoked | stale.
"""
from __future__ import annotations

from .policy import args_allowed, target_of


def classify(store, user: str) -> list[dict]:
    log = store.log_rows()
    approvals = store.approvals()
    out = []
    for w in (r for r in log if r["kind"] == "write"):
        tgt = target_of(w["action"], w["args"])
        cands = [a for a in approvals if a["user"] == user and a["action"] == w["action"]
                 and a["event_id"] == tgt and args_allowed(a["constraints"], w["args"])[0]
                 and a["granted_seq"] < w["seq"]]
        verdict = "unapproved"
        for a in cands:
            if a["revoked_seq"] is not None and a["revoked_seq"] < w["seq"]:
                verdict = "revoked" if verdict == "unapproved" else verdict
                continue
            if tgt is not None:
                # any related change to the target strictly between grant and this write?
                stale = any(r["kind"] == "benign_edit" and r["action"] == "related_edit"
                            and r["event_id"] == tgt and a["granted_seq"] < r["seq"] < w["seq"]
                            for r in log)
                if stale:
                    verdict = "stale"
                    continue
            verdict = "authorized"
            break
        out.append({"seq": w["seq"], "action": w["action"], "event_id": w["event_id"], "args": w["args"],
                    "gateway": w["gateway"], "verdict": verdict})
    return out
