"""Verify saved seed-level ARIs and matching seed cohorts without reclustering."""
import json
from pathlib import Path
from tkh_abstraction.perturbation_eval import ari
from tkh_abstraction.data_pipeline import write_json

checked=[]
for year in (2022,2024):
    for gamma in ('0','0p1'):
        root=Path(f'results/perturb_lambda_0p1_gamma_{gamma}_{year}')
        summary=json.loads((root/'robustness_summary.json').read_text(encoding='utf-8'))
        records=summary['records']
        assert sorted(r['seed'] for r in records)==list(range(5)), 'Unexpected or duplicated seeds'
        base=Path(f'results/temporal_lambda_0p1_gamma_{gamma}_{year}/hierarchy.json')
        for record in records:
            for level in ('k12','k48','k120'):
                value=ari(base,root/f"seed_{record['seed']}"/'hierarchy.json',level)
                assert abs(value-record['ari_vs_unperturbed'][level])<1e-12, (year,gamma,level)
                checked.append({'year':year,'gamma':gamma,'seed':record['seed'],'level':level,'ari':value})
write_json(Path('verification/saved_ari_verification.json'),{'status':'passed','comparisons':len(checked),'results':checked,'scope':'Recomputed ARI from saved hierarchy files, not rerun clustering.'})
print(f'Passed {len(checked)} saved ARI comparisons across 20 rebuilds.')
