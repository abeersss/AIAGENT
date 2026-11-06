# Field-Scoped Authorization for AI Agent Calendar Updates under Concurrent Edits

Manuscript, code, raw transaction logs and audit files for

> Dr. Abeer Alshammari, "Field-Scoped Authorization for AI Agent Calendar Updates under Concurrent Edits," prepared for the *International Journal of Computing and Digital Systems (IJCDS)*.

The study asks one question. When the check runs inside the same database transaction as the write, does field-scoped authorization still let legitimate calendar updates through after unrelated concurrent edits, while blocking writes after an approval-invalidating edit or a revocation?

## Headline results (replay of recorded traces; no fresh model runs)

The data are 319 recorded traces from 23 public model pipelines, all for one AgentDojo task (`user_task_7`). Of these, 309 contain an eligible update. One concurrent change was injected before each trace's first eligible update.

| Concurrent change | No binding | Whole-event binding | Field-scoped binding |
| --- | --- | --- | --- |
| Description edit (unrelated) | 309 safe commits | 309 benign aborts, then 309 scripted recoveries | 309 safe commits |
| Attendee added | 309 **unsafe** commits | 309 correct denials | 309 correct denials |
| Event moved | 309 **unsafe** commits | 309 correct denials | 309 correct denials |
| Revocation before write | 309 correct denials | 309 correct denials | 309 correct denials |

- **Pre-write check:** the same field policy checked in a separate transaction before the write committed all 309 unsafe updates. It also committed 207 of 500 local two-thread SQLite trials with an artificial 2 ms check-to-write gap; the atomic version committed none.
- **Lost updates:** under no binding and under the pre-write check, every update committed after a concurrent move overwrote the moved time. Patch writes preserved concurrent description and attendee edits.
- **Latency:** the median is about 1.5 ms under every binding; median paired differences from no binding were under 0.04 ms in matched no-change runs.

## Layout

| Path | Contents |
| --- | --- |
| `paper/Alshammari_IJCDS_FieldScopedAuthorization.pdf` | Compiled manuscript (official IJCDS LaTeX template, 10 pages) |
| `paper/Alshammari_IJCDS_FieldScopedAuthorization.docx` | Word version of the paper |
| `paper/*.tex`, `references.bib`, template files, `figures/` | Editable LaTeX project; `figures/make_figures.py` redraws the figures from the result files |
| `paper/verification_note.md` | Maps every headline number to the file and key it comes from, and lists open items |
| `study/cta/` | Event store, tool gateways (NB, WE, FS, T1), approval fixture, replay, and the independent safety rule |
| `study/experiments/` | Trace audit, pilot, race test, analysis, audit and regeneration, version sensitivity |
| `study/docs/` | Safety rule as specified before the pilot, related-work notes, reference verification log |
| `study/results/` | Manifests, the 7,656 raw transaction logs (`pilot/txlogs/`), race logs, audit files |
| `study/results/_pilot_v1_superseded/` | First pilot. It is kept for transparency but superseded: it injected the change at the first reschedule call, not the first eligible one |

## Reproducing

```bash
git clone https://github.com/sequrity-ai/agentdojo-benchmark
git -C agentdojo-benchmark checkout b29fdb375df61261662eea53b7e3d430bc2bcda2
python -m venv venv && . venv/bin/activate
pip install -e ./agentdojo-benchmark matplotlib
export AGENTDOJO_DIR=$PWD/agentdojo-benchmark
cd study
python experiments/audit_traces.py        # trace accounting and manifest
python experiments/pilot_reschedule.py    # replay under every binding and change
python experiments/ordering_test.py       # 500 two-thread races per gateway
python experiments/analyze_pilot.py
python experiments/audit_pilot.py         # reconciliation, regenerated tables, latency
python experiments/version_sensitivity.py
```

`study/requirements-lock.txt` lists the exact package versions used. The traces are © their authors under the MIT License; see the AgentDojo benchmark repository.

## Limitations

- The study covers a single task, on simulated records.
- Concurrency is introduced through controlled schedules.
- Recovery after re-approval is scripted.
- No live model was run.

The paper discusses each of these in its Limitations section.
