# Design and acceptance criteria

> Historical record through the earlier submission. The real-document revision,
> current evaluation and remaining review limits are in [the v3 report](real-docs-v3.md).

## Objective

Build a reproducible verifier for claims grounded in supplied passages. Separate
the guarantees code can enforce from the semantic quality experiments must
measure. The [assignment](https://gist.github.com/wsxiaoys/849522ee389e0ce359ef444653084484)
defines the contract and comparison; the [requirements map](assignment-coverage.md)
links each deliverable to its evidence.

## Decisions before implementation

These choices were recorded in the [initial design commit](https://github.com/zxingchen77/citation-grounding-verifier/commit/25e9b3c)
before the service implementation. The later compact candidate and v2 refinement
were selected through the [development experiments](development-process.md).

1. Use Python 3.12 and a small typed HTTP service. Keep model access replaceable.
2. Treat all model outputs and input passages as untrusted data. Validate every
   response before returning success. An exact quote is necessary but is not proof
   of semantic entailment.
3. Preserve numbers, negations, scope, and conditions when extracting claims.
4. Separate provider failures from UNSUPPORTED. Bound input size, time, and retries.
5. Start with a deterministic baseline and a single-call LLM using the same output
   contract. Add complexity only to address observed failures.
6. Build 40 original, explicitly synthetic technical cases: 24 development cases
   and 16 held-out cases. Split by scenario family, not random answer variants.
7. Score end-to-end claim precision/recall and report missed claims, label errors,
   citation validity, evidence sufficiency, latency, token usage, and failures.
8. Record model/configuration, data hash, prompt version, and code revision per run.
   Report unknown costs as unknown, not zero. Include all repair calls.

## Service flow and responsibilities

| Layer | Responsibility | Implementation |
| --- | --- | --- |
| HTTP and contracts | Accept the request, enforce strict field types, and return structured errors | [api.py](../src/grounding/api.py), [models.py](../src/grounding/models.py) |
| Verification strategies | Select deterministic, minimal, staged, compact-v1 or compact-v2 behavior; bound repairs and the request deadline | [verifiers.py](../src/grounding/verifiers.py) |
| Model adapters | Isolate inference transport, call timeout, cancellation, usage and safe traces | [provider.py](../src/grounding/provider.py), [codex_provider.py](../src/grounding/codex_provider.py) |
| Evaluation | Schedule comparable runs; score atomic coverage, labels and sufficient evidence; retain failures and paired uncertainty | [benchmark.py](../src/grounding/benchmark.py), [scoring.py](../src/grounding/scoring.py), [experiment.py](../src/grounding/experiment.py) |
| Reproduction and acceptance | Lock dependencies and exercise the HTTP boundary, model failure paths and artifact integrity | [requirements.lock](../requirements.lock), [tests](../tests/), [HTTP probes](../scripts/smoke_http.py), [CI](../.github/workflows/ci.yml) |

The evaluator invokes the verifier layer directly for quality measurements.
Separate HTTP probes verify the network/service boundary. They answer different
questions and have separate receipts. Within the compact strategies, the request
follows this path:

```mermaid
flowchart LR
    A[POST /verify] --> B[Validate input]
    B --> C[Split source into evidence segments]
    C --> D[Model: atomic claims, verdicts, evidence IDs]
    D --> E[Resolve IDs to original quotes]
    E --> F[Validate schema and exact substrings]
    F --> G[Return verification report]
    F -->|Invalid output: at most one repair| D
    D -->|Provider failure or deadline| H[Explicit HTTP error]
    F -->|Still invalid after repair| H
```

This diagram describes both compact versions. V2 changes the instruction to
include a complete justification in each claim's own citations; segmentation,
evidence resolution, validation and repair limits are shared with v1.

Evidence IDs remove quote transcription from the model's responsibilities. They
do not prove that the selected evidence entails a claim; semantic correctness and
atomic coverage still require evaluation. No retrieval system, database or agent
orchestration is needed for the supplied-context task. The staged alternative is
kept available to test whether its additional calls are justified.

## Acceptance gates

- The HTTP contract and citation invariants hold for every successful response.
- Empty context, non-factual answers, malformed outputs and upstream errors are tested.
- All three implementations run through one benchmark runner.
- Dataset labels, split, and scoring rules are independently reviewable.
- Real model results are kept separate from mocked integration tests.
- A clean checkout can install dependencies, run tests and start the service.
- README contains the results and limitations of the actual submitted version.

## Evaluation integrity

Freeze the final test set before prompt iteration. Run development experiments
first. One-to-one claim matching counts missing claims as false negatives and
duplicates as false positives. Ambiguous alignments need an explicit review file.
Inspecting final-test failures for another improvement makes that set development
material; disclose it and obtain fresh independent validation.

## Public repository scope

Publish code, original examples, decisions, test evidence and experiment summaries.
Keep credentials, recruiting correspondence and unrelated personal files out.
