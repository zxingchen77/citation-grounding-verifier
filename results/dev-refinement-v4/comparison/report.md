# Benchmark report

Scores with review flags are provisional.

| Method | Requests | P | R | F1 | Errors | Review flags | Median seconds | USD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| optimized-v1 | 20 | 0.670 | 0.694 | 0.682 | 0 | 20 | 11.358 | unknown |
| anchored-v4 | 20 | 0.609 | 0.624 | 0.616 | 0 | 20 | 23.028 | unknown |

## Verdict and citation diagnostics

All gold and predicted claims count; missing claims and failed requests are not excluded.
Zero denominators give 0 for class P/R/F1; macro averages all three classes.
Gold-hit rate: a literal citation contains a full gold span of its aligned claim.
It is a strict overlap diagnostic, not a semantic citation-accuracy oracle.

| Method | Verdict macro F1 | Literal quote validity | Gold-span hit rate |
| --- | --- | --- | --- |
| optimized-v1 | 0.739 | 1.000 | 0.655 |
| anchored-v4 | 0.720 | 1.000 | 0.500 |

| Method | Verdict | TP / FP / FN | P | R | F1 |
| --- | --- | --- | --- | --- | --- |
| optimized-v1 | SUPPORTED | 50 / 12 / 11 | 0.806 | 0.820 | 0.813 |
| optimized-v1 | CONTRADICTED | 15 / 3 / 3 | 0.833 | 0.833 | 0.833 |
| optimized-v1 | UNSUPPORTED | 4 / 4 / 2 | 0.500 | 0.667 | 0.571 |
| anchored-v4 | SUPPORTED | 44 / 13 / 17 | 0.772 | 0.721 | 0.746 |
| anchored-v4 | CONTRADICTED | 14 / 8 / 4 | 0.636 | 0.778 | 0.700 |
| anchored-v4 | UNSUPPORTED | 5 / 3 / 1 | 0.625 | 0.833 | 0.714 |

See summary.json for counts, category slices, alignments, and citation checks.
Dollar estimates exclude infrastructure and ignore provider-specific cache discounts.
Unknown usage or prices are not reported as zero cost.
