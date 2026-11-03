import hashlib
import json
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from grounding.benchmark import summarize
from grounding.dataset import inspect_dataset
from grounding.experiment import validate_records
from grounding.models import VerifyResponse, validate_evidence

R = Path(__file__).resolve().parents[2]


def load(p):
    return json.loads((R / p).read_text())


def cases(p):
    return {c["id"]: c for c in map(json.loads, (R / p).read_text().splitlines())}


f = load("results/real-docs-v3/test-freeze.json")
changed = [
    p for p, h in f["sha256"].items() if hashlib.sha256((R / p).read_bytes()).hexdigest() != h
]
assert not changed, changed
old = cases("data/revisions/cases-real-docs-v3-draft0.jsonl")
new = cases("data/cases.jsonl")
for k in new:
    for field in ["context_passages", "generated_answer", "split", "family", "category"]:
        assert old[k][field] == new[k][field], (k, field)
archive = {}
for src, copy in [
    ("data/cases.jsonl", "data/revisions/cases-synthetic-v3.jsonl"),
    ("data/manifest.json", "data/revisions/manifest-synthetic-v3.json"),
]:
    archive[copy] = (
        hashlib.sha256((R / copy).read_bytes()).hexdigest()
        == hashlib.sha256(
            subprocess.check_output(["git", "show", "7ecb597:" + src], cwd=R)
        ).hexdigest()
    )
    assert archive[copy]
runs = {}
for name, ds, summary in [
    ("dev-initial", old, "summary.json"),
    ("dev-initial", new, "reference-summary.json"),
    ("dev-candidate", new, "summary.json"),
    ("test", new, "summary.json"),
]:
    folder = R / "results/real-docs-v3" / name
    m = json.loads((folder / "manifest.json").read_text())
    records = list(map(json.loads, (folder / "predictions.jsonl").read_text().splitlines()))
    validate_records(records, m["execution_schedule"])
    actual = summarize(records, ds, {}, m)
    saved = json.loads((folder / summary).read_text())
    assert actual == saved, (name, summary)
    quotes = 0
    error_counts = Counter()
    request_counts = Counter()
    usage_missing = Counter()
    for r in records:
        request_counts[r["method"]] += 1
        if r.get("error"):
            error_counts[(r["method"], r["error"]["code"])] += 1
        if r.get("response"):
            resp = validate_evidence(
                VerifyResponse.model_validate(r["response"]), ds[r["case_id"]]["context_passages"]
            )
            quotes += sum(len(c.citations) for c in resp.claims)
        usage_missing[r["method"]] += sum(
            not {"prompt_tokens", "completion_tokens"}.issubset(c.get("usage", {}))
            for c in r["trace"]["calls"]
        )
    for method, v in saved.items():
        assert v["f1"] == 2 * v["tp"] / (v["predicted"] + v["gold"])
        assert v["request_failures"] == sum(
            n for (method2, _), n in error_counts.items() if method2 == method
        )
        assert v["calls_missing_usage"] == usage_missing[method]
    if name == "test":
        assert request_counts == {"deterministic": 12, "minimal": 12, "optimized": 12}
        assert {r["repeat"] for r in records} == {0}
        assert f["frozen_at_utc"] < m["started_at_utc"]
    runs[name + "/" + summary] = {
        "summary_recomputed_exactly": True,
        "requests": dict(request_counts),
        "literal_citations_checked": quotes,
        "errors": {method + "/" + code: n for (method, code), n in error_counts.items()},
        "usage_missing": dict(usage_missing),
        "predictions_sha256": hashlib.sha256(
            (folder / "predictions.jsonl").read_bytes()
        ).hexdigest(),
    }
result = {
    "verified_at_utc": datetime.now(UTC).isoformat(),
    "scope": "Executable consistency checks, not human semantic adjudication.",
    "frozen_files_checked": len(f["sha256"]),
    "changed_frozen_files": changed,
    "historical_archives_equal_to_7ecb597": archive,
    "reference_repair_changed_no_inputs": True,
    "dataset": inspect_dataset(R / "data/cases.jsonl"),
    "runs": runs,
    "annotation_status": "AI-drafted; human author review pending",
    "known_annotation_questions": "results/real-docs-v3/annotation-questions.json",
    "http_checks": load("results/real-docs-v3/acceptance/http-checks.json")["all_passed"],
}
(R / "results/real-docs-v3/verification.json").write_text(json.dumps(result, indent=2) + "\n")
print(
    json.dumps(
        {
            "frozen_files": result["frozen_files_checked"],
            "recomputed_runs": len(runs),
            "archival_integrity": all(archive.values()),
            "http_passed": result["http_checks"],
        }
    )
)
