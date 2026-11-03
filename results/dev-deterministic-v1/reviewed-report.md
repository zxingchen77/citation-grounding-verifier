# Benchmark report: automatic and reviewed scores

Review: **author self-review (AI-assisted)**. Automatic scores are retained alongside
reviewed scores; independent human adjudication is not claimed.

| Method | Requests | Automatic P / R / F1 | Reviewed P / R / F1 | Errors | Review flags | Median seconds | Model USD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deterministic | 24 | 0.738 / 0.738 / 0.738 | 0.738 / 0.705 / 0.721 | 0 | 0 | 0.000 | 0.000 |

Automatic scores use the original v1 references (42 dev claims); reviewed scores
use corrected v2 references (44 dev claims). The reference correction is separate
from output review and is not a model improvement.

See [automatic scores](summary.json), [reviewed scores](reviewed-summary.json),
[review decisions](reviews.json), and [provenance](review-provenance.json) for
counts, categories, alignments and evidence checks. Errors and latency are unchanged.
Dollar estimates exclude infrastructure and provider-specific cache discounts.
Unknown usage or prices are not reported as zero cost.
