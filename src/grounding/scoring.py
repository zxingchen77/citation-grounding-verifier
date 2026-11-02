"""Conservative, auditable scoring. Semantic overrides are explicit review data."""

import re
from collections import Counter
from functools import lru_cache

from grounding.verifiers import tokens

LABELS = ("SUPPORTED", "CONTRADICTED", "UNSUPPORTED")


def similarity(a: str, b: str) -> float:
    def normalized(text):
        return re.sub(r"\W+", " ", text.lower()).strip()

    if normalized(a) == normalized(b):
        return 1.0
    # An altered number or logical qualifier is not the same atomic claim.
    if set(re.findall(r"\d+(?:\.\d+)?", a)) != set(re.findall(r"\d+(?:\.\d+)?", b)):
        return 0.0

    def qualifiers(text):
        text = re.sub(r"\bevery\b|\beach\b", "all", text.lower())
        return set(re.findall(r"\b(?:only|all|not|never|may|must)\b", text))

    if qualifiers(a) != qualifiers(b):
        return 0.0
    x, y = tokens(a), tokens(b)
    return 2 * len(x & y) / (len(x) + len(y)) if x and y else 0.0


def align(predictions, gold):
    """Maximum-weight one-to-one matching, with a declared lexical threshold."""
    if len(gold) > 12:
        raise ValueError("This small-dataset scorer supports at most 12 gold claims per case.")
    weights = [[similarity(p["claim_text"], g["claim_text"]) for g in gold] for p in predictions]

    @lru_cache(None)
    def solve(i, mask):
        if i == len(predictions):
            return 0.0, ()
        best, pairs = solve(i + 1, mask)
        for j, value in enumerate(weights[i]):
            if mask & (1 << j) or value < 0.65:
                continue
            rest, tail = solve(i + 1, mask | (1 << j))
            if value + rest > best:
                best, pairs = value + rest, ((i, j),) + tail
        return best, pairs

    return list(solve(0, 0)[1]), weights


def evidence_sufficient(prediction, gold):
    citations = prediction["citations"]
    if gold["verdict"] == "UNSUPPORTED":
        return not citations
    return any(
        all(
            any(c["index"] == e["index"] and e["quote"] in c["quote"] for c in citations)
            for e in group
        )
        for group in gold["evidence_groups"]
    )


def score_case(record, case, review=None):
    predictions = (record.get("response") or {}).get("claims", [])
    gold = case["gold_claims"]
    pairs, weights = align(predictions, gold)
    evidence_overrides = {}
    if review is not None:
        if not review.get("note"):
            raise ValueError("Review overrides require an explanatory note.")
        pairs = [(item["prediction_index"], item["gold_index"]) for item in review["matches"]]
        if len({p for p, _ in pairs}) != len(pairs) or len({g for _, g in pairs}) != len(pairs):
            raise ValueError("Review matching must be one-to-one.")
        for item in review["matches"]:
            i, j = item["prediction_index"], item["gold_index"]
            if not (0 <= i < len(predictions) and 0 <= j < len(gold)):
                raise ValueError("Review references an out-of-range claim.")
            if "evidence_sufficient" in item:
                if type(item["evidence_sufficient"]) is not bool:
                    raise ValueError("evidence_sufficient must be a boolean")
                evidence_overrides[(i, j)] = item["evidence_sufficient"]
    issues, details = [], []
    tp = valid_citations = total_citations = false_supported = 0
    for p in predictions:
        for citation in p["citations"]:
            total_citations += 1
            index = citation["index"]
            valid_citations += bool(
                0 <= index < len(case["context_passages"])
                and citation["quote"].strip()
                and citation["quote"] in case["context_passages"][index]
            )
    for i, j in pairs:
        p, g = predictions[i], gold[j]
        valid = ((p["verdict"] == "UNSUPPORTED") == (len(p["citations"]) == 0)) and all(
            0 <= c["index"] < len(case["context_passages"])
            and c["quote"].strip()
            and c["quote"] in case["context_passages"][c["index"]]
            for c in p["citations"]
        )
        sufficient = evidence_overrides.get((i, j), evidence_sufficient(p, g))
        correct = p["verdict"] == g["verdict"] and valid and sufficient
        tp += bool(correct)
        false_supported += p["verdict"] == "SUPPORTED" and g["verdict"] != "SUPPORTED"
        details.append(
            {
                "prediction_index": i,
                "gold_index": j,
                "similarity": weights[i][j],
                "gold_verdict": g["verdict"],
                "predicted_verdict": p["verdict"],
                "evidence_sufficient": sufficient,
                "correct": bool(correct),
            }
        )
        if weights[i][j] < 1 and review is None:
            issues.append(f"Review semantic alignment of prediction {i} and gold {j}.")
        if p["verdict"] == g["verdict"] and not sufficient and review is None:
            issues.append(f"Review alternative evidence for prediction {i}.")
    if len(pairs) < max(len(predictions), len(gold)) and review is None:
        issues.append("Review unmatched/duplicate claims; missing claims remain false negatives.")
    return {
        "case_id": case["id"],
        "category": case["category"],
        "split": case["split"],
        "tp": tp,
        "fp": len(predictions) - tp,
        "fn": len(gold) - tp,
        "predicted": len(predictions),
        "gold": len(gold),
        "aligned": len(pairs),
        "false_supported": false_supported,
        "non_supported_gold": sum(g["verdict"] != "SUPPORTED" for g in gold),
        "valid_citations": valid_citations,
        "total_citations": total_citations,
        "matches": details,
        "review_needed": issues,
        "reviewed": review is not None,
        "error": record.get("error"),
    }


def aggregate(scores):
    totals = Counter()
    for score in scores:
        for name in [
            "tp",
            "fp",
            "fn",
            "predicted",
            "gold",
            "aligned",
            "false_supported",
            "non_supported_gold",
            "valid_citations",
            "total_citations",
        ]:
            totals[name] += score[name]

    def ratio(a, b):
        return a / b if b else None

    precision = ratio(totals["tp"], totals["predicted"])
    recall = ratio(totals["tp"], totals["gold"])
    f1 = ratio(2 * totals["tp"], 2 * totals["tp"] + totals["fp"] + totals["fn"])
    confusion = Counter(
        (m["gold_verdict"], m["predicted_verdict"]) for s in scores for m in s["matches"]
    )
    per_class = []
    for label in LABELS:
        tp = confusion[label, label]
        predicted = sum(n for (_, p), n in confusion.items() if p == label)
        actual = sum(n for (g, _), n in confusion.items() if g == label)
        per_class.append(2 * tp / (predicted + actual) if predicted + actual else 0.0)
    return {
        **dict(totals),
        "cases": len(scores),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "claim_coverage": ratio(totals["aligned"], totals["gold"]),
        "false_supported_rate": ratio(totals["false_supported"], totals["non_supported_gold"]),
        "quote_validity": ratio(totals["valid_citations"], totals["total_citations"]),
        "request_failures": sum(bool(s["error"]) for s in scores),
        "cases_needing_review": sum(bool(s["review_needed"]) for s in scores),
        "aligned_verdict_macro_f1": sum(per_class) / 3,
        "confusion": {f"{g}->{p}": n for (g, p), n in sorted(confusion.items())},
    }
