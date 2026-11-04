# Reference verification log (literature check, 4 Nov 2026)

"Opened" means the URL that was actually fetched. Items marked **me** were re-read directly in the main session. The rest come from the literature agent and were opened through a summarising fetch tool, so read the full PDFs before citing them in the related-work text.

| # | Reference | Opened | Status |
| --- | --- | --- | --- |
| 1 | E. Debenedetti et al., "AgentDojo: A dynamic environment to evaluate prompt injection attacks and defenses for LLM agents," NeurIPS 2024 D&B, pp. 82895–82920, doi:10.52202/079017-2636 | proceedings.neurips.cc/…/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract.html | verified |
| 2 | T. Shi et al., "Progent: Programmable privilege control for LLM agents," arXiv:2504.11703v2, 2025 | arxiv.org/html/2504.11703v2 | verified |
| 3 | E. Debenedetti et al., "Defeating prompt injections by design," arXiv:2503.18813, 2025 | arxiv.org/abs/2503.18813 | verified |
| 4 | M. Costa et al., "Securing AI agents with information-flow control," arXiv:2505.23643v2, 2025 | arxiv.org/pdf/2505.23643v2 | verified |
| 5 | P. Y. Zhong et al., "RTBAS," arXiv:2502.08966v2, 2025 | arxiv.org/html/2502.08966v2 | verified |
| 6 | L. Tsai and E. Bagdasarian, "Contextual agent security," HotOS '25, arXiv:2501.17070v3 | arxiv.org/html/2501.17070v3 | verified |
| 7 | H. Wang, C. M. Poskitt, J. Sun, "AgentSpec," arXiv:2503.18666, doi:10.1145/3744916.3764546 | arxiv.org/abs/2503.18666v1 | verified (venue unconfirmed) |
| 8 | E. Li et al., "ACE," arXiv:2504.20984v3, doi:10.14722/ndss.2026.230352 | arxiv.org/abs/2504.20984 | verified (venue inferred from DOI) |
| 9 | Y. Wu et al., "IsolateGPT," arXiv:2403.04960v2 | arxiv.org/abs/2403.04960v2 | verified (NDSS 2025 unconfirmed) |
| 10 | K. Zhu et al., "MELON," ICML 2025, arXiv:2502.05174 | icml.cc/virtual/2025/poster/44447 | verified |
| 11 | D. Lilienthal and S. Hong, "Mind the gap: TOCTOU vulnerabilities in LLM-enabled agents," NeurIPS 2025 ML for Systems workshop, arXiv:2508.17155 | arxiv.org/abs/2508.17155 | verified |
| 12 | L. Jiang et al., "Atomicity for agents," arXiv:2603.00476v1, 2026 | arxiv.org/html/2603.00476v1 | verified |
| 13 | I. Santos-Grueiro, "Temporary authority, permanent effects: Commit-time authorization for LLM agents," arXiv:2607.10487v1, 2026 | arxiv.org/abs/2607.10487 | verified (**me**) |
| 14 | Q. Zhang, "Approve the effect, not the tool call," ICML 2026 workshop, OpenReview lClCNawtQB | icml.cc/virtual/2026/67824 | abstract only |
| 15 | Y. Peng and X. Wu, "Stateful governance for concurrent agentic systems," arXiv:2608.02764 | arxiv.org/pdf/2608.02764 | verified (date from a mirror) |
| 16 | Y. Tong, L. Dai, S. Guo, "AID-Guard: Stateful authorization for delegated agent effects," arXiv:2608.21159v1 | arxiv.org/pdf/2608.21159 | verified (**me**) |
| 17 | J. Xu et al., "Beyond single-use tokens," arXiv:2608.01710v1 | arxiv.org/pdf/2608.01710 | verified |
| 18 | Z. Zheng et al., "Stale does not mean unsafe," arXiv:2609.29522v1 | arxiv.org/abs/2609.29522 | verified (**me**; ID/date stamp mismatch to check) |
| 19 | B. Mohammadi et al., "Atomix," arXiv:2602.14849v2 | arxiv.org/abs/2602.14849 | verified |
| 20 | Z. Chen et al., "Cordon," arXiv:2606.17573v1 | alphaxiv.org/abs/2606.17573 (mirror) | mirror only |
| 21 | M. Bishop and M. Dilger, "Checking for race conditions in file accesses," *Computing Systems* 9(2):131–152, 1996 | nob.cs.ucdavis.edu/bishop/papers/1996-compsys | verified |
| 22 | H. T. Kung and J. T. Robinson, "On optimistic methods for concurrency control," *ACM TODS* 6(2):213–226, 1981, doi:10.1145/319566.319567 | research.cs.wisc.edu/…/kung_occ_tds_1981.html | verified |
| 23 | J. H. Saltzer and M. D. Schroeder, "The protection of information in computer systems," *Proc. IEEE* 63(9):1278–1308, 1975, doi:10.1109/PROC.1975.9939 | secondary source plus transcription | verify the DOI before citing |
| 24 | W. S. McPhee, "Operating system integrity in OS/VS2," *IBM Systems Journal*, 1974 | secondary | volume/pages/DOI UNVERIFIED |
| 25 | J. P. Anderson, "Computer security technology planning study," ESD-TR-73-51, 1972 | apps.dtic.mil/sti/pdfs/AD0758206.pdf | verified |
| 26 | D. D. Redell and R. S. Fabry, "Selective revocation of capabilities," IRIA Workshop, 1974, pp. 197–210 | secondary bibliography | verify before citing |
| 27 | R. Fielding, M. Nottingham, J. Reschke, "HTTP semantics," RFC 9110, 2022 | rfc-editor.org/rfc/rfc9110.txt | verified (DOI not shown) |
| 28 | SQLite, "Transaction" documentation | www2.sqlite.org/lang_transaction.html | verified |

Before submission, re-resolve every DOI through Crossref, as was done for the Turbo-NAFS paper.
