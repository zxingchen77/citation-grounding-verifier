# Citation Grounding Verifier

An HTTP service that decomposes an answer into factual claims, verifies them
against supplied passages, and returns exact evidence quotes.

**Status: implementation in progress. No model benchmark results are claimed yet.**

The work compares a deterministic baseline, a minimally prompted LLM, and an
optimized verifier. The benchmark measures claim coverage as well as verdict
and citation correctness, so dropping difficult claims cannot improve the result.

## Development record

- [Design and acceptance criteria](docs/design.md)
- [Experiment log](docs/experiments.md)

Each meaningful change is committed with its tests and evidence. Model results
will be added only after real runs; offline tests are not model evaluations.
