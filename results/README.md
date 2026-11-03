# Run index

The final system is compact-v1 (default `optimized`); use `heldout-v1` for its
authoritative evaluation and `dev-v3` for its selection evidence. The later
`prompt-ablation-v2/comparison` is a two-prompt dev ablation on 12 challenge
cases. `optimized-v2` has not been evaluated on held-out data. The `challenge-dev-v1` run is an earlier
two-round development experiment with one deterministic round and many timeouts;
it is not a held-out result. Earlier runs are
preserved to show the actual experimental history;
their different reference versions must not be mixed into one quality comparison.

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
