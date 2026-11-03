# Per-round and paired report

Counts below are requests; repeated outputs are not new independent cases.

| Round | Method | Unique cases | TP / FP / FN | F1 | Coverage | Quote validity | Evidence sufficiency | Errors | Median / P95 s | Input / output / cached tokens | Calls / repairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | deterministic | 12 | 5 / 32 / 46 | 0.114 | 0.569 | 1.000 | 0.120 | 0 | 0.001 / 0.001 | 0 / 0 / 0 | 0 / None |
| 0 | minimal | 12 | 18 / 21 / 33 | 0.400 | 0.608 | 1.000 | 0.567 | 3 | 15.972 / 90.026 | 113055 / 3438 / 8448 | 12 / 0 |
| 0 | optimized | 12 | 22 / 18 / 29 | 0.484 | 0.588 | 1.000 | 0.724 | 3 | 13.144 / 90.028 | 104900 / 2255 / 25344 | 12 / 0 |

Evidence sufficiency is diagnostic among aligned evidence-required gold claims; it does not replace verdict correctness or literal validation. Token sums include known usage only; missing usage/cache counts are in rounds.json.

Small synthetic samples; intervals describe sampled cluster heterogeneity. Repeated model outputs are kept within clusters, not independent new cases. Cache state, service load and backend overhead are uncontrolled. A single deterministic round is paired only with the corresponding model round.

- minimal minus deterministic: 12 cases, 12 family clusters, paired rounds [0]; F1 difference 0.286, 95% percentile interval [0.10833088235294121, 0.44959041851829945].
- optimized minus deterministic: 12 cases, 12 family clusters, paired rounds [0]; F1 difference 0.370, 95% percentile interval [0.13820437342304456, 0.5720725831441476].
- optimized minus minimal: 12 cases, 12 family clusters, paired rounds [0]; F1 difference 0.084, 95% percentile interval [-0.11840023712737127, 0.26260822850291893].
