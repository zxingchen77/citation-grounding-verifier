import asyncio
import json

import httpx
import pytest

from grounding.models import VerificationError, VerifyRequest, VerifyResponse
from grounding.provider import HTTPModel, Settings, Trace
from grounding.verifiers import verify


async def test_http_request_deadline_cancels_transport_and_retains_failed_call():
    async def handler(_request):
        await asyncio.sleep(1)
        return httpx.Response(200, json=envelope('{"claims": []}'))

    model = HTTPModel(Settings(model="test", api_key="fake"), httpx.MockTransport(handler))
    trace = Trace()
    with pytest.raises(VerificationError) as error:
        await verify(
            VerifyRequest(context_passages=[], generated_answer="A is B."),
            "optimized",
            model,
            trace,
            timeout=0.001,
        )
    assert error.value.code == "verification_timeout" and error.value.status_code == 504
    assert len(trace.calls) == 1 and trace.calls[0]["error_code"] == "cancelled"


async def test_invalid_evidence_id_is_recorded_as_a_failed_repair_call():
    calls = 0

    def handler(_request):
        nonlocal calls
        calls += 1
        content = {
            "claims": [
                {
                    "claim_text": "A is B.",
                    "verdict": "SUPPORTED",
                    "reasoning": "Explicit source.",
                    "evidence_ids": [99 if calls == 1 else 0],
                }
            ]
        }
        return httpx.Response(200, json=envelope(json.dumps(content)))

    model = HTTPModel(Settings(model="test", api_key="fake"), httpx.MockTransport(handler))
    trace = Trace()
    result = await verify(
        VerifyRequest(context_passages=["A is B."], generated_answer="A is B."),
        "optimized",
        model,
        trace,
    )
    assert result.claims[0].citations[0].quote == "A is B."
    assert [c["status"] for c in trace.calls] == ["error", "ok"]
    assert trace.calls[0]["error_code"] == "invalid_output"
    assert "Evidence ID" in trace.calls[0]["validation_error"]


def envelope(content, finish="stop", refusal=None):
    return {
        "model": "resolved-test-version",
        "choices": [{"finish_reason": finish, "message": {"content": content, "refusal": refusal}}],
        "usage": {
            "prompt_tokens": 20,
            "completion_tokens": 4,
            "prompt_tokens_details": {"cached_tokens": 7},
        },
    }


async def test_strict_http_request_success_and_cache_accounting():
    def handler(request):
        assert str(request.url) == "https://provider.invalid/v1/chat/completions"
        body = json.loads(request.content)
        assert body["model"] == "test" and body["max_completion_tokens"] == 128
        assert body["temperature"] == 0
        assert body["response_format"]["json_schema"] == {
            "name": "grounding_output",
            "strict": True,
            "schema": VerifyResponse.model_json_schema(),
        }
        assert json.loads(body["messages"][1]["content"]) == {"data": "original"}
        return httpx.Response(200, json=envelope('{"claims": []}'))

    model = HTTPModel(
        Settings(
            model="test",
            api_key="sentinel-key",
            base_url="https://provider.invalid/v1/",
            temperature=0,
            max_output_tokens=128,
        ),
        httpx.MockTransport(handler),
    )
    trace = Trace()
    assert await model.generate(
        "test", {"data": "original"}, VerifyResponse.model_json_schema(), "test", trace
    ) == {"claims": []}
    assert trace.calls[0]["usage"]["cached_input_tokens"] == 7
    assert trace.calls[0]["response_model"] == "resolved-test-version"
    assert "sentinel-key" not in json.dumps(trace.as_dict())


@pytest.mark.parametrize(
    "failure,code,status",
    [
        ("timeout", "upstream_timeout", 504),
        ("network", "upstream_error", 502),
        ("refusal", "model_refusal", 502),
        ("truncated", "incomplete_output", 502),
        ("rate_limit", "upstream_rate_limit", 502),
    ],
)
async def test_nonrepairable_http_errors_have_one_call_and_preserve_usage(failure, code, status):
    def handler(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("sensitive provider message", request=request)
        if failure == "network":
            raise httpx.ConnectError("sensitive provider message", request=request)
        if failure == "rate_limit":
            return httpx.Response(429, text="sensitive provider body")
        return httpx.Response(
            200,
            json=envelope(
                "partial",
                finish="length" if failure == "truncated" else "stop",
                refusal="refused" if failure == "refusal" else None,
            ),
        )

    model = HTTPModel(Settings(model="test", api_key="fake"), httpx.MockTransport(handler))
    trace = Trace()
    with pytest.raises(VerificationError) as error:
        await verify(
            VerifyRequest(context_passages=[], generated_answer="A is B."),
            "optimized",
            model,
            trace,
        )
    assert error.value.code == code and error.value.status_code == status
    assert len(trace.calls) == 1 and trace.calls[0]["error_code"] == code
    assert "sensitive" not in json.dumps(trace.as_dict()) + str(error.value)
    if failure in {"refusal", "truncated"}:
        assert trace.calls[0]["usage"]["completion_tokens"] == 4
        assert trace.calls[0]["raw_output"] == "partial"


@pytest.mark.parametrize("repair_succeeds", [True, False])
async def test_http_malformed_output_repair_is_bounded_and_all_usage_is_retained(repair_succeeds):
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        content = '{"claims": []}' if repair_succeeds and len(requests) == 2 else "not JSON"
        return httpx.Response(200, json=envelope(content))

    model = HTTPModel(Settings(model="test", api_key="fake"), httpx.MockTransport(handler))
    trace = Trace()
    request = VerifyRequest(context_passages=[], generated_answer="Hello!")
    if repair_succeeds:
        assert not (await verify(request, "optimized", model, trace)).claims
    else:
        with pytest.raises(VerificationError) as error:
            await verify(request, "optimized", model, trace)
        assert error.value.code == "invalid_output"
    assert len(trace.calls) == len(requests) == 2
    assert sum(c["usage"]["prompt_tokens"] for c in trace.calls) == 40
    repair_payload = json.loads(requests[1]["messages"][1]["content"])
    assert repair_payload["original_input"]["answer"] == "Hello!"
    assert "validation_error" in repair_payload
