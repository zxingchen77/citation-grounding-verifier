"""Structural validation and descriptive statistics; not semantic adjudication."""

import argparse
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from grounding.models import Claim, VerifyRequest, VerifyResponse, validate_evidence


def inspect_dataset(path):
    payload = path.read_bytes()
    cases = [json.loads(line) for line in payload.decode().splitlines() if line.strip()]
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Dataset must have nonempty, unique case IDs.")
    families = defaultdict(set)
    stats = {}
    for case in cases:
        families[case["family"]].add(case["split"])
        VerifyRequest(
            context_passages=case["context_passages"], generated_answer=case["generated_answer"]
        )
        if case["split"] not in {"dev", "test"}:
            raise ValueError("Unknown split.")
        claims = case["gold_claims"]
        if not 1 <= len(claims) <= 12 or len({g["id"] for g in claims}) != len(claims):
            raise ValueError("Gold claim IDs must be unique and count within scorer limits.")
        if not case.get("logical_semantics") or not case.get("capabilities"):
            raise ValueError("Challenge cases require explicit semantics and capabilities.")
        for gold in claims:
            if not gold.get("rationale", "").strip():
                raise ValueError("Every gold claim requires an annotation rationale.")
            groups = gold["evidence_groups"]
            if (gold["verdict"] == "UNSUPPORTED") != (not groups):
                raise ValueError("Gold verdict/evidence mismatch.")
            for group in groups or [[]]:
                claim = Claim(
                    claim_text=gold["claim_text"],
                    verdict=gold["verdict"],
                    reasoning=gold["rationale"],
                    citations=group,
                )
                validate_evidence(VerifyResponse(claims=[claim]), case["context_passages"])
    if any(len(splits) != 1 for splits in families.values()):
        raise ValueError("Scenario families must not cross development and test splits.")
    for split in ["all", "dev", "test"]:
        subset = [c for c in cases if split == "all" or c["split"] == split]
        lengths = [sum(map(len, c["context_passages"])) for c in subset]
        counts = [len(c["gold_claims"]) for c in subset]
        combinations = Counter(
            "+".join(sorted({g["verdict"] for g in c["gold_claims"]})) for c in subset
        )
        stats[split] = {
            "cases": len(subset),
            "families": len({c["family"] for c in subset}),
            "claims": sum(counts),
            "categories": dict(Counter(c["category"] for c in subset)),
            "capabilities": dict(Counter(t for c in subset for t in c["capabilities"])),
            "claim_labels": dict(Counter(g["verdict"] for c in subset for g in c["gold_claims"])),
            "label_combinations": dict(combinations),
            "mixed_label_cases": sum(v for k, v in combinations.items() if "+" in k),
            "three_label_cases": sum(v for k, v in combinations.items() if k.count("+") == 2),
            "context_characters": {
                "min": min(lengths),
                "median": statistics.median(lengths),
                "max": max(lengths),
            }
            if lengths
            else None,
            "claims_per_case": dict(sorted(Counter(counts).items())),
        }
    return {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "statistics": stats,
        "families": {f: next(iter(s)) for f, s in sorted(families.items())},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_dataset(args.dataset), indent=2))


if __name__ == "__main__":
    main()
