import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from grounding.dataset import inspect_dataset, validate_document_cases
from grounding.models import VerificationError
from grounding.scoring import aggregate, score_case

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/cases.jsonl"
CASES = [json.loads(line) for line in DATA.read_text().splitlines()]
SOURCES = json.loads((ROOT / "data/sources/real-docs-v3.json").read_text())["sources"]


def test_real_corpus_provenance_balance_and_gold():
    result = inspect_dataset(DATA)
    manifest = json.loads((ROOT / "data/manifest.json").read_text())
    assert result["sha256"] == manifest["sha256"]
    assert result["statistics"]["all"]["cases"] == 32
    for split, size in [("dev", 5), ("test", 3)]:
        assert Counter(c["category"] for c in CASES if c["split"] == split) == {
            "supported": size,
            "distortion": size,
            "extrinsic": size,
            "multi_passage": size,
        }
    assert all(
        c["provenance"]["annotation_status"] == "AI-drafted; human author review pending"
        for c in CASES
    )
    for source in SOURCES.values():
        assert (ROOT / source["license_snapshot"]).is_file()
    for path, key in [
        ("data/real-docs-v3/spec.json", "spec_sha256"),
        ("data/sources/real-docs-v3.json", "sources_sha256"),
    ]:
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == manifest[key]


def test_tampered_source_and_distractor_are_rejected():
    cases = copy.deepcopy(CASES)
    cases[0]["context_passages"][0] = cases[0]["context_passages"][0].replace(
        "SQLite", "OtherDB", 1
    )
    with pytest.raises(ValueError, match="differs"):
        validate_document_cases(cases, SOURCES)
    cases = copy.deepcopy(CASES)
    cases[0]["distractor_passage_indices"] = [999]
    with pytest.raises(ValueError, match="Distractors"):
        validate_document_cases(cases, SOURCES)


def test_same_source_cannot_leak_across_splits():
    cases = copy.deepcopy(CASES)
    clone = copy.deepcopy(cases[0])
    clone.update(id="unrelated-name", family="unrelated-family", split="dev")
    cases.append(clone)
    with pytest.raises(ValueError, match="Source documents"):
        validate_document_cases(cases, SOURCES)


def test_invalid_gold_quote_and_index_are_rejected(tmp_path):
    # Keep source lookup beside the temporary mutated corpus.
    (tmp_path / "sources").symlink_to(ROOT / "data/sources", target_is_directory=True)
    for field, bad in [("quote", "invented source text"), ("index", -1), ("index", 999)]:
        cases = copy.deepcopy(CASES)
        cases[0]["gold_claims"][0]["evidence_groups"][0][0][field] = bad
        path = tmp_path / "cases.jsonl"
        path.write_text("".join(json.dumps(c) + "\n" for c in cases))
        with pytest.raises((ValueError, VerificationError)):
            inspect_dataset(path)


def test_verdict_metrics_include_misses_duplicates_and_request_failures():
    case = {
        "id": "a",
        "category": "fixture",
        "split": "dev",
        "context_passages": ["A is B. C is D."],
        "gold_claims": [
            {
                "claim_text": "A is B.",
                "verdict": "SUPPORTED",
                "evidence_groups": [[{"index": 0, "quote": "A is B."}]],
            },
            {"claim_text": "E is F.", "verdict": "UNSUPPORTED", "evidence_groups": []},
        ],
    }
    prediction = {
        "claim_text": "A is B.",
        "verdict": "SUPPORTED",
        "citations": [{"index": 0, "quote": "A is B."}, {"index": 0, "quote": "C is D."}],
    }
    score = score_case({"response": {"claims": [prediction, prediction]}}, case)
    result = aggregate([score, score_case({"error": {"code": "timeout"}}, case)])
    assert result["verdict_per_class"]["SUPPORTED"] == {
        "tp": 1,
        "predicted": 2,
        "gold": 2,
        "fp": 1,
        "fn": 1,
        "precision": 0.5,
        "recall": 0.5,
        "f1": 0.5,
    }
    assert result["verdict_per_class"]["UNSUPPORTED"]["fn"] == 2
    assert result["verdict_macro_f1"] == pytest.approx(1 / 6)
    assert result["quote_validity"] == 1
    assert result["citation_gold_hit_rate"] == 0.25  # unrelated + duplicate quotes earn no hit
    assert result["request_failures"] == 1
