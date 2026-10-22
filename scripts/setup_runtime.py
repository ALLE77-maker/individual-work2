"""Retrieve the exact upstream source and apply the documented runtime patch."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
UPSTREAM=ROOT/'vendor/lits-llm'
REVISION='1ef347bee7b3f2c10dc504342589b8c951794c2d'
PATCH=ROOT/'patches/lazy_imports.patch'

def run(*args,**kwargs):
    return subprocess.run(list(args),check=True,**kwargs)

UPSTREAM.parent.mkdir(exist_ok=True)
if not UPSTREAM.exists():
    run('git','clone','https://github.com/xinzhel/lits-llm.git',str(UPSTREAM))
    run('git','-C',str(UPSTREAM),'checkout','--detach',REVISION)
actual=subprocess.check_output(['git','-C',str(UPSTREAM),'rev-parse','HEAD'],text=True).strip()
if actual!=REVISION:
    raise RuntimeError(f'Expected upstream revision {REVISION}, found {actual}; refusing to reset existing files')
already=subprocess.run(['git','-C',str(UPSTREAM),'apply','--reverse','--check',str(PATCH)],capture_output=True).returncode==0
if not already:
    run('git','-C',str(UPSTREAM),'apply','--check',str(PATCH))
    run('git','-C',str(UPSTREAM),'apply',str(PATCH))
print('Pinned upstream source and common runtime adaptation are ready.')
