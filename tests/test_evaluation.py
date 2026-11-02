import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from grounding.models import VerifyRequest
from grounding.scoring import aggregate, score_case

ROOT = Path(__file__).resolve().parents[1]
CASES = [json.loads(line) for line in (ROOT / "data/cases.jsonl").read_text().splitlines()]


def test_dataset_labels_and_frozen_split():
    payload = (ROOT / "data/cases.jsonl").read_bytes()
    manifest = json.loads((ROOT / "data/manifest.json").read_text())
    assert hashlib.sha256(payload).hexdigest() == manifest["sha256"]
    assert len(CASES) == len({c["id"] for c in CASES}) == 40
    families = defaultdict(set)
    for case in CASES:
        families[case["family"]].add(case["split"])
        VerifyRequest(
            context_passages=case["context_passages"], generated_answer=case["generated_answer"]
        )
        for gold in case["gold_claims"]:
            assert (gold["verdict"] == "UNSUPPORTED") == (not gold["evidence_groups"])
            for group in gold["evidence_groups"]:
                assert group
                for e in group:
                    assert e["quote"] in case["context_passages"][e["index"]]
    assert all(len(splits) == 1 for splits in families.values())
    assert Counter(c["split"] for c in CASES) == {"dev": 24, "test": 16}


def perfect(case):
    return {
        "response": {
            "claims": [
                {
                    "claim_text": g["claim_text"],
                    "verdict": g["verdict"],
                    "reasoning": "Reference test fixture.",
                    "citations": g["evidence_groups"][0] if g["evidence_groups"] else [],
                }
                for g in case["gold_claims"]
            ]
        }
    }


def test_missing_and_duplicate_claims_cannot_game_score():
    case = CASES[0]
    record = perfect(case)
    assert aggregate([score_case(record, case)])["f1"] == 1
    record["response"]["claims"].pop()
    assert score_case(record, case)["fn"] == 1
    record["response"]["claims"] *= 2
    score = score_case(record, case)
    assert score["tp"] == 1 and score["fp"] == 1 and score["fn"] == 1
    assert aggregate([score_case({"error": {"code": "timeout"}}, case)])["recall"] == 0


def test_real_quote_without_full_evidence_does_not_get_credit():
    case = next(c for c in CASES if c["category"] == "multi_passage")
    record = perfect(case)
    record["response"]["claims"][0]["citations"] = record["response"]["claims"][0]["citations"][:1]
    assert score_case(record, case)["tp"] == 0


def test_wrong_label_is_counted_as_fp_and_fn():
    case = CASES[1]
    record = perfect(case)
    record["response"]["claims"][0]["verdict"] = "SUPPORTED"
    score = score_case(record, case)
    assert score["tp"] == 1 and score["fp"] == 1 and score["fn"] == 1
    assert score["false_supported"] == 1


def test_reviews_cannot_reuse_a_gold_claim():
    case = CASES[0]
    with pytest.raises(ValueError, match="one-to-one"):
        score_case(
            perfect(case),
            case,
            {
                "note": "Invalid review",
                "matches": [
                    {"prediction_index": 0, "gold_index": 0},
                    {"prediction_index": 1, "gold_index": 0},
                ],
            },
        )
