"""Recompute the dev comparison and check the protected test/data/source artifacts."""

import hashlib
import json
import runpy
from collections import Counter
from pathlib import Path

from grounding.benchmark import summarize
from grounding.experiment import validate_records

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    run = OUT / "comparison"
    manifest = load(run / "manifest.json")
    records = list(map(json.loads, (run / "predictions.jsonl").read_text().splitlines()))
    cases = {
        c["id"]: c
        for c in map(json.loads, (ROOT / "data/cases.jsonl").read_text().splitlines())
        if c["split"] == "dev"
    }
    assert manifest["split"] == "dev" and manifest["test_inference_permitted"] is False
    assert all(r["case_id"] in cases for r in records)
    assert sha(ROOT / "data/cases.jsonl") == manifest["dataset_sha256"]
    assert sha(ROOT / "experiments/dev_refinement.py") == manifest["experiment_sha256"]
    assert sha(OUT / "protocol.json") == manifest["protocol_sha256"]
    protected = load(OUT / "protected-hashes.json")["sha256"]
    changed = [p for p, h in protected.items() if sha(ROOT / p) != h]
    assert not changed, changed
    validate_records(records, manifest["execution_schedule"])
    summaries = summarize(records, cases, {}, manifest)
    assert summaries == load(run / "summary.json")
    availability_view = runpy.run_path(str(ROOT / "scripts/summarize_availability.py"))[
        "availability_view"
    ]
    view = availability_view(records, cases, manifest)
    limitation = (
        "Availability exclusions were declared before this dev comparison. Network/backend "
        "causes remain unconfirmed. Conditional cohorts can be selective and do not estimate "
        "full-dev performance. Gold review is pending; repeated outputs stay within families."
    )
    view["policy"]["limitation"] = limitation
    view["common_case_paired_analysis"]["limitation"] = limitation
    baseline, candidate = manifest["methods"]
    common = view["common_cases"]
    base, cand = common[baseline], common[candidate]
    stage_calls = {}
    diagnostics = {}
    for method, s in summaries.items():
        rows = [r for r in records if r["method"] == method]
        counts = Counter(c["stage"] for r in rows for c in r["trace"]["calls"])
        repairs = sum(
            sum(n - 1 for n in Counter(c["stage"] for c in r["trace"]["calls"]).values())
            for r in rows
        )
        stage_calls[method] = {"stage_counts": dict(counts), "structural_repair_calls": repairs}
        scores = s["case_scores"]
        diagnostics[method] = {
            "credited_gold": s["tp"],
            "unaligned_gold": s["gold"] - s["aligned"],
            "unaligned_predictions": s["predicted"] - s["aligned"],
            "aligned_wrong_verdict": sum(
                m["gold_verdict"] != m["predicted_verdict"] for c in scores for m in c["matches"]
            ),
            "aligned_incomplete_gold_evidence": sum(
                m["gold_verdict"] == m["predicted_verdict"] and not m["evidence_sufficient"]
                for c in scores
                for m in c["matches"]
            ),
        }
    numeric_gate = bool(
        base
        and cand
        and cand["f1"] > base["f1"]
        and cand["verdict_macro_f1"] >= base["verdict_macro_f1"]
    )
    result = {
        "scope": "Dev only; automatic scores against unchanged, AI-drafted gold.",
        "review_type": "author self-review (AI-assisted); no reviewed score overrides",
        "protected_files_checked": len(protected),
        "changed_protected_files": changed,
        "original_summary_recomputed_exactly": True,
        "input_sha256": {
            "predictions": sha(run / "predictions.jsonl"),
            "manifest": sha(run / "manifest.json"),
            "dataset": sha(ROOT / "data/cases.jsonl"),
            "experiment": manifest["experiment_sha256"],
            "protocol": manifest["protocol_sha256"],
        },
        "numeric_selection_gate_passed": numeric_gate,
        "selection_note": "Numeric gate alone does not establish semantic improvement or "
        "authorize production promotion. Inspect targeted failures and regressions.",
        "diagnostic_counts_all_attempts": diagnostics,
        "stage_calls": stage_calls,
        **view,
    }
    (OUT / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "common_cases": len(view["common_pairs"]),
                "excluded_requests": len(view["excluded_requests"]),
                "f1": {m: s["f1"] if s else None for m, s in common.items()},
                "macro_f1": {m: s["verdict_macro_f1"] if s else None for m, s in common.items()},
                "numeric_gate_passed": numeric_gate,
                "protected_files_unchanged": len(protected),
            }
        )
    )


if __name__ == "__main__":
    main()
