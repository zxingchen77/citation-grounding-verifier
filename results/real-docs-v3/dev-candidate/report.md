# Benchmark report

Scores with review flags are provisional.

| Method | Requests | P | R | F1 | Errors | Review flags | Median seconds | USD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| optimized-v3 | 20 | 0.655 | 0.671 | 0.663 | 0 | 20 | 14.416 | unknown |

## Verdict and citation diagnostics

All gold and predicted claims count; missing claims and failed requests are not excluded.
Zero denominators give 0 for class P/R/F1; macro averages all three classes.
Gold-hit rate: a literal citation contains a full gold span of its aligned claim.
It is a strict overlap diagnostic, not a semantic citation-accuracy oracle.

| Method | Verdict macro F1 | Literal quote validity | Gold-span hit rate |
| --- | --- | --- | --- |
| optimized-v3 | 0.690 | 1.000 | 0.520 |

| Method | Verdict | TP / FP / FN | P | R | F1 |
| --- | --- | --- | --- | --- | --- |
| optimized-v3 | SUPPORTED | 50 / 10 / 11 | 0.833 | 0.820 | 0.826 |
| optimized-v3 | CONTRADICTED | 13 / 4 / 5 | 0.765 | 0.722 | 0.743 |
| optimized-v3 | UNSUPPORTED | 4 / 6 / 2 | 0.400 | 0.667 | 0.500 |

See summary.json for counts, category slices, alignments, and citation checks.
Dollar estimates exclude infrastructure and ignore provider-specific cache discounts.
Unknown usage or prices are not reported as zero cost.
