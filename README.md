# Citation Grounding Verifier

**Selected system: compact-v1 (`optimized`, the default).** The main evaluation is
[real-docs-v3](results/real-docs-v3/availability-adjusted/report.md). V2/v3 prompts and the
[v4/v5 prototypes](docs/dev-refinement.md) are dev-only. Gold is **AI-drafted, pending human author review**; known reference
issues are [listed explicitly](results/real-docs-v3/annotation-questions.json).

## Held-out comparison

32 real-document cases were split by source family into 20 dev / 12 test cases.
The 12 test cases have 51 gold claims; one frozen pass per method, `gpt-6.1-sol`
via Codex, balanced order, concurrency 1. At the author's request after the run,
quality and latency below exclude availability failures. Gold remains provisional.

| Method | Automatic E2E F1 | Verdict macro-F1 | Median / P95 (s) | Known input / output tokens, all attempts | USD | Scored / excluded requests |
| --- | --- | --- | --- | --- | --- | --- |
| deterministic | 0.114 | 0.109 | 0.001 / 0.001 | 0 / 0 | 0 | 12 / 0 |
| minimal | 0.468 | 0.720 | 14.925 / 29.279 | ≥113,055 / ≥3,438 | unknown | 9 / 3 |
| optimized (compact-v1) | 0.571 | 0.651 | 12.748 / 20.996 | ≥104,900 / ≥2,255 | unknown | 9 / 3 |

Excluded: five timeouts and one upstream error; suspected network/backend variability,
cause unconfirmed. No reruns. Other quality errors remain penalized. Subsets differ:
on the **same seven completed cases**, F1 is **0.043 / 0.464 / 0.586** respectively.
These conditional scores do not estimate the full test set. [Original all-request
F1](results/real-docs-v3/test/report.md) is 0.114 / 0.400 / 0.484. Token lower bounds
retain failed-call usage where known; usage is missing for 2 minimal / 3 optimized calls.

## Run the service and evaluation

Python 3.12, from the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
# Reproduce the deterministic baseline without a model or API key:
python -m grounding.benchmark --methods deterministic --split test \
  --order balanced --seed 1729 --out results/local/v3-baseline
```

Start the selected service using an existing Codex login:

```bash
codex login status
export LLM_BACKEND=codex LLM_MODEL=gpt-6.1-sol
export LLM_TIMEOUT_SECONDS=90 VERIFIER_TIMEOUT_SECONDS=240
VERIFIER_METHOD=optimized uvicorn grounding.api:app --host 127.0.0.1 --port 8000
# In a second shell with the same environment, for a separate reproduction:
grounding-eval --methods deterministic minimal optimized --split test \
  --order balanced --seed 1729 --out results/local/v3-reproduction
```

Use a fresh output directory. A reproduction is separate from the saved one-pass
experiment; test outputs must not be used for prompt selection. For an HTTP model,
configure `LLM_BACKEND=http`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` locally.
See [configuration](.env.example); no credentials are checked in or auto-loaded.

## Failure analysis: what the numbers mean

The non-LLM baseline drops substantially on longer, paraphrased inputs. Even after
excluding availability failures, conservative claim matching and overlong gold spans
affect the LLM scores; a lower score alone does not prove worse factual reasoning.

| Failure / limitation | Actual observed example |
| --- | --- |
| Claim splitting | On dev `postgres-indexes-partial`, the heuristic treats `?` in SQL `x < ?` as a question boundary and discards factual text. |
| Numeric and scope reasoning | On dev `sqlite-lang_with`, it misses the contradiction in the OFFSET/LIMIT quota calculation. |
| Conditions and negation | On dev `python-datetime`, it wrongly supports the claim that leap-second timestamps always map to different datetimes. |
| Multi-passage evidence | On test `postgres-explicit-locking`, minimal cites savepoint release but omits the premise connecting FOR UPDATE to the lock. |
| Citation/scorer mismatch | On test `sqlite-lang_conflict`, minimal's short ABORT clauses are penalized by broader gold spans; verdicts are correct. |
| Availability | Five timeouts and one upstream failure are excluded from conditional quality scores and retained in the original all-request results. |
| Reference ambiguity | On test `sqlite-autoinc`, compact distinguishes “currently empty” from “never contained data”; the frozen gold is too broad under a literal reading. |

True-but-unretrieved facts remain UNSUPPORTED even when known in the real world.
Completed test outputs did not show an outside-knowledge false-support error on
those facts; failed requests and unmatched/split claims prevent a blanket success
claim. All emitted quotes were literal, as enforced by the service; that does not
mean they were sufficient evidence. See the [full failure analysis](docs/real-docs-v3.md).

## Dataset, scoring and interpretation

The [main corpus](data/README.md) has **32 cases / 136 atomic claims**, eight cases
each for supported answers, subtle distortions, extrinsic facts and multi-passage
synthesis. All use original SQLite, PostgreSQL 18 or Python 3.13 prose. Contexts
have 3–4 passages of 300–1,200 characters, with related distractors. Source URLs,
versions, licenses, paragraph offsets, hashes and adaptations are [retained](data/sources/real-docs-v3.json).

Answers and gold are authored adaptations, **not naturally occurring RAGTruth
responses**. Human author sign-off is pending in the [gold workbook](data/real-docs-v3/gold-review.md).
The 20 dev / 12 test families share no input source document. Primary categories
are balanced, but verdict counts are not: 96 supported / 30 contradicted / 10 unsupported.

E2E F1 requires one-to-one claim alignment, correct verdict, literal quotes and a
complete evidence group. Missing, duplicate, wrong and malformed outputs count;
only the explicitly listed availability failures are excluded in the conditional view.
Verdict per-class P/R/F1 and macro-F1 include unmatched claims; citation gold-hit
rate is a strict span-overlap proxy, not semantic truth. Definitions and limitations
are in the [scoring contract](docs/scoring.md) and [conditional report](results/real-docs-v3/availability-adjusted/report.md).
No semantic-review-adjusted headline scores are used in this revision.

## Dev iteration and the test boundary

We analyzed the brief, designed source families and evidence requirements, added
validation/metrics, then compared all methods on dev. A disclosed reference audit
split independent assertions and restored omitted facts without changing inputs.
On the same corrected gold, dev automatic F1 was **0.150 / 0.471 / 0.667**.

One candidate added per-claim evidence completeness and explicit grounded arithmetic.
It fixed the arithmetic assertion but scored **0.663**, so the [predeclared rule](results/real-docs-v3/protocol.json)
retained compact-v1 and closed that experiment. The [freeze](results/real-docs-v3/test-freeze.json)
records code/data/configuration hashes before test. No labels or prompts changed
afterward. A 12-family paired interval does not establish superiority; the model,
provider load, annotation questions and scorer artifacts limit interpretation.

A later [dev-only refinement](docs/dev-refinement.md) compares two-stage extraction
and a focused single-call prompt. Neither improves aggregate dev F1; local arithmetic
and proof fixes are documented. Test results and the production default stay unchanged.

The earlier synthetic held-out F1s were **0.750 / 1.000 / 0.964** (automatic and
reviewed identical), using Astra rather than Sol. Different data and models make
this a historical comparison, not a controlled accuracy change. [History](docs/experiments.md)
and [old data](data/revisions/cases-synthetic-v3.jsonl) remain available. The separate
`challenge-v1` test is still unused; v2 and v3 have no held-out evaluation.

## API and validation

`POST /verify` accepts `context_passages` and `generated_answer`. It returns atomic
`claim_text`, `verdict`, `reasoning` and `citations: [{index, quote}]` records.
Nonempty citations are required for supported/contradicted claims; unsupported
claims have none. Quote copying/validation, bounded repair and deadlines are code
responsibilities. OpenAPI is at `/docs`; `/health` identifies the method.

Errors use `{"error":{"code":"...","message":"..."}}`: 422 invalid request,
503 missing configuration, 502 invalid/upstream output, 504 timeout. Empty answers
skip inference. The historical assignment WAL [request](results/acceptance/sqlite-wal/request.json)
and [real response](results/acceptance/sqlite-wal/response.json) remain a separate HTTP smoke check.
The revision's [localhost checks](results/real-docs-v3/acceptance/http-checks.json) use no new model calls.

```bash
pytest -q
ruff check .
ruff format --check .
python -m grounding.dataset data/cases.jsonl
# Recompute both conditional views without inference:
python scripts/summarize_availability.py --run results/real-docs-v3/test \
  --out results/local/v3-availability
```

[CI](.github/workflows/ci.yml) runs tests, lint, formatting and a no-key dev baseline.
[Requirements mapping](docs/assignment-coverage.md), [architecture](docs/design.md),
[development process](docs/development-process.md) and [verification receipt](results/real-docs-v3/verification.json)
make the analysis → design → implementation → evaluation → delivery sequence inspectable.
Implementation and documentation used Codex assistance. No independent human
adjudication is claimed; pending label review and known limitations are part of the delivery.
