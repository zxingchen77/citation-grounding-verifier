# Experiment log

**Final system: compact-v1 (default `optimized`), evaluated in
[`results/heldout-v1`](../results/heldout-v1/).** `optimized-v2` is a development
ablation and has not been evaluated on held-out data. The challenge test split
remains unused; it will only be run following a separate user decision.

Entries retain decisions at the time of each run, including superseded candidate
choices. All reviews are **author self-review (AI-assisted)**; independent human
adjudication is not claimed. Automatic and reviewed scores appear together.
For the sequence across these experiments, use the
[requirements map](assignment-coverage.md) and [development process](development-process.md).

## 2026-11-02 — Initial design

**Question:** How do we distinguish a working API from a trustworthy verifier?

**Decision:** Enforce output invariants in code and evaluate claim coverage,
judgments, and evidence separately. Freeze a development/test split before tuning.

**Evidence:** The assignment requires exact quote validation and three comparable
approaches. Its examples also require splitting multiple facts from one sentence.

**Next:** Build the HTTP contract and deterministic baseline; author the labeled
dataset; collect the first real model baseline before selecting optimizations.

No quality, latency or dollar-cost result has been measured at this point.

## 2026-11-02 — Contract checks and deterministic development baseline

**Implementation:** A typed HTTP endpoint, exact quote validation, a punctuation/
lexical baseline, single-call LLM verifier, and a staged candidate. The staged
candidate is a hypothesis, not a demonstrated improvement: source-blind extraction
may preserve answer meaning; fixed claim indices may prevent dropped judgments;
bounded repairs may recover mechanically invalid outputs.

**Offline validation:** 23 tests passed. These test invariants, error boundaries,
scorer behavior and dataset integrity, not real LLM quality.

**Measured baseline:** On 24 development cases / 42 claims, deterministic
end-to-end F1 is provisionally 0.738 (31 correct, 11 false positives, 11 false
negatives). All 30 emitted quotes are literal source substrings. Multi-passage
evidence is incomplete, and scope/action changes sometimes pass the lexical check.
Five evidence-review flags still require explicit resolution.

**Decision:** Keep this baseline. Its real quotes and high coverage demonstrate why
those properties alone are insufficient. Run the minimal LLM before deciding
whether the staged candidate is worth its additional calls.

**Runtime:** The machine's shell initially selected Python 3.9 despite an installed
Python 3.12. Recreated the isolated environment with the explicit 3.12 interpreter;
dependency versions are locked. The existing signed-in Codex CLI can produce
schema-constrained JSON, so a local adapter was added without exporting credentials.
A real one-case smoke test returned the correct contradiction. This smoke test is
not included in benchmark scores. CLI startup and framework tokens will remain in
latency/usage measurements; subscription usage does not imply zero monetary cost.

## 2026-11-02 — Minimal model and reference correction

**Observation:** The real minimal model run completed all 24 development requests
with no provider/validation errors. It emitted 44 claims against the initial 42
references. Inspection showed that both Birch queue answers asserted two distinct
behaviors in a contrast: rejecting new jobs and not deleting existing jobs. The
reference had incorrectly merged those behaviors.

**Correction:** Split those development references into atomic claims. Keep every
context and answer unchanged, retain the original dataset and scores, and rescore
both baselines against the revised 44-claim development set. A regression check
also verifies that held-out cases and labels are unchanged. Review decisions are
author self-review (AI-assisted), not independent human review.

**Measured:** Initial automatic F1 on v1 references was 0.977 for minimal and
0.738 for deterministic. After the reference correction and review on v2, F1 is
1.000 and 0.721 respectively; these are different reference sets, not a
same-label automatic-versus-review improvement. Reviewed TP/FP/FN are 44/0/0
and 31/11/13. Minimal's median is 11.319 seconds, with 24 model calls,
259,660 input / 2,813 output tokens.
All originally emitted quotes in both runs are literal substrings. The baseline
still fails evidence sufficiency on multi-passage synthesis. Reference correction
is not claimed as a verifier improvement.

**Next hypothesis:** Since minimal quality is already at the measured ceiling,
evaluate resource use while retaining that quality. Compare the existing staged
candidate with a single-call evidence-ID candidate. The latter emits evidence IDs
and lets code copy source substrings, reducing quote generation and preventing
quote transcription errors. Both candidates must earn their place through the
development comparison. The held-out set remains unused for prompt selection.

**Engineering checks:** Preserve unknown token usage as unknown rather than
inventing zero; record the CLI/runtime version in new runs; explicitly reject
overlong baseline claims instead of allowing an unhandled validation exception.
These boundary fixes do not alter the prompts or evaluated example inputs.

## 2026-11-02 — Candidate disagreement exposes bound ambiguity

**Observation:** The staged candidate interprets "at most 3" as entailing "at most
4". The compact candidate also does so, and treats an unproven tighter upper bound
as unsupported. These are defensible logical readings. The initial labels instead
treated those statements as exact maximum-configuration values. A prompt should
not be forced to reproduce an unstated annotation convention.

**Decision:** Preserve version 2 and the complete candidate run. Clarify exact
configured limits in the Birch, Sable and Elm development families (six cases).
Rerun all three required methods on the complete version 3 development split.
Inputs changed, so old predictions cannot merely be rescored. The remaining cases,
including every held-out example, are unchanged. No verifier prompt changes are
made in response to this ambiguity.

**Tradeoff:** The revised benchmark measures unambiguous numeric configuration
errors. It does not resolve real ambiguous language; that remains a documented
limitation and a reason to use independent annotation on a larger future dataset.
Quality changes caused by this dataset repair are not claimed as model gains.

## 2026-11-02 — Development comparison and selection

All three required methods were rerun on dataset v3, using the same model,
backend, timeouts, concurrency 1 and one pass. The prompts are unchanged from
`compact-v1` / `minimal-v1`; neither candidate was adjusted to force the disputed
bound labels. [Saved results](../results/dev-v3/) include all predictions and the
author self-review (AI-assisted) alignment decisions.

The original runs use `gpt-6-astra` through Codex, Python 3.12.2, no response
cache, and 90-second model / 240-second request deadlines. Methods run in fixed
sequential order; provider prefix caching is uncontrolled. Tokens include CLI
and framework overhead. All calls, errors and repairs are counted.

| Method | Reviewed TP / FP / FN | Automatic F1 | Reviewed F1 | Median seconds | Input tokens | Output tokens |
| --- | --- | --- | --- | --- | --- | --- |
| Deterministic | 31 / 11 / 13 | 0.721 | 0.721 | <0.001 | 0 | 0 |
| Minimal | 43 / 0 / 1 | 0.989 | 0.989 | 10.967 | 259,704 | 2,773 |
| Compact | 44 / 0 / 0 | 1.000 | 1.000 | 9.589 | 261,832 | 2,226 |

Automatic and reviewed TP/FP/FN are identical in this run. Cached input totals
are 109,824 for minimal and 91,520 for compact.

All requests succeeded; both model methods used 24 calls with no repairs. All
emitted quotes were literal substrings. Minimal bundled the two Birch contrast
assertions into one item, leaving one required atomic item unmatched. Compact
split both. The original minimal run split both too, so this single-case difference
must not be advertised as a stable quality improvement.

**Selection:** Keep compact evidence-ID selection as the optimized implementation.
It preserves measured quality, has one-call complexity, mechanically prevents
quote transcription errors and generated about 20% fewer output tokens in this
run. Input tokens increased by about 0.8%; total token volume increased slightly.
The measured median was lower, but cache hits, service load and CLI overhead are
uncontrolled. No overall dollar saving or statistically reliable speedup is claimed.

The staged candidate needed 48 calls on the historical development data and
provided no demonstrated benefit justifying its complexity. Its results remain
available. This comparison combines changes in prompt detail and evidence format;
it does not isolate the causal contribution of every component.

**Next:** Run the real HTTP acceptance probes, freeze the chosen prompts and
implementation, then evaluate all three methods on the untouched 16-case test
split. Do not select or tune using the final-test outputs.

## 2026-11-02 — Held-out evaluation and final interpretation

The final run used the unchanged 16-case / 28-claim test split after the selection
commit. All 48 requests across three methods succeeded without repairs. Literal
quote validation passed for all 19 / 24 / 23 emitted citations respectively.

| Method | Reviewed TP / FP / FN | Automatic F1 | Reviewed F1 | Median / P95 seconds | Input tokens | Output tokens |
| --- | --- | --- | --- | --- | --- | --- |
| Deterministic | 21 / 7 / 7 | 0.750 | 0.750 | <0.001 / <0.001 | 0 | 0 |
| Minimal | 28 / 0 / 0 | 1.000 | 1.000 | 10.183 / 14.679 | 173,157 | 1,831 |
| Compact | 27 / 1 / 1 | 0.964 | 0.964 | 8.765 / 11.442 | 174,573 | 1,460 |

Automatic and reviewed TP/FP/FN are identical. P95 uses nearest rank and equals
the maximum for 16 requests. Cached input totals are 92,928 / 58,240 for minimal /
compact; subscription dollar cost is unknown. The heuristic wrongly supports
3 of 16 non-supported gold claims; neither model emits a false-supported label.

| Category | Cases / gold claims | Deterministic F1 (auto / reviewed) | Minimal F1 (auto / reviewed) | Compact F1 (auto / reviewed) |
| --- | --- | --- | --- | --- |
| Supported | 4 / 8 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| Distortion | 4 / 8 | 0.625 / 0.625 | 1.000 / 1.000 | 0.875 / 0.875 |
| Extrinsic | 4 / 8 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| Multi-passage | 4 / 4 | 0.000 / 0.000 | 1.000 / 1.000 | 1.000 / 1.000 |

**Failure:** Compact labels the changed Quartz port UNSUPPORTED, while the frozen
reference expects CONTRADICTED. Its reasoning points out that stating one listening
port does not explicitly exclude another. The dataset assumes a single configured
port. This assumption is not fully specified in the source, so independent
annotation adjudication is warranted. Keep the original score and label; no test
outputs are used for another prompt change or to select a new winning version.

**Interpretation:** The minimal model has the highest frozen-reference score.
Compact produces 20.3% fewer output tokens, has slightly higher total token volume,
and shows a lower observed median in this one sequential run. These observations
do not prove a stable speedup, dollar saving or quality gain. The test exposes why
the development-set ceiling was insufficient evidence of general reliability.

**Next experiment, not performed:** Independently adjudicate source exclusivity
and bound semantics, then author fresh scenarios that separate exact configured
values, non-exclusive facts and pure logical bounds. Repeat both model methods
with predeclared run counts and alternating order. If the compact tradeoff does
not survive that validation, prefer the minimal method. No additional inference
is claimed for this proposed work.

**Delivery:** Preserve all results and reviews, publish the actual scores and
limitations, and verify the submitted source/data hashes match the frozen run.

## 2026-11-02 — Challenge stage 1, balanced dev runs and availability failure

**Question:** Does the evidence-ID method retain quality on mixed-label,
condition-sensitive, multi-premise examples under balanced repeated execution?

**Implementation:** Added 24 new scenario families (12 dev / 12 test), 103 atomic
claims, annotation rationales and explicit semantics. All answers mix three
labels. The runner now records a reproducible balanced schedule, each case/round
pair, per-round metrics and paired family-bootstrap uncertainty. Default fixed
ordering and historical score reproduction remain available. HTTP transport and
bounded-repair tests were expanded; trace usage now includes cache counts and
validation failures. Both verifier prompt strings are unchanged.

**Reference/scorer review:** Author self-review (AI-assisted) before inference
identified missing premises and segmentation bias. The first union-coverage
implementation incorrectly normalized character boundaries before locating
quotes. The reviewer supplied the IDs 1; 2 versus IDs 12 counterexample. The dev
run finished unchanged, then the scorer was corrected to raw source positions.
Original reports are retained; that fix changes no observed initial-reference
scores. A separately versioned reference audit adds Beacon/Osprey entity links
and an HX-2 evidence alternative; all inputs, verdicts and test records stay
unchanged. Its score changes are not credited as model improvement.

**Measured:** The two balanced model rounds and one deterministic round completed
all 60 scheduled requests, but 29/48 model calls timed out at 90 seconds.

| Method | Round 0 F1 (auto / reviewed) | Round 1 F1 (auto / reviewed) | Pooled F1 (auto / reviewed) | Failed requests |
| --- | --- | --- | --- | --- |
| Deterministic | 0.289 / 0.289 | — | 0.289 / 0.289 | 0 / 12 |
| Minimal | 0.486 / 0.486 | 0.387 / 0.355 | 0.439 / 0.424 | 16 / 24 |
| Optimized | 0.364 / 0.394 | 0.557 / 0.608 | 0.469 / 0.510 | 13 / 24 |

The automatic column preserves scoring against the initial references; the
reviewed column also includes the disclosed reference-only evidence correction.
The model ranking reverses across rounds. Optimized minus minimal has automatic
F1 difference +0.030, interval [-0.182, +0.264], and reviewed difference +0.086,
interval [-0.110, +0.305]. Repetitions remain within 12 family clusters, not new
independent cases. [Automatic reports](../results/challenge-dev-v1/report.md),
[reviewed reports](../results/challenge-dev-v1/reviewed-report.md),
[rounds](../results/challenge-dev-v1/reviewed-rounds-report.md) and
[reference/scorer audit](../results/challenge-dev-v1/scoring-audit.json) are retained.
Both pooled medians are about 90 seconds; failed-call usage is unknown. The run
cannot establish reliable quality ranking, speedup or dollar savings.

**Service evidence:** Actual localhost HTTP acceptance on the minimal Codex
backend passed 7/8 checks; the plain numeric contradiction returned 504 after an
upstream timeout. All six model calls are retained, including the failed call.
No direct external HTTP model credentials were present, so that provider has
controlled transport tests but no real external model acceptance.

**Bounded diagnostic:** For a predeclared availability check, the
protocol fixed maple-cache-supported and archive-release in advance, one minimal
call each, with 180-second model / 360-second request deadlines. Both timed out.
There were exactly two calls and no repeated attempts to obtain success. These
outputs are availability evidence only and do not replace the development run.

**Alternative-model diagnostic:** The same two probes were then predeclared for
one call each on `gpt-6.1-sol`, confirmed in the existing login's model inventory,
with 90/240-second deadlines. Both completed in 9.794 and 14.134 seconds. The
protocol and outputs are retained in `results/availability-alternative-v1/`.
Two successful probes do not establish stable reliability or comparative quality.
The original failures remain part of their runs; no full alternative-model
development comparison or challenge test inference has been performed.

**Decision at this checkpoint:** Keep minimal as a conservative development
candidate for simplicity, without claiming a quality win. This did not replace
the final compact-v1 system or its original held-out evaluation. The run settings,
schedule, hashes and failures remain in the
[saved manifest](../results/challenge-dev-v1/manifest.json) and
[raw predictions](../results/challenge-dev-v1/predictions.jsonl).

**Boundary:** No challenge test inference was performed. The proposed additional
three-round test remains unperformed and is not an active plan. A future
challenge test run requires a separate user decision.

## 2026-11-03 — One bounded self-contained evidence prompt ablation

**Question:** Can explicit per-claim identity, coreference and rule-premise
instructions fix incomplete citations without adding a model call?

**Change:** Added opt-in `optimized-v2`, retaining the original `optimized`
prompt. The candidate asks for a complete justification independently for each
claim, includes the necessary antecedents and prerequisites, and keeps an event
modifier with the event. The adapter now records streaming CLI event timings and
sanitized error codes even when interrupted. Subprocess tests cover cancellation,
partial progress, tool rejection, malformed output and pipe draining.

**Protocol:** After one successful real HTTP preflight, compare both prompts
once on all 12 unchanged challenge dev cases using `gpt-6.1-sol`, concurrency
one, balanced order/seed 1729 and 90/240-second deadlines. Stop on two consecutive
failed requests or 20 minutes. Freeze data, source and prompt hashes first. Do
not edit the candidate after seeing outputs, retry provider errors, or run test.

**Result:** All 24 requests succeeded in 296 seconds with no repairs.

| Metric | Compact-v1 (`optimized`) | `optimized-v2` |
| --- | --- | --- |
| Automatic / reviewed F1 | 0.812 / 0.832 | 0.960 / 1.000 |
| Automatic TP / FP / FN | 41 / 10 / 9 | 48 / 2 / 2 |
| Reviewed TP / FP / FN | 42 / 9 / 8 | 50 / 0 / 0 |
| Median / P95 seconds | 12.258 / 15.014 | 11.365 / 17.934 |
| Input / output tokens | 134,761 / 2,519 | 137,347 / 2,742 |
| Failed requests / repairs | 0 / 0 | 0 / 0 |

V2 fixes eight missing-premise judgments and one extra lateness claim. Both
methods get all 50 aligned verdicts right. Retained reviews accept three
sufficient evidence alternatives under previously used criteria. Review is
author self-review (AI-assisted), not independent human adjudication. No reference
or scorer changes are credited as improvement.

**Tradeoff:** V2 uses 1.9% more input and 8.9% more output tokens. Paired mean
latency changes by +0.151 seconds, with its bootstrap interval spanning zero.
No speed or cost advantage is established. The automatic dev F1 difference is
+0.148, family-bootstrap interval [0.040, 0.254]; the reviewed difference is
+0.168, interval [0.083, 0.260]. Neither is an unseen-accuracy guarantee.

**Decision:** Retain `optimized-v2` as an opt-in dev ablation. Compact-v1 remains
the final system; challenge test stays unused. Preserve the older failures; successful Sol calls do not
explain the Astra timeout cause. All 68 tests, lint, format, real localhost
checks and frozen source/data hash verification pass. See the
[full experiment and artifacts](prompt-ablation-v2.md). No scheduled follow-up
or additional inference is running.
