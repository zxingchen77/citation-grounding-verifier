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

## Remaining delivery checks

The corrected development comparison, final held-out report, real-model HTTP
receipt and final public-repository inspection are recorded when completed.
