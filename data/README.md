# Dataset

The original corpus below is preserved. The separate
[challenge-v1 review candidate](challenge-v1/README.md) adds 24 cases with mixed
labels, explicit logical semantics and annotation rationales. Its test inference
is gated on review; it does not replace or relabel the original results.

40 original synthetic technical specifications, with 72 labeled atomic claims.
These are invented product behaviors. They are not statements about real systems.
Cases and reference labels were authored with AI assistance. Source quote existence
and split integrity are tested automatically; independent human label review has
not been claimed. Reuse is granted under CC0-1.0.

The split is authored by scenario family: 24 development cases and 16 held-out
cases. Each split has equal counts of four primary categories. Variations of the
same specification remain together. `manifest.json` freezes the dataset hash.

Each gold claim has a verdict and zero or more alternative evidence groups.
For supported/contradicted claims, every quote in at least one group is required.
Alternative sufficient evidence can be approved in a transparent review record.
UNSUPPORTED has no evidence group. Some answers combine two facts with semicolons;
the baseline includes a simple punctuation-based clause splitter. Multi-passage cases require two linked premises
and contain a distractor passage.

Limitations: synthetic English cases are short and cleaner than production data.
They do not measure long-context retrieval, conflicting sources, or multilingual
performance. Results must not be extrapolated to those settings.

## Reference-label revision

Version 1 merged two Birch queue assertions into one reference claim: rejecting
new jobs and not deleting existing jobs. Inspecting development predictions exposed
this annotation error. Version 2 splits the compound claim in both variants. Only
development labels changed: all input passages/answers and all held-out cases are
byte-for-byte unchanged. Version 1 is retained in `revisions/`. Both baselines are
rescored from their saved predictions using the same revised references. This is a
label correction, not a model improvement.

## Development wording revision

Version 2's upper-bound wording was ambiguous: "at most 3 attempts" logically
implies "at most 4 attempts", even though a reader might interpret each number as
the exact configured maximum. Similarly, an upper bound of 64 alone does not prove
that 64 is achievable. Model disagreement exposed this problem.

Version 3 states exact configured limits for the Birch, Sable and Elm development
families. All six affected answers and their corresponding references are precise
about the parameter being compared. Original versions and runs remain available.
Because inputs changed, these cases require new inference, not rescoring old
outputs. All three required methods are rerun on the entire development split for
a fair comparison. All 16 held-out cases remain unchanged from version 1.

This clarifies the intended benchmark; it does not establish performance on
ambiguous upper-bound language. A future dataset should separately label exact
configuration values, logical bounds, and claims about observed values.
