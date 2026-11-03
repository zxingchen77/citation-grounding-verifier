# Benchmark report: automatic and reviewed scores

Review: **author self-review (AI-assisted)**. Automatic scores are retained alongside
reviewed scores; independent human adjudication is not claimed.

| Method | Requests | Automatic P / R / F1 | Reviewed P / R / F1 | Errors | Review flags | Median seconds | Model USD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deterministic | 16 | 0.750 / 0.750 / 0.750 | 0.750 / 0.750 / 0.750 | 0 | 0 | 0.000 | 0.000 |
| minimal | 16 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 | 0 | 0 | 10.183 | unknown |
| optimized | 16 | 0.964 / 0.964 / 0.964 | 0.964 / 0.964 / 0.964 | 0 | 0 | 8.765 | unknown |

See [automatic scores](summary.json), [reviewed scores](reviewed-summary.json),
[review decisions](reviews.json), and [provenance](review-provenance.json) for
counts, categories, alignments and evidence checks. Errors and latency are unchanged.
Dollar estimates exclude infrastructure and provider-specific cache discounts.
Unknown usage or prices are not reported as zero cost.
