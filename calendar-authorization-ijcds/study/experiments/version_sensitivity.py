"""Sensitivity check: re-run every reconstructed-version case (and the six unresolved
cases) under suite v1 and compare the safety-rule outcome sequence with the pilot's.
Writes results/pilot/audit/version_sensitivity.json
"""
import json
import multiprocessing as mp
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pilot_reschedule import BENCH, CONDITIONS, PRIMARY, SECONDARY, run   # noqa: E402
from cta.replay import load_trace                                          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "results", "pilot")


def job(c):
    work = tempfile.mkdtemp()
    tr = load_trace(os.path.join(BENCH, c["path"]))
    out = []
    for label, gw in {**PRIMARY, **SECONDARY}.items():
        for cond in CONDITIONS:
            _, scored, info = run(tr, "v1", gw, cond, work)
            out.append({"run_id": f"c{c['case_id']:03d}_{label}_{cond}",
                        "outcomes_v1": [s["outcome"] for s in scored], "utility_v1": info["utility"]})
    return c, out


def main():
    cases = json.load(open(f"{P}/pilot_cases.json"))
    runs = {json.loads(l)["run_id"]: json.loads(l) for l in open(f"{P}/pilot_runs.jsonl")}
    sel = [c for c in cases if c["version_source"] in ("reproduction", "unresolved")]
    same, diff, util_diff, unresolved = 0, [], 0, []
    with mp.Pool(2) as pool:
        for c, out in pool.imap(job, sel):
            for o in out:
                if c["version_source"] == "unresolved":
                    unresolved.append({"case_id": c["case_id"], "pipeline": c["pipeline"], **o})
                    continue
                orig = runs[o["run_id"]]
                if [a["outcome"] for a in orig["attempts"]] == o["outcomes_v1"]:
                    same += 1
                else:
                    diff.append(o["run_id"])
                util_diff += orig["utility"] != o["utility_v1"]
    res = {"reconstructed_runs_compared": same + len(diff), "identical_safety_outcomes": same,
           "different_safety_outcomes": diff, "benchmark_utility_differs_in_runs": util_diff,
           "unresolved_cases_under_v1": unresolved}
    json.dump(res, open(f"{P}/audit/version_sensitivity.json", "w"), indent=1)
    print({k: (v if not isinstance(v, list) else len(v)) for k, v in res.items()})


if __name__ == "__main__":
    main()
