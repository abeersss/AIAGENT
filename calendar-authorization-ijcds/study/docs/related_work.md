# Research-gap check (November 2026)

## Verdict

The working title "Commit-Time Authorization for AI Agent Calendar Changes" and its core mechanism are not novel.

| Work | What it already covers | Verified |
| --- | --- | --- |
| Santos-Grueiro, arXiv:2607.10487 (Jul. 2026) | The title "Commit-Time Authorization for LLM Agents". Defines freshness, effect binding (target, version, ticket) and eligibility (revocation), and measures unauthorized commits. CommitGuard is a *monitor*, not an atomic gateway. Uses a custom 54-task suite, not AgentDojo. | abstract read by me (arxiv.org/abs/2607.10487) |
| Tong, Dai, Guo, AID-Guard, arXiv:2608.21159 (Aug. 2026) | Authority checks and provider mutation in one SQLite transaction (atomic profile). Delegates version/ETag enforcement to the provider. AgentDojo v1.2.2, 4 suites × 4 user tasks. **Does not** compare the same policy at two enforcement points, report revocation-vs-write races on AgentDojo, measure aborts caused by unrelated concurrent edits, or replay recorded model traces. | PDF read by me |
| Zheng et al., "Stale Does Not Mean Unsafe", arXiv:2609.29522 | Global-epoch vs read-set-version vs semantic-predicate guards. Measures unsafe commits and benign interventions. 16 infrastructure tasks in a simulator, frozen proposals from 3 small local models. No calendar, no AgentDojo. | abstract read by me |
| Provenact (arXiv:2608.02764), CapLease (arXiv:2608.01710), EffectGuard (ICML 2026 workshop), Atomix (arXiv:2602.14849), Cordon (arXiv:2606.17573) | Pieces of the mechanism: policy evaluation and effect in one transaction; revocation ordered against commit; approval bound to the resolved effect. | summaries from the literature agent; full PDFs still to be read |
| Lilienthal & Hong, "Mind the Gap", NeurIPS 2025 ML for Systems workshop (arXiv:2508.17155) | TOCTOU in LLM agents (TOCTOU-Bench, built from AgentDojo). No transactions, versions or approvals. | agent-verified |
| Progent (arXiv:2504.11703), CaMeL (arXiv:2503.18813), AgentDojo (NeurIPS 2024 D&B) | An argument-level policy checked *before* each tool call; capability and data-flow policies; the benchmark. | agent-verified |

## Refined research question (pilot)

> On recorded real-model tool calls from AgentDojo Workspace (rescheduling an existing event), how does the **scope** of an approval's binding to event state change two counts: unsafe commits, under a separately specified safety rule, and benign aborts? The three scopes are no binding, whole-event version, and field-scoped binding. All three are enforced atomically at commit. Enforcement timing, the same field-scoped policy checked before the write, is a secondary control.

Established mechanisms are cited, not claimed: TOCTOU (McPhee 1974; Bishop & Dilger 1996), optimistic concurrency control (Kung & Robinson 1981), complete mediation (Saltzer & Schroeder 1975; Anderson 1972), capability revocation (Redell & Fabry 1974), conditional writes (RFC 9110 If-Match), and SQLite `BEGIN IMMEDIATE`.

The contribution is a controlled measurement on public traces. Its distinctive elements are the trace replay, the calendar field semantics and the attendee-change case.

The full verified reference list from the literature check is in `docs/references_verified.md`.
