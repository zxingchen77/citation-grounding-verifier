# Challenge v1 — development extension

This separate, original synthetic corpus contains 24 cases in 24 scenario
families: 12 development cases / 50 atomic claims and 12 test cases / 53 claims.
Every answer contains all three labels; the corpus totals 52 SUPPORTED,
26 CONTRADICTED and 25 UNSUPPORTED claims. Answers contain 4–6 atomic claims.
Context lengths are 624–832 characters (median 705.5), in three natural paragraphs.
The original 40-case corpus and historical predictions and scores remain unchanged.

These are invented technical and operational scenarios, not factual claims about
real products or institutions. Review is **author self-review (AI-assisted)**;
pre-inference reference checks identified evidence coverage issues and corrected
them before the first development run. Independent human annotation is not claimed.
The test split remains unused and requires a separate decision before inference.
Reuse is granted under CC0-1.0.

Reference revision 2 retains the initial corpus in `revisions/`. A subsequent
evidence audit added the missing Beacon/Osprey entity definitions to three
development evidence groups and accepted a self-contained alternative for HX-2's
acknowledgment order. No model input, claim text, verdict, split or held-out record
changed. Rescoring explicitly separates this reference correction from model
performance; it is not a prompt improvement.

Each record contains `family`, `split`, a primary `category`, overlapping
`capabilities`, and explicit `logical_semantics`. Each gold claim has a rationale
and a complete evidence group, or no evidence for UNSUPPORTED. Evidence groups
may span multiple passages. The model receives only passages and the answer;
reference labels, rationales, capability tags and semantic notes are not inputs.

| Capability | Development cases | Test cases |
| --- | --- | --- |
| Conditions and exceptions | 6 | 6 |
| Scope and negation | 9 | 10 |
| Exact configuration | 2 | 2 |
| Logical bounds | 3 | 3 |
| Non-exclusive facts | 2 | 2 |
| Paraphrase and coreference | 2 | 2 |
| Multiple premises | 6 | 7 |
| Related but insufficient distractors | 6 | 4 |

The distinction between an exact setting, a non-exclusive observation and a pure
bound is stated in the source itself. For example, observing one public port
does not exclude another; an expressly sole administrative port does. A bound of
12 entails a bound of 15 but does not establish a bound of 10. Conditions include
exceptions and differences between necessary and sufficient requirements.

Families never cross splits. The test includes different scenario mechanisms,
such as dated ownership transfers, survey denominators, course-set overlap and
transitive package dependencies. Shared reasoning capabilities are intentional;
the small, synthetic construction still limits generalization. All answers have
all three labels, so the corpus does not measure natural label prevalence or
single-label answer performance. The original corpus remains useful for those
different slices.

Development scenarios mostly describe technical workflows; held-out scenarios
also use operational domains. That deliberate domain change is part of this
authored challenge, not an estimate from a random production sample.

Build and inspect without model calls:

```bash
python scripts/build_challenge.py
python -m grounding.dataset data/challenge-v1/cases.jsonl
```

`manifest.json` records the data SHA-256, family allocation, categories, capability
coverage, label combinations, context lengths and claim counts. The builder is
the canonical authoring source; the JSONL is the benchmark input. Structural
validation checks literal evidence, request limits and split isolation, not
semantic truth. Rebuilding must not be used to silently change a frozen test set.

No challenge test model inference has been run. No further test run is scheduled;
a future challenge test requires a separate user decision.
