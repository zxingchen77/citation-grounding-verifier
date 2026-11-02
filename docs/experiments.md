# Experiment log

## 2026-11-02 — Initial design

**Question:** How do we distinguish a working API from a trustworthy verifier?

**Decision:** Enforce output invariants in code and evaluate claim coverage,
judgments, and evidence separately. Freeze a development/test split before tuning.

**Evidence:** The assignment requires exact quote validation and three comparable
approaches. Its examples also require splitting multiple facts from one sentence.

**Next:** Build the HTTP contract and deterministic baseline; author the labeled
dataset; collect the first real model baseline before selecting optimizations.

No quality, latency or dollar-cost result has been measured at this point.
