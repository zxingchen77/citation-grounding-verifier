# Benchmark report

Scores with review flags are provisional.

| Method | Requests | P | R | F1 | Errors | Review flags | Median seconds | USD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| compact-v5 | 20 | 0.684 | 0.635 | 0.659 | 2 | 20 | 11.908 | unknown |

## Verdict and citation diagnostics

All gold and predicted claims count; missing claims and failed requests are not excluded.
Zero denominators give 0 for class P/R/F1; macro averages all three classes.
Gold-hit rate: a literal citation contains a full gold span of its aligned claim.
It is a strict overlap diagnostic, not a semantic citation-accuracy oracle.

| Method | Verdict macro F1 | Literal quote validity | Gold-span hit rate |
| --- | --- | --- | --- |
| compact-v5 | 0.708 | 1.000 | 0.598 |

| Method | Verdict | TP / FP / FN | P | R | F1 |
| --- | --- | --- | --- | --- | --- |
| compact-v5 | SUPPORTED | 44 / 13 / 17 | 0.772 | 0.721 | 0.746 |
| compact-v5 | CONTRADICTED | 14 / 4 / 4 | 0.778 | 0.778 | 0.778 |
| compact-v5 | UNSUPPORTED | 3 / 1 / 3 | 0.750 | 0.500 | 0.600 |

See summary.json for counts, category slices, alignments, and citation checks.
Dollar estimates exclude infrastructure and ignore provider-specific cache discounts.
Unknown usage or prices are not reported as zero cost.
