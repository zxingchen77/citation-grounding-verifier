import copy
import json
import runpy
from pathlib import Path

import pytest

from grounding.models import VerificationError, VerifyRequest
from grounding.provider import Trace

ROOT = Path(__file__).resolve().parents[1]
MODULE = runpy.run_path(str(ROOT / "experiments/dev_refinement.py"))
anchored = MODULE["anchored"]
dev_cases = MODULE["dev_cases"]


class ScriptedModel:
    def __init__(self, outputs):
        self.outputs = iter(copy.deepcopy(outputs))
        self.inputs = []

    async def generate(self, system, payload, schema, stage, trace):
        self.inputs.append((stage, payload))
        result = next(self.outputs)
        trace.calls.append({"stage": stage, "status": "ok", "raw_output": json.dumps(result)})
        return result


def fixture():
    request = VerifyRequest(
        context_passages=["Job A starts. Job B stops."],
        generated_answer="Job A starts. Job B stops.",
    )
    extraction = {
        "claims": [
            {"claim_text": text, "answer_quote": text} for text in ["Job A starts.", "Job B stops."]
        ]
    }
    judgments = {
        "judgments": [
            {
                "claim_index": i,
                "verdict": "SUPPORTED",
                "reasoning": "The supplied sentence states this fact.",
                "evidence_ids": [i],
            }
            for i in [1, 0]
        ]
    }
    return request, extraction, judgments


async def test_answer_only_extraction_and_fixed_order_literal_evidence_resolution():
    request, extraction, judgments = fixture()
    model = ScriptedModel([extraction, judgments])
    response = await anchored(request, model, Trace())
    assert model.inputs[0][1] == {"answer": request.generated_answer}
    assert "answer" not in model.inputs[1][1]
    assert [c.claim_text for c in response.claims] == ["Job A starts.", "Job B stops."]
    assert [c.citations[0].quote for c in response.claims] == ["Job A starts.", "Job B stops."]
    assert all(c.citations[0].index == 0 for c in response.claims)


async def test_nonverbatim_answer_anchor_cannot_reach_judgment():
    request, extraction, _ = fixture()
    extraction["claims"][0]["answer_quote"] = "This is only in the sources, not the answer."
    model = ScriptedModel([extraction, extraction])
    with pytest.raises(VerificationError, match="anchor is not verbatim"):
        await anchored(request, model, Trace())
    assert len(model.inputs) == 2
    assert all(stage.endswith("extract") for stage, _ in model.inputs)


@pytest.mark.parametrize("defect", ["missing", "duplicate", "unknown", "negative", "rewrite"])
async def test_fixed_claim_and_evidence_contract_survives_a_failed_repair(defect):
    request, extraction, judgments = fixture()
    if defect == "missing":
        judgments["judgments"].pop()
    elif defect == "duplicate":
        judgments["judgments"][0]["claim_index"] = 0
    elif defect == "unknown":
        judgments["judgments"][0]["evidence_ids"] = [999]
    elif defect == "negative":
        judgments["judgments"][0]["evidence_ids"] = [-1]
    else:
        judgments["judgments"][0]["claim_text"] = "A rewritten source fact."
    model = ScriptedModel([extraction, judgments, judgments])
    with pytest.raises(VerificationError) as error:
        await anchored(request, model, Trace())
    assert error.value.code == "invalid_output"
    assert len(model.inputs) == 3


async def test_empty_context_preserves_extracted_claims_without_second_call():
    request, extraction, _ = fixture()
    request.context_passages = []
    model = ScriptedModel([extraction])
    response = await anchored(request, model, Trace())
    assert len(model.inputs) == 1
    assert len(response.claims) == 2
    assert all(c.verdict == "UNSUPPORTED" and not c.citations for c in response.claims)


def test_development_selector_never_returns_test_inputs():
    cases = [{"id": "dev-case", "split": "dev"}, {"id": "test-canary", "split": "test"}]
    assert dev_cases("\n".join(map(json.dumps, cases)).encode()) == cases[:1]
    with pytest.raises(ValueError, match="test inference is disabled"):
        dev_cases(json.dumps(cases[1]).encode())
    with pytest.raises(ValueError, match="unique"):
        dev_cases("\n".join(map(json.dumps, cases + cases[:1])).encode())


async def test_v5_reuses_literal_id_resolution_and_records_its_own_stage(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT))
    v5 = runpy.run_path(str(ROOT / "experiments/compact_v5.py"))
    request, _, _ = fixture()
    output = {
        "claims": [
            {
                "claim_text": "Job A starts.",
                "verdict": "SUPPORTED",
                "reasoning": "The sentence states it.",
                "evidence_ids": [0],
            }
        ]
    }
    model = ScriptedModel([output])
    trace = Trace()
    response = await v5["candidate"](request, model, trace)
    assert len(model.inputs) == 1
    assert model.inputs[0][0] == "compact-v5"
    assert trace.calls[0]["stage"] == "compact-v5"
    assert response.claims[0].citations[0].quote == "Job A starts."
    assert set(model.inputs[0][1]) == {"answer", "evidence_segments"}


async def test_v5_keeps_the_bounded_structural_repair(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT))
    v5 = runpy.run_path(str(ROOT / "experiments/compact_v5.py"))
    request, _, _ = fixture()
    output = {
        "claims": [
            {
                "claim_text": "Job A starts.",
                "verdict": "SUPPORTED",
                "reasoning": "Invalid source ID.",
                "evidence_ids": [999],
            }
        ]
    }
    model = ScriptedModel([output, output])
    with pytest.raises(VerificationError) as error:
        await v5["candidate"](request, model, Trace())
    assert error.value.code == "invalid_output"
    assert len(model.inputs) == 2
    assert "validation_error" in model.inputs[1][1]
