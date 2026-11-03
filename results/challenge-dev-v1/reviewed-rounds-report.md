# Per-round and paired report

Review: **author self-review (AI-assisted)**. Quality columns show automatic → reviewed;
see [automatic rounds](rounds.json), [reviewed rounds](reviewed-rounds.json), and
[reference/review provenance](review-provenance.json). No quantitative artifacts were changed.

Counts below are requests; repeated outputs are not new independent cases.

| Round | Method | Unique cases | TP / FP / FN (auto → reviewed) | F1 (auto → reviewed) | Coverage (auto → reviewed) | Quote validity (auto → reviewed) | Evidence sufficiency (auto → reviewed) | Errors | Median / P95 s | Input / output / cached tokens | Calls / repairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | deterministic | 12 | 13 / 27 / 37 → 13 / 27 / 37 | 0.289 → 0.289 | 0.720 → 0.800 | 1.000 → 1.000 | 0.269 → 0.241 | 0 | 0.001 / 0.001 | 0 / 0 / 0 | 0 / None |
| 0 | minimal | 12 | 17 / 3 / 33 → 17 / 3 / 33 | 0.486 → 0.486 | 0.400 → 0.400 | 1.000 → 1.000 | 0.800 → 0.800 | 7 | 90.014 / 90.026 | 54720 / 1590 / 25344 | 12 / 0 |
| 0 | optimized | 12 | 12 / 4 / 38 → 13 / 3 / 37 | 0.364 → 0.394 | 0.320 → 0.320 | 1.000 → 1.000 | 0.667 → 0.750 | 8 | 90.015 / 90.023 | 44653 / 826 / 33280 | 12 / 0 |
| 1 | optimized | 12 | 22 / 7 / 28 → 24 / 5 / 26 | 0.557 → 0.608 | 0.560 → 0.560 | 1.000 → 1.000 | 0.714 → 0.810 | 5 | 47.907 / 90.022 | 78149 / 1435 / 41600 | 12 / 0 |
| 1 | minimal | 12 | 12 / 0 / 38 → 11 / 1 / 39 | 0.387 → 0.355 | 0.240 → 0.240 | 1.000 → 1.000 | 1.000 → 0.889 | 9 | 90.019 / 90.029 | 32818 / 980 / 16896 | 12 / 0 |

Evidence sufficiency is diagnostic among aligned evidence-required gold claims; it does not replace verdict correctness or literal validation. Token sums include known usage only; missing usage/cache counts are in rounds.json.

Small synthetic samples; intervals describe sampled cluster heterogeneity. Repeated model outputs are kept within clusters, not independent new cases. Cache state, service load and backend overhead are uncontrolled. A single deterministic round is paired only with the corresponding model round.

- minimal minus deterministic: 12 cases, 12 family clusters, paired rounds [0]; automatic F1 difference 0.197, 95% interval [-0.07912239639300808, 0.42857702788457946]; reviewed F1 difference 0.197, 95% interval [-0.08204518798114854, 0.44195656871218664].
- optimized minus deterministic: 12 cases, 12 family clusters, paired rounds [0]; automatic F1 difference 0.075, 95% interval [-0.18765323928099817, 0.27679471667674926]; reviewed F1 difference 0.105, 95% interval [-0.1509995368616058, 0.30496044031647745].
- optimized minus minimal: 12 cases, 12 family clusters, paired rounds [0, 1]; automatic F1 difference 0.030, 95% interval [-0.18217106420154802, 0.26371415770609313]; reviewed F1 difference 0.086, 95% interval [-0.109680272723751, 0.30514809902740925].
