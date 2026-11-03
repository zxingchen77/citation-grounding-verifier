# Development-only refinement after availability analysis: v4 and v5

This experiment follows the author's request to diagnose non-network failures and
improve the verifier on **dev only**. It is separate from the closed real-docs-v3
experiment. The previous test outputs have already been observed; no new test
inference, test label edits or test rescoring are part of this iteration.
Compact-v1 remains the production default. The new candidate is a prototype in
[`experiments/dev_refinement.py`](../experiments/dev_refinement.py), not an API method.

**Outcome:** neither v4 nor v5 passes the predeclared development selection rule.
V5 fixes specific arithmetic and evidence problems, but aggregate automatic F1
does not improve. Both attempts, including their regressions, are retained. Further
prompt search should first address the dev scorer/reference ambiguities below.

## What is actually failing?

The earlier compact-v1 development run completed all 20 requests. Against the
unchanged 85-claim reference, its automatic E2E F1 is 0.667, with 58 true positives
out of 89 predicted claims. The 27 uncredited reference claims break down as follows:

| Automatic reason for losing credit | Gold claims | Interpretation |
| --- | --- | --- |
| No claim alignment | 14 | Includes numeric formatting, unresolved subjects, paraphrases and different decomposition |
| Aligned verdict agrees, but full gold evidence is not covered | 12 | Mixes missing premises with sufficient alternative or shorter evidence |
| Aligned verdict disagrees | 1 | Source-grounded arithmetic treated as unavailable knowledge |

There are also 18 unaligned predictions; these are not 18 additional distinct
semantic errors. One unmatched pair contributes both a false positive and a false
negative. An aligned label match is not proof that the reference is correct either.
The [27-item audit](../results/dev-refinement-v4/baseline-failure-audit.json) preserves
the automatic categories and explains each discrepancy. It is **author self-review
(AI-assisted)**, not independent human annotation, and supplies no replacement score.

### Actual reasoning and evidence weaknesses

- **Arithmetic versus outside knowledge:** on `sqlite-partialindex`, compact-v1
  marks the equivalence of `b=3+3` and `b=6` UNSUPPORTED. Basic arithmetic is allowed
  by the task's source-only semantics. The fact that a planner does not recognize
  the equivalence does not make the expressions mathematically different.
- **Missing premises:** on `python-asyncio-task`, the claim is about waiting for
  cancelled siblings after a failure. The citations establish waiting and grouped
  raising, but omit the failure-to-cancellation link. Evidence for another claim
  is not automatically evidence for this claim.
- **Unresolved subjects and conditions:** on `python-sqlite3`, “the module” or
  “the connection” remains in extracted claims. A reader can recover the subject
  from the answer, but a standalone claim should name it. In this scorer, the digit
  `3` inside `sqlite3` is also treated as a number, compounding the matching problem.
- **Fragmented context:** for the repeated-name JSON claim, the selected “instead”
  fragment omits the default qualifier. This is distinct from the overly broad
  reference span, which also contains an unrelated customization paragraph.

### Scorer and reference limitations, not established model mistakes

- `32,766` versus `32766`, and number words versus digits, fail the lexical numeric
  guard. A logically equivalent negative paraphrase can fail the qualifier guard.
- On `sqlite-expridx`, an alternative source sentence explicitly covers WHERE and
  ORDER BY, but gold accepts a different sentence. Both can provide evidence.
- On `python-functools`, the direct “cache is threadsafe” statement refutes the
  not-thread-safe claim, while gold additionally demands the coherence explanation.
- On `sqlite-deterministic`, date and version are split into two predictions but
  kept as one event in gold. Conversely, independently checkable assertions can
  be wrongly merged. Granularity needs a consistent annotation policy.
- The dev `sqlite-partialindex` necessity-versus-sufficiency annotation remains
  disputed. A conservative UNSUPPORTED judgment there is not automatically a bug.

These examples explain why 0.667 E2E F1 cannot be read as “33.3% of factual judgments
are wrong.” Nor do they justify asserting near-perfect semantic accuracy: unmatched
claims, imperfect references and this small sample still require human review.

## Candidate and controls

Anchored-v4 uses two model calls instead of compact-v1's one:

1. Extract from the **answer only**, retain a verbatim answer anchor, resolve its
   subjects/conditions, and avoid splitting event modifiers or duplicating equivalent
   paraphrases. The source passages cannot silently correct the extraction.
2. Judge fixed claim indices against source segments. Explicitly allow grounded
   arithmetic and require each claim's own applicability and causal premises.
   Return evidence IDs; code copies the same segment text used by compact-v1.

Code rejects nonverbatim anchors, missing/duplicate claim judgments and invalid
evidence IDs. A bounded structural repair is allowed once per stage. This does not
guarantee semantic correctness; it makes omissions and stage behavior inspectable.
No source-specific gold values, case IDs or reference quotes are supplied to the model.

The [protocol](../results/dev-refinement-v4/protocol.json) was recorded before this
run. Both methods use `gpt-6.1-sol` through the existing Codex login, concurrency 1,
90-second call / 240-second request deadlines, and one balanced pass over all 20 dev
families. The candidate's extra call is a deliberate quality/cost tradeoff, not an
equal-compute comparison. All prompts, raw outputs, repairs and token usage are saved.

The primary comparison uses the same retained cases after excluding
`upstream_timeout` and `upstream_error`; other output failures remain penalties.
All-attempt results and excluded calls are also retained. Missing responses may
be selective, so the conditional score is not a full-dev accuracy estimate.
The scorer, input data and reference labels stay unchanged. No reviewed score is
used to select the candidate, and no candidate is automatically promoted to production.

## Reproduction

From the repository root, with the environment installed as in the README:

```bash
export LLM_BACKEND=codex LLM_MODEL=gpt-6.1-sol
export LLM_TIMEOUT_SECONDS=90 VERIFIER_TIMEOUT_SECONDS=240
python -m experiments.dev_refinement --out results/local/dev-refinement-v4
```

Use a fresh output directory; the command refuses to overwrite a run. There is no
`--split test` option. Unit tests exercise the development selector, answer-only
extraction, fixed claims, literal citations and bounded invalid-output handling.
The [protected hashes](../results/dev-refinement-v4/protected-hashes.json) cover 121
pre-existing data, production source and result files, including the original test.

## V4 result: reject the two-stage candidate

All 40 requests completed; there are no availability exclusions or repairs. On the
same 20 dev cases / 85 gold claims:

| Method | Auto E2E F1 | Verdict macro-F1 | TP / predicted / gold | Median / P95 seconds | Input / output tokens | Calls |
| --- | --- | --- | --- | --- | --- | --- |
| compact-v1, fresh baseline | 0.682 | 0.739 | 59 / 88 / 85 | 11.358 / 14.570 | 232,832 / 4,915 | 20 |
| anchored-v4 | 0.616 | 0.720 | 53 / 87 / 85 | 23.028 / 28.305 | 458,547 / 9,221 | 40 |

The paired-family F1 difference is -0.066, 95% interval **[-0.157, +0.030]**.
Mean per-case latency rises by 11.822 seconds, interval [10.493, 13.239]. Token
usage includes Codex overhead; subscription dollar cost is unknown.
V4 fails the predeclared numeric selection rule and is not promoted.
The earlier 0.667 baseline and this fresh 0.682 baseline also show run variation.

V4 improves the self-contained sqlite3 claims (2 to 4 credited claims) and fixes
the arithmetic assertion. But it merges JSON's last-value and no-error predicates,
adds unnecessary decomposition in other cases, and still misses one gold-required
TaskGroup premise: it now includes cancellation but omits the explicit waiting
sentence. In aggregate, unaligned gold grows from 15 to 21, while incomplete-evidence
matches stay at 10. Some losses remain scorer/reference artifacts, so the aggregate
decline alone does not establish worse semantic reasoning. It does establish that
this version does not meet the development acceptance rule at its higher cost.

The raw [comparison](../results/dev-refinement-v4/comparison/),
[recomputed analysis](../results/dev-refinement-v4/analysis.json) and
[decision](../results/dev-refinement-v4/decision.json) retain the unsuccessful attempt.
Run `python results/dev-refinement-v4/analyze.py` for an offline recomputation.

## V5 follow-up: keep one call and narrow the changes

The next [protocol](../results/dev-refinement-v5/protocol.json) was recorded before
its inference, after examining V4. It permits one further candidate, compact-v5,
using the existing compact schema, evidence resolver and single structural-repair
limit. The prompt adds self-contained subjects, grounded arithmetic and explicit
per-claim conditional evidence checks; it clarifies separating value and error
assertions after the JSON regression. Source-only extraction is no longer a
separate call. This is a bundled prompt revision, not an isolated causal ablation.

V5 reuses the 20 saved compact-v1 baseline outputs above and runs once on all 20 dev
cases. It is a sequential comparison: latency/cache/load differences cannot be
attributed only to the prompt. Gold/scoring remain unchanged, and test remains
untouched. The same numeric and semantic-inspection gates apply. No further prompt
versions or availability retries are part of this iteration.

```bash
python -m experiments.compact_v5 --out results/local/dev-refinement-v5
```

### V5 result: local improvements, no aggregate gain demonstrated

V5 completed 18 of 20 requests. `python-sqlite3` returned `upstream_error` and
`sqlite-deterministic` hit `upstream_timeout`. Both are excluded from the conditional
quality comparison under the predeclared rule, with no retries. Network/backend
variability is suspected, but the traces do not establish the cause. Quality on
those two cases remains unknown.

The fair comparison is the **same 18 cases / 76 gold claims**:

| Method | Auto E2E F1 | Verdict macro-F1 | TP / predicted / gold | Median / P95 seconds | Input / output tokens on these cases |
| --- | --- | --- | --- | --- | --- |
| saved compact-v1 | 0.714 | 0.781 | 55 / 78 / 76 | 11.358 / 14.875 | 209,463 / 4,413 |
| compact-v5 | 0.697 | 0.774 | 54 / 79 / 76 | 11.827 / 20.098 | 214,085 / 4,894 |

The paired-family F1 difference is -0.018, with 95% interval **[-0.092, +0.055]**.
This does not establish a reliable quality difference. The measured mean latency
difference is +1.452 seconds; the sequential design cannot isolate prompt effects
from cache or backend load. Neither method used a structural repair in these runs.

For completeness, on all 20 attempted requests, v1/v5 automatic F1 is **0.682 /
0.659**. All-attempt known input/output usage is **232,832 / 4,915** for v1 and
**at least 225,964 / 5,148** for v5. V5's upstream-error call reported usage; its
timeout did not. Failed-call consumption is retained where known. Subscription
USD cost remains unknown. It would be misleading to compare v5's 18-case 0.697
against v1's 20-case 0.682 and call that an improvement.

### What changed in the actual outputs?

| Dev example | Baseline or v4 issue | V5 observation | Interpretation |
| --- | --- | --- | --- |
| `sqlite-partialindex` | V1 says `3+3=6` equivalence is UNSUPPORTED | Correctly permits arithmetic and returns SUPPORTED | A real reasoning fix; the separate necessity/sufficiency annotation remains disputed |
| `python-asyncio-task` | V1 omits cancellation; v4 omits explicit waiting | Includes cancellation, waiting and grouped raising in the same claim's citations | A real proof improvement, yet lexical similarity falls to 0.60 below the 0.65 matching threshold, so it receives no automatic credit |
| `python-json` | V4 merges final-value and no-error assertions | Restores separate claims and the default qualifier | Fixes the introduced atomicity regression; overly broad gold spans still suppress credit |
| `postgres-runtime-config-client` | V1 omits the setting when stating the boundary claim | V5 preserves `1500` from the answer and correctly returns CONTRADICTED | Gold omits that number, triggering a numeric-guard mismatch rather than a demonstrated boundary error |
| `sqlite-expridx` | Gold bundles WHERE and ORDER BY applicability | V5 produces two supported claims | Reference/prediction granularity still differs; more detailed output is not automatically better under one-to-one scoring |

The [case analysis](../results/dev-refinement-v5/case-analysis.json) gives exact
prediction indices, source-run paths, quotes, similarities and evidence-coverage
checks for the first four examples. It is **author self-review (AI-assisted)** and
does not override any score. No semantic-reviewed F1 is substituted for automatic F1.
No false-supported output appears among automatically aligned claims in either
comparison; that limited diagnostic does not certify unmatched claims or gold.

The [decision](../results/dev-refinement-v5/decision.json) therefore keeps compact-v1
as default and leaves v4/v5 experimental. The [raw v5 run](../results/dev-refinement-v5/run/)
and [paired analysis](../results/dev-refinement-v5/analysis.json) remain available.
Run `python results/dev-refinement-v5/analyze.py` to reproduce this comparison from
saved outputs; it verifies both original summaries and all 121 protected hashes.

## What should be improved next?

The next priority is a calibrated development measurement, before another prompt
search: distinguish equivalent numeric formatting from changed quantities; make
entity resolution and claim granularity consistent; and accept alternative complete
proofs without requiring irrelevant source text. Keep stricter checks for changed
units, boundaries, negation and scope. Human author review is still needed for the
reference disputes and for a sample of accepted/rejected alignments.

Any scorer/reference revision should be a separately versioned **dev** experiment,
applied equally to all saved baseline and candidate outputs. Its score change must
be reported as measurement repair, not model improvement. Only after that can the
observed arithmetic/proof improvements be assessed without chasing lexical overlap.
This iteration stops after the two recorded candidates; the existing test, labels,
raw outputs and production verifier are unchanged.

The [verification receipt](../results/dev-refinement-v5/verification.json) records
100 passing tests, Ruff lint/format checks, exact saved-summary reproduction,
independent count/latency arithmetic, 348 literal citation checks and 87 extraction
anchor checks. All 121 protected file hashes match. These checks validate execution
and reporting, not the unresolved semantic gold annotations.
