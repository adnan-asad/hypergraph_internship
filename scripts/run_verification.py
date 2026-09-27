"""Capture numerical test and saved-result verification evidence."""
import datetime, json, os, platform, subprocess, sys
from pathlib import Path
from importlib.metadata import version

out=Path('verification'); out.mkdir(exist_ok=True)
env=dict(os.environ, PYTHONPATH=str(Path('src').resolve()))
checks=[]
for name,args in [('unit_tests',['-m','unittest','discover','-s','tests','-v']),('saved_results',['scripts/verify_saved_results.py'])]:
    result=subprocess.run([sys.executable,*args],env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (out/f'{name}.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    checks.append({'check':name,'returncode':result.returncode,'log':f'verification/{name}.log'})
record={'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'dependencies':{p:version(p) for p in ['numpy','scipy','scikit-learn','joblib','threadpoolctl']},'checks':checks,'full_model_or_clustering_rerun':False}
(out/'verification.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,indent=2))
sys.exit(any(c['returncode'] for c in checks))
