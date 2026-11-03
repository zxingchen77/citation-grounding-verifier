import copy
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from grounding.benchmark import summarize, write_summary
from grounding.dataset import inspect_dataset
from grounding.experiment import make_schedule, paired_analysis, validate_records
from grounding.scoring import covered_by_quotes, score_case
from grounding.verifiers import sentences

ROOT = Path(__file__).resolve().parents[1]


def test_joint_literal_coverage_never_skips_negation_conditions_or_passages():
    source = "A must not open; B may open. Approval is required."
    assert covered_by_quotes(source, sentences(source), source)
    assert not covered_by_quotes(source, ["A must", "open", "B may open."], source)
    assert not covered_by_quotes(source, ["A must not open", "B may open."], source)
    assert not covered_by_quotes(source, ["A must open; B may open. Approval is required."], source)
    case = {
        "id": "joint",
        "category": "fixture",
        "split": "dev",
        "context_passages": [source, "Approval is required."],
        "gold_claims": [
            {
                "claim_text": "B may open with approval.",
                "verdict": "SUPPORTED",
                "evidence_groups": [[{"index": 0, "quote": source}]],
            }
        ],
    }
    prediction = {
        "claim_text": "B may open with approval.",
        "verdict": "SUPPORTED",
        "citations": [{"index": 0, "quote": s} for s in sentences(source)],
    }
    assert score_case({"response": {"claims": [prediction]}}, case)["tp"] == 1
    prediction["citations"][-1]["index"] = 1
    assert score_case({"response": {"claims": [prediction]}}, case)["tp"] == 0


def test_joint_coverage_locates_raw_substrings_before_ignoring_separators():
    source = "IDs 1; 2. An unrelated field says IDs 12."
    assert not covered_by_quotes("IDs 1; 2.", ["IDs 12."], source)
    assert covered_by_quotes("IDs 1; 2.", ["IDs 1", "2."], source)
    words = "A cannot enter. Elsewhere the label reads A can not enter."
    assert not covered_by_quotes("A cannot enter.", ["A can not enter."], words)
    assert covered_by_quotes("A cannot enter.", ["A cannot enter."], words)


def test_every_challenge_reference_accepts_complete_segmented_evidence():
    for case in map(json.loads, (ROOT / "data/challenge-v1/cases.jsonl").read_text().splitlines()):
        predictions = []
        for gold in case["gold_claims"]:
            predictions.append(
                {
                    "claim_text": gold["claim_text"],
                    "verdict": gold["verdict"],
                    "citations": [
                        {"index": ref["index"], "quote": part}
                        for ref in (gold["evidence_groups"][0] if gold["evidence_groups"] else [])
                        for part in sentences(ref["quote"])
                    ],
                }
            )
        assert score_case({"response": {"claims": predictions}}, case)["tp"] == len(predictions), (
            case["id"]
        )


def test_challenge_integrity_complexity_and_capability_coverage():
    path = ROOT / "data/challenge-v1/cases.jsonl"
    inspection = inspect_dataset(path)
    manifest = json.loads(path.with_name("manifest.json").read_text())
    for key, value in inspection.items():
        assert manifest[key] == json.loads(json.dumps(value))
    stats = inspection["statistics"]
    assert stats["dev"]["cases"] == stats["test"]["cases"] == 12
    assert stats["all"]["mixed_label_cases"] >= 18
    assert stats["all"]["three_label_cases"] >= 6
    assert 500 <= stats["all"]["context_characters"]["min"]
    assert stats["all"]["context_characters"]["max"] <= 2000
    assert set(stats["test"]["capabilities"]) <= set(stats["dev"]["capabilities"])
    assert set(stats["all"]["claims_per_case"]) <= {3, 4, 5, 6}
    original = [json.loads(line) for line in (ROOT / "data/cases.jsonl").read_text().splitlines()]
    assert set(inspection["families"]).isdisjoint(c["family"] for c in original)


def test_challenge_reference_audit_preserves_inputs_verdicts_and_all_heldout_records():
    folder = ROOT / "data/challenge-v1"
    original = {
        c["id"]: c
        for c in map(
            json.loads, (folder / "revisions/cases-initial.jsonl").read_text().splitlines()
        )
    }
    current = [json.loads(line) for line in (folder / "cases.jsonl").read_text().splitlines()]
    for case in current:
        old = original[case["id"]]
        for field in ["context_passages", "generated_answer", "family", "split", "category"]:
            assert old[field] == case[field]
        assert [(g["claim_text"], g["verdict"]) for g in old["gold_claims"]] == [
            (g["claim_text"], g["verdict"]) for g in case["gold_claims"]
        ]
        if case["split"] == "test":
            assert old == case


def test_balanced_schedule_pairs_rounds_and_single_baseline():
    ids = [f"case-{i}" for i in range(12)]
    methods = ["deterministic", "minimal", "optimized"]
    jobs = make_schedule(ids, methods, 3, "balanced", 28, 1)
    assert jobs == make_schedule(ids, methods, 3, "balanced", 28, 1)
    assert jobs != make_schedule(ids, methods, 3, "balanced", 29, 1)
    assert Counter(j["method"] for j in jobs) == {
        "deterministic": 12,
        "minimal": 36,
        "optimized": 36,
    }
    by_pair = defaultdict(list)
    for job in jobs:
        by_pair[job["pair_id"]].append(job["method"])
    for repeat in range(3):
        orders = [by_pair[f"{repeat}/{case_id}"] for case_id in ids]
        assert sum(o.index("minimal") < o.index("optimized") for o in orders) == 6
        for position in range(len(orders[0])):
            assert len(set(Counter(o[position] for o in orders).values())) == 1
    validate_records(jobs, jobs)
    with pytest.raises(ValueError, match="Duplicate"):
        validate_records(jobs + jobs[:1])
    with pytest.raises(ValueError, match="complete execution schedule"):
        validate_records(jobs[:-1], jobs)
    changed = copy.deepcopy(jobs)
    changed[0]["pair_id"] = "wrong"
    with pytest.raises(ValueError, match="pair ID"):
        validate_records(changed, jobs)


def test_legacy_schedule_and_invalid_parameters():
    assert [
        (j["method"], j["repeat"], j["case_id"])
        for j in make_schedule(["a", "b"], ["minimal", "optimized"], 2)
    ] == [(m, r, c) for m in ["minimal", "optimized"] for r in range(2) for c in ["a", "b"]]
    for methods, repeats, det_repeats in [
        (["minimal", "minimal"], 1, None),
        (["minimal"], 0, None),
        (["deterministic"], 2, 3),
    ]:
        with pytest.raises(ValueError):
            make_schedule(["a"], methods, repeats, deterministic_repeats=det_repeats)


def paired_fixture():
    cases, records = {}, []
    for i in range(4):
        case_id = str(i)
        cases[case_id] = {
            "id": case_id,
            "family": str(i // 2),
            "category": "fixture",
            "split": "dev",
            "context_passages": [],
            "gold_claims": [
                {"claim_text": "A is B.", "verdict": "UNSUPPORTED", "evidence_groups": []}
            ],
        }
        for method in ["minimal", "optimized"]:
            records.append(
                {
                    "case_id": case_id,
                    "method": method,
                    "repeat": 0,
                    "latency_seconds": 3 if method == "minimal" else 2,
                    "trace": {"calls": []},
                    "response": {
                        "claims": [
                            {"claim_text": "A is B.", "verdict": "UNSUPPORTED", "citations": []}
                        ]
                    },
                }
            )
    # Keep a failed request in the pair, contributing an FN and latency.
    records[-1]["error"] = {"code": "upstream_timeout"}
    del records[-1]["response"]
    return cases, records


def test_cluster_bootstrap_keeps_repeats_and_failures_with_their_cases(tmp_path):
    cases, records = paired_fixture()
    first = paired_analysis(records, cases, {}, samples=100)["comparisons"][0]
    repeated = records + [{**r, "repeat": 1} for r in records]
    second = paired_analysis(repeated, cases, {}, samples=100)["comparisons"][0]
    assert first["unique_cases"] == second["unique_cases"] == 4
    assert first["clusters"] == second["clusters"] == 2
    assert first["f1_difference"] == second["f1_difference"]
    assert first["f1_difference"]["estimate"] == pytest.approx(6 / 7 - 1)
    assert first["mean_case_latency_difference_seconds"]["estimate"] == -1
    assert second["paired_requests"] == 8
    write_summary(tmp_path, repeated, cases, {}, {"bootstrap_samples": 100})
    rounds = json.loads((tmp_path / "rounds.json").read_text())
    assert set(rounds) == {"0", "1"}
    assert rounds["1"]["optimized"]["request_failures"] == 1
    assert summarize(repeated, cases, {})["minimal"]["unique_cases"] == 4


def test_unpaired_rounds_are_explicit_and_not_fabricated():
    cases, records = paired_fixture()
    extra = [{**r, "repeat": 1} for r in records if r["method"] == "optimized"]
    result = paired_analysis(records + extra, cases, {}, samples=100)["comparisons"][0]
    assert result["paired_rounds"] == [0]
    assert result["unpaired_right"] == 4


def test_historical_summary_metrics_still_recompute():
    paths = [ROOT / "data/cases.jsonl", *sorted((ROOT / "data/revisions").glob("cases-*.jsonl"))]
    datasets = {
        hashlib.sha256(p.read_bytes()).hexdigest(): {
            c["id"]: c for c in map(json.loads, p.read_text().splitlines())
        }
        for p in paths
    }
    for manifest_path in sorted((ROOT / "results").glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text())
        if manifest["dataset_sha256"] not in datasets:
            continue
        folder = manifest_path.parent
        records = [
            json.loads(line) for line in (folder / "predictions.jsonl").read_text().splitlines()
        ]
        actual = summarize(records, datasets[manifest["dataset_sha256"]], {}, manifest)
        expected = json.loads((folder / "summary.json").read_text())
        for method, summary in expected.items():
            for key, value in summary.items():

                def check_retained(new, old, context=(folder.name, method, key)):
                    if isinstance(old, dict):
                        for k, v in old.items():
                            check_retained(new[k], v)
                    elif isinstance(old, list):
                        assert len(new) == len(old)
                        for x, y in zip(new, old, strict=True):
                            check_retained(x, y)
                    else:
                        assert new == old, context

                check_retained(actual[method][key], value)
