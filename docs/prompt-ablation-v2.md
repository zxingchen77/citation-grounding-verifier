# Self-contained evidence: development ablation, 2026-11-03

**Dev result (v1 / v2): automatic F1 0.812 / 0.960; reviewed F1 0.832 / 1.000.**
All 12 cases completed for each method, with zero failed requests. V2 meets the
predeclared dev selection rule and is available as `VERIFIER_METHOD=optimized-v2`.
The final system remains compact-v1 (default `optimized`), evaluated in
[`results/heldout-v1`](../results/heldout-v1/). V2 is a dev ablation and has not
been evaluated on held-out data.

This iteration tests whether a small prompt change fixes missing citation
premises. It also records enough Codex CLI progress to distinguish a silent
startup from a turn that started but did not finish. It does not diagnose the
cause of the previous `gpt-6-astra` timeouts retroactively.

## Change and fixed comparison

`optimized-v2` extends the existing evidence-ID prompt. Each claim must cite a
complete justification of its own: entity/alias identity, pronoun antecedents,
group membership, applicable rules, conditions and exceptions. Citations on a
different claim cannot supply a missing premise. A modifier stays with its
asserted event instead of becoming a duplicate inferred assertion. The JSON
schema, segmenter, literal quote resolution and one structural repair remain the
same as `optimized` (compact-v1). There are no added model calls for semantic
repair and no use of gold labels in the inference payload.

The [predeclared protocol](../results/prompt-ablation-v2/protocol.json) fixes
`gpt-6.1-sol`, the existing Codex login, 90-second call and 240-second request
deadlines, concurrency one, one round of both methods and a balanced order with
seed 1729. The 12 challenge development cases contain 50 gold claims. Data,
references and scorer are unchanged. Challenge test cases are excluded. There
is one candidate prompt and no follow-up quality run in this iteration.

The protocol selects v2 as an opt-in candidate only if reviewed end-to-end F1
improves, evidence omissions fall, and failed requests and false-supported
claims do not increase. Both methods use the same model and adapter; scores
from the older Astra run are not used as this comparison's control.

## Runtime and HTTP check

The adapter drains stdout and stderr while the process runs. Traces retain
allowlisted event names/counts, first-event and turn timestamps, process exit,
error code, usage when reported and stderr byte count. They do not retain stderr
text or CLI event bodies. A timeout/cancellation preserves observed progress and
kills and reaps the child process. These are CLI event boundaries, not internal
model/network timings or a claimed root-cause diagnosis.

The real localhost `optimized-v2` check completed in 10.342 seconds with two
correct supported claims and verbatim citations. Health, empty-answer and
malformed-input checks also passed. The saved
[HTTP response and check correction](../results/prompt-ablation-v2/preflight/reviewed-checks.json)
and [model trace](../results/prompt-ablation-v2/preflight/calls.jsonl) are retained.
The first ad-hoc assertion incorrectly expected one claim in this two-claim
original dev case; it was corrected against the saved response without a second
model call. The original failed assertion is also retained. Initial health
requests inherited a local proxy and returned an empty 502 before inference;
direct loopback requests use `trust_env=False`. Provider settings were unchanged.

## Results and review

| Metric | Compact-v1 (`optimized`) | Compact-v2 (`optimized-v2`) |
| --- | --- | --- |
| Original automatic TP / FP / FN | 41 / 10 / 9 | 48 / 2 / 2 |
| Original automatic F1 | 0.812 | 0.960 |
| Reviewed TP / FP / FN | 42 / 9 / 8 | 50 / 0 / 0 |
| Reviewed end-to-end F1 | 0.832 | 1.000 |
| Aligned claims / gold | 50 / 50 | 50 / 50 |
| Correct aligned verdicts | 50 / 50 | 50 / 50 |
| Sufficient evidence-required judgments (automatic) | 29 / 38 | 36 / 38 |
| Sufficient evidence-required judgments (reviewed) | 30 / 38 | 38 / 38 |
| Extra predictions | 1 | 0 |
| Requests / failures / repairs | 12 / 0 / 0 | 12 / 0 / 0 |
| Median / P95 seconds | 12.258 / 15.014 | 11.365 / 17.934 |
| Input / output tokens | 134,761 / 2,519 | 137,347 / 2,742 |
| Cached input tokens | 8,448 | 16,896 |

All 24 scheduled requests completed in 296 seconds. Both methods have literal
citations throughout and no false-supported verdicts. V1 emits 51 claims; V2
emits 50. Missing premises occur in listener-inventory (2), batch-bound (1),
latency-population (1), delegation-permissions (1), archive-release (1) and
receipt-semantics (2). V2 fixes all eight and removes the extra lateness claim
in lease-race. The gain is evidence completeness and output granularity, not a
change in verdict accuracy among aligned claims.

All outputs and reasoning underwent author self-review (AI-assisted), not
independent human adjudication. The [review file](../results/prompt-ablation-v2/comparison/reviews.json)
retains every alignment and rationale. Three evidence overrides are applied:
both methods' J9 proof omits a recorded-request caveat that is unnecessary to
that judgment; V2's Nimbus proof uses the cohort policy instead of a specific
node counterexample. These are the same semantic alternatives already accepted
in the prior development review. No dataset or scoring-code edits were made.
The automatic scores remain alongside the reviewed scores.

The paired 12-family bootstrap gives an automatic V2-minus-V1 F1 difference of
+0.148, 95% percentile interval [0.040, 0.254]; the reviewed difference is +0.168,
interval [0.083, 0.260]. The paired mean latency difference is
**+0.151 seconds**, interval [-1.470, +1.694]; the lower median is not evidence
of a reliable speedup, and V2 has the higher P95. V2 uses 1.9% more input tokens
and 8.9% more output tokens. Cache usage differs and dollar cost is unknown.
There is no demonstrated cost reduction.

All 100 aligned verdicts, source/data hashes, schedule positions (six first
positions per method), literal citations and the correct-claim counts
(automatic 41 / 48; reviewed 42 / 50) were rechecked. The count verification does
not call the production scoring functions. [Verification and artifact hashes](../results/prompt-ablation-v2/verification.json),
[raw predictions](../results/prompt-ablation-v2/comparison/predictions.jsonl),
[reviewed summary](../results/prompt-ablation-v2/comparison/reviewed-summary.json)
and [paired report](../results/prompt-ablation-v2/comparison/reviewed-paired.json)
are retained. The frozen implementation is commit `5850663`.

The small synthetic dev set informed the prompt change. A single round and its
bootstrap do not establish generalization, stable reliability or perfect
production accuracy. The new challenge test split remains unused. Sol succeeded
on these 24 requests and one preflight; this does not identify or fix the old
Astra timeout cause. No further inference or scheduled task is running.

## Reproduce

Use a fresh output directory; never overwrite the retained run:

```bash
LLM_BACKEND=codex LLM_MODEL=gpt-6.1-sol \
LLM_TIMEOUT_SECONDS=90 VERIFIER_TIMEOUT_SECONDS=240 \
.venv/bin/grounding-eval --dataset data/challenge-v1/cases.jsonl --split dev \
  --methods optimized optimized-v2 --repeats 1 --order balanced --seed 1729 \
  --out results/local/prompt-ablation-v2
```

The recorded run additionally stops after two consecutive failed requests or
20 minutes; it does not retry provider failures. Each method allows at most one
repair of invalid structured output. The adapter uses the CLI's default reasoning
effort; no effort value is explicitly pinned. Provider cache state and service
load are uncontrolled, and subscription dollar cost is unknown.
