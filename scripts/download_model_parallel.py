"""Resume the public model download in verified ranges on slow connections."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import struct
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT/'references/model_manifest.json').read_text())
repo, rev = manifest['repository'], manifest['revision']
target = ROOT/'models/qwen2.5-3b/model.safetensors'
with target.open('rb') as source:
    n = struct.unpack('<Q',source.read(8))[0]
    header = json.loads(source.read(n))
total = 8+n+max(v['data_offsets'][1] for k,v in header.items() if k!='__metadata__')
if target.stat().st_size == total:
    digest = hashlib.sha256()
    with target.open('rb') as stream:
        while block := stream.read(1024*1024):
            digest.update(block)
    if digest.hexdigest() == manifest['files']['model.safetensors']:
        print('Complete model already matches the saved manifest.',flush=True)
        raise SystemExit(0)
chunks = ROOT/'models/chunks'
chunks.mkdir(exist_ok=True)
size = 8*1024*1024

def get_chunk(i):
    start, end = i*size, min(total,(i+1)*size)-1
    dest = chunks/f'{i:04d}.part'
    for attempt in range(8):
        have = dest.stat().st_size if dest.exists() else 0
        if have == end-start+1:
            return i
        request = urllib.request.Request(
            f'https://huggingface.co/{repo}/resolve/{rev}/model.safetensors?part={i}&offset={have}',
            headers={'Range':f'bytes={start+have}-{end}'})
        try:
            with urllib.request.urlopen(request,timeout=90) as source:
                if source.status != 206 or not source.headers.get('Content-Range','').startswith(f'bytes {start+have}-'):
                    raise RuntimeError('Range response mismatch')
                with dest.open('ab') as stream:
                    while block := source.read(1024*1024):
                        stream.write(block)
        except Exception as error:
            print(f'Chunk {i} retry: {type(error).__name__}',flush=True)
            time.sleep(1)
    raise RuntimeError(f'Incomplete chunk {i}')

count = (total+size-1)//size
with ThreadPoolExecutor(max_workers=16) as pool:
    pending = [pool.submit(get_chunk,i) for i in range(count)]
    for done, future in enumerate(as_completed(pending),1):
        future.result()
        if done%10 == 0 or done==count:
            print(f'Verified chunks {done}/{count}',flush=True)
temp = target.with_suffix('.complete')
digest=hashlib.sha256()
with temp.open('wb') as output:
    for i in range(count):
        data=(chunks/f'{i:04d}.part').read_bytes()
        digest.update(data)
        output.write(data)
assert temp.stat().st_size==total
temp.replace(target)
manifest['files']['model.safetensors']=digest.hexdigest()
(ROOT/'references/model_manifest.json').write_text(json.dumps(manifest,indent=2))
print(f'Complete model: {total} bytes, SHA256 {digest.hexdigest()}',flush=True)
