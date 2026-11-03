"""Separate availability failures from quality, using saved outputs only."""

import argparse
import hashlib
import json
from pathlib import Path

from grounding.benchmark import code_state, summarize
from grounding.experiment import paired_analysis, validate_records

# An explicit rule for this run, not a diagnosis of every upstream failure.
EXCLUDED_CODES = frozenset({"upstream_timeout", "upstream_error"})
LIMITATION = (
    "Post-run, author-requested availability exclusion. Network/backend variability is "
    "suspected but unconfirmed. Conditional cohorts can be biased by missing responses; "
    "they do not estimate performance on the full test set. Gold review is still pending."
)


def availability_view(records, cases, manifest):
    validate_records(records, manifest["execution_schedule"])
    methods = manifest["methods"]
    excluded = [r for r in records if (r.get("error") or {}).get("code") in EXCLUDED_CODES]
    retained = [r for r in records if (r.get("error") or {}).get("code") not in EXCLUDED_CODES]
    keys = [
        {(r["repeat"], r["case_id"]) for r in retained if r["method"] == method}
        for method in methods
    ]
    common = set.intersection(*keys)
    paired = [r for r in retained if (r["repeat"], r["case_id"]) in common]

    def scores(rows):
        summary = summarize(rows, cases, {}, manifest)
        return {
            method: {k: v for k, v in summary[method].items() if k != "case_scores"}
            if method in summary
            else None  # No responses: unknown, never a perfect or zero quality score.
            for method in methods
        }

    comparisons = paired_analysis(
        paired,
        cases,
        {},
        methods=methods,
        samples=manifest.get("bootstrap_samples", 2000),
        seed=manifest.get("bootstrap_seed", 1729),
        cluster=manifest.get("cluster", "family"),
    )
    comparisons["limitation"] = LIMITATION + " Repeats remain within family clusters."
    return {
        "policy": {
            "excluded_error_codes": sorted(EXCLUDED_CODES),
            "retained_errors": "Every other error, including invalid_output, remains penalized.",
            "limitation": LIMITATION,
            "inference_rerun": False,
            "semantic_review_adjustment": False,
            "cost_scope": "All-attempt usage remains reported; excluded calls are not free.",
        },
        "excluded_requests": [
            {
                **{k: r[k] for k in ["method", "repeat", "case_id", "execution_index"]},
                "error_code": r["error"]["code"],
                "latency_seconds": r["latency_seconds"],
            }
            for r in excluded
        ],
        "retained_pairs_by_method": {
            method: [f"{repeat}/{case_id}" for repeat, case_id in sorted(key)]
            for method, key in zip(methods, keys, strict=True)
        },
        "common_pairs": [f"{repeat}/{case_id}" for repeat, case_id in sorted(common)],
        "all_requests": scores(records),
        "availability_adjusted": scores(retained),
        "common_cases": scores(paired),
        "common_case_paired_analysis": comparisons,
    }


def report(view):
    lines = [
        "# Quality conditional on availability",
        "",
        view["policy"]["limitation"],
        "",
        "Exclude only `upstream_timeout` and `upstream_error`; keep all quality failures.",
        "No new inference, gold changes, semantic score adjustments or prompt selection occurred.",
        "",
        "## Per-method retained requests",
        "",
        "These subsets differ. Use the common cohort below for the same-input comparison.",
        "Latency here excludes dropped requests; all-attempt usage is reported separately.",
        "",
        "| Method | Included / attempted | Gold claims | Auto E2E F1 | Verdict macro-F1 "
        "| Median / P95 seconds | Other request failures |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for method, s in view["availability_adjusted"].items():
        n = view["all_requests"][method]["cases"]
        if s is None:
            lines.append(f"| {method} | 0 / {n} | 0 | unknown | unknown | unknown | 0 |")
            continue
        t = s["latency_seconds"]
        lines.append(
            f"| {method} | {s['cases']} / {n} | {s['gold']} | {s['f1']:.3f} | "
            f"{s['verdict_macro_f1']:.3f} | {t['median']:.3f} / "
            f"{t['p95_nearest_rank']:.3f} | {s['request_failures']} |"
        )
    lines += [
        "",
        "## Common retained cases across all methods",
        "",
        "| Method | Requests | Gold claims | Auto E2E F1 | Verdict macro-F1 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for method, s in view["common_cases"].items():
        lines.append(
            f"| {method} | {s['cases']} | {s['gold']} | {s['f1']:.3f} | "
            f"{s['verdict_macro_f1']:.3f} |"
            if s
            else f"| {method} | 0 | 0 | unknown | unknown |"
        )
    lines += ["", "Common repeat/case IDs:", ""]
    lines.extend(f"- `{key}`" for key in view["common_pairs"])
    lines += [
        "",
        "## All-attempt usage and original quality scores",
        "",
        "Tokens include failed calls where known and CLI overhead. Missing usage means",
        "counts are lower bounds; Codex subscription USD cost remains unknown.",
        "",
        "| Method | Original auto F1 | Known input / output tokens | Missing usage calls "
        "| USD | Failed requests |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for method, s in view["all_requests"].items():
        usd = "unknown" if s["estimated_usd"] is None else str(s["estimated_usd"])
        lines.append(
            f"| {method} | {s['f1']:.3f} | {s['input_tokens']:,} / {s['output_tokens']:,} | "
            f"{s['calls_missing_usage']} | {usd} | {s['request_failures']} / {s['cases']} |"
        )
    lines += ["", "## Excluded requests", ""]
    lines.extend(
        f"- `{r['method']}/{r['repeat']}/{r['case_id']}`: `{r['error_code']}`, "
        f"{r['latency_seconds']:.3f} seconds, execution index {r['execution_index']}."
        for r in view["excluded_requests"]
    )
    lines += [
        "",
        "[summary.json](summary.json) contains input hashes, per-class metrics, retained",
        "case IDs and common-family paired bootstrap intervals. Original raw outputs and",
        "the all-request report remain in [../test](../test/).",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=Path("data/cases.jsonl"))
    args = parser.parse_args()
    if args.out.resolve() == args.run.resolve():
        parser.error("Use a separate output directory; original reports must be preserved.")
    inputs = {
        "manifest": (args.run / "manifest.json").read_bytes(),
        "predictions": (args.run / "predictions.jsonl").read_bytes(),
        "original_summary": (args.run / "summary.json").read_bytes(),
        "dataset": args.dataset.read_bytes(),
        "analysis_script": Path(__file__).read_bytes(),
    }
    hashes = {key: hashlib.sha256(data).hexdigest() for key, data in inputs.items()}
    manifest = json.loads(inputs["manifest"])
    if hashes["dataset"] != manifest["dataset_sha256"]:
        parser.error("Dataset differs from the original run; this is not a label rescore.")
    if code_state()["source_sha256"] != manifest["source_sha256"]:
        parser.error("Use the frozen scoring source to reproduce this analysis.")
    cases = {c["id"]: c for c in map(json.loads, inputs["dataset"].splitlines())}
    records = list(map(json.loads, inputs["predictions"].splitlines()))
    if summarize(records, cases, {}, manifest) != json.loads(inputs["original_summary"]):
        parser.error("Original automatic summary does not reproduce exactly.")
    view = availability_view(records, cases, manifest)
    view["input_sha256"] = hashes
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(view, indent=2) + "\n")
    (args.out / "report.md").write_text(report(view))
    print(f"Excluded {len(view['excluded_requests'])} requests; wrote {args.out}.")


if __name__ == "__main__":
    main()
