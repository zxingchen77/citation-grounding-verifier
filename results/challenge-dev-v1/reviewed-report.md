# Benchmark report: automatic and reviewed scores

Review: **author self-review (AI-assisted)**. Automatic scores are retained alongside
reviewed scores; independent human adjudication is not claimed.

| Method | Requests | Automatic P / R / F1 | Reviewed P / R / F1 | Errors | Review flags | Median seconds | Model USD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deterministic | 12 | 0.325 / 0.260 / 0.289 | 0.325 / 0.260 / 0.289 | 0 | 0 | 0.001 | 0.000 |
| minimal | 24 | 0.906 / 0.290 / 0.439 | 0.875 / 0.280 / 0.424 | 16 | 0 | 90.016 | unknown |
| optimized | 24 | 0.756 / 0.340 / 0.469 | 0.822 / 0.370 / 0.510 | 13 | 0 | 90.014 | unknown |

Automatic scores use the initial challenge references; reviewed scores also include
the reference-only evidence correction described in [the audit](scoring-audit.json).
These changes are not credited as a model improvement.

See [automatic scores](summary.json), [reviewed scores](reviewed-summary.json),
[review decisions](reviews.json), and [provenance](review-provenance.json) for
counts, categories, alignments and evidence checks. Errors and latency are unchanged.
Dollar estimates exclude infrastructure and provider-specific cache discounts.
Unknown usage or prices are not reported as zero cost.
