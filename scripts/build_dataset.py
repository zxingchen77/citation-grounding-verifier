"""Rebuild the real-docs-v3 corpus offline from the checked-in source snapshots."""

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

from grounding.dataset import inspect_dataset, reconstruct_passage

ROOT = Path(__file__).resolve().parents[1]


def build():
    spec_path = ROOT / "data/real-docs-v3/spec.json"
    source_path = ROOT / "data/sources/real-docs-v3.json"
    spec = json.loads(spec_path.read_text())
    sources = json.loads(source_path.read_text())["sources"]
    cases = copy.deepcopy(spec["cases"])
    for case in cases:
        case["context_passages"] = [
            reconstruct_passage(p, sources) for p in case["provenance"]["passages"]
        ]
    payload = "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases)
    path = ROOT / "data/cases.jsonl"
    path.write_text(payload)
    inspection = inspect_dataset(path)
    manifest = {
        "dataset_id": "real-docs-v3",
        "version": "3-real-docs",
        "sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "spec_sha256": hashlib.sha256(spec_path.read_bytes()).hexdigest(),
        "sources_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "cases": len(cases),
        "splits": dict(Counter(c["split"] for c in cases)),
        "categories": dict(Counter(c["category"] for c in cases)),
        "annotation_status": spec["annotation_status"],
        "source": "Official documentation excerpts; AI-authored answers and gold, not RAGTruth",
        "licenses": ["LicenseRef-SQLite-Public-Domain", "PostgreSQL", "PSF-2.0"],
        "split_policy": (
            "Source-document families are disjoint; 20 dev / 12 test, 5 / 3 per category."
        ),
        "statistics": inspection["statistics"],
    }
    (ROOT / "data/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    lines = [
        "# Gold review workbook: real-docs-v3",
        "",
        "Status: **AI-drafted; human author review pending** for every case.",
        "Check each atomic claim, label and complete evidence before signing off.",
        "Source-only semantics: a true fact absent from the supplied context is UNSUPPORTED.",
        "Do not revise labels to fit model outputs. Corrections after test require a new version.",
        "",
    ]
    for case in cases:
        lines += [f"## {case['id']} ({case['split']}; {case['category']})", ""]
        lines += [
            "Human review: [ ] accepted  [ ] correction needed",
            "",
            case["generated_answer"],
            "",
        ]
        for i, passage in enumerate(case["context_passages"]):
            source = sources[case["provenance"]["passages"][i]["source_id"]]
            lines += [f"### Passage {i}: [source]({source['url']})", "", passage, ""]
        for g in case["gold_claims"]:
            lines += [
                f"- **{g['id']} {g['verdict']}**: {g['claim_text']}",
                f"  Reason: {g['rationale']}",
            ]
            for group in g["evidence_groups"]:
                for e in group:
                    lines += [f"  Evidence [{e['index']}]: {e['quote']}"]
        lines += ["", "Reviewer notes: ____________________", ""]
    (ROOT / "data/real-docs-v3/gold-review.md").write_text("\n".join(lines))
    print(json.dumps({k: manifest[k] for k in ["dataset_id", "sha256", "cases", "splits"]}))


if __name__ == "__main__":
    build()
