# Run index

The main evaluation is now [real-docs-v3](real-docs-v3/), documented in the
[v3 report](../docs/real-docs-v3.md). It is provisional against AI-drafted gold,
with human author review pending. Compact-v1 remains selected; v2/v3 are dev-only.

| Current artifact | Purpose |
| --- | --- |
| `dev-refinement-v4` | Later dev-only comparison of compact-v1 and an anchored two-stage prototype; 27-item failure audit, protocol and protected artifact hashes |
| `real-docs-v3/dev-initial` | Three methods on 20 dev cases; original draft scores and `reference-` scores on repaired gold |
| `real-docs-v3/dev-candidate` | One compact-v3 dev trial; did not improve the declared selection metric |
| `real-docs-v3/test` | One frozen pass, 12 cases per method; six failed requests retained |
| `real-docs-v3/availability-adjusted` | Post-run author-requested quality view excluding five timeouts and one upstream error; also compares the same seven completed cases |
| `real-docs-v3/test-freeze.json` | Code/data/configuration hashes before test |
| `real-docs-v3/annotation-questions.json` | Known reference questions; no frozen label changed |
| `real-docs-v3/verification.json` | Recomputed scores, hashes, quote checks and HTTP evidence |

Run `python results/real-docs-v3/verify.py` to repeat the offline consistency checks.
The original `challenge-v1` test is unused. The historical index below describes
the earlier synthetic corpus, now archived in
`data/revisions/cases-synthetic-v3.jsonl`; its scores are not current main results.

## Historical runs

| Directory | Dataset / split | Purpose |
| --- | --- | --- |
| `dev-deterministic-v1` | v1 dev, rescored on v2 labels | Initial heuristic baseline and reference audit |
| `dev-minimal-v1` | v1 dev, rescored on v2 labels | First real model baseline; exposed compound reference claims |
| `dev-candidates-v1` | v2 dev | Staged and compact candidates; exposed ambiguous bound wording |
| `dev-v3` | v3 dev | Fresh inference for all three required methods on clarified inputs; selects compact |
| `heldout-v1` | v3 test; test inputs/labels unchanged since v1 | Final evaluation after selection, no further prompt tuning |
| `challenge-dev-v1` | challenge-v1 dev; two LLM rounds, one deterministic round | Balanced paired experiment; preserves real timeouts and original automatic scores |
| `availability-diagnostic-v1` | Two predeclared development probes | One call each on gpt-6-astra at 180 seconds; both timed out |
| `availability-alternative-v1` | The same two development probes | One call each on gpt-6.1-sol at 90 seconds; both completed; availability evidence only |
| `prompt-ablation-v2/comparison` | Unchanged challenge-v1 dev; one balanced round | Same Sol model, old/new evidence prompt: automatic F1 0.812 / 0.960; reviewed F1 0.832 / 1.000; all 24 requests retained |
| `prompt-ablation-v2/preflight` | Original Maple development case | One real localhost v2 model call, plus no-inference checks; initial assertion correction retained |
| `acceptance` | Separate HTTP probes | Clean-checkout and real-model service behavior, outside benchmark scores |

Each benchmark directory contains:

- `manifest.json`: data/source hashes, code revision, model, backend and run settings.
- `predictions.jsonl`: original outputs, failure details, per-call traces and usage.
- `summary.json` / `report.md`: original automatic scoring, including review flags.
- `reviews.json`: explicit alignment/evidence decisions; author self-review (AI-assisted).
- `reviewed-summary.json` / `reviewed-report.md`: rescoring with those decisions.
- `review-provenance.json`: the scored data, original data and review hashes.

`data/revisions/` preserves earlier datasets. A reference-only rescore verifies
that model inputs are unchanged. Version 3 changed six development inputs, so
`dev-v3` contains new inference for the entire development comparison. Original
scores are not overwritten and annotation repair is not counted as model progress.

The original final-test manifest records the selected code revision. Its original
result/document commits retained the same verifier source and dataset hashes.
The challenge revision has separate data/source hashes and does not replace that
historical record.

Earlier quality benchmarks use `gpt-6-astra`; `prompt-ablation-v2` and the
separately labeled alternative availability diagnostic use `gpt-6.1-sol`.
Both use the signed-in Codex CLI, at
concurrency 1, without a response cache. Provider-reported prefix caching is not
disabled or controlled and its token counts are reported. Subscription dollar
cost is unknown. Latency includes CLI startup and framework overhead. The HTTP
API adapter has controlled transport tests, not a separate paid API benchmark.

## Presentation update, 2026-11-03

Reviewer labels are standardized as **author self-review (AI-assisted)**, and
reviewed Markdown reports now show their corresponding automatic scores. Raw
predictions, quantitative JSON summaries, paired analyses, review decisions and
dataset cases are unchanged. Metadata hashes were updated for the renamed review
labels and report presentation. The pre-update artifacts remain in
[commit 09266b5](https://github.com/zxingchen77/citation-grounding-verifier/tree/09266b553e2599944f2d07e165a29d939e06a251/results).
Historical source hashes identify the implementation at each experiment, not the
current service's later HTTP error-format change.
