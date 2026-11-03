"""A single-call dev candidate; reuse compact-v1's schema, resolver and repair policy."""

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from experiments.dev_refinement import dev_cases
from grounding.benchmark import code_state, write_summary
from grounding.experiment import make_schedule, validate_records
from grounding.models import VerificationError, VerifyRequest
from grounding.provider import Settings, Trace, create_model
from grounding.verifiers import COMPACT_PROMPT, optimized

PROMPT = (
    COMPACT_PROMPT
    + """

Make each claim self-contained by naming its subject and retaining the applicable
condition from the answer, rather than leaving 'it', 'the module' or 'that attempt'
unresolved. Keep independently asserted facts separate; do not bundle a statement
of a returned value with a distinct statement about whether an error is raised.
When splitting an assertion, do not repeat the removed assertion inside another
claim's concession. Do not expand the answer using facts found only in the sources.

Source-only verification allows elementary arithmetic, exact unit conversions and
necessary logical deductions on supplied facts. An expression can be mathematically
equivalent to another even when the described system does not recognize it. Missing
verbatim wording alone is not a reason to reject such a deduction. Cite the stated
inputs and explain the deduction; still reject unmentioned outside-world properties.

Audit each claim's evidence against its own subject, condition and outcome. For a
conditional chain, include the trigger, the intermediate change and the terminal
rule, including explicit waiting or ordering rules when the claim asserts them.
Do not borrow premises from another claim's citations. Restore applicability and
default qualifiers if a selected segment begins with an unexplained pronoun or
'instead'. Select only the needed segments, not surrounding unrelated sentences."""
)


class PromptModel:
    def __init__(self, model):
        self.model = model

    async def generate(self, system, payload, schema, stage, trace):
        if stage != "compact-v1":
            raise ValueError("The v5 adapter is only for the compact-v1 pipeline.")
        return await self.model.generate(PROMPT, payload, schema, "compact-v5", trace)


async def candidate(request, model, trace):
    return await optimized(request, PromptModel(model), trace, version="v1")


async def run(args):
    data = args.dataset.read_bytes()
    cases = dev_cases(data)
    cfg = Settings.from_env()
    backend = os.getenv("LLM_BACKEND", "http")
    if not cfg.model or (backend == "http" and not cfg.api_key):
        raise ValueError("A real configured model is required.")
    schedule = make_schedule([c["id"] for c in cases], ["compact-v5"], order="balanced", seed=1729)
    args.out.mkdir(parents=True, exist_ok=False)
    manifest = {
        "started_at_utc": datetime.now(UTC).isoformat(),
        "dataset_sha256": hashlib.sha256(data).hexdigest(),
        "split": "dev",
        "case_ids": [c["id"] for c in cases],
        "methods": ["compact-v5"],
        "repeats": 1,
        "order": "seeded case order; separate sequential run after the v4 comparison",
        "seed": 1729,
        "bootstrap_seed": 1729,
        "bootstrap_samples": 2000,
        "cluster": "family",
        "execution_schedule": schedule,
        "model": cfg.model,
        "backend": backend,
        "temperature": cfg.temperature if backend == "http" else None,
        "max_output_tokens": cfg.max_output_tokens if backend == "http" else None,
        "codex_cli_version": subprocess.check_output(["codex", "--version"], text=True).strip()
        if backend == "codex"
        else None,
        "call_timeout": cfg.call_timeout,
        "request_timeout": cfg.request_timeout,
        "concurrency": 1,
        "response_cache": False,
        "input_price_per_million": os.getenv("INPUT_PRICE_PER_MILLION"),
        "output_price_per_million": os.getenv("OUTPUT_PRICE_PER_MILLION"),
        "nominal_model_calls": 1,
        "structural_repairs": 1,
        "experiment_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(args.protocol.read_bytes()).hexdigest(),
        "test_inference_permitted": False,
        **code_state(),
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    model = create_model(cfg)
    by_id = {c["id"]: c for c in cases}
    records = []
    with (args.out / "predictions.jsonl").open("w") as file:
        for job in schedule:
            case = by_id[job["case_id"]]
            if case["split"] != "dev":
                raise ValueError("Test inference is disabled.")
            request = VerifyRequest(
                context_passages=case["context_passages"],
                generated_answer=case["generated_answer"],
            )
            trace = Trace()
            record = {**job, "started_at_utc": datetime.now(UTC).isoformat()}
            start = time.perf_counter()
            try:
                async with asyncio.timeout(cfg.request_timeout):
                    record["response"] = (await candidate(request, model, trace)).model_dump()
            except TimeoutError:
                record["error"] = {
                    "code": "verification_timeout",
                    "message": "Verification deadline exceeded.",
                }
            except VerificationError as e:
                record["error"] = {"code": e.code, "message": e.message}
            record["latency_seconds"] = time.perf_counter() - start
            record["completed_at_utc"] = datetime.now(UTC).isoformat()
            record["trace"] = trace.as_dict()
            file.write(json.dumps(record) + "\n")
            file.flush()
            records.append(record)
            print(
                f"{len(records)}/{len(schedule)} {job['case_id']} "
                f"{record.get('error', {}).get('code', 'ok')}",
                flush=True,
            )
    validate_records(records, schedule)
    write_summary(args.out, records, by_id, {}, manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("data/cases.jsonl"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--protocol", type=Path, default=Path("results/dev-refinement-v5/protocol.json")
    )
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
