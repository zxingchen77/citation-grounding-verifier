"""Recompute automatic scores after an explicitly audited reference-only revision."""

import argparse
import hashlib
import json
from pathlib import Path

from grounding.benchmark import write_summary
from grounding.experiment import validate_records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=Path("data/cases.jsonl"))
    parser.add_argument("--original-dataset", type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.run / "manifest.json").read_text())
    data = args.dataset.read_bytes()
    cases = {c["id"]: c for c in map(json.loads, data.decode().splitlines())}
    if hashlib.sha256(data).hexdigest() != manifest["dataset_sha256"]:
        if not args.original_dataset:
            parser.error("A changed reference requires --original-dataset.")
        original = args.original_dataset.read_bytes()
        if hashlib.sha256(original).hexdigest() != manifest["dataset_sha256"]:
            parser.error("Original dataset does not match the run.")
        old = {c["id"]: c for c in map(json.loads, original.decode().splitlines())}
        for key in manifest["case_ids"]:
            for field in ["context_passages", "generated_answer", "split", "category", "family"]:
                if old[key][field] != cases[key][field]:
                    parser.error("Inputs and split/family membership must not change.")
    records = [
        json.loads(line) for line in (args.run / "predictions.jsonl").read_text().splitlines()
    ]
    validate_records(records, manifest["execution_schedule"])
    write_summary(args.run, records, cases, {}, manifest, prefix="reference-")
    (args.run / "reference-provenance.json").write_text(
        json.dumps(
            {
                "original_dataset_sha256": manifest["dataset_sha256"],
                "scored_dataset_sha256": hashlib.sha256(data).hexdigest(),
                "predictions_sha256": hashlib.sha256(
                    (args.run / "predictions.jsonl").read_bytes()
                ).hexdigest(),
                "kind": "Unchanged predictions; reference repair, not model improvement",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
