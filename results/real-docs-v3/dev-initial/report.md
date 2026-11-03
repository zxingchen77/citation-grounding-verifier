# Benchmark report

Scores with review flags are provisional.

| Method | Requests | P | R | F1 | Errors | Review flags | Median seconds | USD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deterministic | 20 | 0.177 | 0.139 | 0.156 | 0 | 20 | 0.001 | 0.000 |
| minimal | 20 | 0.459 | 0.494 | 0.476 | 0 | 20 | 12.806 | unknown |
| optimized | 20 | 0.629 | 0.709 | 0.667 | 0 | 20 | 13.269 | unknown |

## Verdict and citation diagnostics

All gold and predicted claims count; missing claims and failed requests are not excluded.
Zero denominators give 0 for class P/R/F1; macro averages all three classes.
Gold-hit rate: a literal citation contains a full gold span of its aligned claim.
It is a strict overlap diagnostic, not a semantic citation-accuracy oracle.

| Method | Verdict macro F1 | Literal quote validity | Gold-span hit rate |
| --- | --- | --- | --- |
| deterministic | 0.121 | 1.000 | 0.769 |
| minimal | 0.774 | 1.000 | 0.578 |
| optimized | 0.734 | 1.000 | 0.627 |

| Method | Verdict | TP / FP / FN | P | R | F1 |
| --- | --- | --- | --- | --- | --- |
| deterministic | SUPPORTED | 7 / 2 / 49 | 0.778 | 0.125 | 0.215 |
| deterministic | CONTRADICTED | 0 / 4 / 18 | 0.000 | 0.000 | 0.000 |
| deterministic | UNSUPPORTED | 4 / 45 / 1 | 0.082 | 0.800 | 0.148 |
| minimal | SUPPORTED | 47 / 12 / 9 | 0.797 | 0.839 | 0.817 |
| minimal | CONTRADICTED | 16 / 2 / 2 | 0.889 | 0.889 | 0.889 |
| minimal | UNSUPPORTED | 4 / 4 / 1 | 0.500 | 0.800 | 0.615 |
| optimized | SUPPORTED | 47 / 15 / 9 | 0.758 | 0.839 | 0.797 |
| optimized | CONTRADICTED | 15 / 3 / 3 | 0.833 | 0.833 | 0.833 |
| optimized | UNSUPPORTED | 4 / 5 / 1 | 0.444 | 0.800 | 0.571 |

See summary.json for counts, category slices, alignments, and citation checks.
Dollar estimates exclude infrastructure and ignore provider-specific cache discounts.
Unknown usage or prices are not reported as zero cost.
