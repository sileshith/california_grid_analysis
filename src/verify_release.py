"""Run release checks from a fresh local clone without publishing anything."""
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]


def main():
    artifact=ROOT/'.artifacts/release-validation';artifact.mkdir(parents=True,exist_ok=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    results={}
    with tempfile.TemporaryDirectory(prefix='grid-release-validation-') as temporary:
        clone=Path(temporary)/'checkout'
        subprocess.run(['git','clone','--no-hardlinks','--branch','release/v1',str(ROOT),str(clone)],check=True)
        def run(name,args):
            completed=subprocess.run(args,cwd=clone,env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            (artifact/(name+'.log')).write_text(completed.stdout)
            results[name]=dict(returncode=completed.returncode)
            print(name,completed.returncode,flush=True)
            return completed
        demo=run('demo',['make','demo','PYTHON='+sys.executable])
        tests=run('tests',[sys.executable,'-m','pytest','-q','--junitxml=.artifacts/tests.xml'])
        if (clone/'.artifacts/tests.xml').exists():
            tree=ElementTree.parse(clone/'.artifacts/tests.xml')
            suites=tree.findall('.//testsuite')
            results['tests'].update({key:sum(int(s.get(key,0)) for s in suites) for key in ['tests','failures','errors','skipped']})
            shutil.copyfile(clone/'.artifacts/tests.xml',artifact/'tests.xml')
        report=run('report',['make','report','PYTHON='+sys.executable])
        pdf=clone/'reports/California_Grid_Analytics_Report_Sileshi_Hirpa.pdf'
        if report.returncode==0:
            r=PdfReader(pdf);results['report'].update(pages=len(r.pages),metadata=dict(r.metadata),letter_pages=all(float(p.mediabox.width)==612 and float(p.mediabox.height)==792 for p in r.pages))
            subprocess.run(['pdffonts',str(pdf)],stdout=(artifact/'fonts.txt').open('w'),check=True)
        notebook_code="""from pathlib import Path
import nbformat
from nbclient import NotebookClient
n=nbformat.read('notebooks/release_results.ipynb',as_version=4)
NotebookClient(n,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(Path.cwd())}}).execute()
nbformat.write(n,'.artifacts/release_results_executed.ipynb')
"""
        run('notebook',[sys.executable,'-c',notebook_code])
        run('hygiene',[sys.executable,'-m','src.check_hygiene'])
        run('lint',[sys.executable,'-m','ruff','check','--select','E9,F63,F7,F82','src','dags','tests'])
        target=clone/'.artifacts/benchmark/hourly.parquet';target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/'.artifacts/benchmark/hourly.parquet',target)
        run('strict_replay',[sys.executable,'-m','src.replay_benchmark','--freeze-ref','53d75a2'])
        published=subprocess.check_output(['git','show','bf7169c:outputs/metrics/forecast_benchmark.json'],cwd=clone)
        results['published_metrics_unchanged']=published==(clone/'outputs/metrics/forecast_benchmark.json').read_bytes()
    result=dict(tested_source_commit=commit,fresh_local_clone=True,python=sys.version.split()[0],checks=results,scope='Local checks in the installed release environment. Hosted CI, Docker operation and network PostgreSQL are unverified. Strict replay retains its actual failing outcome.',published_metrics_sha256=hashlib.sha256(published).hexdigest())
    (ROOT/'outputs/metrics/release_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    if any(results[k]['returncode'] for k in ['demo','tests','report','notebook','hygiene','lint']):raise SystemExit('Release validation has failures. Inspect the recorded checks.')


if __name__=='__main__':main()
