import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from grounding.api import create_app
from grounding.models import VerificationError, VerifyRequest, VerifyResponse, validate_evidence
from grounding.provider import HTTPModel, Settings, Trace
from grounding.verifiers import verify


def report(verdict="SUPPORTED", quote="Cache lasts 7 days.", index=0):
    return {
        "claims": [
            {
                "claim_text": "Cache lasts 7 days.",
                "verdict": verdict,
                "reasoning": "The source gives this duration.",
                "citations": [{"index": index, "quote": quote}],
            }
        ]
    }


class FakeModel:
    def __init__(self, *outputs):
        self.outputs = iter(outputs)
        self.calls = []

    async def generate(self, system, payload, schema, stage, trace):
        self.calls.append((stage, payload))
        value = next(self.outputs)
        if isinstance(value, Exception):
            raise value
        return value


@pytest.mark.parametrize("quote,index", [("Cache lasts 8 days.", 0), ("Cache lasts", 1), (" ", 0)])
def test_invalid_evidence(quote, index):
    with pytest.raises(VerificationError):
        validate_evidence(
            VerifyResponse.model_validate(report(quote=quote, index=index)), ["Cache lasts 7 days."]
        )


@pytest.mark.parametrize("index", [True, -1, "0"])
def test_strict_indices(index):
    with pytest.raises(ValidationError):
        VerifyResponse.model_validate(report(index=index))


def test_unsupported_must_not_have_citations():
    with pytest.raises(VerificationError):
        validate_evidence(
            VerifyResponse.model_validate(report("UNSUPPORTED")), ["Cache lasts 7 days."]
        )


def test_exact_unicode_quote_preserved():
    raw = report(quote="日志保留七天。")
    assert validate_evidence(VerifyResponse.model_validate(raw), ["日志保留七天。"]).claims
    raw["claims"][0]["citations"][0]["quote"] = "日志保留七天."
    with pytest.raises(VerificationError):
        validate_evidence(VerifyResponse.model_validate(raw), ["日志保留七天。"])


def test_http_schema_and_quote_validation():
    model = FakeModel(report(), report(quote="made up"))
    client = TestClient(create_app(model=model, method="minimal"))
    body = {"context_passages": ["Cache lasts 7 days."], "generated_answer": "Cache lasts 7 days."}
    assert client.post("/verify", json=body).json() == report()
    response = client.post("/verify", json=body)
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "invalid_output"
    assert client.post("/verify", json={**body, "extra": 1}).status_code == 422
    assert client.post("/verify", json={**body, "context_passages": "wrong"}).status_code == 422


def test_empty_answer_skips_provider():
    model = FakeModel()
    client = TestClient(create_app(model=model, method="optimized"))
    assert client.post(
        "/verify", json={"context_passages": [], "generated_answer": " "}
    ).json() == {"claims": []}
    assert not model.calls


@pytest.mark.parametrize(
    "body",
    [
        '{"generated_answer": "private text"}',
        '{"context_passages": "private text", "generated_answer": "A is B."}',
        '{"context_passages": [], "generated_answer": "A is B.", "extra": "private text"}',
        '{"context_passages": ["' + "x" * 32001 + '"], "generated_answer": "A is B."}',
        '{"generated_answer": "private text"',
    ],
    ids=["missing-field", "wrong-type", "extra-field", "context-limit", "malformed-json"],
)
def test_invalid_request_uses_error_envelope_without_inference(body):
    model = FakeModel()
    client = TestClient(create_app(model=model, method="optimized"))
    response = client.post("/verify", content=body, headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Request body does not match the verification schema.",
        }
    }
    assert not model.calls


def test_openapi_describes_validation_error_envelope():
    client = TestClient(create_app(model=FakeModel(), method="optimized"))
    schema = client.get("/openapi.json").json()
    error_schema = schema["paths"]["/verify"]["post"]["responses"]["422"]
    assert error_schema["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorResponse"
    }
    assert schema["components"]["schemas"]["ErrorResponse"]["required"] == ["error"]


async def test_staged_preserves_claims_and_repairs_missing_judgment():
    extraction = {
        "claims": [
            {"claim_text": "The cache lasts 7 days.", "answer_quote": "lasts 7 days"},
            {"claim_text": "The cache is encrypted.", "answer_quote": "is encrypted"},
        ]
    }
    good = {
        "judgments": [
            {
                "claim_index": 1,
                "verdict": "UNSUPPORTED",
                "reasoning": "Encryption is not stated.",
                "citations": [],
            },
            {
                "claim_index": 0,
                "verdict": "SUPPORTED",
                "reasoning": "Duration is explicit.",
                "citations": [{"index": 0, "quote": "Cache lasts 7 days."}],
            },
        ]
    }
    model = FakeModel(extraction, {"judgments": []}, good)
    request = VerifyRequest(
        context_passages=["Cache lasts 7 days."],
        generated_answer="The cache lasts 7 days and is encrypted.",
    )
    result = await verify(request, "staged", model)
    assert [c.claim_text for c in result.claims] == [c["claim_text"] for c in extraction["claims"]]
    assert [c.verdict for c in result.claims] == ["SUPPORTED", "UNSUPPORTED"]
    assert len(model.calls) == 3
    assert "context_passages" not in model.calls[0][1]


async def test_repairs_exhausted_never_downgrade_to_unsupported():
    bad = {"claims": [{"claim_text": "x", "answer_quote": "invented"}]}
    model = FakeModel(bad, bad)
    with pytest.raises(VerificationError, match="not verbatim"):
        await verify(
            VerifyRequest(context_passages=[], generated_answer="Actual answer."),
            "staged",
            model,
        )
    assert len(model.calls) == 2


async def test_empty_context_preserves_facts_as_unsupported():
    model = FakeModel(
        {"claims": [{"claim_text": "It has encryption.", "answer_quote": "It has encryption."}]}
    )
    result = await verify(
        VerifyRequest(context_passages=[], generated_answer="It has encryption."),
        "staged",
        model,
    )
    assert result.claims[0].verdict == "UNSUPPORTED"
    assert len(model.calls) == 1


async def test_deadline_is_system_error():
    class Slow:
        async def generate(self, *args):
            await asyncio.sleep(1)

    with pytest.raises(VerificationError) as err:
        await verify(
            VerifyRequest(context_passages=[], generated_answer="A is B."),
            "minimal",
            Slow(),
            timeout=0.001,
        )
    assert err.value.code == "verification_timeout"


@pytest.mark.parametrize("status", [401, 429, 500])
async def test_provider_errors_do_not_leak_body_or_key(status):
    transport = httpx.MockTransport(lambda _: httpx.Response(status, text="private secret details"))
    model = HTTPModel(Settings(model="test", api_key="test-secret"), transport)
    trace = Trace()
    with pytest.raises(VerificationError) as err:
        await model.generate("test", {}, {}, "test", trace)
    assert "secret" not in str(err.value)
    assert "test-secret" not in str(trace.as_dict())
    assert len(trace.calls) == 1


async def test_provider_tracks_usage_on_truncated_output():
    response = {
        "choices": [{"finish_reason": "length", "message": {"content": "{}"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    model = HTTPModel(
        Settings(model="test", api_key="fake"),
        httpx.MockTransport(lambda _: httpx.Response(200, json=response)),
    )
    trace = Trace()
    with pytest.raises(VerificationError) as err:
        await model.generate("test", {}, {}, "test", trace)
    assert err.value.code == "incomplete_output"
    assert trace.calls[0]["usage"]["completion_tokens"] == 5


@pytest.mark.parametrize("method", ["optimized", "optimized-v2"])
async def test_compact_selects_two_sources_without_generating_quotes(method):
    model = FakeModel(
        {
            "claims": [
                {
                    "claim_text": "Nova has a 300 ms timeout.",
                    "verdict": "SUPPORTED",
                    "reasoning": "Nova uses this profile.",
                    "evidence_ids": [0, 1],
                }
            ]
        }
    )
    request = VerifyRequest(
        context_passages=["Nova uses profile A.", "Profile A times out at 300 ms."],
        generated_answer="Nova has a 300 ms timeout.",
    )
    result = await verify(request, method, model)
    assert [c.index for c in result.claims[0].citations] == [0, 1]
    assert [c.quote for c in result.claims[0].citations] == request.context_passages
    assert len(model.calls) == 1


@pytest.mark.parametrize("method", ["optimized", "optimized-v2"])
async def test_compact_repairs_unknown_evidence_id(method):
    bad = {
        "claims": [
            {
                "claim_text": "A is B.",
                "verdict": "SUPPORTED",
                "reasoning": "Stated.",
                "evidence_ids": [99],
            }
        ]
    }
    good = {
        "claims": [
            {
                "claim_text": "A is B.",
                "verdict": "SUPPORTED",
                "reasoning": "Stated.",
                "evidence_ids": [0],
            }
        ]
    }
    model = FakeModel(bad, good)
    result = await verify(
        VerifyRequest(context_passages=["A is B."], generated_answer="A is B."), method, model
    )
    assert result.claims[0].citations[0].quote == "A is B."
    assert len(model.calls) == 2
