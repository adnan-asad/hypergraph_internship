"""Constrained development-only weight selection and paired final comparison.

Stdlib only, Python 3.10+. This module does not generate or judge hierarchies.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import random
from statistics import mean


def weight_grid():
    """Small proposed search space, not calibrated or recommended final weights."""
    return [(a, b) for a in (0.0, 0.1, 1.0) for b in (0.0, 0.1, 1.0)]


def number(value, low, high, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} outside [{low}, {high}]")
    return float(value)


def select_weights(trials, *, min_stability, max_overclaim, coherence_tolerance=0.02):
    """Maximize independent dev coherence, subject to explicit quality limits.

    Each row is one config/seed. All rows must have identical dev evaluation IDs
    and protocol ID. The semantic-only baseline is required. Semantic degradation
    beyond coherence_tolerance relative to that baseline is disallowed.
    Thresholds and the search space must be frozen before examining trial scores.
    This is empirical model selection, not a significance test or training of J.
    """
    number(min_stability, -1, 1, "min_stability")
    number(max_overclaim, 0, 1, "max_overclaim")
    number(coherence_tolerance, 0, 1, "coherence_tolerance")
    if not trials:
        raise ValueError("No development trials")
    configs = defaultdict(list)
    reference = None
    seen = set()
    for row in trials:
        if row.get("split") != "development":
            raise ValueError("Selection accepts development data only")
        ids = row.get("evaluation_ids")
        protocol = row.get("protocol_id")
        if not isinstance(ids, list) or not ids or not all(isinstance(x, str) and x for x in ids):
            raise ValueError("Provide fixed nonempty evaluation_ids")
        if len(ids) != len(set(ids)) or not isinstance(protocol, str) or not protocol:
            raise ValueError("Duplicate evaluation IDs or missing protocol_id")
        cohort = (protocol, tuple(sorted(ids)))
        if reference is None:
            reference = cohort
        elif cohort != reference:
            raise ValueError("All trials must use the same evaluation cohort and protocol")
        a = number(row.get("lambda"), 0, math.inf, "lambda")
        b = number(row.get("gamma"), 0, math.inf, "gamma")
        seed = row.get("seed")
        if type(seed) is not int:
            raise ValueError("seed must be an integer")
        key = (a, b, seed)
        if key in seen:
            raise ValueError("Duplicate config/seed")
        seen.add(key)
        for metric, low, high in [("coherence", 0, 1), ("stability", -1, 1), ("overclaim_rate", 0, 1)]:
            number(row.get(metric), low, high, metric)
        configs[a, b].append(row)
    if (0.0, 0.0) not in configs:
        raise ValueError("Semantic-only baseline lambda=gamma=0 is required")
    seeds = {r["seed"] for r in configs[0.0, 0.0]}
    if any({r["seed"] for r in rows} != seeds for rows in configs.values()):
        raise ValueError("Every configuration must use the same seeds")
    baseline = mean(r["coherence"] for r in configs[0.0, 0.0])
    summary = []
    for (a, b), rows in sorted(configs.items()):
        m = {k: mean(r[k] for r in rows) for k in ("coherence", "stability", "overclaim_rate")}
        reasons = []
        if m["coherence"] < baseline - coherence_tolerance:
            reasons.append("coherence below baseline tolerance")
        if m["stability"] < min_stability:
            reasons.append("stability below declared minimum")
        if m["overclaim_rate"] > max_overclaim:
            reasons.append("overclaim rate above declared maximum")
        summary.append({"lambda": a, "gamma": b, **m, "feasible": not reasons,
                        "rejection_reasons": reasons, "seed_count": len(rows)})
    feasible = [r for r in summary if r["feasible"]]
    # Predeclared tie order: coherence, stability, lower overclaim, smaller weights.
    chosen = max(feasible, key=lambda r: (r["coherence"], r["stability"],
                                        -r["overclaim_rate"], -r["lambda"], -r["gamma"])) if feasible else None
    return {"status": "selected" if chosen else "no_feasible_configuration",
            "selected": chosen, "trials": summary, "protocol_id": reference[0],
            "development_evaluation_ids": list(reference[1]), "seeds": sorted(seeds),
            "selection_rule": "maximize independent dev coherence subject to fixed quality limits",
            "constraints": {"min_stability": min_stability, "max_overclaim": max_overclaim,
                            "coherence_tolerance": coherence_tolerance},
            "warning": "Development selection is not evidence of held-out improvement."}


def paired_family_bootstrap(rows, *, excluded_development_ids, repetitions=5000, seed=0):
    """Paired bootstrap for one higher-is-better held-out metric in [0,1].

    Rows: evaluation_id, family_id, split='held_out', baseline, candidate.
    Related questions share a family; resample whole families. The estimand is
    equal-family mean of within-family mean paired differences, NOT query-macro.
    No scores from tuning may appear here. This cannot prove genuine independence
    if the user mislabels records, families, or development exposure.
    """
    if type(repetitions) is not int or repetitions < 100:
        raise ValueError("Use at least 100 bootstrap repetitions")
    groups = defaultdict(list)
    seen = set()
    excluded = set(excluded_development_ids)
    for r in rows:
        ident, family = r.get("evaluation_id"), r.get("family_id")
        if not isinstance(ident, str) or not ident or not isinstance(family, str) or not family:
            raise ValueError("Missing evaluation_id or family_id")
        if r.get("split") != "held_out" or ident in excluded:
            raise ValueError("Held-out comparison contains development or incorrectly tagged data")
        if ident in seen:
            raise ValueError("Duplicate evaluation ID")
        seen.add(ident)
        groups[family].append(number(r.get("candidate"), 0, 1, "candidate") -
                              number(r.get("baseline"), 0, 1, "baseline"))
    if len(groups) < 2:
        raise ValueError("At least two independent families are required")
    differences = [mean(groups[k]) for k in sorted(groups)]
    rng = random.Random(seed)
    samples = sorted(mean(rng.choices(differences, k=len(differences))) for _ in range(repetitions))
    def quantile(p):
        pos = (len(samples) - 1) * p
        lo = int(pos)
        hi = min(lo + 1, len(samples) - 1)
        return samples[lo] + (samples[hi] - samples[lo]) * (pos - lo)
    return {"mean_difference": mean(differences), "approximate_95_percent_interval": [quantile(.025), quantile(.975)],
            "family_count": len(groups), "evaluation_count": len(rows), "bootstrap_seed": seed,
            "bootstrap_repetitions": repetitions, "estimand": "equal-family mean candidate-minus-baseline",
            "per_family_difference": {k: mean(v) for k, v in sorted(groups.items())},
            "warning": "Small family counts give fragile intervals; no general outperformance claim follows."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--trials", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--min-stability", type=float, required=True)
    p.add_argument("--max-overclaim", type=float, required=True)
    p.add_argument("--coherence-tolerance", type=float, default=.02)
    a = p.parse_args()
    result = select_weights(json.loads(a.trials.read_text(encoding="utf8")), min_stability=a.min_stability,
                            max_overclaim=a.max_overclaim, coherence_tolerance=a.coherence_tolerance)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x", encoding="utf8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(result["status"])


if __name__ == "__main__":
    main()
