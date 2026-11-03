# Real-document corpus v3

The main corpus is now [`cases.jsonl`](cases.jsonl): **32 cases / 136 atomic
claims**, adapted from original SQLite, PostgreSQL 18 and Python 3.13 documentation.
The former 40-case synthetic corpus is archived byte-for-byte in
[`revisions/cases-synthetic-v3.jsonl`](revisions/cases-synthetic-v3.jsonl), with its
original manifest. Historical results must use that archived corpus.

## Construction and provenance

All 32 cases use real documentation prose, not invented products. We chose the
official-documentation route allowed by the revision brief. We examined
[RAGTruth](https://github.com/ParticleMedia/RAGTruth), but did **not** import its
answers or human hallucination labels. Our answers are AI-authored paraphrases
with controlled errors; they are not naturally occurring RAG outputs. This remains
a constructed benchmark, not a representative production sample.

Each case has 3–4 passages, each 300–1,200 characters, with at least one related
passage unused by its gold evidence. Total context is 1,090–2,926 characters
(median 1,712.5), compared with a mean of 143.2 in the old corpus. Length alone
is not proof of difficulty. Source snapshots preserve exact prose after HTML
entity decoding and whitespace normalization; long paragraphs may be excerpted
at sentence boundaries. Gold quotations are literal substrings of the model input.

[`sources/real-docs-v3.json`](sources/real-docs-v3.json) records original URLs,
versions, retrieval times, page hashes, normalized paragraphs and licensing.
Per-case provenance records paragraph IDs, excerpt offsets, hashes and edits.
[`real-docs-v3/spec.json`](real-docs-v3/spec.json) holds the authored answers and
gold. Run `python scripts/build_dataset.py` to rebuild offline. The historical
synthetic generator is now `scripts/build_synthetic_dataset.py` and writes only
to the archive paths.

| Source | Cases | Terms and retained notices |
| --- | --- | --- |
| SQLite | 12 | [Public-domain documentation](https://www.sqlite.org/copyright.html); [notice](sources/licenses/sqlite.html) |
| PostgreSQL 18 | 10 | [PostgreSQL License](https://www.postgresql.org/about/licence/); [notice](sources/licenses/postgres.html) |
| Python 3.13 | 10 | [PSF license for documentation](https://docs.python.org/3.13/license.html); [notice](sources/licenses/python.html) |

The source licenses govern the excerpts. Repository-authored adaptations are
covered by the repository license; this does not relicense the source documents.
No private data, credentials or copyrighted news benchmark passages were imported.

## Coverage and split

| Primary answer category | Dev | Test | Total |
| --- | --- | --- | --- |
| Supported | 5 | 3 | 8 |
| Subtle distortion | 5 | 3 | 8 |
| Extrinsic | 5 | 3 | 8 |
| Multi-passage | 5 | 3 | 8 |

The split has 20 dev / 12 test source-document families. No source document used
as a model input appears in both splits. Related technologies occur on both sides;
this is topic-family separation, not an unseen-product test. All labels and splits
were authored before model evaluation. The category is the answer's primary
stress test, not the verdict of every claim: 24 cases mix labels. Gold totals are
96 SUPPORTED / 30 CONTRADICTED / 10 UNSUPPORTED; classes are **not** balanced.

Covered difficulties include 1,000 vs 1,001 pages, inclusive compression-level
bounds, milliseconds to seconds, binary MB versus decimal bytes, ISO week dates,
truth-sufficient versus truth-necessary conditions, reversed exceptions, negation,
expanded scope, true-but-unretrieved facts, pronouns, mixed true/false clauses,
and valid or invalid combinations of premises from different passages. Capability
tags and counts are in [`manifest.json`](manifest.json).

For true-but-unretrieved facts, a separate `external_fact_check` records where the
fact is actually documented. It is audit material and **never sent to the model**.
Only `context_passages` and `generated_answer` are inference inputs.

## Annotation and limitations

Every claim has an explicit rationale, verdict and alternative `evidence_groups`.
At least one complete group is required for SUPPORTED/CONTRADICTED; UNSUPPORTED
has no quotes. A conjunction is split when its parts are independently testable;
conditions and comparative relations stay attached to the proposition they qualify.
A correct external fact is still UNSUPPORTED if these excerpts do not establish it.
Arithmetic and necessary logical consequences are permitted; missing information
is not treated as contradiction.

**All gold labels are AI-drafted; human author review is pending.** One project
author is responsible for the benchmark, with AI assistance, but no completed
human review or independent annotation is claimed. The
[gold review workbook](real-docs-v3/gold-review.md) contains every answer,
passage, label, rationale and quote with space for the author's decisions.
Programmatic checks cannot decide whether the gold semantics are right.

Test results against these labels are provisional. Test is run only after a
recorded code/data/configuration freeze, once per method; its outputs cannot
select prompts or trigger relabeling in this version. Human corrections after
that run require a new version and disclosure, not a retroactive improvement.
The separate `challenge-v1` test split remains unused.

Other limits: technical English only, modest context lengths, only 12 test
families, few unsupported claims, known public documents that may be in model
training, no inter-annotator agreement, and no naturally occurring retrieval noise
or conflicting source authority. The benchmark exposes failure modes; it cannot
establish deployment accuracy.

Validate without model access: `python -m grounding.dataset data/cases.jsonl`.
Tests also reject altered source text, source leakage, invalid distractors,
nonliteral gold quotes and out-of-range indices.

The [pre-test annotation audit](real-docs-v3/annotation-audit.json) splits independent
facts and restores omitted assertions across six cases (two previously unrun test cases included). Inputs and
verdicts are unchanged. The original draft and all initial automatic scores remain
archived; rescoring on corrected references is not a model improvement.
