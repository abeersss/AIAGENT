# Verification note: "Field-Scoped Authorization for AI Agent Calendar Updates under Concurrent Edits"

Dr. Abeer Alshammari, Research Practitioner, Kuwait. Prepared 4 Nov 2026; revised 6 Nov 2026 after the reviewer's report.

All paths are relative to the study folder (`calendar-authorization-ijcds/study/` in https://github.com/abeersss/AIAGENT). Every number below was re-read from the named file after the final compile, and each one matches the manuscript.

## 1. Headline results and their source files

| Claim in the paper | Value | File (key) |
| --- | --- | --- |
| Trace files / replayable / with reschedule call (Table III) | 416 / 371 / 325 | `results/pilot/audit/reconciliation.json` (`reconciliation`) |
| Version logged / reconstructed / unresolved | 140 / 179 / 6 (all gpt-4o-2024-05-13) | same file; `unresolved_cases` lists the 6 paths |
| Resolved, eligible, first-eligible, later-eligible, never eligible | 319 / 309 / 201 / 108 / 10 | `reconciliation.json`; `results/pilot/pilot_cases.json` |
| Reconstruction split v1 / v1.1.1 / v1.2 | 137 / 34 / 8 | `results/pilot/audit/version_evidence.json` |
| 27 reconstructed versions contradict the published run date | 27 | `version_evidence.json`; per pipeline in `audit/per_pipeline.json` |
| Safety outcomes unchanged under v1 for all reconstructed runs | 4,296 of 4,296; utility differs in 462 | `results/pilot/audit/version_sensitivity.json` |
| No binding, attendee change or move: unsafe commits | 309 each | `results/pilot/audit/regenerated_tables.json` (`NB:A`, `NB:T`) |
| Whole event, description edit: benign aborts, then scripted recovery | 309, 309 | `regenerated_tables.json` (`WE:U`) |
| Field scoped, description edit: immediate safe commits | 309 | `regenerated_tables.json` (`FS:U`) |
| Field scoped, attendee change, move or revocation: correct denials | 309 each | `regenerated_tables.json` (`FS:A`, `FS:T`, `FS:R`) |
| Pre-write field check (T1): unsafe after A, T, R | 309 each | `regenerated_tables.json` (`T1:A`, `T1:T`, `T1:R`) |
| Patch after-images: description kept (NB, WE after re-approval, FS, T1) and attendees kept (NB, T1), 309 each; moved start/end overwritten under NB and T1, 309 each | as stated in §6B | `results/pilot/txlogs/*.jsonl` (first agent write after the concurrent edit; before/after images) |
| Injected-change comparison uses 309 traces; 10 resolved traces with no eligible attempt excluded | 309 / 10 | `reconciliation.json`; `pilot_cases.json` |
| Tables regenerated from raw logs match the pilot runs | 0 mismatches | `regenerated_tables.json` (`_attempt_sequence_mismatches_vs_pilot_runs`) |
| Raw transaction logs | 7,656 runs | `results/pilot/pilot_runs.jsonl`, `results/pilot/txlogs/*.jsonl` |
| Raw log excerpt (Table VII), case 249 | four cells | `results/pilot/txlog_excerpts.md` |
| Local two-thread SQLite trials (2 ms artificial check-to-write gap), atomic FS: write first / denied / unsafe | 254 / 246 / 0 | `results/pilot/ordering_results.json` (`stress.A2_committime_diffscope`) |
| Local two-thread SQLite trials, T1 | 52 / 241 / 207 | `ordering_results.json` (`stress.T1_precheck_fieldscope`) |
| Matched latency on 429 calls (median, p95, paired diff) | NB 1.507/2.695; WE 1.473/2.466/−0.029; FS 1.476/2.584/−0.017; T1 1.456/2.456/−0.035 ms | `results/pilot/audit/latency_matched.json` |
| Utility agreement at trace level | 319/319 under every binding (182 true); 140/140 on logged-version traces | `results/pilot/audit/utility_trace_level.json` |
| Benchmark defect: ground truth passes 59 of 60; user_task_7 fails under v1 | 59/60 | `results/unmodified_groundtruth.json` |
| Denial reasons (Table IX), argument patterns (Table X) | as tabled | `results/pilot/pilot_runs.jsonl`; `results/pilot/pilot_summary.json` |
| Per-pipeline accounting (Table VIII) | 23 rows, totals 325/6/140/179/27/309/201 | `results/pilot/audit/per_pipeline.json` |
| Safety rule (written before the pilot ran) | S1–S4 | `docs/safety_rule.md`, `cta/safety_rule.py` |

Replay, injected schedules and fresh runs are reported separately. **No fresh model runs were made**, so the paper reports none. Every agent behaviour comes from recorded traces, and recovery after denial is a scripted protocol.

## 2. Manuscript checks done

- Built with the official IJCDS LaTeX package (`IJCDS_Latex_4_8_2024.zip`). The class, bst, master file and style files are unchanged. Page size is the template's active setting: US Letter, 8.5 × 11 in (21.6 × 27.9 cm, the "21 × 28 cm" page). The A4 line in the template is commented out.
- 10 pages including references and appendices (limit 10–15).
- Abstract: 188 words by whitespace count (limit 200).
- No undefined citations or references and no overfull boxes. I inspected every page as an image.
- 18 references, IEEE numbered in citation order, each one cited. Preprints are marked.
  - [5] CaMeL now cites the published version: IEEE SaTML 2026, Munich, pp. 587–618, DOI 10.1109/SaTML68715.2026.00040. Checked on IEEE Xplore (document 11691650) on 6 Nov 2026.
  - [10] Santos-Grueiro now cites v2, revised 31 Oct 2026. Checked on the arXiv abstract page and in the v2 source. The text and Table I now describe atomic validation at the sink and the SQLite transaction-runtime integration.
- The journal masthead now shows only the journal name and logo. The template's sample volume and issue, dummy DOI and received/accepted dates were removed; the editor assigns these at acceptance.
- The trace source is cited with its full commit hash (ref. [3]). The code and logs are in https://github.com/abeersss/AIAGENT, folder `calendar-authorization-ijcds`.

## 3. Reviewer corrections (6 Nov 2026)

| Reviewer point | Change made |
| --- | --- |
| §5B: injection said to coincide with the first eligible attempt in all 319 traces | Now states 309 traces have an eligible attempt; the other 10 are excluded from the injected-change comparison. |
| §6B: "No concurrent change was lost" | Removed. Preservation is now limited to description and attendee edits as shown in the after-images. Event moves are reported separately: under NB and T1, all 309 committed updates overwrote the moved start and end (lost updates). |
| §6C and abstract: "real races" | Now "local two-thread SQLite trials", with the artificial 2 ms check-to-write gap stated in the abstract and the text. |
| §6D: "adds no measurable cost"; inference would dominate | Replaced with the observed result: median paired differences under 0.04 ms in absolute value in matched no-change runs. The inference claim is removed. |
| Abstract length | Cut to 188 words. |
| Affiliation, masthead placeholders | Byline is "Dr. Abeer Alshammari, Research Practitioner, Kuwait". Publisher fields are handled as described in §2. |
| [5] CaMeL, [10] Santos-Grueiro | Updated as described in §2. The contribution is repositioned: atomic validation is prior work, and this paper measures which fields to bind and what whole-event binding costs. |
| Reproducibility statement | Section 9 now gives the repository and folder, and lists the README with the run commands and package versions. |

## 4. Remaining items for the author

1. **"Dr." in the byline:** this was requested. IJCDS style normally omits titles, so check with the journal.
2. **No fresh model runs:** agent recovery after denial is untested; recovery in the paper is scripted.
3. **Version evidence:** 27 reconstructed versions conflict with published run dates. Safety outcomes are unaffected (4,296/4,296), but utility for reconstructed traces is not independent evidence.
4. **Preprints:** [4], [6], [10], [11] and [12] remain arXiv preprints. Re-check them for published versions before submission. [12] showed an arXiv ID/date-stamp mismatch.
5. **Not yet done:** the EDAS cover letter and the similarity check (under 15%).
6. **Word file:** made from the LaTeX source in a two-column journal layout. The PDF remains the reference version.
