import asyncio
import json
from pathlib import Path

import httpx
import pytest

from grounding.benchmark import summarize
from grounding.codex_provider import CodexModel
from grounding.models import VerificationError, VerifyRequest
from grounding.provider import HTTPModel, Settings, Trace
from grounding.scoring import score_case
from grounding.verifiers import verify


class FakeProcess:
    returncode = None
    killed = False

    def __init__(self, output, event=None, delay=0):
        self.output = output
        self.event = event
        self.delay = delay

    async def communicate(self, _input):
        await asyncio.sleep(self.delay)
        self.output.write_text('{"claims": []}')
        self.returncode = 0
        return (json.dumps(self.event or {}).encode(), b"")

    def kill(self):
        self.killed = True
        self.returncode = -9

    async def wait(self):
        return self.returncode


async def test_codex_timeout_kills_process(monkeypatch):
    processes = []

    async def spawn(*args, **kwargs):
        assert "read-only" in args and "--ignore-user-config" in args
        assert "shell_tool" in args and "multi_agent" in args and "apps" in args
        p = FakeProcess(Path(args[args.index("--output-last-message") + 1]), delay=1)
        processes.append(p)
        return p

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    trace = Trace()
    with pytest.raises(VerificationError) as error:
        await CodexModel(Settings(model="test", call_timeout=0.001)).generate(
            "prompt", {}, {}, "stage", trace
        )
    assert error.value.code == "upstream_timeout"
    assert processes[0].killed
    assert len(trace.calls) == 1


async def test_codex_rejects_tool_assisted_results(monkeypatch):
    async def spawn(*args, **kwargs):
        return FakeProcess(
            Path(args[args.index("--output-last-message") + 1]),
            {"type": "item.completed", "item": {"type": "command_execution"}},
        )

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    with pytest.raises(VerificationError) as error:
        await CodexModel(Settings(model="test")).generate("prompt", {}, {}, "stage", Trace())
    assert error.value.code == "unexpected_tool_use"


@pytest.mark.parametrize("usage", [None, {}, {"input_tokens": -1, "output_tokens": True}])
async def test_codex_missing_usage_is_not_invented_as_zero(monkeypatch, usage):
    async def spawn(*args, **kwargs):
        return FakeProcess(
            Path(args[args.index("--output-last-message") + 1]),
            {"type": "turn.completed", "usage": usage},
        )

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    trace = Trace()
    await CodexModel(Settings(model="test")).generate("prompt", {}, {}, "stage", trace)
    assert trace.calls[0]["usage"] == {}


@pytest.mark.parametrize("body", [[], None, {"choices": []}])
async def test_malformed_provider_envelope_is_a_controlled_error(body):
    model = HTTPModel(
        Settings(model="test", api_key="fake"),
        httpx.MockTransport(lambda _: httpx.Response(200, json=body)),
    )
    with pytest.raises(VerificationError) as error:
        await model.generate("prompt", {}, {}, "stage", Trace())
    assert error.value.code == "invalid_output"


async def test_baseline_claim_limit_is_explicit():
    request = VerifyRequest(context_passages=[], generated_answer="A is a fact. " * 65)
    with pytest.raises(VerificationError) as error:
        await verify(request, "deterministic")
    assert error.value.code == "too_many_claims" and error.value.status_code == 422


async def test_baseline_oversize_claim_is_a_controlled_error():
    with pytest.raises(VerificationError) as error:
        await verify(
            VerifyRequest(context_passages=[], generated_answer="a" * 4001), "deterministic"
        )
    assert error.value.code == "claim_too_long" and error.value.status_code == 422


def test_rescoring_prices_are_pinned_and_subscription_is_not_free(monkeypatch):
    case = {
        "id": "x",
        "category": "extrinsic",
        "split": "dev",
        "context_passages": [],
        "gold_claims": [{"claim_text": "A is B.", "verdict": "UNSUPPORTED", "evidence_groups": []}],
    }
    record = {
        "case_id": "x",
        "method": "minimal",
        "repeat": 0,
        "latency_seconds": 1,
        "response": {
            "claims": [{"claim_text": "A is B.", "verdict": "UNSUPPORTED", "citations": []}]
        },
        "trace": {"calls": [{"usage": {"prompt_tokens": 10, "completion_tokens": 5}}]},
    }
    manifest = {"backend": "http", "input_price_per_million": "1", "output_price_per_million": "2"}
    monkeypatch.setenv("INPUT_PRICE_PER_MILLION", "9999")
    result = summarize([record], {"x": case}, {}, manifest)["minimal"]
    assert result["estimated_usd"] == 0.00002
    result = summarize([record], {"x": case}, {}, {**manifest, "backend": "codex"})["minimal"]
    assert result["estimated_usd"] is None


def test_review_cannot_override_nonverbatim_quote():
    case = {
        "id": "x",
        "category": "supported",
        "split": "dev",
        "context_passages": ["A is B."],
        "gold_claims": [
            {
                "claim_text": "A is B.",
                "verdict": "SUPPORTED",
                "evidence_groups": [[{"index": 0, "quote": "A is B."}]],
            }
        ],
    }
    record = {
        "response": {
            "claims": [
                {
                    "claim_text": "A is B.",
                    "verdict": "SUPPORTED",
                    "citations": [{"index": 0, "quote": "invented"}],
                }
            ]
        }
    }
    review = {
        "note": "Cannot turn invented evidence into a valid quote.",
        "matches": [{"prediction_index": 0, "gold_index": 0, "evidence_sufficient": True}],
    }
    assert score_case(record, case, review)["tp"] == 0
