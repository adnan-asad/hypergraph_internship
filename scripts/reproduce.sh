#!/usr/bin/env bash
# Usage: bash scripts/reproduce.sh /absolute/input/data /absolute/empty/output [full]
# Run with the project's Python virtual environment activated. Linux/WSL, Python 3.10.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
input=$(cd "$1" && pwd)
mkdir -p "$2"
out=$(cd "$2" && pwd)
if [ -n "$(ls -A "$out")" ]; then
  echo "Choose an empty output directory to preserve existing experiments." >&2
  exit 1
fi
export PYTHONPATH="$repo/src"
cd "$out"
mkdir -p data/raw
cp "$input/tkh_collection10.json" "$input/questions.csv" "$input/ground_truth.json" data/raw/
python -m tkh_abstraction.data_pipeline --output data/processed/baseline_input
revision=1110a243fdf4706b3f48f1d95db1a4f5529b4d41
for year in 2020 2022 2024 2026; do
  python -m tkh_abstraction.semantic_baseline --input "data/processed/baseline_input/snapshot_${year}.json" --output "results/semantic_ward_${year}" --revision "$revision"
done
for spec in '0 0' '0.1 0p1' '1 1'; do
  read -r weight suffix <<< "$spec"
  python -m tkh_abstraction.hypergraph_agglomerative --lambda "$weight" --output "results/hypergraph_agglomerative_lambda_${suffix}_2020"
done
base=results/hypergraph_agglomerative_lambda_0p1_2020
python -m tkh_abstraction.identity --base "$base" --prefix H2020
python -m tkh_abstraction.labels --snapshot data/processed/baseline_input/snapshot_2020.json --run "$base"
for spec in '0 0 G0' '0.1 0p1 G01'; do
  read -r gamma suffix prefix <<< "$spec"
  prev="$base"
  for year in 2022 2024; do
    cur="results/temporal_lambda_0p1_gamma_${suffix}_${year}"
    python -m tkh_abstraction.temporal_hypergraph --snapshot "data/processed/baseline_input/snapshot_${year}.json" --prev-hierarchy "$prev/hierarchy.json" --cache "results/semantic_ward_${year}/embeddings.npz" --output "$cur" --lambda 0.1 --gamma "$gamma"
    python -m tkh_abstraction.identity --prev "$prev" --cur "$cur" --prefix "${prefix}_${year}"
    python -m tkh_abstraction.labels --snapshot "data/processed/baseline_input/snapshot_${year}.json" --run "$cur"
    prev="$cur"
  done
done
run26=results/temporal_lambda_0p1_gamma_0p1_2026_eval
prev24=results/temporal_lambda_0p1_gamma_0p1_2024
python -m tkh_abstraction.temporal_hypergraph --snapshot data/processed/baseline_input/snapshot_2026.json --prev-hierarchy "$prev24/hierarchy.json" --cache results/semantic_ward_2026/embeddings.npz --output "$run26" --lambda 0.1 --gamma 0.1
python -m tkh_abstraction.identity --prev "$prev24" --cur "$run26" --prefix G01_2026
python -m tkh_abstraction.labels --snapshot data/processed/baseline_input/snapshot_2026.json --run "$run26"
python -m tkh_abstraction.retrieval --snapshot data/processed/baseline_input/snapshot_2026.json --hierarchy "$run26/hierarchy.json" --cache results/semantic_ward_2026/embeddings.npz --output results/retrieval_frozen_2026_gamma0p1.json
# Answer access starts only after retrieval is frozen.
python -m tkh_abstraction.score_retrieval --retrieval results/retrieval_frozen_2026_gamma0p1.json --output results/retrieval_score_2026_gamma0p1.json
python -m tkh_abstraction.coherence_eval --snapshot data/processed/baseline_input/snapshot_2024.json --hierarchy "$prev24/hierarchy.json" --output results/coherence_null_2024_gamma0p1.json
python -m tkh_abstraction.evaluation_scaffold
for suffix in 0 0p1; do
  prev="$base"
  prevyear=2020
  for year in 2022 2024; do
    cur="results/temporal_lambda_0p1_gamma_${suffix}_${year}"
    python -m tkh_abstraction.stability_metrics --prev "$prev/hierarchy.json" --cur "$cur/hierarchy.json" --output "results/stability_bootstrap_${prevyear}_${year}_gamma${suffix}.json"
    if [ "${3:-}" = full ]; then
      gamma=0; if [ "$suffix" = 0p1 ]; then gamma=0.1; fi
      python -m tkh_abstraction.perturbation_eval --snapshot "data/processed/baseline_input/snapshot_${year}.json" --cache "results/semantic_ward_${year}/embeddings.npz" --prev-hierarchy "$prev/hierarchy.json" --base-hierarchy "$cur/hierarchy.json" --output "results/perturb_lambda_0p1_gamma_${suffix}_${year}" --gamma "$gamma"
    fi
    prev="$cur"; prevyear="$year"
  done
done
if [ "${3:-}" = full ]; then
  python -m tkh_abstraction.final_eval_artifacts --all
fi
