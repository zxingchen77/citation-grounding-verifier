import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

import httpx

from grounding.models import VerificationError


@dataclass
class Trace:
    calls: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self):
        return asdict(self)


class Model(Protocol):
    async def generate(
        self, system: str, payload: dict, schema: dict, stage: str, trace: Trace
    ) -> dict: ...


@dataclass(frozen=True)
class Settings:
    model: str = ""
    api_key: str = field(default="", repr=False)
    base_url: str = "https://api.openai.com/v1"
    call_timeout: float = 30
    request_timeout: float = 120
    temperature: float | None = None

    @classmethod
    def from_env(cls):
        temp = os.getenv("LLM_TEMPERATURE")
        return cls(
            model=os.getenv("LLM_MODEL", ""),
            api_key=os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")),
            base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
            call_timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
            request_timeout=float(os.getenv("VERIFIER_TIMEOUT_SECONDS", "120")),
            temperature=float(temp) if temp else None,
        )


class HTTPModel:
    """OpenAI-compatible Chat Completions; no hidden retry or credential logging."""

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.transport = transport

    async def generate(
        self, system: str, payload: dict, schema: dict, stage: str, trace: Trace
    ) -> dict:
        cfg = self.settings
        if not cfg.api_key or not cfg.model:
            raise VerificationError("not_configured", "Set LLM_API_KEY and LLM_MODEL.", 503)
        body = {
            "model": cfg.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "grounding_output",
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        if cfg.temperature is not None:
            body["temperature"] = cfg.temperature
        record: dict[str, Any] = {"stage": stage, "model": cfg.model, "status": "error"}
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=cfg.call_timeout, transport=self.transport) as c:
                r = await c.post(
                    cfg.base_url.rstrip("/") + "/chat/completions",
                    json=body,
                    headers={"Authorization": f"Bearer {cfg.api_key}"},
                )
            record["http_status"] = r.status_code
            if r.is_error:
                code = "upstream_rate_limit" if r.status_code == 429 else "upstream_error"
                raise VerificationError(code, f"Model provider returned HTTP {r.status_code}.")
            result = r.json()
            record["usage"] = result.get("usage", {})
            choice = result["choices"][0]
            if choice["message"].get("refusal"):
                raise VerificationError("model_refusal", "The model declined this request.")
            if choice.get("finish_reason") != "stop":
                raise VerificationError(
                    "incomplete_output", "Model output did not finish normally."
                )
            record["raw_output"] = choice["message"].get("content")
            parsed = json.loads(record["raw_output"])
            if not isinstance(parsed, dict):
                raise ValueError("expected an object")
            record["status"] = "ok"
            return parsed
        except httpx.TimeoutException as e:
            raise VerificationError("upstream_timeout", "Model request timed out.", 504) from e
        except httpx.HTTPError as e:
            raise VerificationError("upstream_error", "Cannot reach model provider.") from e
        except (ValueError, KeyError, IndexError, TypeError, AttributeError) as e:
            raise VerificationError("invalid_output", "Model returned malformed output.") from e
        finally:
            record["latency_seconds"] = time.perf_counter() - started
            trace.calls.append(record)


def create_model(settings: Settings) -> Model:
    backend = os.getenv("LLM_BACKEND", "http")
    if backend == "http":
        return HTTPModel(settings)
    if backend == "codex":
        from grounding.codex_provider import CodexModel

        return CodexModel(settings)
    raise ValueError("LLM_BACKEND must be http or codex")
