# Verification note: "Field-Scoped Authorization for AI Agent Calendar Updates under Concurrent Edits"

Dr. Abeer Saleh Alshammari. Prepared 4 Nov 2026 for the author's review.

All paths are relative to the study project (`cta/project/`). Every number below was re-read from the named file after the final compile, and each one matches the manuscript.

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
| Tables regenerated from raw logs match the pilot runs | 0 mismatches | `regenerated_tables.json` (`_attempt_sequence_mismatches_vs_pilot_runs`) |
| Raw transaction logs | 7,656 runs | `results/pilot/pilot_runs.jsonl`, `results/pilot/txlogs/*.jsonl` |
| Raw log excerpt (Table VII), case 249 | four cells | `results/pilot/txlog_excerpts.md` |
| Two-thread races, atomic FS: write first / denied / unsafe | 254 / 246 / 0 | `results/pilot/ordering_results.json` (`stress.A2_committime_diffscope`) |
| Two-thread races, T1 | 52 / 241 / 207 | `ordering_results.json` (`stress.T1_precheck_fieldscope`) |
| Matched latency on 429 calls (median, p95, paired diff) | NB 1.507/2.695; WE 1.473/2.466/−0.029; FS 1.476/2.584/−0.017; T1 1.456/2.456/−0.035 ms | `results/pilot/audit/latency_matched.json` |
| Utility agreement at trace level | 319/319 under every binding (182 true); 140/140 on logged-version traces | `results/pilot/audit/utility_trace_level.json` |
| Benchmark defect: ground truth passes 59 of 60; user_task_7 fails under v1 | 59/60 | `results/unmodified_groundtruth.json` |
| Denial reasons (Table IX), argument patterns (Table X) | as tabled | `results/pilot/pilot_runs.jsonl`; `results/pilot/pilot_summary.json` |
| Per-pipeline accounting (Table VIII) | 23 rows, totals 325/6/140/179/27/309/201 | `results/pilot/audit/per_pipeline.json` |
| Safety rule (written before the pilot ran) | S1–S4 | `docs/safety_rule.md`, `cta/safety_rule.py` |

Replay, injected schedules and fresh runs are reported separately. **No fresh model runs were made**, so the paper reports none. Every agent behaviour comes from recorded traces, and recovery after denial is a scripted protocol.

## 2. Manuscript checks done

- Built with the official IJCDS LaTeX package (`IJCDS_Latex_4_8_2024.zip` from ijcds.uob.edu.bh/for-authors). The class, bst, master file and style files are unchanged; only content fields in `ijcds_header.tex` were edited.
- 10 pages including references and appendices (target 10–15).
- Abstract: 198 words (limit 200).
- No undefined citations or references and no overfull boxes. The remaining log warnings come from the template itself.
- I inspected every page as an image: no clipped tables or figures.
- 18 references, IEEE numbered in citation order. Each is cited, and preprints are marked "arXiv preprint". DOIs or URLs and the opened sources are recorded in `cta/project/docs/references_verified.md` and the header of `references.bib`.
- The trace source is cited with its full commit hash, b29fdb375df61261662eea53b7e3d430bc2bcda2 (ref. [3]).
- No template text is left in the body. The template's journal header placeholders are kept on purpose; see the blockers below.

## 3. Blockers and items for the author

1. **Affiliation:** department, organization, city and country are a bracketed placeholder in the byline.
2. **Correspondence:** the footer uses engineera209@gmail.com. Confirm this address, or give an institutional one.
3. **"Dr." in the byline:** this was requested. IJCDS style normally omits titles, so check with the journal.
4. **Journal header fields:** "2024, VOL. 17, NO. 1, 1–10", DOI `ijcds/XXXXXX` and "Received/Revised/Accepted [date]" are template placeholders for the editor.
5. **Public repository URL** for the code and logs still needs to be added (Section 9).
6. **No fresh model runs:** there was no model API key and no route to download model weights. Agent recovery after denial is therefore untested.
7. **Version evidence:** 27 reconstructed versions conflict with published run dates. Safety outcomes are unaffected (4,296/4,296 identical), but utility for reconstructed traces is not independent evidence.
8. **Preprints:** six cited works are arXiv preprints: [4]–[6] (2025) and [10]–[12] (Jul–Sep 2026). [9] is a workshop paper. Zheng et al. [12] showed an arXiv ID/date-stamp mismatch to recheck before submission. Before final submission, re-check every preprint for a published version.
9. **Submission requirements outside the manuscript:** the EDAS cover letter and the journal's similarity check (under 15%) have not been run.
10. **Word copy:** produced by automatic conversion for review only. The layout is single-column and the tables are simplified. The PDF is the reference version.
