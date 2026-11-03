import copy
import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

from grounding.experiment import make_schedule

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/summarize_availability.py"
availability_view = runpy.run_path(str(SCRIPT))["availability_view"]


def fixture_run():
    cases = {
        name: {
            "id": name,
            "family": name,
            "category": "fixture",
            "split": "test",
            "context_passages": ["A is B."],
            "gold_claims": [
                {
                    "claim_text": "A is B.",
                    "verdict": "SUPPORTED",
                    "evidence_groups": [[{"index": 0, "quote": "A is B."}]],
                }
            ],
        }
        for name in ["a", "b"]
    }
    methods = ["minimal", "optimized"]
    schedule = make_schedule(list(cases), methods)
    records = [
        {
            **job,
            "response": {
                "claims": [
                    {
                        "claim_text": "A is B.",
                        "verdict": "SUPPORTED",
                        "citations": [{"index": 0, "quote": "A is B."}],
                    }
                ]
            },
            "latency_seconds": 1,
            "trace": {"calls": []},
        }
        for job in schedule
    ]
    return records, cases, {"methods": methods, "execution_schedule": schedule}


@pytest.mark.parametrize("availability_error", ["upstream_timeout", "upstream_error"])
@pytest.mark.parametrize("quality_error", ["invalid_output", "unrecognized_error"])
def test_exclude_availability_but_keep_quality_errors_in_both_cohorts(
    availability_error, quality_error
):
    records, cases, manifest = fixture_run()
    for r, code in zip(records[:2], [availability_error, quality_error], strict=True):
        r.pop("response")
        r["error"] = {"code": code}
    original = copy.deepcopy(records)
    view = availability_view(records, cases, manifest)
    assert records == original
    assert len(view["excluded_requests"]) == 1
    assert view["common_pairs"] == ["0/b"]
    assert view["availability_adjusted"]["minimal"]["gold"] == 1
    assert view["availability_adjusted"]["optimized"]["gold"] == 2
    for cohort in ["availability_adjusted", "common_cases"]:
        assert view[cohort]["minimal"]["f1"] == 0
        assert view[cohort]["minimal"]["request_failures"] == 1
        assert view[cohort]["optimized"]["f1"] == 1
    assert view["common_cases"]["optimized"]["gold"] == 1


def test_no_retained_cases_is_unknown_and_incomplete_runs_are_rejected():
    records, cases, manifest = fixture_run()
    for r in records:
        r.pop("response")
        r["error"] = {"code": "upstream_timeout"}
    view = availability_view(records, cases, manifest)
    assert view["common_pairs"] == []
    assert all(s is None for s in view["common_cases"].values())
    assert all(s is None for s in view["availability_adjusted"].values())
    with pytest.raises(ValueError, match="complete execution schedule"):
        availability_view(records[:-1], cases, manifest)


def test_saved_availability_report_reproduces_without_mutating_the_original(tmp_path):
    run = ROOT / "results/real-docs-v3/test"
    original = {p: p.read_bytes() for p in run.iterdir() if p.is_file()}
    subprocess.run(
        [sys.executable, str(SCRIPT), "--run", str(run), "--out", str(tmp_path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    saved = ROOT / "results/real-docs-v3/availability-adjusted"
    for name in ["summary.json", "report.md"]:
        assert (tmp_path / name).read_bytes() == (saved / name).read_bytes()
    assert all(p.read_bytes() == data for p, data in original.items())
    view = json.loads((tmp_path / "summary.json").read_text())
    assert len(view["excluded_requests"]) == 6
    assert len(view["common_pairs"]) == 7
    assert view["availability_adjusted"]["minimal"]["f1"] == pytest.approx(36 / 77)
    assert view["availability_adjusted"]["optimized"]["f1"] == pytest.approx(44 / 77)
    assert view["common_cases"]["deterministic"]["f1"] == pytest.approx(2 / 47)
    assert view["common_cases"]["minimal"]["f1"] == pytest.approx(26 / 56)
    assert view["common_cases"]["optimized"]["f1"] == pytest.approx(34 / 58)
