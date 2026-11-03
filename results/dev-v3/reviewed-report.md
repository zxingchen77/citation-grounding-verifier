# Benchmark report: automatic and reviewed scores

Review: **author self-review (AI-assisted)**. Automatic scores are retained alongside
reviewed scores; independent human adjudication is not claimed.

| Method | Requests | Automatic P / R / F1 | Reviewed P / R / F1 | Errors | Review flags | Median seconds | Model USD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deterministic | 24 | 0.738 / 0.705 / 0.721 | 0.738 / 0.705 / 0.721 | 0 | 0 | 0.000 | 0.000 |
| minimal | 24 | 1.000 / 0.977 / 0.989 | 1.000 / 0.977 / 0.989 | 0 | 0 | 10.967 | unknown |
| optimized | 24 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 | 0 | 0 | 9.589 | unknown |

See [automatic scores](summary.json), [reviewed scores](reviewed-summary.json),
[review decisions](reviews.json), and [provenance](review-provenance.json) for
counts, categories, alignments and evidence checks. Errors and latency are unchanged.
Dollar estimates exclude infrastructure and provider-specific cache discounts.
Unknown usage or prices are not reported as zero cost.
