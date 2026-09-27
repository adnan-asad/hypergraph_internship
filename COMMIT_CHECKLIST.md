# Copy and commit the final handoff

This folder is an audited copy of the uploaded repository, not the live WSL checkout. No commit or push was performed. Copy its contents into your repository after preserving any newer local work. Do not replace your `.git`, `.venv`, local data or model caches; none are included here.

## Commit

- `src/`, `tests/`, `scripts/`: supplied implementation plus the identity/portability fixes, audit and verification scripts.
- `README.md`, `report.md`, `metrics.json`, `AI_USAGE.md`, `COMMIT_CHECKLIST.md`.
- `requirements.txt`, `requirements-test.txt` and the historical pinned lists.
- `docs/`, including the assessment, final status and actual developer-review evidence.
- `submission/`: four canonical hierarchy/event exports.
- `results/`: saved experiments and scoring evidence. `.gitignore` now permits these JSON/CSV records and excludes `.npz` caches. Some old status files are historical; the root report/metrics are authoritative.
- `verification/` and `MANIFEST.sha256`: verification evidence and package-file hashes.
- `evaluation_llm/`: protocol, frozen anonymized packets, unchanged LLM judgments, aggregation, and actual/pending human checks. Keep the identity key hidden from any new judge; it is an audit key, not a credential.

Do not commit virtual environments, credentials, `.pi/`, raw supplied data, processed snapshot copies or embedding caches. Prefer a private repository for the supplied assessment material unless public release is authorized. For a public repository, remove the assessment/data-derived artifacts if their redistribution is not permitted.

## Review before committing

```bash
git status --short
git diff --stat
git diff -- src tests scripts README.md .gitignore
PYTHONPATH=src python -m unittest discover -s tests -v
git add src tests scripts docs submission results verification evaluation_llm
git add README.md report.md metrics.json AI_USAGE.md COMMIT_CHECKLIST.md
git add requirements.txt requirements-test.txt requirements-baseline.txt requirements-semantic.txt .gitignore MANIFEST.sha256
git diff --cached --stat
git commit -m "Package temporal hypergraph assessment with audited evaluation and limitations"
```

Only push after reviewing the staged files. The manifest describes this handoff; regenerate it if you change package files. It intentionally excludes the manifest itself and Python cache files.

## Be ready to explain

1. Why the exact Ward increase differs from cosine centroid distance.
2. Why lower fragmentation cannot establish scientific coherence.
3. What a counted quotient preserves and why internal edges are retained.
4. Why temporal history changes by stage and why gamma is not always beneficial.
5. Why developer annotation counts cannot be treated as independent group-level ratings.
6. Why a copied gloss can be mechanically faithful yet scientifically unhelpful.
7. Why the saved retrieval result does not demonstrate improved question answering.
