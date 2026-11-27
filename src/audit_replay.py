"""Quantify strict frozen replay differences without changing published metrics."""
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def differences(a, b, path=''):
    if type(a) != type(b):
        return [dict(path=path, published=a, replayed=b)]
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return [dict(path=path, published_keys=list(a), replayed_keys=list(b))]
        return sum((differences(a[k], b[k], path+'/'+k) for k in a), [])
    if isinstance(a, list):
        if len(a) != len(b):
            return [dict(path=path, published_length=len(a), replayed_length=len(b))]
        return sum((differences(x,y,path+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))), [])
    return [] if a == b else [dict(path=path, published=a, replayed=b)]


def compare(published, actual):
    result = {}
    for p in published['authority_metrics']:
        if p['method'] != 'prophet':
            continue
        row = next(r for r in actual['authority_metrics'] if r['method']=='prophet' and r['balancing_authority']==p['balancing_authority'])
        for key, value in p.items():
            if not isinstance(value,(int,float)) or row[key] == value:
                continue
            d = abs(row[key]-value)
            result.setdefault(key, []).append(dict(authority=p['balancing_authority'],absolute=d,relative=d/abs(value) if value else None,published=value,replayed=row[key]))
    summary = {}
    for key, rows in result.items():
        finite = [r for r in rows if r['relative'] is not None]
        summary[key] = dict(units='MW' if key.endswith('_mw') else 'hours',max_absolute=max(rows,key=lambda r:r['absolute']),max_relative=max(finite,key=lambda r:r['relative']) if finite else None,undefined_relative_authorities=[r['authority'] for r in rows if r['relative'] is None],rows=rows)
    return summary


def main():
    expected = subprocess.check_output(['git','show','bf7169c:outputs/metrics/forecast_benchmark.json'],cwd=ROOT)
    assert expected == (ROOT/'outputs/metrics/forecast_benchmark.json').read_bytes()
    published=json.loads(expected)
    out=ROOT/'.artifacts/replay';out.mkdir(parents=True,exist_ok=True)
    runs=[]
    for run in range(2):
        with tempfile.TemporaryDirectory(prefix='grid-replay-audit-') as temp:
            clone=Path(temp)/'checkout'
            subprocess.run(['git','clone','--no-hardlinks',str(ROOT),str(clone)],check=True)
            subprocess.run(['git','checkout','--detach','53d75a2'],cwd=clone,check=True)
            target=clone/'.artifacts/benchmark/hourly.parquet';target.parent.mkdir(parents=True)
            shutil.copyfile(ROOT/'.artifacts/benchmark/hourly.parquet',target)
            subprocess.run([sys.executable,'-m','src.benchmark','score'],cwd=clone,check=True)
            actual=(clone/'outputs/metrics/forecast_benchmark.json').read_bytes()
            (out/f'run{run+1}.json').write_bytes(actual)
            obj=json.loads(actual)
            diff=differences(published,obj)
            prophet_indexes={str(i) for i,r in enumerate(published['authority_metrics']) if r['method']=='prophet'}
            other=[r for r in diff if not (len(r['path'].split('/'))>2 and r['path'].split('/')[1]=='authority_metrics' and r['path'].split('/')[2] in prophet_indexes)]
            runs.append(dict(run=run+1,sha256=hashlib.sha256(actual).hexdigest(),byte_identical=actual==expected,differences=diff,other_field_differences=other,prophet=compare(published,obj)))
    a=json.loads((out/'run1.json').read_text());b=json.loads((out/'run2.json').read_text())
    result=dict(published_commit='bf7169c',published_sha256=hashlib.sha256(expected).hexdigest(),platform=platform.platform(),machine=platform.machine(),python=platform.python_version(),packages={k:importlib.metadata.version(k) for k in ['prophet','cmdstanpy','lightgbm','pandas','numpy','scipy','scikit-learn']},thread_environment={k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','STAN_NUM_THREADS']},fit_arguments=dict(prophet_explicit_seed=False,prophet_explicit_threads=False,lightgbm_random_state=42,lightgbm_n_jobs=1),runs=runs,repeat_byte_identical=(out/'run1.json').read_bytes()==(out/'run2.json').read_bytes(),repeat_differences=differences(a,b),repeat_prophet=compare(a,b),cause='unresolved')
    (ROOT/'outputs/metrics/replay_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    p=ROOT/'docs/freeze_scope.md'
    text=p.read_text().split('\n## Quantified replay audit')[0]
    lines=['','## Quantified replay audit','','Both fresh local clone runs were compared with the published JSON at `bf7169c`. The strict byte comparison outcome remains '+('PASS.' if all(r['byte_identical'] for r in runs) else 'FAIL.')+' Every field outside Prophet authority metrics matched exactly in both runs, including LightGBM, authority, previous-week, moving-average, and all headline fields.' if all(not r['other_field_differences'] for r in runs) else 'Other fields differed. See the audit JSON.','','The first run has the following maxima across authorities. Relative differences divide by the absolute published value. A zero published value gives an undefined relative difference.','','| Prophet metric | Units | Largest absolute difference | Authority | Largest relative difference | Authority |','| --- | --- | ---: | --- | ---: | --- |']
    for key,row in runs[0]['prophet'].items():
        ar=row['max_absolute'];rr=row['max_relative']
        lines.append(f"| {key} | {row['units']} | {ar['absolute']:.12g} | {ar['authority']} | {rr['relative']:.9%} | {rr['authority']} |")
    lines += ['',f"Platform: {result['platform']}. Machine: {result['machine']}. Python: {result['python']}. Packages: "+', '.join(f"{k} {v}" for k,v in result['packages'].items())+'.','','The immutable Prophet constructor and fit call set neither a seed nor a thread count. LightGBM explicitly sets random_state and n_jobs as recorded in the audit JSON. Thread environment values are recorded there. No frozen source was changed.','','The repeated same-environment run '+('was byte identical to the first run.' if result['repeat_byte_identical'] else 'differed from the first run. This demonstrates run-to-run variation in the tested environment.')+' The original scoring runtime is unavailable. The cause of the published-versus-replay difference remains unresolved. Detailed row differences, undefined relative values, package versions, and repeat comparisons are in [the audit metrics](../outputs/metrics/replay_audit.json).']
    p.write_text(text+'\n'.join(lines)+'\n')
    print(json.dumps({k:result[k] for k in ['repeat_byte_identical','cause','packages']},indent=2))


if __name__=='__main__':main()
