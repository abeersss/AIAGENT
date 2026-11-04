"""Print raw transaction logs for one recorded trace across all bindings and changes.

Usage: python experiments/txlog_excerpts.py [case_id]   (default: the gpt-4o clean trace)
Writes results/pilot/txlog_excerpts.md
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "results", "pilot")
cases = json.load(open(f"{P}/pilot_cases.json"))
if len(sys.argv) > 1:
    case = cases[int(sys.argv[1])]
else:
    case = next(c for c in cases if c["pipeline"] == "gpt-4o-2024-05-13" and c["condition"] == "none")
cid = case["case_id"]
KEEP = ("participants", "status", "start_time", "end_time", "description")


def brief(d):
    if not d:
        return "—"
    out = {k: d.get(k) for k in KEEP}
    if out.get("description") and len(out["description"]) > 40:
        out["description"] = "…" + out["description"][-40:]
    return json.dumps(out, ensure_ascii=False)


lines = [f"# Raw transaction logs: case {cid}", "",
         f"Trace `{case['path']}` ([download]({case['raw_url']})), pipeline `{case['pipeline']}`, "
         f"condition `{case['condition']}`, suite {case['suite_version']}.", "",
         "Every row is copied from the run's SQLite `log` table (`results/pilot/txlogs/<run>.jsonl`). "
         "`seq` is the commit order. Before- and after-images are cut to the fields the safety rule "
         "reads, plus the description.", ""]
runs = {json.loads(l)["run_id"]: json.loads(l) for l in open(f"{P}/pilot_runs.jsonl")}
for b in ("NB", "WE", "FS", "T1"):
    for e in ("U", "A", "T", "R"):
        rid = f"c{cid:03d}_{b}_{e}"
        rows = [json.loads(l) for l in open(f"{P}/txlogs/{rid}.jsonl")]
        verdicts = [f"{a['outcome']} ({a['verdict']})" for a in runs[rid]["attempts"]]
        lines += [f"## {rid} → {', '.join(verdicts)}", "", "| seq | kind | actor | action | event | reason | "
                  "version before→after | before-image | after-image |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for r in rows:
            if r["kind"] == "grant":
                lines.append(f"| {r['seq']} | grant | {r['actor']} | {r['action']} | {r['event_id']} | | "
                             f"bound to v{r['version_before']} | {brief(r['data_before'])} | |")
                continue
            lines.append(f"| {r['seq']} | {r['kind']} | {r['actor']} | {r['action'] or ''} | {r['event_id'] or ''} | "
                         f"{r['reason'] or ''} | {r['version_before']}→{r['version_after']} | {brief(r['data_before'])} | "
                         f"{brief(r['data_after'])} |")
        lines.append("")
open(f"{P}/txlog_excerpts.md", "w").write("\n".join(lines))
print("\n".join(lines[:60]))
