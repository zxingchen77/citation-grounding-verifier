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

from grounding.models import VerificationError, VerifyRequest
from grounding.provider import Settings, Trace, create_model
from grounding.scoring import aggregate, score_case
from grounding.verifiers import verify


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
    groups = defaultdict(list)
    for r in records:
        key = f"{r['method']}/{r['repeat']}/{r['case_id']}"
        groups[r["method"]].append((r, score_case(r, cases[r["case_id"]], reviews.get(key))))
    summaries = {}
    for method, entries in groups.items():
        runs, scores = zip(*entries, strict=True)
        result = aggregate(scores)
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
        "| Method | Cases | P | R | F1 | Errors | Review flags | Median seconds | USD |",
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
    return results


async def run(args):
    data = args.dataset.read_bytes()
    cases = [json.loads(line) for line in data.decode().splitlines() if line.strip()]
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Dataset IDs must be unique.")
    selected = [c for c in cases if args.split == "all" or c["split"] == args.split]
    if not selected or args.repeats < 1:
        raise ValueError("Select nonempty cases and at least one repeat.")
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
    with (args.out / "predictions.jsonl").open("w") as file:
        for method in args.methods:
            for repeat in range(args.repeats):
                for case in selected:
                    trace = Trace()
                    record = {"method": method, "repeat": repeat, "case_id": case["id"]}
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
                    record["trace"] = trace.as_dict()
                    records.append(record)
                    file.write(json.dumps(record) + "\n")
                    file.flush()
                    print(
                        f"{method} {case['id']} {'ERROR' if record.get('error') else 'ok'}",
                        flush=True,
                    )
    write_summary(args.out, records, {c["id"]: c for c in cases}, {}, manifest)


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
        choices=["deterministic", "minimal", "optimized", "staged"],
        default=["deterministic", "minimal", "optimized"],
    )
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        asyncio.run(run(args))
    except ValueError as e:
        parser.error(str(e))


if __name__ == "__main__":
    main()
