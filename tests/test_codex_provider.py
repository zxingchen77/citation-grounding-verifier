"""Exercise real subprocess pipes without invoking Codex or making model calls."""

import asyncio
import json
import sys

import pytest

from grounding.codex_provider import CodexModel
from grounding.models import VerificationError, VerifyRequest
from grounding.provider import Settings, Trace
from grounding.verifiers import verify

CHILD = """
import json, pathlib, sys, time
cfg = json.loads(sys.argv[1])
sys.stdin.buffer.read()
for event in cfg.get('events', []):
    print(json.dumps(event), flush=True)
sys.stderr.write('private-diagnostic-secret' * cfg.get('stderr_copies', 0))
sys.stderr.flush()
time.sleep(cfg.get('delay', 0))
if cfg.get('output', True):
    pathlib.Path(sys.argv[2]).write_text(cfg.get('raw', '{"claims": []}'))
sys.exit(cfg.get('exit_code', 0))
"""


@pytest.fixture
def child_process(monkeypatch):
    original = asyncio.create_subprocess_exec
    processes = []

    def configure(**config):
        async def spawn(*args, **kwargs):
            assert "read-only" in args and "--ignore-user-config" in args
            assert all(x in args for x in ["shell_tool", "multi_agent", "apps"])
            output = args[args.index("--output-last-message") + 1]
            process = await original(
                sys.executable, "-u", "-c", CHILD, json.dumps(config), output, **kwargs
            )
            processes.append(process)
            return process

        monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
        return processes

    return configure


@pytest.mark.parametrize("started", [False, True])
async def test_timeout_retains_progress_and_kills_process(child_process, started):
    processes = child_process(
        events=[{"type": "turn.started"}] if started else [], delay=5, stderr_copies=10000
    )
    trace = Trace()
    with pytest.raises(VerificationError) as error:
        await CodexModel(Settings(model="test", call_timeout=0.5)).generate(
            "prompt", {}, {}, "stage", trace
        )
    assert error.value.code == "upstream_timeout"
    assert processes[0].returncode == -9
    call = trace.calls[0]
    assert call["error_code"] == "upstream_timeout"
    assert call["last_phase"] == ("turn_in_progress" if started else "waiting_for_first_event")
    assert ("turn.started" in call["progress_seconds"]) == started
    assert "private-diagnostic-secret" not in json.dumps(trace.as_dict())
    assert "usage" not in call


async def test_request_deadline_cancels_and_reaps_child(child_process):
    processes = child_process(events=[{"type": "turn.started"}], delay=5)
    trace = Trace()
    with pytest.raises(VerificationError) as error:
        await verify(
            VerifyRequest(context_passages=[], generated_answer="A is B."),
            "minimal",
            CodexModel(Settings(model="test", call_timeout=5)),
            trace,
            timeout=0.5,
        )
    assert error.value.code == "verification_timeout"
    assert processes[0].returncode == -9
    assert trace.calls[0]["error_code"] == "cancelled"


async def test_tool_event_is_rejected_before_child_finishes(child_process):
    processes = child_process(
        events=[{"type": "item.completed", "item": {"type": "command_execution"}}], delay=5
    )
    trace = Trace()
    with pytest.raises(VerificationError) as error:
        await CodexModel(Settings(model="test", call_timeout=1)).generate(
            "prompt", {}, {}, "stage", trace
        )
    assert error.value.code == "unexpected_tool_use"
    assert processes[0].returncode == -9
    assert trace.calls[0]["error_code"] == "unexpected_tool_use"


@pytest.mark.parametrize("usage", [None, {}, {"input_tokens": -1, "output_tokens": True}])
async def test_missing_usage_is_not_invented_as_zero(child_process, usage):
    child_process(events=[{"type": "turn.completed", "usage": usage}])
    trace = Trace()
    await CodexModel(Settings(model="test")).generate("prompt", {}, {}, "stage", trace)
    assert trace.calls[0]["usage"] == {}


async def test_progress_usage_and_large_stderr_are_drained(child_process):
    child_process(
        events=[
            {"type": "turn.started"},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "private"}},
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "cached_input_tokens": 3,
                },
            },
        ],
        stderr_copies=10000,
    )
    trace = Trace()
    assert await CodexModel(Settings(model="test")).generate("prompt", {}, {}, "stage", trace) == {
        "claims": []
    }
    call = trace.calls[0]
    assert call["usage"] == {"prompt_tokens": 10, "completion_tokens": 5, "cached_input_tokens": 3}
    assert call["last_phase"] == "complete" and call["stderr_bytes"] > 65536
    assert list(call["progress_seconds"].values()) == sorted(call["progress_seconds"].values())
    assert "private" not in json.dumps(trace.as_dict())


@pytest.mark.parametrize(
    "config,code",
    [
        ({"exit_code": 1}, "upstream_error"),
        (
            {"events": [{"type": "turn.failed", "error": {"message": "private-secret"}}]},
            "upstream_error",
        ),
        ({"output": False}, "incomplete_output"),
        ({"raw": "not-json"}, "invalid_output"),
    ],
)
async def test_failure_codes_are_retained_without_diagnostic_bodies(child_process, config, code):
    child_process(**config)
    trace = Trace()
    with pytest.raises(VerificationError) as error:
        await CodexModel(Settings(model="test")).generate("prompt", {}, {}, "stage", trace)
    assert error.value.code == code
    assert trace.calls[0]["error_code"] == code
    assert "private-secret" not in str(error.value) + json.dumps(trace.as_dict())
