# Per-round and paired report

Counts below are requests; repeated outputs are not new independent cases.

| Round | Method | Unique cases | TP / FP / FN | F1 | Coverage | Quote validity | Evidence sufficiency | Errors | Median / P95 s | Input / output / cached tokens | Calls / repairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | deterministic | 12 | 13 / 27 / 37 | 0.289 | 0.800 | 1.000 | 0.241 | 0 | 0.001 / 0.001 | 0 / 0 / 0 | 0 / None |
| 0 | minimal | 12 | 17 / 3 / 33 | 0.486 | 0.400 | 1.000 | 0.800 | 7 | 90.014 / 90.026 | 54720 / 1590 / 25344 | 12 / 0 |
| 0 | optimized | 12 | 13 / 3 / 37 | 0.394 | 0.320 | 1.000 | 0.750 | 8 | 90.015 / 90.023 | 44653 / 826 / 33280 | 12 / 0 |
| 1 | optimized | 12 | 24 / 5 / 26 | 0.608 | 0.560 | 1.000 | 0.810 | 5 | 47.907 / 90.022 | 78149 / 1435 / 41600 | 12 / 0 |
| 1 | minimal | 12 | 11 / 1 / 39 | 0.355 | 0.240 | 1.000 | 0.889 | 9 | 90.019 / 90.029 | 32818 / 980 / 16896 | 12 / 0 |

Evidence sufficiency is diagnostic among aligned evidence-required gold claims; it does not replace verdict correctness or literal validation. Token sums include known usage only; missing usage/cache counts are in rounds.json.

Small synthetic samples; intervals describe sampled cluster heterogeneity. Repeated model outputs are kept within clusters, not independent new cases. Cache state, service load and backend overhead are uncontrolled. A single deterministic round is paired only with the corresponding model round.

- minimal minus deterministic: 12 cases, 12 family clusters, paired rounds [0]; F1 difference 0.197, 95% percentile interval [-0.08204518798114854, 0.44195656871218664].
- optimized minus deterministic: 12 cases, 12 family clusters, paired rounds [0]; F1 difference 0.105, 95% percentile interval [-0.1509995368616058, 0.30496044031647745].
- optimized minus minimal: 12 cases, 12 family clusters, paired rounds [0, 1]; F1 difference 0.086, 95% percentile interval [-0.109680272723751, 0.30514809902740925].
