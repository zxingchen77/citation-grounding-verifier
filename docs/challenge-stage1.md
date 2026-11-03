# Challenge revision — stage 1 review packet

This is the historical stage 1 checkpoint. The later
[v2 development comparison](prompt-ablation-v2.md) and current
[requirement coverage](assignment-coverage.md) describe subsequent progress.
The proposed challenge held-out evaluation below has not been performed.

Status: **development checkpoint; final runtime selection and held-out evaluation pending**.
The original data and historical predictions are unchanged. This packet covers
implementation, reference construction, development evidence and a proposed
freeze. It is not a completed held-out evaluation.

## Changes and verification

- Added [challenge-v1](../data/challenge-v1/README.md): 24 disjoint scenario
  families, 12 dev / 12 test, 103 claims, 4–6 claims per answer, 624–832 context
  characters. All answers contain all three labels. Every claim has a rationale
  and sufficient evidence references; logical semantics and overlapping
  capability tags are explicit. Independent human annotation is not claimed.
- Added reproducible balanced method permutations, actual execution indices,
  case/round pair IDs, per-round reports and paired family bootstrap intervals.
  Old fixed-order commands remain supported. Repeats do not inflate the number
  of independent cases. Duplicate/incomplete saved schedules are rejected.
- Added strict joint quote coverage at original source-character positions.
  Separate literal citations can jointly cover a reference across sentence or
  semicolon boundaries, but omitted words, conditions, negation and cross-passage
  substitution do not get credit.
- HTTP provider traces retain cache tokens, response model IDs, partial outputs
  on refusal/truncation, and sanitized error codes. Mechanically invalid results
  that trigger repair are marked failed even when their JSON parsed successfully.
  Repairs and failed calls remain in usage/call totals.
- Added real-server acceptance tracing and receipts that retain failed checks.
  Direct HTTP transport tests cover strict schema requests, successful responses,
  malformed envelopes/output, refusal, truncation, provider errors, timeouts,
  cancellation and bounded repair. These tests use controlled transports and are
  not represented as real external HTTP model acceptance.

Local verification: **59 tests passed**, lint and format checks passed. The
existing Starlette TestClient deprecation warning remains. The original 40-case
deterministic command completed, and saved historical summary metrics were
recomputed without differences. The actual localhost deterministic service passed
all three checks. These are local checks; no new remote CI run or push is claimed.

## Development protocol and results

Inference ran from commit `7dc81d4`, with a clean source tree, using `gpt-6-astra`
through Codex CLI `0.166.0-alpha.5.1`, Python 3.12.2, concurrency 1, no response
cache, a 90-second model deadline and 240-second request deadline. The seed was
1729. Both LLM methods ran twice on the same 12 dev cases; deterministic ran once.
Each round balanced pairwise method precedence. The model received only passages
and the answer. No prompt was changed before or after these runs.

All **60 scheduled requests** are retained. Of **48 model calls, 29 timed out**;
their token usage is unknown. The failures are included as false negatives and in
latency, error and call totals. No failed request was retried to obtain a better
benchmark score. Model-call counts describe adapter invocations; any internal CLI
network behavior is outside this measurement.

Reviewed results, with explicit AI-assisted alignment/evidence decisions:

| Method | Round 0 TP / FP / FN | Round 0 F1 | Round 1 TP / FP / FN | Round 1 F1 | Pooled F1 | Failed requests |
| --- | --- | --- | --- | --- | --- | --- |
| Deterministic | 13 / 27 / 37 | 0.289 | — | — | 0.289 | 0 / 12 |
| Minimal | 17 / 3 / 33 | 0.486 | 11 / 1 / 39 | 0.355 | 0.424 | 16 / 24 |
| Optimized | 13 / 3 / 37 | 0.394 | 24 / 5 / 26 | 0.608 | 0.510 | 13 / 24 |

There are **12 unique cases / families per method**, not 24 independent cases for
each LLM. The two model methods each have 100 gold-claim opportunities, reflecting
two observations of the same 50 claims. Deterministic has 50.

The optimized-minus-minimal pooled F1 difference is **+0.086**, with a paired
family-bootstrap 95% percentile interval of **[-0.110, +0.305]** (2,000 draws,
seed 1729). Round rankings reverse. This small, failure-heavy run does not
establish a stable quality gain or a reliable performance ranking.

| Method | Claim coverage | Valid literal quotes | Evidence sufficiency among aligned evidence-required claims | Median / P95 seconds | Calls / repairs |
| --- | --- | --- | --- | --- | --- |
| Deterministic | 0.800 | 22 / 22 | 7 / 29 | <0.002 / <0.002 | 0 / 0 |
| Minimal | 0.320 | 37 / 37 | 20 / 24 | 90.016 / 90.026 | 24 / 0 |
| Optimized | 0.440 | 54 / 54 | 26 / 33 | 90.014 / 90.022 | 24 / 0 |

Evidence sufficiency is a diagnostic; verdict correctness and literal validation
remain separate requirements. Complete metrics and pair-level counts are in the
[reviewed summary](../results/challenge-dev-v1/reviewed-summary.json),
[per-round report](../results/challenge-dev-v1/reviewed-rounds-report.md) and
[paired analysis](../results/challenge-dev-v1/reviewed-paired.json).

| Method | Known input tokens | Known output tokens | Known cached input tokens | Calls with unknown usage |
| --- | --- | --- | --- | --- |
| Minimal | 87,538 | 2,570 | 42,240 | 16 |
| Optimized | 122,802 | 2,261 | 74,880 | 13 |

These token sums are **lower bounds**, not complete totals. The methods completed
different numbers of requests. Neither the known token sums nor the
timeout-dominated medians establish cost savings or a speedup. Subscription dollar
cost remains unknown; provider prefix caching is uncontrolled.

## Failures, reference corrections and candidate decision

The lexical baseline still confuses written number changes, scope, related
entities and multi-premise evidence. Both model methods can choose a correct
verdict but omit the source identifying a rule's entity. For example, Kestrel's
administrative claims cite the relay rule without citing the sentence that
identifies that relay as Kestrel. Quotes from a different output claim are not
silently borrowed. The optimized archive judgment similarly omits R17's identity
and hold relation. These remain scored errors.

Optimized round 1 also emits an additional lateness item for J8. The retained
reference treats "late" as a qualifier of the recorded request; the additional
record counts as an FP under that granularity. This judgment is disclosed for the
review chat to check, rather than changing gold granularity to fit that output.
Its shorter but sufficient J9 evidence and an alternative silver-cohort proof
are explicitly approved in the retained review file.

Before inference, a separate AI review chat identified missing reference premises
and segmentation bias. The first joint-coverage implementation then exposed a
bug: removing separators before matching could relocate `IDs 12` onto an
unrelated `IDs 1; 2` span. The dev run was allowed to finish on its original
implementation. Original predictions/reports remain unchanged. The corrected
scorer locates raw substrings first and passes the reviewer-provided regression.
It leaves the observed initial-reference dev scores unchanged.

Reference revision 2 subsequently adds Beacon/Osprey entity antecedents and a
self-contained HX-2 evidence alternative. Only three development reference
records changed; all inputs, claim texts, verdicts and complete test records are
unchanged. The initial data is retained in `data/challenge-v1/revisions/`.
Automatic TP counts move from **13 / 29 / 34** to **12 / 28 / 35** due to that
reference audit. Explicit semantic reviews then yield **13 / 28 / 37**. These
differences are scoring/reference corrections, **not model improvements**. See
[scoring audit](../results/challenge-dev-v1/scoring-audit.json) and
[review provenance](../results/challenge-dev-v1/review-provenance.json).

**Candidate recommendation:** retain the unchanged `minimal-v1` and `compact-v1`
prompts for the frozen comparison, with `minimal` as the conservative serving
recommendation. This is a simplicity choice under inconclusive evidence, not a
claim that minimal won this pooled dev score. No new prompt variant is promoted;
backend failures dominate these small rounds and optimized has no established
stable gain. The existing optimized method remains selectable.

## Availability and HTTP acceptance

The existing ChatGPT/Codex sign-in was available; no credentials were read from
files or exported. The shell had no existing HTTP API key/model configuration.
**Direct external HTTP model acceptance remains unverified**. The
[availability receipt](../results/acceptance/challenge-provider-availability.json)
records only configuration presence and nonsecret runtime metadata.

The real minimal service at localhost completed all eight acceptance probes:
**7 passed; the plain numeric-contradiction probe failed with HTTP 504 after its
90-second model deadline**. Non-factual text, empty context, instruction-like
context, mixed claims, multiple premises, empty answers and invalid-input rejection
passed. The [receipt](../results/acceptance/challenge-minimal-http/checks.json),
[service configuration](../results/acceptance/challenge-minimal-http/service.json)
and [actual calls](../results/acceptance/challenge-minimal-http/calls.jsonl) retain
successes, the failure, raw outputs and known usage. This is not an all-pass receipt.

A bounded availability diagnostic was declared separately: one existing dev case
(`maple-cache-supported`) and one challenge dev case (`archive-release`), one
minimal call each, with 180-second model and 360-second request deadlines. No
retries or test cases are allowed. Its [protocol](../results/availability-diagnostic-v1/protocol.json)
was saved before execution. The outcome is reported in the freeze candidate;
it cannot replace or beautify the complete dev comparison.

**Diagnostic outcome:** both requests timed out, at 180.024 and 180.030 seconds,
with unknown token usage. Exactly two calls were made and no further retry was
performed. Increasing the deadline did not validate a usable runtime. The cause
of the intermittent failures is undetermined; the local process check showed no
orphaned subprocesses belonging to this run. Code and data can be reviewed now,
but **no model runtime/deadline is recommended for final-test approval yet**.
The 90/240-second evaluated configuration remains recorded for reproduction,
not presented as an operationally approved setting.

A final bounded alternative-model diagnostic used `gpt-6.1-sol`, verified in the
existing login's noncredential model inventory. The same two predeclared dev
probes each received one call with 90/240-second deadlines. Both completed:
`maple-cache-supported` in 9.794 seconds and `archive-release` in 14.134 seconds.
The [protocol and raw outputs](../results/availability-alternative-v1/) are retained.
This establishes observed availability on two probes only. It does not establish
stable reliability, a quality gain or a replacement benchmark. The automatic
score has one unresolved evidence-review flag and is not used to rank models.
No further model calls or final-test inference were made before work was paused.

## Reproduce and review

```bash
python -m grounding.dataset data/challenge-v1/cases.jsonl
ruff check .
ruff format --check .
pytest -q

grounding-score --run results/challenge-dev-v1 \
  --dataset data/challenge-v1/cases.jsonl \
  --original-dataset data/challenge-v1/revisions/cases-initial.jsonl \
  --reviews results/challenge-dev-v1/reviews.json
```

The [freeze candidate](challenge-freeze-candidate.json) pins the implementation,
data, prompt hashes, proposed model settings and final schedule. The original dev
command is preserved in its manifest: balanced seed 1729, two model rounds, one
deterministic round, 90/240-second deadlines. A new directory is required for
any fresh inference.

Remaining work: review all labels/evidence and the scorer, resolve the model
availability/deadline decision, approve the freeze, then run the predeclared
three-round challenge test comparison. The test outputs must not be used to tune
prompts or relabel this evaluation. This publication preserves a development
checkpoint, not a completed final evaluation.
