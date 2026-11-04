"""Tables for the reschedule pilot, computed only from results/pilot/pilot_runs.jsonl,
pilot_cases.json and the raw transaction logs.

Writes results/pilot/pilot_tables.md and results/pilot/pilot_summary.json.
"""
import collections
import json
import os
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "results", "pilot")
runs = [json.loads(l) for l in open(f"{P}/pilot_runs.jsonl")]
cases = {c["case_id"]: c for c in json.load(open(f"{P}/pilot_cases.json"))}
EDITS = ["none", "U", "A", "T", "R", "R_after"]
EDIT_NAME = {"none": "no concurrent change", "U": "unrelated edit (description)",
             "A": "invalidating edit (attendee added)", "T": "invalidating edit (event moved)",
             "R": "revocation before write", "R_after": "revocation after write"}
BIND = {"NB": "No binding", "WE": "Whole-event version", "FS": "Field-scoped",
        "T1": "Field-scoped, checked before write"}


def agg(sel):
    o = collections.Counter()
    t = collections.Counter()
    for r in sel:
        if r["edit"] != "none" and r.get("target_index") is None:
            t["not_applicable"] += 1      # no attempt with the approved arguments: no injection point
            continue
        outs = [a["outcome"] for a in r["attempts"]]
        o.update(outs)
        t["traces"] += 1
        t["fired"] += bool(r["fired"])
        for k in ("unsafe_commit", "benign_abort", "correct_block", "safe_commit"):
            t[f"traces_{k}"] += k in outs
        t["retry_committed"] += r["retry"]["retry_committed"]
        t["reapproved"] += r["retry"]["reapproved"]
        t["utility"] += r["utility"]
    return o, t


def table(bindings, title):
    lines = [f"### {title}", "",
             "Unit: recorded traces (one replay per trace and cell). Counts in parentheses are agent reschedule "
             "attempts scored by the independent safety rule.", "",
             "| Concurrent change | Binding | Traces | Not applicable (no approvable attempt) | Change injected | Traces with unsafe commit (attempts) | "
             "Traces with benign abort (attempts) | Correct blocks (attempts) | Safe commits (attempts) | "
             "Committed on retry after scripted re-approval |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    summ = {}
    for e in EDITS:
        for b in bindings:
            sel = [r for r in runs if r["binding"] == b and r["edit"] == e]
            o, t = agg(sel)
            summ[f"{b}:{e}"] = {"outcomes": dict(o), "traces": dict(t)}
            lines.append(f"| {EDIT_NAME[e]} | {BIND[b]} | {t['traces']} | {t['not_applicable']} | {t['fired']} | "
                         f"{t['traces_unsafe_commit']} ({o['unsafe_commit']}) | {t['traces_benign_abort']} ({o['benign_abort']}) | "
                         f"{t['traces_correct_block']} ({o['correct_block']}) | {t['traces_safe_commit']} ({o['safe_commit']}) | "
                         f"{t['retry_committed']} |")
    return lines, summ


def main():
    out = ["# Reschedule pilot: binding scope (AgentDojo user_task_7, replay)", ""]
    n_cases = len(cases)
    resolved = [c for c in cases.values() if c["suite_version"]]
    out += [f"- Recorded traces with a reschedule call: **{n_cases}** "
            f"({len({c['pipeline'] for c in cases.values()})} pipelines); version resolved for {len(resolved)} "
            f"({collections.Counter(c['version_source'] for c in cases.values())}).",
            f"- Trace conditions: {dict(collections.Counter(c['condition'] for c in cases.values()))}.",
            f"- Suite versions used: {dict(collections.Counter(c['suite_version'] for c in resolved))}.", ""]
    first_ok = collections.Counter()
    for c in resolved:
        a = c["first_reschedule_args"]
        first_ok[(a.get("new_start_time") == "2024-05-20 10:00" and a.get("new_end_time") in (None, "2024-05-20 11:00"))] += 1
    out += [f"- First reschedule attempt matches the approved arguments in {first_ok[True]} traces; "
            f"{first_ok[False]} use other values or formats (e.g. '10:00:00'), which the policy denies under every binding.", ""]
    l1, s1 = table(["NB", "WE", "FS"], "Table 1. Primary comparison: binding scope (all checked atomically at commit)")
    l2, s2 = table(["FS", "T1"], "Table 2. Secondary control: enforcement timing, same field-scoped policy")
    out += l1 + [""] + l2 + [""]

    # patch semantics
    pp = collections.Counter((r["binding"], r["edit"], r["patch_preserved"]) for r in runs if r["edit"] in ("U", "A"))
    out += ["### Patch semantics", "",
            "Of the committed agent reschedules that followed a concurrent edit, how many kept that edit in the "
            "after-image (`True`), or lost it (`False`):", "",
            "| Binding | Edit | Preserved | Lost | No commit |", "| --- | --- | --- | --- | --- |"]
    for b in ["NB", "WE", "FS", "T1"]:
        for e in ["U", "A"]:
            out.append(f"| {BIND[b]} | {EDIT_NAME[e]} | {pp[(b, e, True)]} | {pp[(b, e, False)]} | {pp[(b, e, None)]} |")
    out.append("")

    # per pipeline (NB, A) and (T1, R)
    out += ["### Unsafe commits by pipeline", "",
            "| Pipeline | Traces | No binding, attendee edit | Whole-event, attendee edit | Field-scoped, attendee edit | "
            "Field-scoped before write, revocation |", "| --- | --- | --- | --- | --- | --- |"]
    pipes = sorted({r["pipeline"] for r in runs})
    for p in pipes:
        def cnt(b, e):
            return sum(1 for r in runs if r["pipeline"] == p and r["binding"] == b and r["edit"] == e
                       and any(a["outcome"] == "unsafe_commit" for a in r["attempts"]))
        nt = sum(1 for r in runs if r["pipeline"] == p and r["binding"] == "NB" and r["edit"] == "none")
        out.append(f"| {p} | {nt} | {cnt('NB', 'A')} | {cnt('WE', 'A')} | {cnt('FS', 'A')} | {cnt('T1', 'R')} |")
    out.append("")

    # utility under no concurrent change
    out += ["### Benchmark utility (original AgentDojo check), no concurrent change", "",
            "| Binding | Traces | Utility true | Logged utility true (same traces) |", "| --- | --- | --- | --- |"]
    logged = {}
    for l in open(os.path.join(ROOT, "results", "trace_audit.jsonl")):
        d = json.loads(l)
        logged[d["path"]] = d.get("logged_utility")
    for b in ["NB", "WE", "FS", "T1"]:
        sel = [r for r in runs if r["binding"] == b and r["edit"] == "none"]
        out.append(f"| {BIND[b]} | {len(sel)} | {sum(r['utility'] for r in sel)} | "
                   f"{sum(bool(logged.get(cases[r['case_id']]['path'])) for r in sel)} |")
    out.append("")

    # latency
    out += ["### Gateway latency (reschedule calls; authorization + SQLite transaction, excluding benchmark mirroring)", "",
            "| Binding | Calls | Median (ms) | p95 (ms) |", "| --- | --- | --- | --- |"]
    lat = {}
    for b in ["NB", "WE", "FS", "T1"]:
        xs = sorted(x for r in runs if r["binding"] == b for x in r["latency_ms"])
        p95 = xs[int(0.95 * (len(xs) - 1))] if xs else float("nan")
        lat[b] = {"n": len(xs), "median": statistics.median(xs) if xs else None, "p95": p95}
        out.append(f"| {BIND[b]} | {len(xs)} | {lat[b]['median']:.3f} | {p95:.3f} |")
    out.append("")
    open(f"{P}/pilot_tables.md", "w").write("\n".join(out))
    json.dump({"primary": s1, "secondary": s2, "latency": lat}, open(f"{P}/pilot_summary.json", "w"), indent=1)
    print("\n".join(out))


if __name__ == "__main__":
    main()
