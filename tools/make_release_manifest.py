"""Create checksum metadata from real files; never invent a download URL."""
import argparse, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--repo',default='')
p.add_argument('--folder',default='release')
a=p.parse_args()
release=Path(a.folder);release.mkdir(parents=True,exist_ok=True)
entries=[]
for file in sorted(release.glob('TaskLock-v5.0.0-*')):
    if file.suffix.lower() not in ('.exe','.zip'):continue
    sha=hashlib.sha256(file.read_bytes()).hexdigest()
    entries.append({'filename':file.name,'sha256':sha,'bytes':file.stat().st_size,
        'download_url':f'https://github.com/{a.repo}/releases/download/v5.0.0/{file.name}' if a.repo else None})
manifest={'product':'TaskLock','publisher':'Tavlokyn Studios','version':'5.0.0',
          'published':bool(a.repo and entries),'repository':a.repo or None,'files':entries}
(release/'release-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('Manifest with',len(entries),'files')
