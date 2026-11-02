"""Reproducible schedules and paired, cluster-level uncertainty estimates."""

import itertools
import random
import statistics
from collections import defaultdict

from grounding.scoring import score_case


def make_schedule(
    case_ids, methods, repeats=1, order="fixed", seed=1729, deterministic_repeats=None
):
    if not case_ids or len(set(case_ids)) != len(case_ids):
        raise ValueError("Select nonempty, unique cases.")
    if not methods or len(set(methods)) != len(methods):
        raise ValueError("Methods must be nonempty and unique.")
    if repeats < 1 or (
        deterministic_repeats is not None and not 1 <= deterministic_repeats <= repeats
    ):
        raise ValueError("Repeats must be positive; deterministic repeats cannot exceed repeats.")
    if order not in {"fixed", "balanced"}:
        raise ValueError("Unknown execution order.")
    counts = {
        m: deterministic_repeats or repeats if m == "deterministic" else repeats for m in methods
    }
    if order == "fixed":
        jobs = [(m, r, c) for m in methods for r in range(counts[m]) for c in case_ids]
    else:
        rng = random.Random(seed)
        cases = list(case_ids)
        rng.shuffle(cases)
        jobs = []
        for repeat in range(repeats):
            active = [m for m in methods if repeat < counts[m]]
            permutations = list(itertools.permutations(active))
            rng.shuffle(permutations)
            # Each complete n! block balances position and every pair's order.
            # Partial blocks are retained and disclosed in the saved schedule.
            for i, case_id in enumerate(cases):
                jobs.extend((m, repeat, case_id) for m in permutations[i % len(permutations)])
    return [
        {
            "execution_index": i,
            "method": method,
            "repeat": repeat,
            "case_id": case_id,
            "pair_id": f"{repeat}/{case_id}",
        }
        for i, (method, repeat, case_id) in enumerate(jobs)
    ]


def validate_records(records, schedule=None):
    keys = [(r["method"], r["repeat"], r["case_id"]) for r in records]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate method/repeat/case records cannot be paired or scored.")
    if schedule is not None:
        expected = [(r["method"], r["repeat"], r["case_id"]) for r in schedule]
        if keys != expected:
            raise ValueError("Saved predictions do not match the complete execution schedule.")
        for actual, planned in zip(records, schedule, strict=True):
            if any(actual.get(k) != v for k, v in planned.items()):
                raise ValueError("Execution index or pair ID differs from the saved schedule.")


def _f1(scores):
    tp, fp, fn = (sum(s[k] for s in scores) for k in ["tp", "fp", "fn"])
    return 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0


def _percentile(values, probability):
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (position - lower) * (ordered[upper] - ordered[lower])


def paired_analysis(
    records, cases, reviews, methods=None, samples=2000, seed=1729, cluster="family"
):
    """Resample paired families, keeping all their cases and rounds together.

    F1 is recomputed from counts in each draw, not averaged across claim F1s.
    Latency is the mean of within-case mean differences across paired rounds.
    Neither the sample size nor the resampling unit is inflated by repeats.
    """
    if samples < 100 or cluster not in {"family", "case"}:
        raise ValueError("Use at least 100 bootstrap draws and cluster by family or case.")
    validate_records(records)
    indexed = defaultdict(dict)
    for record in records:
        method, repeat, case_id = record["method"], record["repeat"], record["case_id"]
        key = f"{method}/{repeat}/{case_id}"
        indexed[method][(repeat, case_id)] = (
            record,
            score_case(record, cases[case_id], reviews.get(key)),
        )
    results = []
    for left, right in itertools.combinations(methods or list(indexed), 2):
        a, b = indexed[left], indexed[right]
        common = sorted(a.keys() & b.keys())
        clusters = defaultdict(list)
        pairs = []
        for repeat, case_id in common:
            family = cases[case_id].get("family", case_id)
            ar, asc = a[repeat, case_id]
            br, bsc = b[repeat, case_id]
            pair = {
                "pair_id": f"{repeat}/{case_id}",
                "case_id": case_id,
                "family": family,
                "repeat": repeat,
                "left": {k: asc[k] for k in ["tp", "fp", "fn"]},
                "right": {k: bsc[k] for k in ["tp", "fp", "fn"]},
                "latency_difference_seconds": br["latency_seconds"] - ar["latency_seconds"],
                "execution_indices": [ar.get("execution_index"), br.get("execution_index")],
            }
            pairs.append(pair)
            clusters[family if cluster == "family" else case_id].append(pair)

        def metrics(groups):
            combined = [p for group in groups for p in group]
            latency_deltas = []
            for group in groups:
                by_case = defaultdict(list)
                for p in group:
                    by_case[p["case_id"]].append(p["latency_difference_seconds"])
                latency_deltas.extend(statistics.mean(v) for v in by_case.values())
            return (
                _f1([p["right"] for p in combined]) - _f1([p["left"] for p in combined]),
                statistics.mean(latency_deltas),
            )

        result = {
            "left": left,
            "right": right,
            "difference": "right minus left",
            "paired_requests": len(common),
            "unique_cases": len({c for _, c in common}),
            "unique_families": len({p["family"] for p in pairs}),
            "paired_rounds": sorted({r for r, _ in common}),
            "unpaired_left": len(a.keys() - b.keys()),
            "unpaired_right": len(b.keys() - a.keys()),
            "cluster": cluster,
            "clusters": len(clusters),
            "bootstrap_samples": samples,
            "bootstrap_seed": seed,
            "pairs": pairs,
        }
        if clusters:
            groups = list(clusters.values())
            point = metrics(groups)
            rng = random.Random(seed)
            draws = [metrics(rng.choices(groups, k=len(groups))) for _ in range(samples)]
            for i, name in enumerate(["f1_difference", "mean_case_latency_difference_seconds"]):
                result[name] = {
                    "estimate": point[i],
                    "percentile_95_interval": [
                        _percentile([d[i] for d in draws], p) for p in [0.025, 0.975]
                    ]
                    if len(clusters) >= 2
                    else None,
                }
        results.append(result)
    return {
        "method": "paired cluster percentile bootstrap",
        "limitation": (
            "Small synthetic samples; intervals describe sampled cluster heterogeneity. "
            "Repeated model outputs are kept within clusters, not independent new cases. "
            "Cache state, service load and backend overhead are uncontrolled. "
            "A single deterministic round is paired only with the corresponding model round."
        ),
        "comparisons": results,
    }
