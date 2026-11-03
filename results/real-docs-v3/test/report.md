# Benchmark report

Scores with review flags are provisional.

| Method | Requests | P | R | F1 | Errors | Review flags | Median seconds | USD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deterministic | 12 | 0.135 | 0.098 | 0.114 | 0 | 12 | 0.001 | 0.000 |
| minimal | 12 | 0.462 | 0.353 | 0.400 | 3 | 12 | 15.972 | unknown |
| optimized | 12 | 0.550 | 0.431 | 0.484 | 3 | 12 | 13.144 | unknown |

## Verdict and citation diagnostics

All gold and predicted claims count; missing claims and failed requests are not excluded.
Zero denominators give 0 for class P/R/F1; macro averages all three classes.
Gold-hit rate: a literal citation contains a full gold span of its aligned claim.
It is a strict overlap diagnostic, not a semantic citation-accuracy oracle.

| Method | Verdict macro F1 | Literal quote validity | Gold-span hit rate |
| --- | --- | --- | --- |
| deterministic | 0.109 | 1.000 | 0.600 |
| minimal | 0.625 | 1.000 | 0.553 |
| optimized | 0.565 | 1.000 | 0.571 |

| Method | Verdict | TP / FP / FN | P | R | F1 |
| --- | --- | --- | --- | --- | --- |
| deterministic | SUPPORTED | 2 / 1 / 33 | 0.667 | 0.057 | 0.105 |
| deterministic | CONTRADICTED | 0 / 2 / 12 | 0.000 | 0.000 | 0.000 |
| deterministic | UNSUPPORTED | 4 / 28 / 0 | 0.125 | 1.000 | 0.222 |
| minimal | SUPPORTED | 19 / 6 / 16 | 0.760 | 0.543 | 0.633 |
| minimal | CONTRADICTED | 11 / 0 / 1 | 1.000 | 0.917 | 0.957 |
| minimal | UNSUPPORTED | 1 / 2 / 3 | 0.333 | 0.250 | 0.286 |
| optimized | SUPPORTED | 18 / 6 / 17 | 0.750 | 0.514 | 0.610 |
| optimized | CONTRADICTED | 10 / 2 / 2 | 0.833 | 0.833 | 0.833 |
| optimized | UNSUPPORTED | 1 / 3 / 3 | 0.250 | 0.250 | 0.250 |

See summary.json for counts, category slices, alignments, and citation checks.
Dollar estimates exclude infrastructure and ignore provider-specific cache discounts.
Unknown usage or prices are not reported as zero cost.
