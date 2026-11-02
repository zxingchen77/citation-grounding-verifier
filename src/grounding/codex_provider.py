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
                )
                stdout, _stderr = await asyncio.wait_for(
                    process.communicate(prompt.encode()), timeout=self.settings.call_timeout
                )
                if process.returncode:
                    raise VerificationError(
                        "upstream_error", f"Codex exited with status {process.returncode}."
                    )
                for line in stdout.decode().splitlines():
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    if event.get("type") == "turn.completed":
                        usage = event.get("usage", {})
                        record["usage"] = {
                            "prompt_tokens": usage.get("input_tokens", 0),
                            "completion_tokens": usage.get("output_tokens", 0),
                            "cached_input_tokens": usage.get("cached_input_tokens", 0),
                        }
                    item = event.get("item", {})
                    if item.get("type") in {"command_execution", "mcp_tool_call", "web_search"}:
                        raise VerificationError(
                            "unexpected_tool_use", "Evaluation rejects model tool use."
                        )
                raw = output_path.read_text()
                record["raw_output"] = raw
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    raise ValueError("expected JSON object")
                record["status"] = "ok"
                return parsed
        except TimeoutError as e:
            raise VerificationError("upstream_timeout", "Codex model call timed out.", 504) from e
        except FileNotFoundError as e:
            raise VerificationError(
                "not_configured", "Codex executable or output is missing.", 503
            ) from e
        except (ValueError, TypeError) as e:
            raise VerificationError("invalid_output", "Codex returned malformed JSON.") from e
        finally:
            if process is not None and process.returncode is None:
                process.kill()
                await process.wait()
            record["latency_seconds"] = time.perf_counter() - start
            trace.calls.append(record)
