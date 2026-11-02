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
