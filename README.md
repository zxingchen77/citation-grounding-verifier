# Citation Grounding Verifier

**Final system: compact-v1 (`optimized`, the default).** It extracts atomic claims,
selects evidence IDs, and copies exact source quotes. The authoritative evaluation
is [`results/heldout-v1`](results/heldout-v1/). `optimized-v2` is a dev ablation
and has **not** been evaluated on held-out data.

## Held-out comparison

16 cases / 28 claims; one pass per method, `gpt-6-astra` via Codex, concurrency 1.
Token totals cover all 16 requests per method, including CLI overhead.

| Method | Automatic F1 | Reviewed F1 | Median / P95 (s) | Input / output tokens | Model USD | Failed requests |
| --- | --- | --- | --- | --- | --- | --- |
| `deterministic` | 0.750 | 0.750 | <0.001 / <0.001 | 0 / 0 | 0 | 0 / 16 |
| `minimal` | 1.000 | 1.000 | 10.183 / 14.679 | 173,157 / 1,831 | unknown | 0 / 16 |
| `optimized` (compact-v1) | 0.964 | 0.964 | 8.765 / 11.442 | 174,573 / 1,460 | unknown | 0 / 16 |

## Run the service and evaluation

Python 3.12; from the repository root, using an existing Codex login:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
codex login status
export LLM_BACKEND=codex LLM_MODEL=gpt-6-astra
export LLM_TIMEOUT_SECONDS=90 VERIFIER_TIMEOUT_SECONDS=240
VERIFIER_METHOD=optimized uvicorn grounding.api:app --host 127.0.0.1 --port 8000
```

In a second shell with the same environment, use a fresh output directory:

```bash
grounding-eval --methods deterministic minimal optimized --split test \
  --out results/local/heldout-rerun
# Credential-free development check:
grounding-eval --methods deterministic --split dev --out results/local/baseline
```

These commands use the original corpus. They do not run the challenge test split.
Model access is required for LLM methods; a rerun is separate from the frozen result.

## API and example

`POST /verify` accepts `context_passages: list[str]` and `generated_answer: str`.
Each returned claim has `claim_text`, `verdict`, `reasoning`, and
`citations: [{index, quote}]`. OpenAPI is at `/docs`; `/health` reports the method.

```bash
curl -sS http://127.0.0.1:8000/verify \
  -H 'Content-Type: application/json' \
  --data-binary @results/acceptance/sqlite-wal/request.json
```

The assignment's SQLite WAL example has a saved
[request](results/acceptance/sqlite-wal/request.json),
[response](results/acceptance/sqlite-wal/response.json) and
[acceptance receipt](results/acceptance/sqlite-wal/checks.json).
This is a separate `optimized` HTTP smoke check using `gpt-6.1-sol`, not a new
held-out result. Runtime settings and model traces are retained alongside it.

The model handles claim decomposition and source-only semantic judgments. Code
requires nonempty citations for `SUPPORTED` / `CONTRADICTED`, empty citations for
`UNSUPPORTED`, valid zero-based indices and exact substrings. One structural
repair is allowed for the optimized method; a real quote alone does not prove
that a claim is supported. Provider failures are never relabeled `UNSUPPORTED`.

Errors use `{"error":{"code":"...","message":"..."}}`: invalid input is 422,
missing configuration 503, invalid model output/upstream errors 502, and timeouts
504. Empty answers skip inference. Limits: 32 passages, 32,000 characters per
passage, 100,000 total context characters, 16,000 answer characters, 64 claims,
and 8 citations per claim.

## Methods and provider options

| Method | Design | Model calls per request |
| --- | --- | --- |
| `deterministic` | Punctuation, lexical overlap, numeric/negation heuristics | 0 |
| `minimal` | Short prompt; model emits claims, verdicts and quotes | 1 |
| `optimized` | Compact-v1: evidence IDs resolved to exact source text | 1; at most 2 with repair |

The experimental `staged` and `optimized-v2` methods remain selectable. Their
history and development results are in the [experiment log](docs/experiments.md).
The challenge test split remains unused; any new run requires a separate decision.

For a compatible strict-JSON-schema Chat Completions API, set `LLM_BACKEND=http`,
`LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY` locally. See [configuration](.env.example).
Those files are not auto-loaded. A credential-free service uses
`VERIFIER_METHOD=deterministic uvicorn grounding.api:app --host 127.0.0.1 --port 8000`.

The Codex adapter uses the existing sign-in in an isolated temporary directory,
disables tools/connectors, and rejects observed tool calls. It is intended for a
trusted workstation. Tested CLI version: `0.166.0-alpha.5.1`. Real benchmarks use
Codex; the external HTTP provider has controlled transport tests, not live acceptance.

## Dataset, scoring and interpretation

The [original dataset](data/README.md) has 40 synthetic cases / 72 atomic claims:
10 cases each for supported answers, subtle distortions, extrinsic hallucinations,
and multi-passage synthesis. Families are separated into 24 dev / 16 test cases.

End-to-end F1 requires one-to-one claim alignment, the correct verdict, literal
citations and sufficient evidence. Missing claims count as false negatives;
wrong or duplicate predictions count as false positives. Failed requests stay
in the denominator. The lexical aligner can need explicit review; both automatic
and reviewed scores are shown. Review is **author self-review (AI-assisted)**,
not independent human adjudication. See the [scoring contract](docs/scoring.md).

Compact-v1 was selected on development data before the held-out run. Minimal
has the highest frozen-reference score. Compact emits 20.3% fewer output tokens,
but slightly more total tokens; its lower observed median is not a proven speedup.
Different cache hits, fixed ordering and one small run limit comparison. Cached
input totals are 92,928 for minimal and 58,240 for optimized. Subscription dollar
cost is unknown; zero model tokens for the baseline excludes infrastructure cost.

**Key failures:** lexical overlap misses scope and complete multi-passage evidence.
On `quartz-tls-distortion`, compact returns `UNSUPPORTED` for port 7444 because
the source's port 7443 is not explicitly exclusive; the frozen reference expects
`CONTRADICTED`. The mismatch and label are retained. Short synthetic English cases
and author self-review do not establish production accuracy or generalization.

[Automatic report](results/heldout-v1/report.md),
[reviewed report](results/heldout-v1/reviewed-report.md), and
[raw predictions](results/heldout-v1/predictions.jsonl) preserve the full comparison.
To recompute without inference, copy the run to a scratch directory and invoke
`grounding-score --run COPY --dataset data/cases.jsonl --reviews COPY/reviews.json`.

## Validation and project record

```bash
pytest -q
ruff check .
ruff format --check .
```

[CI](.github/workflows/ci.yml) runs these checks plus a deterministic dev benchmark.
The [acceptance record](docs/acceptance.md) distinguishes unit/transport tests,
actual localhost model checks and historical clean-checkout reproduction.

- [Assignment requirements and evidence](docs/assignment-coverage.md)
- [Analysis, architecture, implementation and delivery process](docs/development-process.md)
- [Architecture and module responsibilities](docs/design.md)
- [Experiments: baseline selection, Astra failures and v2 dev ablation](docs/experiments.md)
- [Full run index](results/README.md)

Implementation and documentation were developed with Codex assistance. Commit
history and retained artifacts record the actual iterations. This repository is
the public deliverable requested by the
[assignment](https://gist.github.com/wsxiaoys/849522ee389e0ce359ef444653084484).
