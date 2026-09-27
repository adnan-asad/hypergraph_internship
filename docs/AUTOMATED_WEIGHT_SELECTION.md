# Automated weight selection: bounded extension

## What this adds

A development-only hyperparameter selector plus a paired comparison utility.
This is outer-loop empirical selection, not neural training of lambda/gamma and
not minimization of J over weights. No real weights have been selected: the
hierarchy engine and independent measurement pipeline are not implemented here.

## Required sequence

1. Finish the hierarchy engine and normalize its S, H and T terms. Inspect their
   merge-delta scales; [0,1] normalization alone does not equalize influence.
2. Freeze development units and a disjoint final audit, search grid, budgets,
   evaluation protocol and admissibility thresholds. Record a manifest before
   executing weight experiments. Freeze semantically related question families
   together if any queries are used in development.
3. Run each configuration on the same snapshots and seeds. Proposed starting
   grid: lambda/gamma in {0, 0.1, 1}; nine configurations. These are exploratory
   values, not validated scales. Keep the original three ablations as controls.
4. Independently score development coherence, temporal stability and overclaims.
   Coherence must not use the embedding driving clustering. Use fixed anchor
   items/pairs or a predeclared blinded audit design; keep evaluation IDs stable
   across variants. Missing ratings are errors to resolve, not zeros to insert.
5. Select the highest development coherence under the declared minimum stability,
   maximum overclaim rate and coherence-loss tolerance. This coherence-first
   preference is a design decision to justify, not a universal optimum. Preserve
   all trials and rejection reasons; do not relax thresholds just to get a winner.
6. Freeze the selected config. Run disjoint final audits and the downstream
   benchmark with identical candidate/evidence budgets for every retrieval method.
   Report recall/cost trade-offs, failures, and paired uncertainty. Do not retune
   after reading final scores without labeling the next analysis exploratory.

The supplied benchmark has already been inspected. It can be isolated from the
weight-selection code, but must not be described as a never-seen test set.

## Development trial JSON

The command expects a JSON list of records, one per (lambda, gamma, seed). Each
record needs:

- split: development
- protocol_id: frozen evaluation-protocol identifier
- evaluation_ids: fixed identifiers of development evaluation units
- lambda, gamma: nonnegative numbers
- seed: integer (same seed set for all configurations)
- coherence: independently judged score normalized to [0,1]
- stability: fixed temporal stability aggregate, e.g. ARI in [-1,1]
- overclaim_rate: measured assertion failure rate in [0,1]

The semantic-only configuration lambda=gamma=0 is mandatory. Metrics use a fixed
aggregation over snapshots and levels, excluding trivial singleton-level ARI.
Quality limits apply to configuration means across seeds; report per-seed values
too. Store raw ratings and denominators beside the summary trial JSON.

Example invocation after REAL development results exist (threshold values must be
chosen and justified beforehand, not copied as if universally appropriate):

```bash
PYTHONPATH=src python -m tkh_abstraction.tuning \
  --trials results/dev_trials.json \
  --output results/selected_weights.json \
  --min-stability 0.7 --max-overclaim 0.1 --coherence-tolerance 0.02
```

Outputs refuse to overwrite existing selection records. If no configuration
meets the constraints, the result says so rather than declaring a winner.

## Final comparison

paired_family_bootstrap accepts paired baseline/candidate scores for ONE metric
in [0,1] where higher is better, such as target recall. Input records include
evaluation_id, family_id and split=held_out. Related questions must share a family.
Pass development IDs so exact overlap is rejected. Family definitions and final
independence still require human checks: the tool cannot detect renamed leakage.

The estimate is an equal-family mean difference. Each resampled family contributes
its mean paired difference; larger families do not get more weight. This differs
from query-macro averaging. Report both per-question scores and this estimand
clearly. The approximate 95% percentile interval is fragile with few families.
An interval excluding zero does not prove general superiority, compensate for
unfair retrieval budgets, or cover many post-hoc comparisons without adjustment.

## How to state the contribution

Before results: "We add development-based automatic selection of structural and
temporal regularization weights and evaluate the frozen configuration against
fixed-weight baselines."

After results: name the exact baseline, metric, paired difference, uncertainty,
sample and resource budget. Report negative/inconclusive findings. No promised
outperformance, no invented scores and no global state-of-the-art claim.

## Deadline

Cap the extension at one small search. If independent development ratings or
runtime exceed the budget, deliver fixed weights with sensitivity analysis and
document this tuner as optional. Keep the required evaluation and report intact.

The tests use synthetic scores only to verify selection and interval mechanics.
They are not research results. Automatic trial execution awaits the hierarchy
engine; manual JSON editing must not be used to manufacture favorable scores.
