"""Compare v5 with saved v1 dev outputs without rerunning either method."""

import hashlib
import json
import runpy
from pathlib import Path

from grounding.benchmark import summarize
from grounding.experiment import validate_records

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cases = {
        c["id"]: c
        for c in map(json.loads, (ROOT / "data/cases.jsonl").read_text().splitlines())
        if c["split"] == "dev"
    }
    sources = {
        "optimized-v1": ROOT / "results/dev-refinement-v4/comparison",
        "compact-v5": OUT / "run",
    }
    inputs, records, manifests = {}, [], {}
    for method, folder in sources.items():
        manifest = json.loads((folder / "manifest.json").read_text())
        rows = list(map(json.loads, (folder / "predictions.jsonl").read_text().splitlines()))
        validate_records(rows, manifest["execution_schedule"])
        assert manifest["split"] == "dev" and manifest["test_inference_permitted"] is False
        assert sha(ROOT / "data/cases.jsonl") == manifest["dataset_sha256"]
        assert all(r["case_id"] in cases for r in rows)
        assert summarize(rows, cases, {}, manifest) == json.loads(
            (folder / "summary.json").read_text()
        )
        records.extend(r for r in rows if r["method"] == method)
        manifests[method] = manifest
        inputs[method] = {
            "source_run": str(folder.relative_to(ROOT)),
            "predictions_sha256": sha(folder / "predictions.jsonl"),
            "manifest_sha256": sha(folder / "manifest.json"),
        }
    baseline, candidate = (manifests[m] for m in sources)
    for field in [
        "case_ids",
        "dataset_sha256",
        "model",
        "backend",
        "call_timeout",
        "request_timeout",
    ]:
        assert baseline[field] == candidate[field], field
    assert sha(ROOT / "experiments/compact_v5.py") == candidate["experiment_sha256"]
    assert sha(OUT / "protocol.json") == candidate["protocol_sha256"]
    protected = json.loads((ROOT / "results/dev-refinement-v4/protected-hashes.json").read_text())[
        "sha256"
    ]
    changed = [p for p, h in protected.items() if sha(ROOT / p) != h]
    assert not changed, changed
    # Preserve both runs' execution metadata; this is an explicitly sequential comparison.
    comparison = {
        "methods": list(sources),
        "execution_schedule": [
            {k: r[k] for k in ["execution_index", "method", "repeat", "case_id", "pair_id"]}
            for r in records
        ],
        "backend": candidate["backend"],
        "bootstrap_samples": 2000,
        "bootstrap_seed": 1729,
        "cluster": "family",
    }
    view = runpy.run_path(str(ROOT / "scripts/summarize_availability.py"))["availability_view"](
        records, cases, comparison
    )
    limitation = (
        "Dev-only adaptive, sequential comparison with reused baseline outputs; not a new "
        "interleaved experiment. Availability exclusions were declared before v5 inference. "
        "Latency/cache/load differences are confounded, and gold still awaits human review."
    )
    view["policy"]["limitation"] = limitation
    view["common_case_paired_analysis"]["limitation"] = limitation
    a, b = (view["common_cases"][m] for m in sources)
    gate = bool(a and b and b["f1"] > a["f1"] and b["verdict_macro_f1"] >= a["verdict_macro_f1"])
    result = {
        "scope": limitation,
        "source_runs": inputs,
        "baseline_reused": True,
        "original_summaries_recomputed_exactly": True,
        "protected_files_checked": len(protected),
        "changed_protected_files": changed,
        "numeric_selection_gate_passed": gate,
        "semantic_review_adjustment": False,
        **view,
    }
    (OUT / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "common_cases": len(view["common_pairs"]),
                "excluded_requests": len(view["excluded_requests"]),
                "f1": {m: s["f1"] if s else None for m, s in view["common_cases"].items()},
                "macro_f1": {
                    m: s["verdict_macro_f1"] if s else None for m, s in view["common_cases"].items()
                },
                "numeric_gate_passed": gate,
                "protected_files_unchanged": len(protected),
            }
        )
    )


if __name__ == "__main__":
    main()
