# Quality conditional on availability

Post-run, author-requested availability exclusion. Network/backend variability is suspected but unconfirmed. Conditional cohorts can be biased by missing responses; they do not estimate performance on the full test set. Gold review is still pending.

Exclude only `upstream_timeout` and `upstream_error`; keep all quality failures.
No new inference, gold changes, semantic score adjustments or prompt selection occurred.

## Per-method retained requests

These subsets differ. Use the common cohort below for the same-input comparison.
Latency here excludes dropped requests; all-attempt usage is reported separately.

| Method | Included / attempted | Gold claims | Auto E2E F1 | Verdict macro-F1 | Median / P95 seconds | Other request failures |
| --- | --- | --- | --- | --- | --- | --- |
| deterministic | 12 / 12 | 51 | 0.114 | 0.109 | 0.001 / 0.001 | 0 |
| minimal | 9 / 12 | 38 | 0.468 | 0.720 | 14.925 / 29.279 | 0 |
| optimized | 9 / 12 | 37 | 0.571 | 0.651 | 12.748 / 20.996 | 0 |

## Common retained cases across all methods

| Method | Requests | Gold claims | Auto E2E F1 | Verdict macro-F1 |
| --- | --- | --- | --- | --- |
| deterministic | 7 | 28 | 0.043 | 0.076 |
| minimal | 7 | 28 | 0.464 | 0.613 |
| optimized | 7 | 28 | 0.586 | 0.569 |

Common repeat/case IDs:

- `0/postgres-ddl-constraints`
- `0/postgres-explicit-locking`
- `0/python-concurrent.futures`
- `0/python-pathlib`
- `0/sqlite-autoinc`
- `0/sqlite-lang_conflict`
- `0/sqlite-withoutrowid`

## All-attempt usage and original quality scores

Tokens include failed calls where known and CLI overhead. Missing usage means
counts are lower bounds; Codex subscription USD cost remains unknown.

| Method | Original auto F1 | Known input / output tokens | Missing usage calls | USD | Failed requests |
| --- | --- | --- | --- | --- | --- |
| deterministic | 0.114 | 0 / 0 | 0 | 0.0 | 0 / 12 |
| minimal | 0.400 | 113,055 / 3,438 | 2 | unknown | 3 / 12 |
| optimized | 0.484 | 104,900 / 2,255 | 3 | unknown | 3 / 12 |

## Excluded requests

- `optimized/0/python-zipfile`: `upstream_timeout`, 90.028 seconds, execution index 13.
- `minimal/0/postgres-functions-sequence`: `upstream_timeout`, 90.026 seconds, execution index 21.
- `minimal/0/postgres-indexes-index-only-scans`: `upstream_timeout`, 90.025 seconds, execution index 29.
- `optimized/0/sqlite-isolation`: `upstream_timeout`, 90.028 seconds, execution index 31.
- `minimal/0/sqlite-isolation`: `upstream_error`, 23.214 seconds, execution index 32.
- `optimized/0/python-tempfile`: `upstream_timeout`, 90.025 seconds, execution index 35.

[summary.json](summary.json) contains input hashes, per-class metrics, retained
case IDs and common-family paired bootstrap intervals. Original raw outputs and
the all-request report remain in [../test](../test/).
