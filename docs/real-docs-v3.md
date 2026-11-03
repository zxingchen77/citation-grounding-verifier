# Real-document revision: evaluation and failure analysis

## Problem and design

The earlier main corpus contained invented systems and very short contexts (mean
143.2 characters/case). Its 16-case held-out result was automatic/reviewed F1
0.750/0.750 for deterministic, 1.000/1.000 for minimal and 0.964/0.964 for compact-v1.
A perfect score alone does not prove that a dataset is easy. Here the synthetic
vocabulary, near-copy answers, short evidence and few claims together limited what
that result could demonstrate. Those files and results remain intact in the archive.

The new corpus uses 32 real-document cases, four categories with eight cases each,
and 136 atomic claims. There are 20 development families / 85 claims and 12 test
families / 51 claims. Each input has 3–4 passages of 300–1,200 characters, including
related distractors. Source documents are separated across splits; source retrieval,
licenses, edits and paragraph hashes are recorded. See [dataset construction](../data/README.md).

The design adds distinctions that word overlap cannot safely settle: boundary
versus exact value, binary versus decimal units, sufficient versus necessary
conditions, ordinary behavior versus exceptions, an external fact versus an
entailed fact, and a correct premise versus an invalid combined conclusion.
Mixed clauses require decomposition before the individual judgments can be useful.

The service architecture is intentionally unchanged: typed HTTP boundary,
method-specific inference, deterministic quote validation, explicit failures,
and an offline scorer. Real text should expose weaknesses in that architecture
before prompting changes are credited with improvements.

## Annotation and experimental discipline

Gold labels are **AI-drafted; human author review pending**. The single project
author has a [complete review workbook](../data/real-docs-v3/gold-review.md), but
no completed human or independent annotation is claimed. The answers are authored
adaptations of official prose, not actual RAGTruth responses or inherited human
labels. Test results are provisional with respect to this gold.

The [protocol](../results/real-docs-v3/protocol.json) predates inference. Use one
balanced-order pass on dev with the same model and timeouts for all methods;
allow at most one additional optimized candidate driven by recorded dev failures.
Selection uses automatic end-to-end F1 with no increase in failed requests, then
verdict macro F1, retaining compact-v1 on a primary-score tie. Semantic output
reviews explain score artifacts separately. No prompt is selected on test.

The first dev outputs exposed ambiguous gold granularity and omitted assertions.
A [reference audit](../data/real-docs-v3/annotation-audit.json) split compound references and restored omitted dev assertions across six cases before any test inference.
The original draft, inputs and initial scores remain available. All methods are
rescored on the same corrected references without rerunning inference. These are
annotation repairs, not a performance gain from changing the model. No existing
verdict, source passage, answer or split was changed.

The automatic aligner also rejects some equivalent wordings (e.g. digit grouping
or a changed negation construction), and gold spans can be longer than a sufficient
proof. The report must distinguish these scoring limitations from model judgment
errors. Both automatic and any explicitly reviewed scores are retained.

## Metrics

Primary end-to-end F1 requires a matched atomic claim, correct verdict, literal
quotes and a complete gold evidence group. Missing, duplicate, incorrect and failed
outputs count. Verdict-only per-class P/R/F1 and macro-F1 include unmatched claims;
the legacy aligned-only macro diagnostic is not the main verdict metric.

Literal quote validity is exact substring hits / emitted citations. Citation
accuracy is reported as a strict gold-span hit proxy: at least one complete gold
span for the aligned claim must appear in the citation. It is not semantic truth;
a shorter sufficient quote may fail it, and a long irrelevant-containing quote may
pass it. Complete-group sufficiency is separate. See [the scoring contract](scoring.md).

Latency is observed wall-clock median/P95; token counts include Codex CLI overhead
and available cache usage. Dollar cost under the existing subscription is unknown,
not zero. One run on 12 test families is not a stable speed or population-accuracy
estimate. Cluster bootstrap intervals reflect only the sampled case heterogeneity.

## Results and iteration

The development run and subsequent frozen test artifacts are recorded below once
complete. Test results will not be used to choose another prompt or edit the gold.

### Development measurements and decision

| Method / prompt | Automatic E2E F1 | Verdict macro-F1 | TP / predicted / gold | Failed requests |
| --- | --- | --- | --- | --- |
| deterministic | 0.150 | 0.115 | 11 / 62 / 85 | 0 / 20 |
| minimal | 0.471 | 0.759 | 40 / 85 / 85 | 0 / 20 |
| optimized / compact-v1 | 0.667 | 0.732 | 58 / 89 / 85 | 0 / 20 |
| candidate / compact-v3 | 0.663 | 0.690 | 57 / 87 / 85 | 0 / 20 |

All rows use the same repaired gold. The first three use
[automatic reference rescoring](../results/real-docs-v3/dev-initial/reference-report.md)
of the original saved outputs; the candidate uses its
[original report](../results/real-docs-v3/dev-candidate/report.md).
No semantic-review-adjusted scores are substituted for these measurements.

The sequence was: minimal single-call verification → compact-v1 evidence-ID
selection → one compact-v3 candidate adding v2's per-claim completeness audit and
source-grounded arithmetic. Code/schema validation is identical across compact
variants. This is a bounded development iteration, not a claim that each step wins.
Compact-v3 correctly marks `b=3+3` and `b=6` equivalent using arithmetic; both earlier
LLM methods marked that assertion UNSUPPORTED. It also completes the foreign-key
no-effect citation. Other differences offset those gains: the overall automatic
score is lower, so [selection.json](../results/real-docs-v3/selection.json) retains
**compact-v1 as the default `optimized` system**. Both v2 and v3 remain dev-only.

One candidate disagreement deserves human review: `sqlite-partialindex`'s source
states an *if* condition for using the index, while the answer states it as a
requirement. The frozen gold interprets the paragraph as establishing necessity;
v3 rejects that inference. This is a reference-interpretation dispute, not a
proven candidate error. It can matter for this tiny dev-score difference. The
[annotation question](../results/real-docs-v3/annotation-questions.json) is retained;
no gold, candidate or selection was changed after the test freeze.

Automatic E2E and verdict-only scores disagree about which LLM is better because
evidence completeness and alignment are separate from verdict classification.
Compact's sentence IDs also fit full-sentence gold spans more readily than minimal's
short quotes. The difference is therefore not evidence of superior semantic reasoning.

### Failure examples from development

These are actual saved outputs. Examples marked as scorer/reference limitations
are deliberately kept separate from model errors.

| Type | Case and observed output | Diagnosis |
| --- | --- | --- |
| Claim splitting | `postgres-indexes-partial`, deterministic loses the planning/inequality assertion and retains a fragment beginning “is insufficient…” | The punctuation splitter treats the `?` in `x < ?` as a question boundary and discards the preceding factual text. |
| Numeric/boundary reasoning | `sqlite-lang_with`, deterministic marks the false OFFSET/LIMIT quota conclusion UNSUPPORTED | Token overlap cannot combine the row-count and skipped-row rules to refute the numerical conclusion. |
| Negation/exception | `python-datetime`, deterministic marks the leap-second inputs-always-differ claim SUPPORTED | High overlap with a source saying the outputs can be identical does not detect the reversed exception. |
| Multi-passage synthesis | `python-functools`, deterministic marks later invalidation of the latest concurrent getter's value UNSUPPORTED | It selects one similar sentence instead of composing the race behavior and deletion rule. |
| Evidence completeness | `python-asyncio-task`, compact-v1 omits the failure-causes-cancellation premise from the wait-for-cancelled-children proof | Waiting and grouped raising alone do not supply that entire chain. V3 still omits the premise on this particular claim; the attempted fix is not complete. |
| Arithmetic vs outside knowledge | `sqlite-partialindex`, minimal and compact-v1 return UNSUPPORTED for the equivalent expressions | The supplied expressions support elementary arithmetic. The candidate fixes this assertion but does not win overall. |
| Alignment artifact | `sqlite-limits`, both LLMs produce correct `32,766` / `65,536` facts that fail the gold's ungrouped-number matching | Numeric-token guards reject equivalent formatting. This is not a model numeric error. |
| Evidence-span artifact | `sqlite-datatype3`, minimal quotes the exact INT cast clause but loses credit because gold includes the whole sentence with a NUMERIC contrast | The quote is sufficient for that atomic cast result; strict span coverage overpenalizes it. No verdict correction is justified. |

True-but-unretrieved facts are also tested (e.g. Python JSON's default NaN behavior
when its explaining paragraph is excluded). Do not invent an outside-knowledge
leakage failure when an output correctly returns UNSUPPORTED. Test outcomes for
this category are reported separately below.

All returned citations in dev pass literal validation. That is enforced by the
service and is **not** 100% semantic citation accuracy. Invalid-output requests,
if any, would remain failures in the end-to-end counts. Raw outputs, runtime traces,
case alignments and stricter gold-span hits remain in the result directories.

## Frozen test result

The [test freeze](../results/real-docs-v3/test-freeze.json) precedes the manifest's
start timestamp and records 54 file hashes, runtime configuration and selected
code revision `2b619e9`. The scheduled 36 requests ran exactly once: 12 each for
deterministic, minimal and compact-v1. Neither v2 nor v3 was run on test. No frozen
code, data or configuration was changed after that run.

| Method | Automatic E2E F1 | Verdict macro-F1 | TP / FP / FN | Literal quote validity | Gold-span hit rate |
| --- | --- | --- | --- | --- | --- |
| deterministic | 0.114 | 0.109 | 5 / 32 / 46 | 1.000 | 0.600 |
| minimal | 0.400 | 0.625 | 18 / 21 / 33 | 1.000 | 0.553 |
| optimized / compact-v1 | 0.484 | 0.565 | 22 / 18 / 29 | 1.000 | 0.571 |

Per-class P/R/F1, raw counts, confusion entries and alignments are in the
[automatic test report](../results/real-docs-v3/test/report.md) and
[summary](../results/real-docs-v3/test/summary.json). No semantic output-review score
is presented as a replacement. Human gold review remains pending.

| Method | Median / P95 seconds | Known input / output tokens | Calls with missing usage | Failed requests |
| --- | --- | --- | --- | --- |
| deterministic | 0.001 / 0.001 | 0 / 0 | 0 | 0 / 12 |
| minimal | 15.972 / 90.026 | 113,055 / 3,438 | 2 / 12 | 3 / 12 |
| optimized | 13.144 / 90.028 | 104,900 / 2,255 | 3 / 12 | 3 / 12 |

LLM token figures are **lower bounds**, not complete totals, because five timed-out
calls did not return usage. One additional failed call did report usage and is
included. Known cached input is 8,448 / 25,344 tokens for minimal / optimized.
Subscription dollar cost remains unknown. The baseline uses no model tokens;
its local compute is not priced.

The paired bootstrap's optimized-minus-minimal E2E F1 difference is +0.084, with
a 95% percentile interval of **[-0.118, +0.263]** across 12 source families. The
paired mean latency difference is +3.586 seconds with interval [-21.888, +30.034].
Neither supports a reliable quality or speed advantage. These intervals also
cannot account for unknown gold correctness or future backend variability.

### Test failures and what they do—and do not—show

1. **Availability:** optimized timed out on `python-zipfile`, `sqlite-isolation`
   and `python-tempfile`; minimal timed out on `postgres-functions-sequence` and
   `postgres-indexes-index-only-scans`. Minimal's `sqlite-isolation` call instead
   produced upstream error events despite a zero process exit code. All six
   failures remain in the denominators. Traces show the requests started but do
   not establish a common root cause. No retry, longer-timeout rerun or deletion
   was used to improve the published test score.
2. **Evidence applicability:** minimal's `postgres-explicit-locking` result cites
   the savepoint-release rule but not the separate FOR UPDATE lock premise;
   compact-v1 includes both. On `python-concurrent.futures`, minimal's performance
   quote omits the separate ProcessPoolExecutor applicability statement. This is
   missing per-claim evidence, not an invalid verbatim quote.
3. **Decomposition and reference granularity:** minimal merges INTEGER affinity
   and absence of a rowid alias in `sqlite-withoutrowid`, missing a separate gold
   record. Conversely, both LLMs split the WAL introduction's version/date, which
   this reference keeps as one event. `postgres-indexes-index-only-scans` also
   has a GiST/SP-GiST combined gold versus separate output records. These are
   granularity disagreements requiring human judgment, not all semantic failures.
4. **Scoring artifacts:** on `sqlite-lang_conflict`, all returned LLM verdicts are
   SUPPORTED as expected, yet minimal gets 0/5 automatic E2E credit because of
   shortened spans and alignment. Compact gets 2/5. On `python-pathlib`, literal
   evidence correctly refutes remembered directories, but each split gold still
   carries the original broader evidence group. These are conservative-reference
   penalties; they must not be described as demonstrated faulty reasoning.
5. **Gold issue exposed by test:** in `sqlite-autoinc`, compact returns UNSUPPORTED
   for the unqualified empty-table-first-key claim. The source guarantees 1 only
   if the table has **never contained data**. The frozen SUPPORTED gold is too
   broad under a literal reading; compact's distinction is defensible. The issue
   is recorded for author review, with no relabeling or rescoring after test.
6. **External knowledge boundary:** completed LLM outputs correctly mark the WAL
   introduction fact in `sqlite-withoutrowid`, the MVCC fact in
   `postgres-functions-sequence` (optimized), and the `mkstemp` race fact in
   `python-tempfile` (minimal) as UNSUPPORTED when their explanatory passages are
   excluded. No outside-knowledge false-support failure was observed on these
   completed examples. Timeouts and matching losses prevent calling the category
   solved; no failure example has been invented to fill a table.

### Old versus new

| Method | Old synthetic held-out F1 (auto / reviewed) | New real-document test F1 (automatic) |
| --- | --- | --- |
| deterministic | 0.750 / 0.750 | 0.114 |
| minimal | 1.000 / 1.000 | 0.400 |
| optimized | 0.964 / 0.964 | 0.484 |

The non-LLM algorithm and compact-v1 prompt remain the same, but the dataset,
claim counts and model differ (old Astra, new Sol), and the new run has provider
failures. This is a historical comparison, not an estimate of an isolated model
improvement or degradation. It exposes engineering and evaluation failure modes;
it does **not** prove that all the new score loss reflects harder semantic reasoning.

## Verification and remaining work

Source/data/configuration hashes, schedule completeness, literal quotes, archived
synthetic data and saved-score recomputation are checked in the
[verification receipt](../results/real-docs-v3/verification.json). The localhost
[HTTP checks](../results/real-docs-v3/acceptance/http-checks.json) exercise health,
empty answers, the 422 error envelope and deterministic inference without adding
model calls. Pytest, Ruff and CI cover code behavior, not gold semantics.

Before treating this as a definitive assessment, the author still needs to review
all labels, settle the three recorded annotation questions and resolve granularity/
evidence-span issues. Those corrections belong in a separately versioned benchmark;
this test has already been observed. A naturally occurring RAG-answer sample and
more families would improve external validity. A future availability investigation
needs separate probes; this run alone does not identify the cause of the failures.
The revision completes the traceable data and experimental workflow, while openly
retaining these limitations rather than claiming the assignment is now guaranteed
to pass or that a better automatic score proves a better verifier.

A third [annotation question](../results/real-docs-v3/annotation-questions.json)
concerns `python-zipfile`: its answer states bzip2's lower bound, while the gold
adds an upper bound from the source. That reference may over-specify the answer.
The resulting automatic mismatch is not demonstrated model failure. These known
issues mean the gold is not yet ready to be claimed as a fully validated benchmark.
