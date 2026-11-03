import argparse
import asyncio
import hashlib
import json
import os
import platform
import statistics
import subprocess
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from grounding.experiment import make_schedule, paired_analysis, validate_records
from grounding.models import VerificationError, VerifyRequest
from grounding.provider import Settings, Trace, create_model
from grounding.scoring import aggregate, score_case
from grounding.verifiers import METHODS, verify


def code_state():
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        dirty = bool(
            subprocess.check_output(
                [
                    "git",
                    "status",
                    "--porcelain",
                    "--",
                    "src",
                    "tests",
                    "data",
                    "scripts",
                    "pyproject.toml",
                    "requirements.lock",
                    ".github",
                ],
                text=True,
            ).strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        revision, dirty = "unknown", True
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode() + path.read_bytes())
    return {
        "git_revision": revision,
        "working_tree_dirty": dirty,
        "source_sha256": digest.hexdigest(),
    }


def summarize(records, cases, reviews, manifest=None):
    manifest = manifest or {}
    validate_records(records)
    groups = defaultdict(list)
    for r in records:
        key = f"{r['method']}/{r['repeat']}/{r['case_id']}"
        groups[r["method"]].append((r, score_case(r, cases[r["case_id"]], reviews.get(key))))
    summaries = {}
    for method, entries in groups.items():
        runs, scores = zip(*entries, strict=True)
        result = aggregate(scores)
        result["unique_cases"] = len({r["case_id"] for r in runs})
        result["rounds"] = sorted({r["repeat"] for r in runs})
        evidence_matches = [
            m for s in scores for m in s["matches"] if m["gold_verdict"] != "UNSUPPORTED"
        ]
        result["aligned_evidence_required"] = len(evidence_matches)
        result["sufficient_evidence_matches"] = sum(
            m["evidence_sufficient"] for m in evidence_matches
        )
        result["evidence_sufficiency"] = (
            result["sufficient_evidence_matches"] / len(evidence_matches)
            if evidence_matches
            else None
        )
        times = sorted(r["latency_seconds"] for r in runs)
        result["latency_seconds"] = {
            "median": statistics.median(times),
            "max": max(times),
            "p95_nearest_rank": times[max(0, int(len(times) * 0.95 + 0.999) - 1)],
        }
        calls = [c for r in runs for c in r["trace"]["calls"]]
        result["model_calls"] = len(calls)
        result["input_tokens"] = sum(c.get("usage", {}).get("prompt_tokens", 0) for c in calls)
        result["output_tokens"] = sum(c.get("usage", {}).get("completion_tokens", 0) for c in calls)
        result["cached_input_tokens"] = sum(
            c.get("usage", {}).get("cached_input_tokens", 0) for c in calls
        )
        result["calls_missing_usage"] = sum(
            not {"prompt_tokens", "completion_tokens"}.issubset(c.get("usage", {})) for c in calls
        )
        result["calls_missing_cache_usage"] = sum(
            "cached_input_tokens" not in c.get("usage", {}) for c in calls
        )
        result["failed_model_calls"] = sum(c.get("status") == "error" for c in calls)
        result["repair_calls"] = (
            sum(max(0, len(r["trace"]["calls"]) - 1) for r in runs)
            if method in {"minimal", "optimized", "optimized-v2"}
            else None
        )
        in_price, out_price = (
            manifest.get("input_price_per_million"),
            manifest.get("output_price_per_million"),
        )
        result["estimated_usd"] = 0.0 if not calls else None
        if (
            calls
            and in_price
            and out_price
            and not result["calls_missing_usage"]
            and manifest.get("backend") != "codex"
        ):
            result["estimated_usd"] = (
                result["input_tokens"] * float(in_price)
                + result["output_tokens"] * float(out_price)
            ) / 1e6
        result["by_category"] = {
            k: aggregate([s for s in scores if s["category"] == k])
            for k in sorted({s["category"] for s in scores})
        }
        result["by_split"] = {
            k: aggregate([s for s in scores if s["split"] == k])
            for k in sorted({s["split"] for s in scores})
        }
        result["case_scores"] = list(scores)
        summaries[method] = result
    return summaries


def write_summary(path, records, cases, reviews, manifest=None, prefix=""):
    results = summarize(records, cases, reviews, manifest)
    (path / f"{prefix}summary.json").write_text(json.dumps(results, indent=2) + "\n")

    def fmt(v):
        return "unknown" if v is None else f"{v:.3f}"

    lines = [
        "# Benchmark report",
        "",
        "Scores with review flags are provisional.",
        "",
        "| Method | Requests | P | R | F1 | Errors | Review flags | Median seconds | USD |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, r in results.items():
        lines.append(
            f"| {name} | {r['cases']} | {fmt(r['precision'])} | {fmt(r['recall'])} | "
            f"{fmt(r['f1'])} | {r['request_failures']} | {r['cases_needing_review']} | "
            f"{fmt(r['latency_seconds']['median'])} | {fmt(r['estimated_usd'])} |"
        )
    lines += [
        "",
        f"See {prefix}summary.json for counts, category slices, alignments, and citation checks.",
        "Dollar estimates exclude infrastructure and ignore provider-specific cache discounts.",
        "Unknown usage or prices are not reported as zero cost.",
        "",
    ]
    (path / f"{prefix}report.md").write_text("\n".join(lines))
    manifest = manifest or {}
    rounds = {
        str(repeat): summarize(
            [r for r in records if r["repeat"] == repeat], cases, reviews, manifest
        )
        for repeat in sorted({r["repeat"] for r in records})
    }
    paired = paired_analysis(
        records,
        cases,
        reviews,
        methods=manifest.get("methods"),
        samples=manifest.get("bootstrap_samples", 2000),
        seed=manifest.get("bootstrap_seed", 1729),
        cluster=manifest.get("cluster", "family"),
    )
    (path / f"{prefix}rounds.json").write_text(json.dumps(rounds, indent=2) + "\n")
    (path / f"{prefix}paired.json").write_text(json.dumps(paired, indent=2) + "\n")
    details = [
        "# Per-round and paired report",
        "",
        "Counts below are requests; repeated outputs are not new independent cases.",
        "",
        (
            "| Round | Method | Unique cases | TP / FP / FN | F1 | Coverage | Quote "
            "validity | Evidence sufficiency | Errors | Median / P95 s | Input / output / "
            "cached tokens | Calls / repairs |"
        ),
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for repeat, methods in rounds.items():
        for method, r in methods.items():
            details.append(
                f"| {repeat} | {method} | {r['unique_cases']} | "
                f"{r['tp']} / {r['fp']} / {r['fn']} | "
                f"{fmt(r['f1'])} | {fmt(r['claim_coverage'])} | {fmt(r['quote_validity'])} | "
                f"{fmt(r['evidence_sufficiency'])} | {r['request_failures']} | "
                f"{fmt(r['latency_seconds']['median'])} / "
                f"{fmt(r['latency_seconds']['p95_nearest_rank'])} | "
                f"{r['input_tokens']} / {r['output_tokens']} / {r['cached_input_tokens']} | "
                f"{r['model_calls']} / {r['repair_calls']} |"
            )
    details.extend(
        [
            "",
            "Evidence sufficiency is diagnostic among aligned evidence-required gold claims; "
            "it does not replace verdict correctness or literal validation. Token sums include "
            "known usage only; missing usage/cache counts are in rounds.json.",
            "",
            paired["limitation"],
            "",
        ]
    )
    for comparison in paired["comparisons"]:
        estimate = comparison.get("f1_difference")
        details.append(
            f"- {comparison['right']} minus {comparison['left']}: "
            f"{comparison['unique_cases']} cases, "
            f"{comparison['clusters']} {comparison['cluster']} clusters, "
            f"paired rounds {comparison['paired_rounds']}; F1 difference "
            f"{fmt(estimate['estimate']) if estimate else 'unavailable'}, "
            f"95% percentile interval {estimate['percentile_95_interval'] if estimate else None}."
        )
    (path / f"{prefix}rounds-report.md").write_text("\n".join(details) + "\n")
    return results


async def run(args):
    data = args.dataset.read_bytes()
    cases = [json.loads(line) for line in data.decode().splitlines() if line.strip()]
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Dataset IDs must be unique.")
    selected = [c for c in cases if args.split == "all" or c["split"] == args.split]
    if not selected or args.repeats < 1:
        raise ValueError("Select nonempty cases and at least one repeat.")
    schedule = make_schedule(
        [c["id"] for c in selected],
        args.methods,
        args.repeats,
        args.order,
        args.seed,
        args.deterministic_repeats,
    )
    if args.bootstrap_samples < 100:
        raise ValueError("Use at least 100 bootstrap draws.")
    cfg = Settings.from_env()
    backend = os.getenv("LLM_BACKEND", "http")
    if any(m != "deterministic" for m in args.methods) and (
        not cfg.model or (backend == "http" and not cfg.api_key)
    ):
        raise ValueError(
            "Real LLM runs require LLM_API_KEY and LLM_MODEL; no mock fallback is used."
        )
    args.out.mkdir(parents=True, exist_ok=False)
    cli_version = None
    if backend == "codex" and any(m != "deterministic" for m in args.methods):
        cli_version = subprocess.check_output(["codex", "--version"], text=True).strip()
    manifest = {
        "started_at_utc": datetime.now(UTC).isoformat(),
        "dataset_sha256": hashlib.sha256(data).hexdigest(),
        "split": args.split,
        "case_ids": [c["id"] for c in selected],
        "methods": args.methods,
        "repeats": args.repeats,
        "deterministic_repeats": args.deterministic_repeats,
        "order": args.order,
        "seed": args.seed,
        "bootstrap_seed": args.seed,
        "bootstrap_samples": args.bootstrap_samples,
        "cluster": args.cluster,
        "execution_schedule": schedule,
        "model": cfg.model or None,
        "backend": backend,
        "temperature": cfg.temperature if backend == "http" else None,
        "max_output_tokens": cfg.max_output_tokens if backend == "http" else None,
        "python_version": platform.python_version(),
        "codex_cli_version": cli_version,
        "call_timeout": cfg.call_timeout,
        "request_timeout": cfg.request_timeout,
        "concurrency": 1,
        "response_cache": False,
        "input_price_per_million": os.getenv("INPUT_PRICE_PER_MILLION"),
        "output_price_per_million": os.getenv("OUTPUT_PRICE_PER_MILLION"),
        **code_state(),
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    model, records = create_model(cfg), []
    by_id = {c["id"]: c for c in cases}
    with (args.out / "predictions.jsonl").open("w") as file:
        for job in schedule:
            method, case = job["method"], by_id[job["case_id"]]
            trace = Trace()
            record = {**job, "started_at_utc": datetime.now(UTC).isoformat()}
            start = time.perf_counter()
            try:
                response = await verify(
                    VerifyRequest(
                        context_passages=case["context_passages"],
                        generated_answer=case["generated_answer"],
                    ),
                    method,
                    model,
                    trace,
                    timeout=cfg.request_timeout,
                )
                record["response"] = response.model_dump()
            except VerificationError as e:
                record["error"] = {"code": e.code, "message": e.message}
            record["latency_seconds"] = time.perf_counter() - start
            record["completed_at_utc"] = datetime.now(UTC).isoformat()
            record["trace"] = trace.as_dict()
            records.append(record)
            file.write(json.dumps(record) + "\n")
            file.flush()
            print(
                f"{job['execution_index']} round={job['repeat']} {method} {case['id']} "
                f"{'ERROR' if record.get('error') else 'ok'}",
                flush=True,
            )
    validate_records(records, schedule)
    write_summary(args.out, records, by_id, {}, manifest)


def score_main():
    parser = argparse.ArgumentParser(description="Rescore saved predictions without model calls.")
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=Path("data/cases.jsonl"))
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument(
        "--original-dataset",
        type=Path,
        help="Allow a reference-only revision after verifying identical inputs.",
    )
    args = parser.parse_args()
    data = args.dataset.read_bytes()
    manifest = json.loads((args.run / "manifest.json").read_text())
    cases = {c["id"]: c for c in map(json.loads, data.decode().splitlines())}
    if hashlib.sha256(data).hexdigest() != manifest["dataset_sha256"]:
        if args.original_dataset is None:
            parser.error(
                "Dataset hash differs; provide the recorded original dataset to audit labels."
            )
        original = args.original_dataset.read_bytes()
        if hashlib.sha256(original).hexdigest() != manifest["dataset_sha256"]:
            parser.error("Original dataset hash does not match the recorded run.")
        old_cases = {c["id"]: c for c in map(json.loads, original.decode().splitlines())}
        for case_id in manifest["case_ids"]:
            for field in ["context_passages", "generated_answer", "split", "category"]:
                if cases.get(case_id, {}).get(field) != old_cases[case_id][field]:
                    parser.error("Rescoring cannot change model inputs or evaluation partitions.")
    records = [
        json.loads(line) for line in (args.run / "predictions.jsonl").read_text().splitlines()
    ]
    validate_records(records, manifest.get("execution_schedule"))
    review_document = json.loads(args.reviews.read_text())
    if not review_document.get("reviewer") or not review_document.get("review_type"):
        parser.error("Reviews must identify reviewer and review_type (e.g. AI-assisted).")
    reviews = review_document["records"]
    valid_keys = {f"{r['method']}/{r['repeat']}/{r['case_id']}" for r in records}
    if set(reviews) - valid_keys:
        parser.error("Review contains keys not present in the selected run.")
    write_summary(args.run, records, cases, reviews, manifest, prefix="reviewed-")
    (args.run / "review-provenance.json").write_text(
        json.dumps(
            {
                "reviewer": review_document["reviewer"],
                "review_type": review_document["review_type"],
                "reviews_sha256": hashlib.sha256(args.reviews.read_bytes()).hexdigest(),
                "original_dataset_sha256": manifest["dataset_sha256"],
                "scored_dataset_sha256": hashlib.sha256(data).hexdigest(),
                "scorer": code_state(),
            },
            indent=2,
        )
        + "\n"
    )


def main():
    parser = argparse.ArgumentParser(description="Run real grounding evaluations.")
    parser.add_argument("--dataset", type=Path, default=Path("data/cases.jsonl"))
    parser.add_argument("--split", choices=["dev", "test", "all"], default="dev")
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=METHODS,
        default=["deterministic", "minimal", "optimized"],
    )
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument(
        "--deterministic-repeats",
        type=int,
        help="Defaults to --repeats; use 1 for a single baseline round.",
    )
    parser.add_argument("--order", choices=["fixed", "balanced"], default="fixed")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--cluster", choices=["family", "case"], default="family")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        asyncio.run(run(args))
    except ValueError as e:
        parser.error(str(e))


if __name__ == "__main__":
    main()
