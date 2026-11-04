"""Build the case manifest and run the unmodified-benchmark checks.

Outputs (results/):
  benchmark_pin.json            repository, commit, version, license
  task_inclusion.json           inclusion criteria, task IDs and counts, applicable attacks
  unmodified_groundtruth.json   AgentDojo's own GroundTruthPipeline on each included task, per suite version
  trace_reproduction.jsonl      each recorded trace replayed with no gateway logic vs its logged result
  case_manifest.json            the traces used downstream, with their resolved suite version
"""
import glob
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentdojo.agent_pipeline.ground_truth_pipeline import GroundTruthPipeline
from agentdojo.functions_runtime import FunctionsRuntime
from agentdojo.task_suite.load_suites import get_suite

from cta.policy import WRITE_TOOLS
from cta.replay import Schedule, load_trace, run_one

BENCH = os.environ.get("AGENTDOJO_DIR", "/home/claude/cta/agentdojo-benchmark")
RUNS = os.path.join(BENCH, "runs")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
VERSIONS = ["v1", "v1.1.1", "v1.1.2", "v1.2", "v1.2.1", "v1.2.2"]
EXISTING = {"reschedule_calendar_event", "cancel_calendar_event", "add_calendar_event_participants"}


def git(*a):
    return subprocess.check_output(["git", "-C", BENCH, *a], text=True).strip()


def main():
    os.makedirs(OUT, exist_ok=True)
    pin = {"repository": git("remote", "get-url", "origin"), "commit": git("rev-parse", "HEAD"),
           "commit_date": git("log", "-1", "--format=%cI"), "package_version": "0.1.35",
           "license": open(os.path.join(BENCH, "LICENSE")).read().splitlines()[0]}
    json.dump(pin, open(f"{OUT}/benchmark_pin.json", "w"), indent=2)

    # --- inclusion -------------------------------------------------------------------
    incl = {"criteria": {
        "strict": "Workspace user tasks whose ground-truth calls include a tool that modifies an EXISTING "
                  "calendar event (reschedule_calendar_event, cancel_calendar_event, add_calendar_event_participants)",
        "expanded": "strict set plus Workspace user tasks whose ground-truth calls include create_calendar_event",
        "applicable_attacks": "injection tasks whose ground-truth calls include a calendar write tool",
        "suite_version_for_counts": "v1.2.2 (latest at the pinned commit); identical membership in all versions"},
        "per_version": {}}
    for v in VERSIONS:
        s = get_suite(v, "workspace")
        env = s.load_and_inject_default_environment({})
        strict, expanded = [], []
        for tid, t in s.user_tasks.items():
            fns = {c.function for c in t.ground_truth(env.model_copy(deep=True))}
            if fns & EXISTING:
                strict.append(tid)
            if fns & WRITE_TOOLS:
                expanded.append(tid)
        attacks = [iid for iid, it in s.injection_tasks.items()
                   if {c.function for c in it.ground_truth(env.model_copy(deep=True))} & WRITE_TOOLS]
        key = lambda x: int(x.split("_")[-1])
        incl["per_version"][v] = {"n_user_tasks": len(s.user_tasks), "n_injection_tasks": len(s.injection_tasks),
                                  "strict": sorted(strict, key=key), "expanded": sorted(expanded, key=key),
                                  "calendar_injection_tasks": sorted(attacks, key=key)}
    json.dump(incl, open(f"{OUT}/task_inclusion.json", "w"), indent=2)
    tasks = incl["per_version"]["v1.2.2"]["expanded"]
    print("strict", incl["per_version"]["v1.2.2"]["strict"], "expanded", tasks)

    # --- unmodified benchmark: ground-truth pipeline ---------------------------------------
    gt = []
    for v in VERSIONS:
        s = get_suite(v, "workspace")
        for tid in tasks:
            ut = s.user_tasks[tid]
            u, _ = s.run_task_with_pipeline(GroundTruthPipeline(ut), ut, None, {})
            row = {"suite_version": v, "user_task": tid, "utility": bool(u)}
            for iid in incl["per_version"][v]["calendar_injection_tasks"]:
                it = s.injection_tasks[iid]
                env = s.load_and_inject_default_environment({})
                _, sec = s.run_task_with_pipeline(GroundTruthPipeline(it), it, None, {})
                row[f"{iid}_ground_truth_security"] = bool(sec)
            gt.append(row)
    json.dump(gt, open(f"{OUT}/unmodified_groundtruth.json", "w"), indent=2)
    print("ground truth utility true:", sum(r["utility"] for r in gt), "/", len(gt))

    # --- recorded traces -----------------------------------------------------------------
    work = tempfile.mkdtemp()
    manifest, repro = [], open(f"{OUT}/trace_reproduction.jsonl", "w")
    for pipe in sorted(os.listdir(RUNS)):
        for tid in tasks:
            paths = glob.glob(f"{RUNS}/{pipe}/workspace/{tid}/none/none.json") + \
                    sorted(glob.glob(f"{RUNS}/{pipe}/workspace/{tid}/*/injection_task_2.json"))
            for p in paths:
                tr = load_trace(p)
                logged_v = tr.get("benchmark_version")
                cands = [logged_v] if logged_v else VERSIONS
                results = {}
                for v in cands:
                    r = run_one(tr, v, "G0_none", Schedule(), work)
                    match = r["utility"] == bool(tr["utility"]) and (
                        tr.get("injection_task_id") is None or r["security"] == bool(tr["security"]))
                    results[v] = {"utility": r["utility"], "security": r["security"], "match": match}
                matched = [v for v in cands if results[v]["match"]]
                resolved = logged_v or (matched[0] if matched else None)
                rec = {"path": os.path.relpath(p, BENCH), "pipeline": pipe, "user_task": tid,
                       "attack_type": tr.get("attack_type"), "injection_task": tr.get("injection_task_id"),
                       "logged_version": logged_v, "logged_utility": tr["utility"], "logged_security": tr["security"],
                       "candidates": results, "matching_versions": matched, "resolved_version": resolved,
                       "n_calls": len(tr["_calls"]), "error": tr.get("error")}
                repro.write(json.dumps(rec) + "\n")
                if resolved:
                    manifest.append({k: rec[k] for k in ("path", "pipeline", "user_task", "attack_type",
                                                         "injection_task", "resolved_version")} |
                                    {"version_source": "logged" if logged_v else "reproduction",
                                     "reproduced": bool(matched)})
    repro.close()
    json.dump(manifest, open(f"{OUT}/case_manifest.json", "w"), indent=1)
    print("traces in manifest:", len(manifest))


if __name__ == "__main__":
    main()
