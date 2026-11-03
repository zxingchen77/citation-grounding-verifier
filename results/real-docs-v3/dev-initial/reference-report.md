# Benchmark report

Scores with review flags are provisional.

| Method | Requests | P | R | F1 | Errors | Review flags | Median seconds | USD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deterministic | 20 | 0.177 | 0.129 | 0.150 | 0 | 20 | 0.001 | 0.000 |
| minimal | 20 | 0.471 | 0.471 | 0.471 | 0 | 20 | 12.806 | unknown |
| optimized | 20 | 0.652 | 0.682 | 0.667 | 0 | 20 | 13.269 | unknown |

## Verdict and citation diagnostics

All gold and predicted claims count; missing claims and failed requests are not excluded.
Zero denominators give 0 for class P/R/F1; macro averages all three classes.
Gold-hit rate: a literal citation contains a full gold span of its aligned claim.
It is a strict overlap diagnostic, not a semantic citation-accuracy oracle.

| Method | Verdict macro F1 | Literal quote validity | Gold-span hit rate |
| --- | --- | --- | --- |
| deterministic | 0.115 | 1.000 | 0.769 |
| minimal | 0.759 | 1.000 | 0.590 |
| optimized | 0.732 | 1.000 | 0.655 |

| Method | Verdict | TP / FP / FN | P | R | F1 |
| --- | --- | --- | --- | --- | --- |
| deterministic | SUPPORTED | 7 / 2 / 54 | 0.778 | 0.115 | 0.200 |
| deterministic | CONTRADICTED | 0 / 4 / 18 | 0.000 | 0.000 | 0.000 |
| deterministic | UNSUPPORTED | 4 / 45 / 2 | 0.082 | 0.667 | 0.145 |
| minimal | SUPPORTED | 49 / 10 / 12 | 0.831 | 0.803 | 0.817 |
| minimal | CONTRADICTED | 16 / 2 / 2 | 0.889 | 0.889 | 0.889 |
| minimal | UNSUPPORTED | 4 / 4 / 2 | 0.500 | 0.667 | 0.571 |
| optimized | SUPPORTED | 51 / 11 / 10 | 0.823 | 0.836 | 0.829 |
| optimized | CONTRADICTED | 15 / 3 / 3 | 0.833 | 0.833 | 0.833 |
| optimized | UNSUPPORTED | 4 / 5 / 2 | 0.444 | 0.667 | 0.533 |

See reference-summary.json for counts, category slices, alignments, and citation checks.
Dollar estimates exclude infrastructure and ignore provider-specific cache discounts.
Unknown usage or prices are not reported as zero cost.
