# Citation Grounding Verifier

A Python HTTP service that splits an answer into atomic factual claims, checks
each against supplied passages, and returns exact evidence quotes. It compares a
deterministic baseline, a minimal single-call LLM, and an optimized evidence-ID
verifier. A two-stage candidate is retained as an experimental alternative.

**Latest development result (2026-11-03):** on the same 12 challenge dev cases
and `gpt-6.1-sol` model, the new `optimized-v2` evidence prompt raises reviewed
end-to-end F1 from **0.832 to 1.000** (42/50 to 50/50 gold claims correctly
verified). All 24 comparison requests succeeded. It fixes eight missing-premise
citations and one extra claim. All **68 local tests** pass. This is one small,
AI-reviewed development run; it does not establish 100% production accuracy.
No challenge test inference has been run. See the
[comparison, raw results and limitations](docs/prompt-ablation-v2.md).

The earlier Astra development run had 29 timeouts in 48 model calls; those
failures and the [stage 1 packet](docs/challenge-stage1.md) remain available.

**Historical results:** on the original 16-case held-out set, end-to-end F1 is **0.750 / 1.000 / 0.964**
for deterministic / minimal / optimized. The compact candidate uses fewer output
tokens but does not establish a quality improvement. The original delivery's 39
checks, clean-checkout reproduction and eight real-model HTTP checks passed.

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
export LLM_MODEL=gpt-6.1-sol     # must be available to your account
export LLM_TIMEOUT_SECONDS=90
export VERIFIER_TIMEOUT_SECONDS=240
export VERIFIER_METHOD=optimized-v2
uvicorn grounding.api:app --host 127.0.0.1 --port 8000
```

The Codex adapter uses `codex exec --output-schema` in a temporary directory,
ignores user configuration, disables tools/connectors and rejects observed tool
calls. It uses the CLI's existing sign-in without reading or exporting credentials.
It is a trusted-workstation adapter, not a public inference gateway. These real
benchmarks use Codex; the HTTP provider is covered by mocked transport tests.
The tested CLI version is `0.166.0-alpha.5.1`; older releases may lack required flags.
[`.env.example`](.env.example) lists configuration; files are not auto-loaded.

## How the approaches differ

| Method | Processing | Model calls per request |
| --- | --- | --- |
| `deterministic` | Punctuation splitting, lexical overlap, numeric/negation heuristics | 0 |
| `minimal` | One short prompt; model emits claims, labels and quotes | 1 |
| `optimized` | Model selects source-segment IDs; code copies the exact quotes | 1, at most 2 with repair |
| `optimized-v2` | Same evidence-ID path, with per-claim identity and premise completeness instructions | 1, at most 2 with repair |
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
  --dataset data/revisions/cases-v2.jsonl \
  --reviews results/dev-minimal-v1/reviews.json \
  --original-dataset data/revisions/cases-v1.jsonl
```

Runs save raw predictions, model traces, failures, latency, usage, data/source
hashes, parameters and Git revision. Review results are separate files and preserve
the original automatic scores. All model calls, including repairs, are counted.
No mock fallback is used by the benchmark runner.

## Evaluation report

### Self-contained evidence prompt comparison

One balanced round on the unchanged 12 challenge dev cases / 50 claims, using
the same `gpt-6.1-sol` configuration for both methods:

| Metric | `optimized` (v1) | `optimized-v2` |
| --- | --- | --- |
| Reviewed TP / FP / FN | 42 / 9 / 8 | 50 / 0 / 0 |
| End-to-end F1 | 0.832 | 1.000 |
| Sufficient evidence among 38 aligned evidence-required claims | 30 / 38 | 38 / 38 |
| Failed requests / repairs | 0 / 0 | 0 / 0 |
| Median / P95 seconds | 12.258 / 15.014 | 11.365 / 17.934 |
| Input / output tokens | 134,761 / 2,519 | 137,347 / 2,742 |

Both methods get all 50 aligned verdicts right. The improvement is in complete
citations and claim granularity. The family-bootstrap F1 difference is +0.168
with a 95% interval [0.083, 0.260]; this describes these development families,
not unseen accuracy. V2 uses more input and output tokens. Its paired mean
latency difference is +0.151 seconds with an interval spanning zero, so there
is no established speed or cost saving. Subscription dollar cost is unknown.

Use `VERIFIER_METHOD=optimized-v2` to try the selected dev candidate. The existing
`optimized` name retains v1 for reproducibility. Reviews are by the implementing
AI chat, not independent human review. The automatic scores, all review decisions,
source/data hashes and full raw outputs are in the
[experiment packet](docs/prompt-ablation-v2.md). The earlier Astra timeouts have
not been causally explained by this successful Sol run.

### Earlier challenge development revision (Astra)

The [new challenge corpus](data/challenge-v1/README.md) has 12 dev cases / 50
claims and 12 held-out cases / 53 claims, with disjoint families. It preserves the
original corpus. All new answers mix SUPPORTED, CONTRADICTED and UNSUPPORTED
claims; this authored distribution is not natural label prevalence.

| Method | Round 0 F1 | Round 1 F1 | Pooled TP / FP / FN | Pooled F1 | Failed requests |
| --- | --- | --- | --- | --- | --- |
| Deterministic | 0.289 | — | 13 / 27 / 37 | 0.289 | 0 / 12 |
| Minimal | 0.486 | 0.355 | 28 / 4 / 72 | 0.424 | 16 / 24 |
| Optimized | 0.394 | 0.608 | 37 / 8 / 63 | 0.510 | 13 / 24 |

Each method covers 12 unique cases. LLM repetitions are retained within those
cases, not counted as new independent examples. The paired family-bootstrap 95%
interval for optimized minus minimal F1 is **[-0.110, +0.305]**, around +0.086.
Both pooled median latencies are about 90 seconds, dominated by timeouts. Token
sums are incomplete because failed calls have unknown usage; no speedup or cost
saving is established. [Raw predictions](results/challenge-dev-v1/predictions.jsonl),
[rounds](results/challenge-dev-v1/reviewed-rounds-report.md),
[paired records](results/challenge-dev-v1/reviewed-paired.json) and
[scoring/reference corrections](results/challenge-dev-v1/scoring-audit.json)
are retained. The two prompts are unchanged.

Minimal remains the conservative serving recommendation for simplicity under
inconclusive evidence; this is not a claim that it won the pooled dev score.
Actual localhost model acceptance passed 7/8 checks, with one upstream timeout.
Two separate, predeclared dev availability probes also timed out at 180 seconds.
An additional bounded diagnostic used the same two probes with `gpt-6.1-sol`;
both completed, in 9.794 and 14.134 seconds. These two calls establish observed
availability only, not stable reliability or a quality comparison. The
[alternative-model protocol and outputs](results/availability-alternative-v1/)
are retained separately from the development benchmark.
The final-test runtime/deadline therefore remains **unapproved pending review and
backend availability**. Direct external HTTP model acceptance is still unverified
because no existing HTTP credentials were configured. No challenge test model
inference has been performed.

### Original corpus protocol

Runs on 2026-11-02 use `gpt-6-astra` through Codex, Python 3.12.2, concurrency 1,
one pass per method, no response cache, 90-second model and 240-second request
deadlines. Methods run sequentially in the same order; provider prefix caching is
uncontrolled. Results include all requests and repairs. Explicit review records
are AI-assisted, not independent human adjudication.

### Development comparison

Dataset v3: 24 cases, 44 atomic claims. No unresolved alignment-review flags.

| Method | Correct / gold | Precision | Recall | End-to-end F1 | Median seconds | Model calls |
| --- | --- | --- | --- | --- | --- | --- |
| Deterministic | 31 / 44 | 0.738 | 0.705 | 0.721 | <0.001 | 0 |
| Minimal LLM | 43 / 44 | 1.000 | 0.977 | 0.989 | 10.967 | 24 |
| Optimized LLM | 44 / 44 | 1.000 | 1.000 | 1.000 | 9.589 | 24 |

All requests succeeded and all emitted quotes were literal substrings. The
minimal model combined two Birch assertions into one output item; compact split
both. The first minimal run had split both too, so this small observed difference
does not establish a stable accuracy improvement.

| Model method | Input tokens | Cached input tokens | Output tokens |
| --- | --- | --- | --- |
| Minimal | 259,704 | 109,824 | 2,773 |
| Optimized | 261,832 | 91,520 | 2,226 |

The optimized method generated about 20% fewer output tokens while input tokens
increased about 0.8%. Total token volume increased slightly. It was selected for
observed quality retention, fewer generated quotes and one-call complexity;
there is no demonstrated overall dollar saving or statistically reliable speedup.

### Held-out test

The unchanged 16-case / 28-claim test split was evaluated after selection in
commit `f7780b19c9d724371dc99e96bb67af2f8608ee6c`. No prompts, verifier logic or
reference labels were changed after inspecting test outputs.

| Method | Correct / gold | Precision | Recall | End-to-end F1 | Median seconds | P95 seconds | Model calls |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Deterministic | 21 / 28 | 0.750 | 0.750 | 0.750 | <0.001 | <0.001 | 0 |
| Minimal LLM | 28 / 28 | 1.000 | 1.000 | 1.000 | 10.183 | 14.679 | 16 |
| Optimized LLM | 27 / 28 | 0.964 | 0.964 | 0.964 | 8.765 | 11.442 | 16 |

P95 uses nearest rank; with only 16 requests it equals the maximum. All 48
requests succeeded with no repairs. All emitted quotes were valid (19/19,
24/24 and 23/23 respectively). The baseline wrongly supported 3 of 16
non-supported gold claims; neither model method produced a false-supported label.
There are no unresolved automatic alignment/evidence-review flags. The semantic
annotation ambiguity below remains a limitation of the frozen references.

| Category | Cases / gold claims | Deterministic F1 | Minimal F1 | Optimized F1 |
| --- | --- | --- | --- | --- |
| Supported | 4 / 8 | 1.000 | 1.000 | 1.000 |
| Distortion | 4 / 8 | 0.625 | 1.000 | 0.875 |
| Extrinsic | 4 / 8 | 1.000 | 1.000 | 1.000 |
| Multi-passage | 4 / 4 | 0.000 | 1.000 | 1.000 |

| Model method | Input tokens | Cached input tokens | Output tokens |
| --- | --- | --- | --- |
| Minimal | 173,157 | 92,928 | 1,831 |
| Optimized | 174,573 | 58,240 | 1,460 |

The optimized candidate generated 20.3% fewer output tokens and had a lower
observed median, with slightly higher total token volume. Different cache hits,
fixed method ordering and one run prevent a reliable causal latency conclusion.

**Scored failure: `quartz-tls-distortion`.** The source says the gateway listens
on port 7443; the answer says 7444. The frozen reference treats the port as a
single configured value and expects `CONTRADICTED`. Compact returned
`UNSUPPORTED`, explaining that listening on another port was not excluded. This
is a defensible reading of an underspecified source. We retain the original label
and count the mismatch; we do not repair the test label to improve the score.
The certificate-requirement claim in the same answer was correctly contradicted.

**Conclusion:** minimal achieves the highest frozen-reference score in this run.
The development-selected compact candidate trades fewer generated tokens for one
test-label mismatch; its quality superiority is unproven. Resolving exclusivity
annotations independently and repeating evaluation on fresh cases is the next
useful experiment. Both implementations remain selectable without changing code.

### Cost and artifacts

Token counts include CLI/framework overhead. Subscription monetary cost is
**unknown**, not zero. Optional HTTP API price inputs produce token-based
estimates, not invoices; infrastructure and cache discounts are excluded.

- [Final development predictions and reviewed scores](results/dev-v3/)
- [Held-out predictions, scores and review records](results/heldout-v1/)
- [Run index, original experiments and reference versions](results/README.md)
- [Real HTTP and clean-checkout acceptance](docs/acceptance.md)

### Failure analysis and iteration

| Observation | What changed or was learned |
| --- | --- |
| Lexical overlap approves “every plan” against an Enterprise-only source | Scope and action words need semantic judgment; real quotes can still support wrong verdicts. |
| A synthesis quote describes a policy but omits which system uses it | Scoring requires every necessary premise, not just a matching source sentence. |
| A contrast bundles two independent queue behaviors | Atomic-reference and one-to-one output rules expose granularity errors; the compact prompt explicitly preserves both assertions. |
| “At most 3” logically entails “at most 4” | Original development labels assumed exact configuration limits. Clarified six development inputs and reran all methods; old runs remain available. |
| Two-stage extraction and verification uses twice as many calls | The historical candidate used 48 calls without demonstrated compensating benefit; retain the simpler selected approach. |
| A test source states a port without saying it is exclusive | Compact returns UNSUPPORTED while the frozen label expects CONTRADICTED. Preserve the mismatch and disclose the annotation assumption. |

The [experiment log](docs/experiments.md) records hypotheses, observations and
decisions. The first reference correction split a compound gold claim without
changing inputs; the later wording correction changed development inputs and
therefore required fresh inference. Neither is counted as a model improvement.
All held-out examples remain unchanged from the original dataset.

## Limits and engineering record

These short, synthetic English cases do not establish production accuracy,
long-context retrieval, conflicting-source policy, multilingual quality, or robust
prompt-injection resistance. Sentence segmentation can give broader citations than
necessary. One run does not measure model variance; no independent human review
has been performed. Model/CLI versions and service load may affect reproduction.

- [Design, requirements and acceptance gates](docs/design.md)
- [Experiment log: questions, evidence, decisions and next steps](docs/experiments.md)
- [Acceptance evidence](docs/acceptance.md), [tests](tests/) and [GitHub Actions checks](.github/workflows/ci.yml)

Implementation and documentation were developed with Codex assistance. Commit
history and retained artifacts record the actual iterations. This repository is
the public deliverable requested by the
[assignment](https://gist.github.com/wsxiaoys/849522ee389e0ce359ef444653084484).
