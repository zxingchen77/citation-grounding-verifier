"""Run a localhost-only real-provider acceptance server with credential-free traces.

Use scripts/smoke_http.py as the client. No model is substituted or mocked here.
The output folder must be new; the wrapper saves actual provider calls and usage.
"""

import argparse
import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import uvicorn

from grounding.api import create_app
from grounding.benchmark import code_state
from grounding.provider import Settings, create_model


class RecordedModel:
    def __init__(self, model, output):
        self.model = model
        self.output = output

    async def generate(self, system, payload, schema, stage, trace):
        started = datetime.now(UTC).isoformat()
        before = len(trace.calls)
        try:
            return await self.model.generate(system, payload, schema, stage, trace)
        finally:
            record = {
                "started_at_utc": started,
                "completed_at_utc": datetime.now(UTC).isoformat(),
                "stage": stage,
                "system_sha256": hashlib.sha256(system.encode()).hexdigest(),
                "schema_sha256": hashlib.sha256(
                    json.dumps(schema, sort_keys=True).encode()
                ).hexdigest(),
                "payload": payload,
                "calls": trace.calls[before:],
            }
            with self.output.open("a") as file:
                file.write(json.dumps(record) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--method", choices=["minimal", "optimized", "optimized-v2"], required=True)
    args = parser.parse_args()
    cfg = Settings.from_env()
    backend = os.getenv("LLM_BACKEND", "http")
    if not cfg.model or (backend == "http" and not cfg.api_key):
        parser.error("Configure an authorized real model; there is no mock fallback.")
    args.out.mkdir(parents=True, exist_ok=False)
    manifest = {
        "started_at_utc": datetime.now(UTC).isoformat(),
        "backend": backend,
        "model": cfg.model,
        "method": args.method,
        "call_timeout": cfg.call_timeout,
        "request_timeout": cfg.request_timeout,
        "temperature": cfg.temperature if backend == "http" else None,
        "max_output_tokens": cfg.max_output_tokens if backend == "http" else None,
        "codex_cli_version": subprocess.check_output(["codex", "--version"], text=True).strip()
        if backend == "codex"
        else None,
        "url": f"http://127.0.0.1:{args.port}",
        "note": "Real local HTTP service; model calls and usage are retained in calls.jsonl.",
        **code_state(),
    }
    (args.out / "service.json").write_text(json.dumps(manifest, indent=2) + "\n")
    model = RecordedModel(create_model(cfg), args.out / "calls.jsonl")
    uvicorn.run(create_app(model=model, method=args.method), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
