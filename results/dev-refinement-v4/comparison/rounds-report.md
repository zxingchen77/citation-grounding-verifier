# Per-round and paired report

Counts below are requests; repeated outputs are not new independent cases.

| Round | Method | Unique cases | TP / FP / FN | F1 | Coverage | Quote validity | Evidence sufficiency | Errors | Median / P95 s | Input / output / cached tokens | Calls / repairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | optimized-v1 | 20 | 59 / 29 / 26 | 0.682 | 0.824 | 1.000 | 0.833 | 0 | 11.358 / 14.570 | 232832 / 4915 / 33792 | 20 / 0 |
| 0 | anchored-v4 | 20 | 53 / 34 / 32 | 0.616 | 0.753 | 1.000 | 0.814 | 0 | 23.028 / 28.305 | 458547 / 9221 / 41984 | 40 / None |

Evidence sufficiency is diagnostic among aligned evidence-required gold claims; it does not replace verdict correctness or literal validation. Token sums include known usage only; missing usage/cache counts are in rounds.json.

Small synthetic samples; intervals describe sampled cluster heterogeneity. Repeated model outputs are kept within clusters, not independent new cases. Cache state, service load and backend overhead are uncontrolled. A single deterministic round is paired only with the corresponding model round.

- anchored-v4 minus optimized-v1: 20 cases, 20 family clusters, paired rounds [0]; F1 difference -0.066, 95% percentile interval [-0.156505367464905, 0.03037100806641805].
