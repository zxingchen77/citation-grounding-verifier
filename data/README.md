# Dataset

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
