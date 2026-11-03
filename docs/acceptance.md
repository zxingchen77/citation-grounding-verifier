# Acceptance record

The records below identify the version and scope of each check. For the overall
delivery, see [requirement coverage](assignment-coverage.md). Original held-out
results and the later v2 development checks are separate validation stages.

## Submission cleanup and SQLite WAL acceptance, 2026-11-03

The final system remains compact-v1 (default `optimized`), evaluated in
`results/heldout-v1`. The prompt, inference strategy, corpus cases and historical
numeric results are unchanged. `optimized-v2` remains a dev ablation without a
held-out result; no challenge test inference was run.

- `pytest -q`: **74 passed**, with the existing Starlette/httpx deprecation warning.
- `ruff check .`: passed; `ruff format --check .`: 54 files already formatted.
- Invalid requests, including malformed JSON, now return HTTP 422 with the same
  `{"error":{"code":"invalid_request","message":"..."}}` envelope as other
  service errors. The six added checks cover validation failures without model
  calls and the matching OpenAPI error schema.
- One real localhost request sent the assignment's unchanged SQLite WAL example
  to `optimized` using `gpt-6.1-sol` through the existing Codex login. It completed
  in **33.903 seconds**, with four claims matching the example's verdicts:
  CONTRADICTED / SUPPORTED / SUPPORTED / UNSUPPORTED. All quotes are verbatim;
  health and the 422 error check also passed. There was one model call, no retry
  and no repair. The temporary server was stopped afterward.

The [request](../results/acceptance/sqlite-wal/request.json),
[response](../results/acceptance/sqlite-wal/response.json),
[checks](../results/acceptance/sqlite-wal/checks.json),
[provider trace](../results/acceptance/sqlite-wal/calls.jsonl) and
[configuration/source hash](../results/acceptance/sqlite-wal/service.json) are
retained. This Sol smoke check is separate from the original Astra held-out
comparison. It verifies this example, not overall model accuracy.

Reviewer-label and Markdown presentation changes are described in the
[run index](../results/README.md#presentation-update-2026-11-03); quantitative
artifacts and semantic review decisions are preserved. Historical source hashes
identify the implementation at the time of each run. The current source differs
because of the HTTP error-contract change, which does not change either prompt.

## Evidence-prompt update, 2026-11-03

Implementation commit `5850663` passes all 68 tests, Ruff lint and formatting.
The added subprocess tests run local Python children without making model calls;
they verify timeout/cancellation cleanup, retained partial progress, large-pipe
draining, tool rejection and sanitized failure codes.

The actual localhost `optimized-v2` service passed health, empty-answer,
malformed-input and one real Sol inference check. The two-claim response was
correct; the ad-hoc harness initially expected one claim and was corrected by
rescoring the saved response, with no new inference. Both records are retained.
All 24 requests in the subsequent balanced old/new dev comparison completed
without retries or repairs. Source/data hashes remain fixed. See the
[experiment and receipts](prompt-ablation-v2.md). Direct external HTTP-provider
acceptance and challenge test inference are outside this iteration.

## Reproduction in a clean checkout

On 2026-11-02, commit `ab5e5877c9bb0a938cda448c293ffb8d68271995` was cloned into
a new temporary directory. A separate Python 3.12 virtual environment installed
`requirements.lock` from PyPI and installed the project with `--no-deps -e .`.
No project-local configuration or credentials were copied.

- All 39 tests passed. The pinned Starlette TestClient emits one deprecation
  warning about its httpx integration; the tests and actual HTTP checks pass.
- Uvicorn started on a localhost TCP port and `/health` returned 200.
- Real HTTP requests validated empty answers, numeric contradictions, exact
  quotes and rejection of a malformed request with 422.
- The installed `grounding-eval` command completed the 24-case deterministic
  development benchmark.
- GitHub Actions independently passes installation, formatting, lint, tests and
  a deterministic evaluation on Linux / Python 3.12.

The [saved HTTP responses](../results/acceptance/clean-checkout-http.json) contain
the original request data and measured responses. These checks use the
deterministic backend and are not represented as model-quality evidence.

## Repeat the HTTP checks

Start the service as described in the README, then run:

```bash
python scripts/smoke_http.py --url http://127.0.0.1:8000 \
  --out results/local/http-baseline.json
```

With the optimized real model backend running, add `--llm` to exercise non-factual
answers, absent context, instruction-like source text, mixed factual claims and
multi-passage evidence. Output paths must be new, so prior receipts are preserved.

Malformed model JSON, invalid citations, bounded repair, provider failures and
timeout cancellation are covered by deterministic tests using controlled fake
providers. Real provider outages are not induced to claim test coverage.

## Real-model HTTP acceptance

The optimized service passed all eight HTTP acceptance checks on 2026-11-02,
using the signed-in Codex backend with `gpt-6-astra`, 90-second model timeout and
240-second request timeout. The exercised service was launched from commit
`2e0a2b7d023bb03dd4fbfbba102b9422de597d6e`; verifier source is unchanged from the
development run. [Saved requests and responses](../results/acceptance/optimized-http.json)
cover empty answers, non-factual text, empty context despite a real-world true
claim, a numeric contradiction, an instruction embedded in context, mixed claims,
multiple evidence premises, and malformed-input rejection.

The instruction probe is one functional check, not evidence of comprehensive
prompt-injection robustness. Acceptance cases are separate from benchmark scores.

## Original evaluation freeze

The original compact verifier was selected in commit
`f7780b19c9d724371dc99e96bb67af2f8608ee6c`, before any
held-out inference. That run used all three required approaches on the
unchanged 16-case test split, one pass, concurrency 1, the same model and timeouts.
Its implementation was not reselected using those final-test results.

The source SHA-256 is
`39b9d668ea12374894fe93864dacd84f52c9b93fc9ceca064728d5ef94473e74`;
the dataset SHA-256 is
`cce60eb5be10675e61d6e7e3b41981a25c123a3a3e205425697e11d5d986dfc2`.
These hashes identify the original frozen experiment. Later challenge and v2
runs have their own manifests; their source versions must not be assigned these
held-out scores.

## Original evaluation completed

The [held-out report](../results/heldout-v1/reviewed-report.md) includes all 16
cases and all three required approaches. Automatic and reviewed end-to-end F1
are both 0.750 / 1.000 / 0.964 for deterministic / minimal / optimized.
The optimized candidate's one frozen-label mismatch is discussed in the README;
no post-test relabeling or prompt tuning was performed. Review records resolve
the three flagged heuristic evidence cases without adding credit.

At the original delivery, source and data hashes were checked against both final development
and held-out manifests and are identical. Their recorded source trees were clean.
The repository, README and dataset are accessible through unauthenticated HTTPS;
the final results are included in the concluding repository inspection.

## Challenge stage 1 acceptance (separate from the original delivery)

Commit `2e63e261119a985833390acb3e4d26db125dcb28` passes 59 local tests, lint and
format checks. The original 40-case deterministic command and historical summary
recomputation pass. The real deterministic localhost service passes three checks;
its [receipt](../results/acceptance/challenge-baseline-http.json) is retained.

The real minimal Codex-backed service uses gpt-6-astra with 90/240-second deadlines.
It completes eight probes: seven pass and the numeric-contradiction probe returns
504 after a model timeout. This is **not an all-pass acceptance result**. The
[checks](../results/acceptance/challenge-minimal-http/checks.json),
[configuration](../results/acceptance/challenge-minimal-http/service.json) and
[provider traces](../results/acceptance/challenge-minimal-http/calls.jsonl) contain
actual requests, responses and known usage. No mock supplied these responses.

To reproduce with a configured real backend and new output directories:

```bash
python scripts/serve_acceptance.py --method minimal --port 8877 \
  --out results/local/acceptance-service
# In another shell:
python scripts/smoke_http.py --url http://127.0.0.1:8877 --llm \
  --continue-on-error --out results/local/acceptance-service/checks.json
```

A separate predeclared diagnostic makes exactly two dev calls at 180/360-second
deadlines. Both time out. [Its protocol and outputs](../results/availability-diagnostic-v1/)
are retained without retries; they do not replace the full dev comparison.

A final [alternative-model diagnostic](../results/availability-alternative-v1/)
used the same two predeclared dev probes with `gpt-6.1-sol` and 90/240-second
deadlines. Both calls completed (9.794 and 14.134 seconds), without retries.
This is limited availability evidence, not an all-pass HTTP acceptance run or
a new quality benchmark.

No direct external HTTP key/model configuration was available. HTTPModel's
strict-schema, usage, malformed-output, refusal, transport-error, cancellation,
timeout and repair checks are controlled transport tests, not external API
acceptance. No credential file was read or exported and no new service was bought.

The additional challenge test split has not been sent to a verifier. No challenge
test run is scheduled; a future run requires a separate user decision. The final
system remains compact-v1 (default `optimized`), evaluated on the original 16-case
held-out split in `results/heldout-v1`. See the [experiment log](experiments.md)
and [v2 dev ablation](prompt-ablation-v2.md) for the separate development work.
