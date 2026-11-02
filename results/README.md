# Run index

Use `dev-v3` for the final development comparison and `heldout-v1` for final
verification. Earlier runs are preserved to show the actual experimental history;
their different reference versions must not be mixed into one quality comparison.

| Directory | Dataset / split | Purpose |
| --- | --- | --- |
| `dev-deterministic-v1` | v1 dev, rescored on v2 labels | Initial heuristic baseline and reference audit |
| `dev-minimal-v1` | v1 dev, rescored on v2 labels | First real model baseline; exposed compound reference claims |
| `dev-candidates-v1` | v2 dev | Staged and compact candidates; exposed ambiguous bound wording |
| `dev-v3` | v3 dev | Fresh inference for all three required methods on clarified inputs; selects compact |
| `heldout-v1` | v3 test; test inputs/labels unchanged since v1 | Final evaluation after selection, no further prompt tuning |
| `acceptance` | Separate HTTP probes | Clean-checkout and real-model service behavior, outside benchmark scores |

Each benchmark directory contains:

- `manifest.json`: data/source hashes, code revision, model, backend and run settings.
- `predictions.jsonl`: original outputs, failure details, per-call traces and usage.
- `summary.json` / `report.md`: original automatic scoring, including review flags.
- `reviews.json`: explicit alignment/evidence decisions, labeled AI-assisted.
- `reviewed-summary.json` / `reviewed-report.md`: rescoring with those decisions.
- `review-provenance.json`: the scored data, original data and review hashes.

`data/revisions/` preserves earlier datasets. A reference-only rescore verifies
that model inputs are unchanged. Version 3 changed six development inputs, so
`dev-v3` contains new inference for the entire development comparison. Original
scores are not overwritten and annotation repair is not counted as model progress.

The final-test manifest records the selected code revision. Later result/document
commits retain the same verifier source and dataset hashes; no circular claim is
made that a commit can contain its own future hash in a result manifest.

All real model runs here use `gpt-6-astra` through the signed-in Codex CLI, at
concurrency 1, without a response cache. Provider-reported prefix caching is not
disabled or controlled and its token counts are reported. Subscription dollar
cost is unknown. Latency includes CLI startup and framework overhead. The HTTP
API adapter has controlled transport tests, not a separate paid API benchmark.
