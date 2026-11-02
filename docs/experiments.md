# Experiment log

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
explicitly AI-assisted, not represented as independent human review.

**Measured:** Minimal: 44 true positives, 0 false positives, 0 false negatives,
F1 1.000, median 11.319 seconds, 24 model calls, 259,660 input / 2,813 output tokens.
Deterministic: 31 true positives, 11 false positives, 13 false negatives, F1 0.721.
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
explicit AI-assisted alignment reviews.

| Method | TP / FP / FN | End-to-end F1 | Median seconds | Input tokens | Output tokens |
| --- | --- | --- | --- | --- | --- |
| Deterministic | 31 / 11 / 13 | 0.721 | <0.001 | 0 | 0 |
| Minimal | 43 / 0 / 1 | 0.989 | 10.967 | 259,704 | 2,773 |
| Compact | 44 / 0 / 0 | 1.000 | 9.589 | 261,832 | 2,226 |

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
