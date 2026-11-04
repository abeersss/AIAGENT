"""Audit the recorded traces in the pinned benchmark repository before claiming coverage.

For every file runs/<pipeline>/workspace/<task>/<condition>/<injection>.json of the included
calendar tasks, record whether it is a real JSON trace (not a Git LFS pointer), which tool
calls it contains, whether every call has a function name and an argument dict for a tool
that exists in the suite, and whether it contains the task's calendar write.

Outputs:
  results/trace_audit.jsonl            one row per trace file
  results/trace_audit_summary.json     coverage by pipeline / task / condition
  results/pilot_manifest.json          the exact traces used by the reschedule pilot
"""
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agentdojo.task_suite.load_suites import get_suite  # noqa: E402

BENCH = os.environ.get("AGENTDOJO_DIR", "/home/claude/cta/agentdojo-benchmark")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
PIN = json.load(open(f"{OUT}/benchmark_pin.json"))
RAW = f"https://raw.githubusercontent.com/sequrity-ai/agentdojo-benchmark/{PIN['commit']}/"
TASKS = json.load(open(f"{OUT}/task_inclusion.json"))["per_version"]["v1.2.2"]["expanded"]
WRITES = {"create_calendar_event", "reschedule_calendar_event", "add_calendar_event_participants",
          "cancel_calendar_event"}
TOOLS = {f.name for f in get_suite("v1.2.2", "workspace").tools} | \
        {f.name for f in get_suite("v1", "workspace").tools}


def audit(path):
    rel = os.path.relpath(path, BENCH)
    parts = rel.split(os.sep)            # runs/pipe/workspace/task/cond/file
    row = {"path": rel, "raw_url": RAW + rel, "pipeline": parts[1], "user_task": parts[3],
           "condition": parts[4], "file": parts[5], "bytes": os.path.getsize(path)}
    head = open(path, "rb").read(200)
    if head.startswith(b"version https://git-lfs"):
        row.update(status="lfs_pointer")
        return row
    try:
        d = json.load(open(path))
    except Exception as e:
        row.update(status=f"unparseable: {type(e).__name__}")
        return row
    calls, bad = [], 0
    for m in d.get("messages") or []:
        if m.get("role") == "assistant":
            for c in m.get("tool_calls") or []:
                ok = isinstance(c.get("function"), str) and isinstance(c.get("args"), dict) and c["function"] in TOOLS
                bad += 0 if ok else 1
                calls.append({"function": c.get("function"), "args": c.get("args")})
    writes = [c for c in calls if c["function"] in WRITES]
    row.update(status="ok", logged_version=d.get("benchmark_version"), attack_type=d.get("attack_type"),
               injection_task=d.get("injection_task_id"), logged_utility=d.get("utility"),
               logged_security=d.get("security"), run_error=d.get("error"), n_messages=len(d.get("messages") or []),
               n_tool_calls=len(calls), n_malformed_calls=bad, write_calls=writes,
               replayable=bool(calls) and bad == 0)
    return row


def main():
    rows = []
    for t in TASKS:
        for p in sorted(glob.glob(f"{BENCH}/runs/*/workspace/{t}/*/*.json")):
            rows.append(audit(p))
    with open(f"{OUT}/trace_audit.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    pipes = sorted({r["pipeline"] for r in rows})
    all_pipes = sorted(os.listdir(f"{BENCH}/runs"))
    summ = {"pinned_commit": PIN["commit"], "pipelines_in_repo": len(all_pipes),
            "pipelines_with_workspace_calendar_traces": len(pipes), "trace_files": len(rows),
            "status": dict(collections.Counter(r["status"] for r in rows)),
            "replayable": sum(1 for r in rows if r.get("replayable")),
            "by_task": {}, "by_pipeline": {}, "pipelines_without_traces": sorted(set(all_pipes) - set(pipes))}
    for t in TASKS:
        rr = [r for r in rows if r["user_task"] == t and r.get("replayable")]
        summ["by_task"][t] = {"replayable_traces": len(rr), "pipelines": len({r["pipeline"] for r in rr}),
                              "clean": sum(1 for r in rr if r["condition"] == "none"),
                              "with_any_write_call": sum(1 for r in rr if r["write_calls"])}
    for p in pipes:
        rr = [r for r in rows if r["pipeline"] == p]
        summ["by_pipeline"][p] = {"files": len(rr), "replayable": sum(1 for r in rr if r.get("replayable")),
                                  "conditions": sorted({r["condition"] for r in rr}),
                                  "logged_versions": sorted({str(r.get("logged_version")) for r in rr})}
    json.dump(summ, open(f"{OUT}/trace_audit_summary.json", "w"), indent=1)

    # --- reschedule pilot manifest: user_task_7, every condition ----------------------------
    pilot = []
    for r in rows:
        if r["user_task"] != "user_task_7" or not r.get("replayable"):
            continue
        res = [c for c in r["write_calls"] if c["function"] == "reschedule_calendar_event"]
        pilot.append({k: r[k] for k in ("path", "raw_url", "pipeline", "condition", "file", "attack_type",
                                         "injection_task", "logged_version", "logged_utility", "logged_security")}
                     | {"reschedule_calls": res, "has_reschedule": bool(res)})
    json.dump(pilot, open(f"{OUT}/pilot_manifest.json", "w"), indent=1)
    print(json.dumps({k: summ[k] for k in ("pipelines_in_repo", "pipelines_with_workspace_calendar_traces",
                                           "trace_files", "status", "replayable", "pipelines_without_traces")}, indent=1))
    print("user_task_7 traces:", len(pilot), "with reschedule call:", sum(p["has_reschedule"] for p in pilot))


if __name__ == "__main__":
    main()
