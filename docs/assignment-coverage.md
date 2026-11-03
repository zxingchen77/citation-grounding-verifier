# Assignment requirements and evidence

This mapping follows the [assignment](https://gist.github.com/wsxiaoys/849522ee389e0ce359ef444653084484),
rechecked from its raw source on 2026-11-03. The revision replaces the main
synthetic evaluation with real-document excerpts. The [v3 report](real-docs-v3.md)
explains the data, dev decisions, frozen test and limitations.

| Requirement | Delivery and evidence | Remaining limit |
| --- | --- | --- |
| Python HTTP service; `POST /verify` | [API](../src/grounding/api.py), [types](../src/grounding/models.py), [contract tests](../tests/test_contract.py) | Semantic judgments still depend on the selected method. |
| Atomic claims, three verdicts and explanations | [Verifier methods](../src/grounding/verifiers.py), [saved outputs](../results/real-docs-v3/) | Splitting and qualifier preservation are measured failure modes. |
| Literal quotes and valid passage indices | `validate_evidence` checks exact substrings, bounds and verdict-specific citation presence; evidence IDs copy source text | A genuine quote can still be irrelevant or incomplete. |
| Graceful malformed inputs and provider failures | Structured 422/502/503/504 errors; bounded repair and timeouts; [tests](../tests/) | Real experiments use Codex; external HTTP provider has controlled transport tests only. |
| At least 20 labeled JSONL cases | [32 cases / 136 claims](../data/cases.jsonl); [source and license catalog](../data/sources/real-docs-v3.json) | Answers and gold are AI-authored adaptations, not raw RAGTruth responses. |
| Balanced supported / distortion / extrinsic / multi-passage scenarios | Eight cases per primary category; 20 dev / 12 test; [construction](../data/README.md) | Verdict counts are not balanced: 96 S / 30 C / 10 U. |
| Subtle errors and synthesis | Off-by-one counts, units, dates, condition direction, exceptions, scope, absent true facts, mixed clauses and multi-premise deductions | Small technical-English corpus; no broad production claim. |
| Deterministic, minimal LLM and optimized LLM comparison | Same [runner](../src/grounding/benchmark.py) and [scorer](../src/grounding/scoring.py), retained schedules, outputs and manifests | Test gold is provisional pending the author's human review. |
| Quality, latency/cost and failure report in README | [Main report](../README.md), [case-level failure analysis](real-docs-v3.md), per-class metrics in saved reports | Automatic alignment/span matching is conservative, not a semantic oracle. Subscription USD is unknown. |
| Eval-driven iteration | [Protocol](../results/real-docs-v3/protocol.json), [dev candidate rationale](../results/real-docs-v3/candidate-rationale.json), [experiment log](experiments.md) | One dev candidate and one test pass; no stability or causal latency claim. |
| Reproducible public repository | Locked dependencies, offline data rebuild, no-key baseline, saved-output rescoring and [CI](../.github/workflows/ci.yml) | New model inference requires an existing login or local HTTP configuration. |

The three assessment dimensions are addressed concretely: evaluation rigor through
source provenance, separated families, explicit reference repairs and counted
failures; hill climbing through recorded dev observations and one bounded candidate;
engineering quality through typed boundaries, deterministic quote checks and
repeatable offline verification. These are inspectable artifacts, not a promise
that the reviewer will award a particular score.

Human author review has **not** been completed or impersonated. The
[gold workbook](../data/real-docs-v3/gold-review.md) is the remaining author task.
The old 40-case corpus and its scores remain an appendix. The original
`challenge-v1` test is still unused. AI assistance is disclosed openly; being able
to explain the code and these evaluation limitations remains essential.
