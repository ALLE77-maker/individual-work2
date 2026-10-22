"""Download public, pinned model assets and the primary paper; no credentials."""
import hashlib
import json
from pathlib import Path
import urllib.request
import struct

ROOT = Path(__file__).resolve().parents[1]
REPO = "mlx-community/Qwen2.5-3B-Instruct-4bit"

def fetch(url, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        print(f"Downloading {target.name}", flush=True)
        with urllib.request.urlopen(url, timeout=120) as source, target.open("wb") as dest:
            while block := source.read(1024 * 1024):
                dest.write(block)
    if target.suffix == '.safetensors':
        with target.open('rb') as source:
            n = struct.unpack('<Q', source.read(8))[0]
            header = json.loads(source.read(n))
        expected = 8 + n + max(v['data_offsets'][1] for k, v in header.items() if k != '__metadata__')
        attempts = 0
        while target.stat().st_size < expected:
            offset = target.stat().st_size
            attempts += 1
            if attempts > 300:
                raise RuntimeError('Model download did not complete')
            print(f'Resuming {target.name}: {offset}/{expected}', flush=True)
            req = urllib.request.Request(url, headers={'Range': f'bytes={offset}-'})
            with urllib.request.urlopen(req, timeout=120) as source:
                print('Resume response:', source.status, source.headers.get('Content-Range'), flush=True)
                if source.status != 206:
                    raise RuntimeError('Server did not honor range request; refusing corrupt append')
                with target.open('ab') as dest:
                    while block := source.read(1024 * 1024):
                        dest.write(block)
        if target.stat().st_size != expected:
            raise RuntimeError('Safetensors length mismatch')
    digest = hashlib.sha256()
    with target.open('rb') as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()

saved_manifest = ROOT / 'references' / 'model_manifest.json'
saved = json.loads(saved_manifest.read_text()) if saved_manifest.exists() else None
endpoint = f"https://huggingface.co/api/models/{REPO}"
if saved:
    endpoint += '/revision/' + saved['revision']
with urllib.request.urlopen(endpoint, timeout=60) as stream:
    meta = json.load(stream)
revision = meta["sha"]
manifest = {"repository": REPO, "revision": revision, "files": {}}
for item in meta["siblings"]:
    name = item["rfilename"]
    if name.endswith((".json", ".safetensors", ".jinja", ".txt", ".model")):
        actual_hash = fetch(
            f"https://huggingface.co/{REPO}/resolve/{revision}/{name}", ROOT / "models" / "qwen2.5-3b" / name)
        if saved and name in saved['files'] and actual_hash != saved['files'][name]:
            raise RuntimeError(f'Asset hash mismatch for pinned file {name}')
        manifest['files'][name] = actual_hash
(ROOT / "references" / "model_manifest.json").write_text(json.dumps(manifest, indent=2))
fetch("https://aclanthology.org/2026.acl-demo.5.pdf", ROOT / "references" / "lits_paper.pdf")
print("All public assets downloaded.", flush=True)
