# Scoring contract

The unit is an atomic claim. Primary end-to-end precision is correct predictions
divided by all predictions; recall is correctly verified gold claims divided by all
gold claims. F1 uses their harmonic mean. A true positive needs a one-to-one
semantic match, the correct label, valid literal citations and sufficient evidence.
Every other prediction is a false positive; every gold claim not correctly verified
is a false negative. A wrong label therefore contributes both an FP and an FN.
Failed requests contribute all their gold claims as FNs and are counted separately.

A compound prediction can receive credit for at most one contained reference
claim. Additional required atomic records remain unmatched, even if their words
appear inside the compound sentence. This measures the required atomic output
granularity; it is deliberately more forgiving than rejecting every compound
prediction outright. The Birch reviews demonstrate this rule for all methods.

The automatic aligner uses maximum-weight one-to-one matching with a declared
token-similarity threshold (0.65), rejecting changed numeric values and selected
logical qualifiers. This is a conservative heuristic, not a semantic oracle.
Exact normalized matches need no lexical alignment review. Other matches and
unmatched predictions are flagged. All alignment details are saved.

Evidence is automatically credited if literal citations cover a complete allowed
reference evidence group. Adjacent or overlapping citations from the same passage
may jointly cover a reference quote. The scorer locates exact quote occurrences
in the original source text and checks their original character intervals. Every
reference character except whitespace and semicolon separators must be covered.
It never removes characters before locating a quote, skips words, negation,
numbers, conditions or premises, or merges coverage across passages.
Literal citation validation still runs separately. This prevents sentence or
semicolon segmentation from systematically penalizing the evidence-ID method.
A shorter but sufficient quote may require explicit
review. Review records can replace alignment and evidence sufficiency, but cannot
override literal quote validation or verdict correctness. Review records must be
one-to-one, include a rationale and be retained. This project's review is labeled
**author self-review (AI-assisted)**; independent human review is not implied.
Reports display automatic scores alongside reviewed scores. A reference revision
must be identified separately from a review adjustment on unchanged labels.

Matched-claim label Macro F1 is diagnostic only. Primary recall and F1 always
include missed claims. Report raw counts alongside all rates. The false-support
rate uses non-supported gold claims as its denominator and is presented alongside
coverage and request failures.

Final-test results are not used to select prompts. Synthetic short English cases
do not establish production accuracy. Cost estimates require explicit prices and
known token usage. Codex subscription usage is reported in tokens and calls rather
than as a purported API invoice.

## Repeated paired experiments

`--order fixed` retains the original method-major execution order. With
`--order balanced --seed 1729`, cases are reproducibly shuffled and each round
cycles through a shuffled list of all permutations of the active methods. Every
complete factorial block balances positions and pairwise precedence. A partial
block is possible for other case counts and is visible in the saved schedule.
With 12 cases and three or two methods, each round is fully balanced. No response
cache is added; provider prefix caching remains uncontrolled.

The manifest stores the complete schedule, seed and configuration. Every raw
record contains an execution index, zero-based round (`repeat`), `pair_id`, and
start/end timestamps. An unsuccessful request remains in its pair. Duplicate
records and incomplete or changed saved schedules are rejected during rescoring.
`--deterministic-repeats 1` runs the baseline only in round 0; the default retains
the historical behavior of using `--repeats` for every method.

`summary.json` retains pooled counts for compatibility; its `cases` field counts
requests, while `unique_cases` counts independent case identities. `rounds.json`
and `rounds-report.md` give every round separately. Coverage, citation validity,
evidence sufficiency, raw TP/FP/FN, request failures, latency, token totals, missing
usage/cache counters, model calls and repair calls are reported. Evidence
sufficiency is a diagnostic among aligned evidence-required gold claims; it
does not replace literal validity or verdict correctness.

`paired.json` saves matched counts for each case and shared round. Differences
are right minus left. The paired percentile bootstrap samples entire scenario
families with replacement and retains all cases and repeated outputs inside each
drawn family. F1 is recomputed from pooled TP/FP/FN in every draw. Latency compares
the mean of each case's mean within-round difference. The default is 2,000 draws
with the recorded seed; `--cluster case` is available when appropriate.

Repeated outputs are never treated as independent new cases. A single baseline
round is compared only with the corresponding LLM round, and unpaired records are
counted explicitly. The 12-family challenge split yields limited uncertainty
estimates; intervals reflect sampled family heterogeneity and do not establish
population accuracy, future model variance or a causal speedup. AI-assisted
alignment/evidence reviews must be retained for every affected round.
