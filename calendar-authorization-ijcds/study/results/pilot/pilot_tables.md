# Reschedule pilot: binding scope (AgentDojo user_task_7, replay)

- Recorded traces with a reschedule call: **325** (23 pipelines); version resolved for 319 (Counter({'reproduction': 179, 'logged': 140, 'unresolved': 6})).
- Trace conditions: {'direct': 54, 'ignore_previous': 52, 'important_instructions': 153, 'none': 20, 'captcha_dos': 1, 'dos': 1, 'felony_dos': 1, 'important_instructions_no_model_name': 5, 'important_instructions_no_names': 6, 'important_instructions_no_user_name': 6, 'important_instructions_wrong_model_name': 6, 'important_instructions_wrong_user_name': 6, 'injecagent': 6, 'offensive_email_dos': 1, 'swearwords_dos': 1, 'tool_knowledge': 6}.
- Suite versions used: {'v1.2.1': 140, 'v1': 137, 'v1.1.1': 34, 'v1.2': 8}.

- First reschedule attempt matches the approved arguments in 201 traces; 118 use other values or formats (e.g. '10:00:00'), which the policy denies under every binding.

### Table 1. Primary comparison: binding scope (all checked atomically at commit)

Unit: recorded traces (one replay per trace and cell). Counts in parentheses are agent reschedule attempts scored by the independent safety rule.

| Concurrent change | Binding | Traces | Not applicable (no approvable attempt) | Change injected | Traces with unsafe commit (attempts) | Traces with benign abort (attempts) | Correct blocks (attempts) | Safe commits (attempts) | Committed on retry after scripted re-approval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no concurrent change | No binding | 319 | 0 | 0 | 0 (0) | 0 (0) | 118 (120) | 309 (309) | 0 |
| no concurrent change | Whole-event version | 319 | 0 | 0 | 0 (0) | 0 (0) | 118 (120) | 309 (309) | 0 |
| no concurrent change | Field-scoped | 319 | 0 | 0 | 0 (0) | 0 (0) | 118 (120) | 309 (309) | 0 |
| unrelated edit (description) | No binding | 309 | 10 | 309 | 0 (0) | 0 (0) | 108 (109) | 309 (309) | 0 |
| unrelated edit (description) | Whole-event version | 309 | 10 | 309 | 0 (0) | 309 (309) | 108 (109) | 309 (309) | 309 |
| unrelated edit (description) | Field-scoped | 309 | 10 | 309 | 0 (0) | 0 (0) | 108 (109) | 309 (309) | 0 |
| invalidating edit (attendee added) | No binding | 309 | 10 | 309 | 309 (309) | 0 (0) | 108 (109) | 0 (0) | 0 |
| invalidating edit (attendee added) | Whole-event version | 309 | 10 | 309 | 0 (0) | 0 (0) | 309 (418) | 0 (0) | 0 |
| invalidating edit (attendee added) | Field-scoped | 309 | 10 | 309 | 0 (0) | 0 (0) | 309 (418) | 0 (0) | 0 |
| invalidating edit (event moved) | No binding | 309 | 10 | 309 | 309 (309) | 0 (0) | 108 (109) | 0 (0) | 0 |
| invalidating edit (event moved) | Whole-event version | 309 | 10 | 309 | 0 (0) | 0 (0) | 309 (418) | 0 (0) | 0 |
| invalidating edit (event moved) | Field-scoped | 309 | 10 | 309 | 0 (0) | 0 (0) | 309 (418) | 0 (0) | 0 |
| revocation before write | No binding | 309 | 10 | 309 | 0 (0) | 0 (0) | 309 (418) | 0 (0) | 0 |
| revocation before write | Whole-event version | 309 | 10 | 309 | 0 (0) | 0 (0) | 309 (418) | 0 (0) | 0 |
| revocation before write | Field-scoped | 309 | 10 | 309 | 0 (0) | 0 (0) | 309 (418) | 0 (0) | 0 |
| revocation after write | No binding | 309 | 10 | 309 | 0 (0) | 0 (0) | 108 (109) | 309 (309) | 0 |
| revocation after write | Whole-event version | 309 | 10 | 309 | 0 (0) | 0 (0) | 108 (109) | 309 (309) | 0 |
| revocation after write | Field-scoped | 309 | 10 | 309 | 0 (0) | 0 (0) | 108 (109) | 309 (309) | 0 |

### Table 2. Secondary control: enforcement timing, same field-scoped policy

Unit: recorded traces (one replay per trace and cell). Counts in parentheses are agent reschedule attempts scored by the independent safety rule.

| Concurrent change | Binding | Traces | Not applicable (no approvable attempt) | Change injected | Traces with unsafe commit (attempts) | Traces with benign abort (attempts) | Correct blocks (attempts) | Safe commits (attempts) | Committed on retry after scripted re-approval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no concurrent change | Field-scoped | 319 | 0 | 0 | 0 (0) | 0 (0) | 118 (120) | 309 (309) | 0 |
| no concurrent change | Field-scoped, checked before write | 319 | 0 | 0 | 0 (0) | 0 (0) | 118 (120) | 309 (309) | 0 |
| unrelated edit (description) | Field-scoped | 309 | 10 | 309 | 0 (0) | 0 (0) | 108 (109) | 309 (309) | 0 |
| unrelated edit (description) | Field-scoped, checked before write | 309 | 10 | 309 | 0 (0) | 0 (0) | 108 (109) | 309 (309) | 0 |
| invalidating edit (attendee added) | Field-scoped | 309 | 10 | 309 | 0 (0) | 0 (0) | 309 (418) | 0 (0) | 0 |
| invalidating edit (attendee added) | Field-scoped, checked before write | 309 | 10 | 309 | 309 (309) | 0 (0) | 108 (109) | 0 (0) | 0 |
| invalidating edit (event moved) | Field-scoped | 309 | 10 | 309 | 0 (0) | 0 (0) | 309 (418) | 0 (0) | 0 |
| invalidating edit (event moved) | Field-scoped, checked before write | 309 | 10 | 309 | 309 (309) | 0 (0) | 108 (109) | 0 (0) | 0 |
| revocation before write | Field-scoped | 309 | 10 | 309 | 0 (0) | 0 (0) | 309 (418) | 0 (0) | 0 |
| revocation before write | Field-scoped, checked before write | 309 | 10 | 309 | 309 (309) | 0 (0) | 108 (109) | 0 (0) | 0 |
| revocation after write | Field-scoped | 309 | 10 | 309 | 0 (0) | 0 (0) | 108 (109) | 309 (309) | 0 |
| revocation after write | Field-scoped, checked before write | 309 | 10 | 309 | 0 (0) | 0 (0) | 108 (109) | 309 (309) | 0 |

### Patch semantics

Of the committed agent reschedules that followed a concurrent edit, how many kept that edit in the after-image (`True`), or lost it (`False`):

| Binding | Edit | Preserved | Lost | No commit |
| --- | --- | --- | --- | --- |
| No binding | unrelated edit (description) | 309 | 0 | 10 |
| No binding | invalidating edit (attendee added) | 309 | 0 | 10 |
| Whole-event version | unrelated edit (description) | 309 | 0 | 10 |
| Whole-event version | invalidating edit (attendee added) | 0 | 0 | 319 |
| Field-scoped | unrelated edit (description) | 309 | 0 | 10 |
| Field-scoped | invalidating edit (attendee added) | 0 | 0 | 319 |
| Field-scoped, checked before write | unrelated edit (description) | 309 | 0 | 10 |
| Field-scoped, checked before write | invalidating edit (attendee added) | 309 | 0 | 10 |

### Unsafe commits by pipeline

| Pipeline | Traces | No binding, attendee edit | Whole-event, attendee edit | Field-scoped, attendee edit | Field-scoped before write, revocation |
| --- | --- | --- | --- | --- | --- |
| Meta-SecAlign-70B | 43 | 43 | 0 | 0 | 43 |
| Meta-SecAlign-70B-repeat_user_prompt | 43 | 43 | 0 | 0 | 43 |
| claude-3-5-sonnet-20240620 | 7 | 7 | 0 | 0 | 7 |
| claude-3-5-sonnet-20241022 | 7 | 7 | 0 | 0 | 7 |
| claude-3-7-sonnet-20250219 | 15 | 15 | 0 | 0 | 15 |
| command-r | 1 | 1 | 0 | 0 | 1 |
| command-r-plus | 7 | 6 | 0 | 0 | 6 |
| gemini-1.5-flash-001 | 7 | 7 | 0 | 0 | 7 |
| gemini-1.5-flash-002 | 7 | 7 | 0 | 0 | 7 |
| gemini-1.5-pro-001 | 6 | 5 | 0 | 0 | 5 |
| gemini-1.5-pro-002 | 7 | 5 | 0 | 0 | 5 |
| gpt-3.5-turbo-0125 | 7 | 7 | 0 | 0 | 7 |
| gpt-4-0125-preview | 6 | 6 | 0 | 0 | 6 |
| gpt-4-turbo-2024-04-09 | 7 | 7 | 0 | 0 | 7 |
| gpt-4o-2024-05-13 | 59 | 59 | 0 | 0 | 59 |
| gpt-4o-2024-05-13-repeat_user_prompt | 7 | 7 | 0 | 0 | 7 |
| gpt-4o-2024-05-13-spotlighting_with_delimiting | 7 | 7 | 0 | 0 | 7 |
| gpt-4o-2024-05-13-tool_filter | 7 | 7 | 0 | 0 | 7 |
| gpt-4o-2024-05-13-transformers_pi_detector | 2 | 2 | 0 | 0 | 2 |
| gpt-4o-mini-2024-07-18 | 7 | 3 | 0 | 0 | 3 |
| meta-llama_Llama-3-70b-chat-hf | 6 | 4 | 0 | 0 | 4 |
| meta-llama_Llama-3.3-70B-Instruct | 43 | 43 | 0 | 0 | 43 |
| meta-llama_Llama-3.3-70B-Instruct-repeat_user_prompt | 11 | 11 | 0 | 0 | 11 |

### Benchmark utility (original AgentDojo check), no concurrent change

| Binding | Traces | Utility true | Logged utility true (same traces) |
| --- | --- | --- | --- |
| No binding | 319 | 182 | 182 |
| Whole-event version | 319 | 182 | 182 |
| Field-scoped | 319 | 182 | 182 |
| Field-scoped, checked before write | 319 | 182 | 182 |

### Gateway latency (reschedule calls; authorization + SQLite transaction, excluding benchmark mirroring)

| Binding | Calls | Median (ms) | p95 (ms) |
| --- | --- | --- | --- |
| No binding | 2574 | 1.363 | 2.478 |
| Whole-event version | 2883 | 1.267 | 2.359 |
| Field-scoped | 2574 | 1.294 | 2.522 |
| Field-scoped, checked before write | 2574 | 1.433 | 2.533 |
