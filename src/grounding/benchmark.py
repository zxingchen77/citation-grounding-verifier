import argparse
import asyncio
import hashlib
import json
import os
import statistics
import subprocess
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from grounding.models import VerificationError, VerifyRequest
from grounding.provider import HTTPModel, Settings, Trace
from grounding.scoring import aggregate, score_case
from grounding.verifiers import verify


def code_state():
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
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


def summarize(records, cases, reviews):
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
        result["calls_missing_usage"] = sum(not c.get("usage") for c in calls)
        in_price, out_price = (
            os.getenv("INPUT_PRICE_PER_MILLION"),
            os.getenv("OUTPUT_PRICE_PER_MILLION"),
        )
        result["estimated_usd"] = 0.0 if not calls else None
        if calls and in_price and out_price and not result["calls_missing_usage"]:
            result["estimated_usd"] = (
                result["input_tokens"] * float(in_price)
                + result["output_tokens"] * float(out_price)
            ) / 1e6
        result["by_category"] = {
            k: aggregate([s for s in scores if s["category"] == k])
            for k in sorted({s["category"] for s in scores})
        }
        result["case_scores"] = list(scores)
        summaries[method] = result
    return summaries


def write_summary(path, records, cases, reviews):
    results = summarize(records, cases, reviews)
    (path / "summary.json").write_text(json.dumps(results, indent=2) + "\n")

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
        "See summary.json for counts, category slices, alignments, and citation checks.",
        "Dollar estimates exclude infrastructure and ignore provider-specific cache discounts.",
        "Unknown usage or prices are not reported as zero cost.",
        "",
    ]
    (path / "report.md").write_text("\n".join(lines))
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
    if any(m != "deterministic" for m in args.methods) and (not cfg.api_key or not cfg.model):
        raise ValueError(
            "Real LLM runs require LLM_API_KEY and LLM_MODEL; no mock fallback is used."
        )
    args.out.mkdir(parents=True, exist_ok=False)
    manifest = {
        "started_at_utc": datetime.now(UTC).isoformat(),
        "dataset_sha256": hashlib.sha256(data).hexdigest(),
        "split": args.split,
        "case_ids": [c["id"] for c in selected],
        "methods": args.methods,
        "repeats": args.repeats,
        "model": cfg.model or None,
        "backend": "chat_completions",
        "temperature": cfg.temperature,
        "call_timeout": cfg.call_timeout,
        "request_timeout": cfg.request_timeout,
        "concurrency": 1,
        "response_cache": False,
        "input_price_per_million": os.getenv("INPUT_PRICE_PER_MILLION"),
        "output_price_per_million": os.getenv("OUTPUT_PRICE_PER_MILLION"),
        **code_state(),
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    model, records = HTTPModel(cfg), []
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
    write_summary(args.out, records, {c["id"]: c for c in cases}, {})


def main():
    parser = argparse.ArgumentParser(description="Run real grounding evaluations.")
    parser.add_argument("--dataset", type=Path, default=Path("data/cases.jsonl"))
    parser.add_argument("--split", choices=["dev", "test", "all"], default="dev")
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=["deterministic", "minimal", "optimized"],
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
