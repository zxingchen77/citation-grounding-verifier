# Citation Grounding Verifier

A Python HTTP service that splits an answer into atomic factual claims, checks
each against supplied passages, and returns exact evidence quotes. It compares a
deterministic baseline, a minimal single-call LLM, and an optimized evidence-ID
verifier. A two-stage candidate is retained as an ablation.

**Progress:** service and offline checks work; real development baselines are
recorded below. Candidate comparison and held-out evaluation are in progress.

## Run the service

Python 3.12 is the tested runtime. From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
pytest -q

# No credentials required for this baseline.
VERIFIER_METHOD=deterministic uvicorn grounding.api:app --host 127.0.0.1 --port 8000
```

```bash
curl -sS http://127.0.0.1:8000/verify \
  -H 'Content-Type: application/json' \
  -d '{"context_passages":["Cache lasts 7 days."],"generated_answer":"Cache lasts 8 days."}'
```

The response contains `claims`, each with `claim_text`, `verdict`, `reasoning`,
and `citations: [{index, quote}]`. This example is `CONTRADICTED` with the original
seven-day quote. OpenAPI documentation is at `/docs`; `/health` is a liveness check.

For an OpenAI-compatible Chat Completions API with strict JSON-schema support:

```bash
export LLM_BACKEND=http
export LLM_BASE_URL=https://api.openai.com/v1
export LLM_MODEL=your-structured-output-model
export LLM_API_KEY=your-key       # set locally; never commit
export VERIFIER_METHOD=optimized
uvicorn grounding.api:app --host 127.0.0.1 --port 8000
```

For local evaluation using an existing ChatGPT/Codex subscription:

```bash
codex login status
export LLM_BACKEND=codex
export LLM_MODEL=gpt-6-astra     # must be available to your account
export LLM_TIMEOUT_SECONDS=90
export VERIFIER_TIMEOUT_SECONDS=240
export VERIFIER_METHOD=optimized
uvicorn grounding.api:app --host 127.0.0.1 --port 8000
```

The Codex adapter uses `codex exec --output-schema` in a temporary directory,
ignores user configuration, disables tools/connectors and rejects observed tool
calls. It uses the CLI's existing sign-in without reading or exporting credentials.
It is a trusted-workstation adapter, not a public inference gateway. These real
benchmarks use Codex; the HTTP provider is covered by mocked transport tests.
[`.env.example`](.env.example) lists configuration; files are not auto-loaded.

## How the approaches differ

| Method | Processing | Model calls per request |
| --- | --- | --- |
| `deterministic` | Punctuation splitting, lexical overlap, numeric/negation heuristics | 0 |
| `minimal` | One short prompt; model emits claims, labels and quotes | 1 |
| `optimized` | Model selects source-segment IDs; code copies the exact quotes | 1, at most 2 with repair |
| `staged` | Source-blind extraction, then fixed-index verification | Normally 2, at most 4 with repairs |

All successful responses pass strict typed validation and deterministic citation
checks. `SUPPORTED` and `CONTRADICTED` require evidence; `UNSUPPORTED` requires
empty citations. Out-of-range indices and nonverbatim quotes are rejected. Quote
existence alone does **not** establish semantic correctness.

The optimized path avoids regenerating source text. It preserves segment order
and passage indices, selects every premise needed for a judgment, and resolves
IDs back to literal substrings. One repair is allowed for invalid structured
output. Provider failures are errors, never silently relabeled `UNSUPPORTED`.

Input validation returns HTTP 422; missing model configuration returns 503;
provider/malformed-output errors return 502; timeouts return 504. Model errors use
`{"error":{"code":"...","message":"..."}}`. Limits are 32 passages, 32,000
characters per passage, 100,000 context characters, 16,000 answer characters,
64 output claims and 8 citations per claim. Empty answers skip inference; factual
claims with no source support remain unsupported.

## Dataset and scoring

[`data/cases.jsonl`](data/cases.jsonl) contains **40 original synthetic cases and
72 labeled claims**, balanced across supported answers, subtle distortions,
extrinsic hallucinations and multi-passage synthesis. Scenario families stay
together: 24 development cases / 44 claims and 16 held-out cases / 28 claims.
Dataset construction and review are AI-assisted; independent human annotation is
not claimed. See [dataset notes](data/README.md) and the frozen hashes.

Primary end-to-end F1 requires one-to-one claim alignment, the correct verdict,
literal citations and sufficient evidence. Missing claims are false negatives;
duplicates and incorrect predictions are false positives. Failed requests count
against recall. The lexical aligner flags paraphrases and ambiguous evidence for
explicit, retained review. [Scoring details](docs/scoring.md) explain this
heuristic's limitations and the review format. Label-only F1 is diagnostic.

```bash
# Each run needs a new output directory; previous results are not overwritten.
grounding-eval --methods deterministic --split dev --out results/local/baseline

# After selecting a real provider above:
grounding-eval --methods deterministic minimal optimized --split test \
  --out results/local/heldout

# Re-score saved outputs, without more inference, using an explicit review file:
grounding-score --run results/dev-minimal-v1 \
  --reviews results/dev-minimal-v1/reviews.json \
  --original-dataset data/revisions/cases-v1.jsonl
```

Runs save raw predictions, model traces, failures, latency, usage, data/source
hashes, parameters and Git revision. Review results are separate files and preserve
the original automatic scores. All model calls, including repairs, are counted.
No mock fallback is used by the benchmark runner.

## Results so far

Real development runs on 2026-11-02, `gpt-6-astra` through Codex, concurrency 1,
one pass per method. Both rows use the corrected 44-claim references and explicit
AI-assisted reviews; there are no outstanding alignment-review flags.

| Method | Correct / gold | Precision | Recall | End-to-end F1 | Median seconds | Model calls |
| --- | --- | --- | --- | --- | --- | --- |
| Deterministic | 31 / 44 | 0.738 | 0.705 | 0.721 | <0.001 | 0 |
| Minimal LLM | 44 / 44 | 1.000 | 1.000 | 1.000 | 11.319 | 24 |

The minimal run used 259,660 input and 2,813 output tokens, including CLI/framework
overhead. Subscription monetary cost is **unknown**, not zero. Optional HTTP API
price inputs produce token-based estimates, not invoices; infrastructure and cache
discounts are excluded. No latency significance is claimed from one sequential run.

- [Deterministic predictions and reviewed scores](results/dev-deterministic-v1/)
- [Minimal model predictions and reviewed scores](results/dev-minimal-v1/)

Observed failures and decisions:

1. The lexical baseline emits real quotes but misses scope/action changes and
   necessary multi-passage premises. Literal quote validity cannot replace a
   grounding metric.
2. The model exposed an annotation error: two Birch queue assertions had been
   merged into one reference. Only those development labels were corrected; inputs
   and held-out cases are unchanged. Both saved baseline runs were rescored. This
   is a reference correction, not a model improvement.
3. The minimal model is already at the development-set ceiling. The next experiment
   compares staged verification with compact evidence selection for resource use
   and quality retention, without assuming more stages improve accuracy.

## Limits and engineering record

These short, synthetic English cases do not establish production accuracy,
long-context retrieval, conflicting-source policy, multilingual quality, or robust
prompt-injection resistance. Sentence segmentation can give broader citations than
necessary. One run does not measure model variance; no independent human review
has been performed. Model/CLI versions and service load may affect reproduction.

- [Design, requirements and acceptance gates](docs/design.md)
- [Experiment log: questions, evidence, decisions and next steps](docs/experiments.md)
- [Tests](tests/) and [GitHub Actions checks](.github/workflows/ci.yml)

Implementation and documentation were developed with Codex assistance. Commit
history and retained artifacts show actual iterations rather than a reconstructed
success story. This repository is the public deliverable requested by the
[assignment](https://gist.github.com/wsxiaoys/849522ee389e0ce359ef444653084484).
