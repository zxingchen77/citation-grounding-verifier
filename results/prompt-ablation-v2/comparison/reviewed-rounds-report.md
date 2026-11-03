# Per-round and paired report

Review: **author self-review (AI-assisted)**. Quality columns show automatic → reviewed;
see [automatic rounds](rounds.json), [reviewed rounds](reviewed-rounds.json), and
[reference/review provenance](review-provenance.json). No quantitative artifacts were changed.

Counts below are requests; repeated outputs are not new independent cases.

| Round | Method | Unique cases | TP / FP / FN (auto → reviewed) | F1 (auto → reviewed) | Coverage (auto → reviewed) | Quote validity (auto → reviewed) | Evidence sufficiency (auto → reviewed) | Errors | Median / P95 s | Input / output / cached tokens | Calls / repairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | optimized | 12 | 41 / 10 / 9 → 42 / 9 / 8 | 0.812 → 0.832 | 1.000 → 1.000 | 1.000 → 1.000 | 0.763 → 0.789 | 0 | 12.258 / 15.014 | 134761 / 2519 / 8448 | 12 / 0 |
| 0 | optimized-v2 | 12 | 48 / 2 / 2 → 50 / 0 / 0 | 0.960 → 1.000 | 1.000 → 1.000 | 1.000 → 1.000 | 0.947 → 1.000 | 0 | 11.365 / 17.934 | 137347 / 2742 / 16896 | 12 / 0 |

Evidence sufficiency is diagnostic among aligned evidence-required gold claims; it does not replace verdict correctness or literal validation. Token sums include known usage only; missing usage/cache counts are in rounds.json.

Small synthetic samples; intervals describe sampled cluster heterogeneity. Repeated model outputs are kept within clusters, not independent new cases. Cache state, service load and backend overhead are uncontrolled. A single deterministic round is paired only with the corresponding model round.

- optimized-v2 minus optimized: 12 cases, 12 family clusters, paired rounds [0]; automatic F1 difference 0.148, 95% interval [0.039999999999999925, 0.2535499108734402]; reviewed F1 difference 0.168, 95% interval [0.08333333333333337, 0.26].
