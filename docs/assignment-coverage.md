# Assignment requirements and evidence

The core service, dataset, benchmark runner and README deliverables are present.
The original submission includes the required three-method comparison on both
development and held-out data. The later `optimized-v2` candidate has a separate
development comparison; the original held-out scores are not its test scores.

This mapping follows the [original assignment](https://gist.github.com/wsxiaoys/849522ee389e0ce359ef444653084484),
rechecked on 2026-11-03. “Implemented” identifies code and validation evidence,
not a guarantee that every model judgment is correct. For the reasoning behind
the implementation, see the [development process](development-process.md).

## Required deliverables

| Requirement | What is delivered | Evidence and scope |
| --- | --- | --- |
| HTTP endpoint in a permitted language | Python 3.12 / FastAPI `POST /verify` | [Endpoint and HTTP error mapping](../src/grounding/api.py); [request tests](../tests/test_contract.py). Implemented. |
| Passage list and generated answer as input; structured claim report as output | Strict request and response types with claim text, verdict, reasoning and citations | [Typed contract](../src/grounding/models.py). Extra fields and invalid types are rejected. |
| Atomic claims and source-based judgments | Minimal, compact and staged prompts preserve quantities, negation, conditions and scope; all three verdicts are represented | [Verifier strategies](../src/grounding/verifiers.py); [claim alignment and coverage scoring](scoring.md). Implemented and empirically evaluated; semantic errors remain measurable. |
| Brief explanation for each judgment | Each output claim has nonempty reasoning linked to support, contradiction or missing evidence | [Output models](../src/grounding/models.py); [saved real outputs](../results/heldout-v1/predictions.jsonl). |
| Verdict-specific citation presence | Nonempty citations for supported/contradicted claims; none for unsupported claims | `validate_evidence` in [models.py](../src/grounding/models.py); [contract checks](../tests/test_contract.py). Enforced in code. |
| Valid source indices and literal quotes | Strict nonnegative indices, bounds checks and exact substring checks before success | [Evidence validation](../src/grounding/models.py); [invalid-index and Unicode-quote tests](../tests/test_contract.py). Compact methods resolve selected IDs to original text. |
| Graceful edge cases and model failures | Empty answers skip inference; absent context does not become outside-world evidence; invalid output, provider errors and deadlines return explicit errors | [Verifier control flow](../src/grounding/verifiers.py), [HTTP provider tests](../tests/test_http_provider.py), [subprocess tests](../tests/test_codex_provider.py), [HTTP receipts](acceptance.md). Controlled tests and real probes are identified separately. |
| At least 20 labeled JSON or JSONL cases | 40 original cases / 72 claims, split into 24 dev and 16 test cases by scenario family | [Dataset](../data/cases.jsonl), [construction and split](../data/README.md), [integrity tests](../tests/test_evaluation.py). Meets the required count without relying on the extension. |
| Balanced coverage of the four requested scenario types | 10 supported, 10 distortion, 10 extrinsic and 10 multi-passage cases | [Dataset notes](../data/README.md). The separate [24-case challenge extension](../data/challenge-v1/README.md) adds mixed labels and harder semantics. |
| Compare a non-LLM baseline, minimal LLM and optimized LLM | All three run through one evaluator; the original frozen comparison is complete | [Runner](../src/grounding/benchmark.py), [original dev report](../results/dev-v3/reviewed-report.md), [original held-out report](../results/heldout-v1/reviewed-report.md). V2 has a two-prompt dev ablation, not a new full three-method test. |
| README report covering quality, latency/cost and failures | Claim-level end-to-end scores, latency, token/cache usage, errors and concrete failure analysis | [Evaluation report](../README.md#evaluation-report). Subscription dollar cost is unknown; token use is reported without claiming an invoice or a cost saving. |
| Public repository with code, data and runnable instructions | Service, evaluator, dependency lock, datasets, commands and result artifacts | [Repository](https://github.com/zxingchen77/citation-grounding-verifier), [service instructions](../README.md#run-the-service), [benchmark commands](../README.md#dataset-and-scoring), [CI](../.github/workflows/ci.yml). |

Character offsets and reuse of external benchmarks are optional in the brief.
This implementation returns literal quotes without offsets and uses original
synthetic examples. The required submission is a public repository; a hosted
production endpoint is not a stated deliverable.

## How the three evaluation dimensions are demonstrated

| Assignment dimension | Concrete evidence | What the reader should assess |
| --- | --- | --- |
| Evaluation Rigor | [Scoring contract](scoring.md), family-separated data, [frozen original test manifest](../results/heldout-v1/manifest.json), retained predictions/reviews, [paired challenge analysis](../results/prompt-ablation-v2/comparison/reviewed-paired.json) | Missing and duplicate claims affect scores; a literal quote can still be insufficient. Failed calls stay in the denominator. Repeated outputs are grouped by case/family. Annotation and review are AI-assisted, not independent human adjudication. |
| Eval-Driven Hill Climbing | [Experiment log](experiments.md), [candidate comparison](../results/dev-candidates-v1/README.md), [v2 prompt ablation](prompt-ablation-v2.md) | Baseline comparisons expose lexical and semantic failure modes; candidate measurements motivate one-call evidence selection; missing-premise errors motivate per-claim evidence completeness. Reference repairs are separated from model improvements. |
| Engineering Quality | [Architecture](design.md), typed contracts, bounded repair/deadlines, [68-test acceptance record](acceptance.md), locked dependencies and [CI](../.github/workflows/ci.yml) | Deterministic checks reject malformed citations, provider failures stay distinct from unsupported claims, and saved artifacts support recomputation. Real HTTP checks do not stand in for broad model-quality evaluation. |

## Keep the result scopes separate

| Result | Model and data | Supported conclusion |
| --- | --- | --- |
| Original three-method held-out run | `gpt-6-astra`; 16 test cases / 28 claims; deterministic / minimal / compact-v1 | F1 **0.750 / 1.000 / 0.964** under the frozen references. Minimal has the highest score in this run. [Report](../results/heldout-v1/reviewed-report.md). |
| Later paired prompt comparison | `gpt-6.1-sol`; 12 challenge dev cases / 50 claims; compact-v1 / compact-v2 | Reviewed F1 **0.832 / 1.000**; eight evidence omissions and one extra claim removed, with all 24 requests successful. This is one AI-reviewed dev round. [Report](prompt-ablation-v2.md). |

The original required comparison is delivered. The newer candidate has **not**
received a fresh three-method comparison or challenge held-out evaluation. The
12 challenge test cases remain unused. Direct external HTTP-model acceptance is
also unverified: actual model runs used the existing Codex login, while HTTPModel
has controlled transport tests. These boundaries remain visible in the delivery.

Earlier Astra timeouts are retained in [their development run](../results/challenge-dev-v1/).
Successful Sol calls do not identify their cause. Neither the original output-token
reduction nor the newer F1 gain establishes a stable latency or dollar-cost win.
