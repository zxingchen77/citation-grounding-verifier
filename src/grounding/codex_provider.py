"""Optional local evaluation adapter using the user's existing Codex sign-in.

This is a local, trusted-workstation adapter, not a public inference gateway.
No credentials are read or exported by this module.
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path

from grounding.models import VerificationError
from grounding.provider import Settings, Trace


async def collect_process(process, prompt: bytes, record: dict, started: float):
    """Drain pipes concurrently; retain event timings, never stderr or event bodies."""
    progress = record["progress_seconds"]
    counts = record["event_counts"]

    async def send_input():
        process.stdin.write(prompt)
        try:
            await process.stdin.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            process.stdin.close()

    async def read_events():
        while line := await process.stdout.readline():
            try:
                event = json.loads(line)
            except ValueError:
                record["non_json_stdout_lines"] += 1
                continue
            if not isinstance(event, dict):
                continue
            kind = event.get("type")
            if kind not in {
                "thread.started",
                "turn.started",
                "turn.completed",
                "turn.failed",
                "item.started",
                "item.updated",
                "item.completed",
                "error",
            }:
                kind = "other"
            counts[kind] = counts.get(kind, 0) + 1
            elapsed = time.perf_counter() - started
            progress.setdefault("first_event", elapsed)
            record["last_event"] = kind
            if kind in {"thread.started", "turn.started", "turn.completed", "turn.failed"}:
                progress.setdefault(kind, elapsed)
            if kind in {"turn.failed", "error"}:
                record["upstream_error_event"] = True
            if kind == "turn.completed":
                usage = event.get("usage")
                usage = usage if isinstance(usage, dict) else {}
                record["usage"] = {
                    target: usage[source]
                    for source, target in {
                        "input_tokens": "prompt_tokens",
                        "output_tokens": "completion_tokens",
                        "cached_input_tokens": "cached_input_tokens",
                    }.items()
                    if type(usage.get(source)) is int and usage[source] >= 0
                }
            item = event.get("item", {})
            if isinstance(item, dict):
                if item.get("type") == "agent_message":
                    progress.setdefault("first_agent_message", elapsed)
                if item.get("type") in {"command_execution", "mcp_tool_call", "web_search"}:
                    raise VerificationError(
                        "unexpected_tool_use", "Evaluation rejects model tool use."
                    )

    async def discard_stderr():
        while chunk := await process.stderr.read(65536):
            record["stderr_bytes"] += len(chunk)

    tasks = [asyncio.create_task(f()) for f in (send_input, read_events, discard_stderr)]
    try:
        await asyncio.gather(*tasks)
        await process.wait()
        progress["process_exit"] = time.perf_counter() - started
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


class CodexModel:
    def __init__(self, settings: Settings, executable: str = "codex"):
        self.settings = settings
        self.executable = executable

    async def generate(
        self, system: str, payload: dict, schema: dict, stage: str, trace: Trace
    ) -> dict:
        if not self.settings.model:
            raise VerificationError("not_configured", "Set LLM_MODEL for reproducible runs.", 503)
        record = {
            "stage": stage,
            "model": self.settings.model,
            "backend": "codex_cli",
            "status": "error",
            "progress_seconds": {},
            "event_counts": {},
            "stderr_bytes": 0,
            "non_json_stdout_lines": 0,
        }
        start = time.perf_counter()
        process = None
        try:
            with tempfile.TemporaryDirectory(prefix="grounding-") as directory:
                folder = Path(directory)
                schema_path, output_path = folder / "schema.json", folder / "answer.json"
                schema_path.write_text(json.dumps(schema))
                args = [
                    self.executable,
                    "exec",
                    "--ignore-user-config",
                    "--ephemeral",
                    "--skip-git-repo-check",
                    "--sandbox",
                    "read-only",
                    "--json",
                    "--model",
                    self.settings.model,
                    "--cd",
                    directory,
                    "--output-schema",
                    str(schema_path),
                    "--output-last-message",
                    str(output_path),
                    "-c",
                    "project_doc_max_bytes=0",
                    "-c",
                    'web_search="disabled"',
                ]
                # Exclude personal connectors, project context, tools and delegated work.
                for feature in [
                    "shell_tool",
                    "apps",
                    "plugins",
                    "multi_agent",
                    "browser_use",
                    "computer_use",
                    "image_generation",
                    "view_image",
                    "memories",
                ]:
                    args += ["--disable", feature]
                args.append("-")
                prompt = (
                    "Perform a JSON-only data transformation. Do not use tools, inspect files, "
                    "or access external information.\n\n"
                    + system
                    + "\n\nINPUT DATA:\n"
                    + json.dumps(payload, ensure_ascii=False)
                )
                process = await asyncio.create_subprocess_exec(
                    *args,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=directory,
                    limit=1024 * 1024,
                )
                record["progress_seconds"]["process_spawned"] = time.perf_counter() - start
                await asyncio.wait_for(
                    collect_process(process, prompt.encode(), record, start),
                    timeout=self.settings.call_timeout,
                )
                if process.returncode or record.get("upstream_error_event"):
                    raise VerificationError(
                        "upstream_error", f"Codex exited with status {process.returncode}."
                    )
                if not output_path.is_file():
                    raise VerificationError("incomplete_output", "Codex produced no output file.")
                raw = output_path.read_text()
                record["raw_output"] = raw
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    raise ValueError("expected JSON object")
                record["status"] = "ok"
                return parsed
        except TimeoutError as e:
            record["error_code"] = "upstream_timeout"
            raise VerificationError("upstream_timeout", "Codex model call timed out.", 504) from e
        except FileNotFoundError as e:
            record["error_code"] = "not_configured"
            raise VerificationError("not_configured", "Codex executable is missing.", 503) from e
        except (ValueError, TypeError) as e:
            record["error_code"] = "invalid_output"
            raise VerificationError("invalid_output", "Codex returned malformed JSON.") from e
        except VerificationError as e:
            record["error_code"] = e.code
            raise
        except asyncio.CancelledError:
            record["error_code"] = "cancelled"
            raise
        finally:
            if process is not None and process.returncode is None:
                process.kill()
                await process.wait()
            progress = record["progress_seconds"]
            record["last_phase"] = (
                "complete"
                if record["status"] == "ok"
                else "finalizing"
                if "turn.completed" in progress
                else "turn_in_progress"
                if "turn.started" in progress
                else "waiting_for_turn"
                if "first_event" in progress
                else "waiting_for_first_event"
            )
            if process is not None:
                record["exit_code"] = process.returncode
            record["latency_seconds"] = time.perf_counter() - start
            trace.calls.append(record)
