# Development process and delivery decisions

The project proceeds from a source-grounding contract to a small service, measured
baselines, targeted changes and retained acceptance evidence. The aim is to make
each design decision inspectable alongside the observation that motivated it.
The [requirements map](assignment-coverage.md) connects the delivery to the brief;
the [experiment log](experiments.md) retains the detailed measurements.

## 1 Analyze the goal and define success

The supplied passages are the evidence boundary. A statement can be true in the
world and still be unsupported here. An answer can contain several independently
testable facts, and a quote can be real while failing to justify a judgment.
These distinctions make an API smoke test insufficient as a quality measure.

Before implementation, the [initial design commit](https://github.com/zxingchen77/citation-grounding-verifier/commit/25e9b3c)
recorded the typed contract, exact quote checks, error boundaries, 40-case plan,
development/test split and measurement criteria. Success was defined on three
levels: valid service responses, complete claim-and-evidence verification, and
reproducible comparisons including failures and resource use.

## 2 Design the architecture around those risks

The initial architecture separated HTTP handling, verifier strategies, model
access and evaluation. This lets the same request contract and scoring rules
apply to both a heuristic and model-based methods. The compact evidence-ID path
was selected later from experiments; it was not assumed to be the winner at the
start. The [architecture diagram and module map](design.md#service-flow-and-responsibilities)
show the current implementation.

Two responsibilities stay separate. The model extracts claims and judges their
relationship to evidence. Code enforces types, citation presence, index bounds,
exact source text, time limits and bounded repair. Evidence IDs reduce quote
transcription errors by having code copy the selected source segments. They do
not prove semantic entailment, which must still be evaluated.

The task provides its source passages, so it did not require a retrieval system,
database or agent orchestration. A replaceable provider interface supports an
OpenAI-compatible HTTP API and the existing local Codex login used in the real
experiments. The latter avoids introducing new credentials or a purchased service.

## 3 Implement the contract and establish baselines

The [first implementation](https://github.com/zxingchen77/citation-grounding-verifier/commit/1ebe23a)
added the typed service, deterministic and minimal-model paths, an experimental
staged path and bounded provider handling. The
[dataset and scorer commit](https://github.com/zxingchen77/citation-grounding-verifier/commit/5e124f2)
then made the comparisons executable on 40 labeled examples, with 24 development
and 16 test cases separated by family.

The non-LLM method establishes what sentence splitting and lexical overlap can
achieve. The minimal single-call model is the quality reference for deciding
whether additional machinery earns its cost. The evaluator counts missing
claims, duplicate claims, wrong labels and insufficient evidence, instead of
scoring only the labels of the easiest matched claims.

## 4 Use observed failures to choose changes

| Observation | Decision and implementation | Evidence and interpretation |
| --- | --- | --- |
| Lexical similarity misses scope and multi-passage premises | Keep the heuristic as a control; compare semantic LLM judgments under the same scoring contract | [Original development comparison](../results/dev-v3/reviewed-report.md). Literal quotes alone are not enough. |
| Some development references merge two facts or confuse an upper bound with an exact setting | Correct the development references/wording, retain prior versions, and rerun when inputs change | [Reference history](../data/README.md) and [experiment log](experiments.md). These score changes are not model improvements. |
| Two-stage extraction and verification doubles model calls without demonstrated compensating benefit | Select one-call evidence-ID verification for the optimized method; retain the staged alternative | [Candidate comparison](../results/dev-candidates-v1/README.md). Fewer output tokens did not establish lower total cost. |
| The original held-out set exposes a non-exclusive-port annotation ambiguity | Keep the frozen score and disclose the failure instead of changing its label to raise F1 | [Held-out results](../results/heldout-v1/reviewed-report.md) and [failure analysis](../README.md#dataset-scoring-and-interpretation). Minimal scores higher in this run. |
| Short original cases reach a score ceiling, while fixed execution order limits latency comparisons | Author the separate challenge cases and predeclare balanced paired runs | [Challenge data](../data/challenge-v1/README.md) and [experiment schedule](../results/challenge-dev-v1/manifest.json). More difficult data and balanced order precede the new run. |
| The challenge run produces 29 timeouts in 48 model calls | Retain the failures, use bounded availability probes, and later add streaming progress traces | [Challenge experiment](experiments.md#2026-11-02--challenge-stage-1-balanced-dev-runs-and-availability-failure). Availability diagnostics are separate from quality comparisons; the old timeout cause remains unresolved. |
| A claim's own citations omit identity, antecedents or applicable prerequisites | Add `optimized-v2` instructions for a complete per-claim justification and preserve modifiers with their asserted event | [Fixed-protocol v1/v2 dev comparison](prompt-ablation-v2.md). Same Sol model, same 12 cases, one balanced round; automatic F1 0.812 / 0.960 and reviewed F1 0.832 / 1.000. |

For example, the old Kestrel administrative-port judgment cites the port rule but
does not cite the passage identifying the relay as Kestrel. A correct verdict
with this incomplete evidence still loses credit. V2 includes the identity
premise in each dependent claim's citations. It fixes eight such judgments across
six dev scenarios and removes one extra lateness assertion. The
[saved predictions](../results/prompt-ablation-v2/comparison/predictions.jsonl)
and [review decisions](../results/prompt-ablation-v2/comparison/reviews.json)
make that change inspectable.

The latest experiment changes only the prompt between the two methods; the
model, data, source-segmentation rules, schemas and scorer are shared. Its gain
does not come from dropping failed requests or editing gold labels. V2 uses more
input and output tokens, and its paired latency interval includes no difference.
It is selected as an opt-in dev candidate, not a proven production improvement.

## 5 Validate implementation and qualify the results

Validation has distinct roles. Contract/provider tests cover deterministic
invariants and error behavior. Actual localhost requests exercise the service
with real model calls. Dataset and saved-output checks establish what was
evaluated. The original comparison froze its selected implementation before
running the 16-case test; the latest v2 experiment uses development data only.

The [acceptance record](acceptance.md) separates the original clean-checkout and
eight-probe model acceptance, the v2 preflight, and the current 74-test suite
with the compact-v1 SQLite WAL HTTP check. [CI](../.github/workflows/ci.yml) installs
locked dependencies and runs lint, formatting, tests and a deterministic benchmark. CI does not make paid
model calls or certify semantic accuracy.

For v2, all 24 comparison requests completed with no repairs. Data/source hashes,
schedule positions, literal quotes and the correct-claim counts (automatic
41 / 48; reviewed 42 / 50) were
[checked against the retained artifacts](../results/prompt-ablation-v2/verification.json).
Reference and output review are author self-review (AI-assisted), not independent
human annotation.

## 6 Deliver a reproducible repository

The original service, three-method evaluation and held-out report were delivered
in [the original results commit](https://github.com/zxingchen77/citation-grounding-verifier/commit/e04959a).
The later [v2 implementation](https://github.com/zxingchen77/citation-grounding-verifier/commit/5850663)
and [its experiment packet](https://github.com/zxingchen77/citation-grounding-verifier/commit/6497601)
extend that delivery without replacing historical outputs. README commands,
dependency locks, dataset versions, manifests, raw predictions and explicit
reviews let a reader run the service or recompute the reported results.

The final system remains compact-v1 (default `optimized`), with
[`results/heldout-v1`](../results/heldout-v1/) as its evaluation record.
`optimized-v2` remains a dev ablation; it has not been evaluated on held-out data.

The remaining validation scope is specific: the new candidate has no fresh
three-method or challenge held-out result, the extra 12 test cases remain unused,
and the direct external HTTP provider has not been accepted against a live model.
The latest small synthetic dev result does not establish unseen accuracy. These
are recorded boundaries of the submission, not completed experiments.
