# Acceptance record

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

## Final evaluation freeze

The compact verifier was selected in commit
`f7780b19c9d724371dc99e96bb67af2f8608ee6c`, before any
held-out inference. The final run uses all three required approaches on the
unchanged 16-case test split, one pass, concurrency 1, the same model and timeouts.
No prompts or verifier logic will be selected using final-test results.

The source SHA-256 is
`39b9d668ea12374894fe93864dacd84f52c9b93fc9ceca064728d5ef94473e74`;
the dataset SHA-256 is
`cce60eb5be10675e61d6e7e3b41981a25c123a3a3e205425697e11d5d986dfc2`.
Subsequent commits may add documentation and result artifacts without changing
these tested inputs or implementation.

## Remaining delivery checks

The final held-out report and final public-repository inspection are recorded
when completed. The repository, README and dataset were already reachable by
unauthenticated HTTPS requests before the final report was added.
