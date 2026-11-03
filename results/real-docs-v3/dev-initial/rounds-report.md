# Per-round and paired report

Counts below are requests; repeated outputs are not new independent cases.

| Round | Method | Unique cases | TP / FP / FN | F1 | Coverage | Quote validity | Evidence sufficiency | Errors | Median / P95 s | Input / output / cached tokens | Calls / repairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | deterministic | 20 | 11 / 51 / 68 | 0.156 | 0.532 | 1.000 | 0.263 | 0 | 0.001 / 0.001 | 0 / 0 / 0 | 0 / None |
| 0 | minimal | 20 | 39 / 46 / 40 | 0.476 | 0.848 | 1.000 | 0.556 | 0 | 12.806 / 16.689 | 224781 / 6800 / 25344 | 20 / 0 |
| 0 | optimized | 20 | 56 / 33 / 23 | 0.667 | 0.835 | 1.000 | 0.839 | 0 | 13.269 / 18.428 | 231232 / 5193 / 33792 | 20 / 0 |

Evidence sufficiency is diagnostic among aligned evidence-required gold claims; it does not replace verdict correctness or literal validation. Token sums include known usage only; missing usage/cache counts are in rounds.json.

Small synthetic samples; intervals describe sampled cluster heterogeneity. Repeated model outputs are kept within clusters, not independent new cases. Cache state, service load and backend overhead are uncontrolled. A single deterministic round is paired only with the corresponding model round.

- minimal minus deterministic: 20 cases, 20 family clusters, paired rounds [0]; F1 difference 0.320, 95% percentile interval [0.20189526763825055, 0.44923857616446217].
- optimized minus deterministic: 20 cases, 20 family clusters, paired rounds [0]; F1 difference 0.511, 95% percentile interval [0.37961963992593134, 0.644316500806885].
- optimized minus minimal: 20 cases, 20 family clusters, paired rounds [0]; F1 difference 0.191, 95% percentile interval [0.08024929022414176, 0.31170222505970324].
