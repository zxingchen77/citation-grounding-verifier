# Scoring contract

The unit is an atomic claim. Primary end-to-end precision is correct predictions
divided by all predictions; recall is correctly verified gold claims divided by all
gold claims. F1 uses their harmonic mean. A true positive needs a one-to-one
semantic match, the correct label, valid literal citations and sufficient evidence.
Every other prediction is a false positive; every gold claim not correctly verified
is a false negative. A wrong label therefore contributes both an FP and an FN.
Failed requests contribute all their gold claims as FNs and are counted separately.

The automatic aligner uses maximum-weight one-to-one matching with a declared
token-similarity threshold (0.65), rejecting changed numeric values and selected
logical qualifiers. This is a conservative heuristic, not a semantic oracle.
Exact normalized matches need no lexical alignment review. Other matches and
unmatched predictions are flagged. All alignment details are saved.

Evidence is automatically credited if literal citations cover a complete allowed
reference evidence group. A shorter but sufficient quote may require explicit
review. Review records can replace alignment and evidence sufficiency, but cannot
override literal quote validation or verdict correctness. Review records must be
one-to-one, include a rationale and be retained. AI-assisted review must be labeled
as such; independent human review is not implied.

Matched-claim label Macro F1 is diagnostic only. Primary recall and F1 always
include missed claims. Report raw counts alongside all rates. The false-support
rate uses non-supported gold claims as its denominator and is presented alongside
coverage and request failures.

Final-test results are not used to select prompts. Synthetic short English cases
do not establish production accuracy. Cost estimates require explicit prices and
known token usage. Codex subscription usage is reported in tokens and calls rather
than as a purported API invoice.
