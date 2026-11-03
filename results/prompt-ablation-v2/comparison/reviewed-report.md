# Benchmark report: automatic and reviewed scores

Review: **author self-review (AI-assisted)**. Automatic scores are retained alongside
reviewed scores; independent human adjudication is not claimed.

| Method | Requests | Automatic P / R / F1 | Reviewed P / R / F1 | Errors | Review flags | Median seconds | Model USD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| optimized | 12 | 0.804 / 0.820 / 0.812 | 0.824 / 0.840 / 0.832 | 0 | 0 | 12.258 | unknown |
| optimized-v2 | 12 | 0.960 / 0.960 / 0.960 | 1.000 / 1.000 / 1.000 | 0 | 0 | 11.365 | unknown |

See [automatic scores](summary.json), [reviewed scores](reviewed-summary.json),
[review decisions](reviews.json), and [provenance](review-provenance.json) for
counts, categories, alignments and evidence checks. Errors and latency are unchanged.
Dollar estimates exclude infrastructure and provider-specific cache discounts.
Unknown usage or prices are not reported as zero cost.
