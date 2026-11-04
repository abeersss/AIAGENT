"""True concurrency test: a revocation and an agent reschedule on two SQLite connections
in two threads.

Part 1, forced orders (deterministic): (a) the revocation commits first, then the write;
(b) the write's transaction holds the lock, the revocation waits and commits afterwards.
Part 2, stress: both threads are released together with random jitter, N times per gateway,
and the raw logs are scored with the independent safety rule.

Gateways: field-scoped at commit time (A2) vs the same field-scoped policy checked before the
write (T1, with a short window between its check and its write in which the revocation can land).
"""
import json
import os
import random
import sys
import tempfile
import threading
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agentdojo.functions_runtime import FunctionsRuntime          # noqa: E402
from agentdojo.task_suite.load_suites import get_suite             # noqa: E402

from cta import fixtures, safety_rule                               # noqa: E402
from cta.gateways import GATEWAYS                                   # noqa: E402
from cta.store import EventStore                                    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "pilot")
ARGS = {"event_id": "5", "new_start_time": "2024-05-20 10:00", "new_end_time": "2024-05-20 11:00"}


def setup(work):
    suite = get_suite("v1.2.2", "workspace")
    ut = suite.user_tasks["user_task_7"]
    env = ut.init_environment(suite.load_and_inject_default_environment({}))
    fd, path = tempfile.mkstemp(suffix=".sqlite", dir=work)
    os.close(fd)
    st = EventStore(path)
    st.load_events(env.calendar)
    specs = [s for s in fixtures.approval_specs(suite, ut.ID, env) if s["action"] == "reschedule_calendar_event"]
    aid = fixtures.grant_all(st, specs)[0]
    return suite, env, st, aid, path


def one(gw_name, mode, work, jitter=None, window_s=0.002):
    suite, env, st, aid, path = setup(work)
    other = st.other_connection()                     # the user's device: a separate connection
    in_check = threading.Event()

    def hook(gap, ctx):
        if gap == "check_write":
            in_check.set()
            time.sleep(window_s)                      # realistic gap between check and write

    gw = GATEWAYS[gw_name](st, FunctionsRuntime(suite.tools), env, fixtures.USER, window_hook=hook)

    if mode == "revoke_first":
        other.revoke(aid)
        gw.call("reschedule_calendar_event", dict(ARGS))
    elif mode == "write_first":
        # hold the write lock as the agent's transaction would, start the revocation, then commit
        started = threading.Event()
        def revoker():
            started.set()
            other.revoke(aid)                         # blocks on SQLite's lock until the writer commits
        st.conn.execute("BEGIN IMMEDIATE")
        a, d = gw._find(st.conn, "reschedule_calendar_event", ARGS, "field")
        t = threading.Thread(target=revoker)
        t.start()
        started.wait()
        time.sleep(0.05)
        st.apply_write(st.conn, "reschedule_calendar_event", ARGS, env.calendar.account_email,
                       a["approval_id"], gw_name)
        st.conn.execute("COMMIT")
        t.join()
    else:  # stress: release both together
        go = threading.Barrier(2)
        def agent():
            go.wait()
            time.sleep(jitter[0])
            gw.call("reschedule_calendar_event", dict(ARGS))
        def user():
            go.wait()
            time.sleep(jitter[1])
            other.revoke(aid)
        ts = [threading.Thread(target=agent), threading.Thread(target=user)]
        [t.start() for t in ts]
        [t.join() for t in ts]
    log = st.log_rows()
    scored = safety_rule.score(log, st.approvals())
    order = [r["kind"] for r in log if r["kind"] in ("write", "deny", "revoke")]
    st.conn.close(); other.conn.close(); os.remove(path)
    return {"outcomes": [s["outcome"] for s in scored], "order": order, "log": log}


def main():
    os.makedirs(OUT, exist_ok=True)
    work = tempfile.mkdtemp()
    res = {"forced": {}, "stress": {}}
    with open(f"{OUT}/ordering_txlogs.jsonl", "w") as fh:
        for gw in ("A2_committime_diffscope", "T1_precheck_fieldscope"):
            for mode in ("revoke_first", "write_first"):
                r = one(gw, mode, work)
                res["forced"][f"{gw}:{mode}"] = {"outcomes": r["outcomes"], "commit_order": r["order"]}
                for row in r["log"]:
                    fh.write(json.dumps({"run": f"{gw}:{mode}", **row}) + "\n")
    rng = random.Random(20261104)
    n = int(os.environ.get("N_STRESS", "500"))
    for gw in ("A2_committime_diffscope", "T1_precheck_fieldscope"):
        c = Counter()
        for _ in range(n):
            r = one(gw, "stress", work, jitter=(rng.uniform(0, 0.004), rng.uniform(0, 0.004)))
            c[(tuple(r["outcomes"]), tuple(r["order"]))] += 1
        res["stress"][gw] = {"n": n, "seed": 20261104,
                             "unsafe_commits": sum(v for (o, _), v in c.items() if "unsafe_commit" in o),
                             "safe_commits": sum(v for (o, _), v in c.items() if "safe_commit" in o),
                             "correct_blocks": sum(v for (o, _), v in c.items() if "correct_block" in o),
                             "patterns": {f"{list(o)} order={list(od)}": v for (o, od), v in c.items()}}
    json.dump(res, open(f"{OUT}/ordering_results.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
