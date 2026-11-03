# Per-round and paired report

Counts below are requests; repeated outputs are not new independent cases.

| Round | Method | Unique cases | TP / FP / FN | F1 | Coverage | Quote validity | Evidence sufficiency | Errors | Median / P95 s | Input / output / cached tokens | Calls / repairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | deterministic | 20 | 11 / 51 / 74 | 0.150 | 0.482 | 1.000 | 0.270 | 0 | 0.001 / 0.001 | 0 / 0 / 0 | 0 / None |
| 0 | minimal | 20 | 40 / 45 / 45 | 0.471 | 0.824 | 1.000 | 0.545 | 0 | 12.806 / 16.689 | 224781 / 6800 / 25344 | 20 / 0 |
| 0 | optimized | 20 | 58 / 31 / 27 | 0.667 | 0.835 | 1.000 | 0.806 | 0 | 13.269 / 18.428 | 231232 / 5193 / 33792 | 20 / 0 |

Evidence sufficiency is diagnostic among aligned evidence-required gold claims; it does not replace verdict correctness or literal validation. Token sums include known usage only; missing usage/cache counts are in rounds.json.

Small synthetic samples; intervals describe sampled cluster heterogeneity. Repeated model outputs are kept within clusters, not independent new cases. Cache state, service load and backend overhead are uncontrolled. A single deterministic round is paired only with the corresponding model round.

- minimal minus deterministic: 20 cases, 20 family clusters, paired rounds [0]; F1 difference 0.321, 95% percentile interval [0.20340756290074957, 0.45079006016506].
- optimized minus deterministic: 20 cases, 20 family clusters, paired rounds [0]; F1 difference 0.517, 95% percentile interval [0.37620367384293557, 0.6638010149478573].
- optimized minus minimal: 20 cases, 20 family clusters, paired rounds [0]; F1 difference 0.196, 95% percentile interval [0.08095955283689453, 0.3176529834214295].
