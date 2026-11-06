"""Fetch the reviewed public stereo release without storing binary media in Git."""
import concurrent.futures,hashlib,json,shutil,tempfile,urllib.request,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parent
BASE='https://github.com/Shouchen77/data-acquisition/releases/download/stereo-samples-20261106/'

def fetch():
    release=json.loads((ROOT/'output/stereo_sample_manifest.json').read_text())
    manifest=release['files']
    if all((ROOT/n).is_file() and hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v['sha256'] for n,v in manifest.items()):return
    with tempfile.TemporaryDirectory() as temp:
        archive=Path(temp)/'samples.zip'
        def part_file(part):
            if PurePosixPath(part['name']).name!=part['name']:raise ValueError('Invalid part name')
            p=Path(temp)/part['name']
            with urllib.request.urlopen(BASE+part['name'],timeout=180) as response,p.open('wb') as f:shutil.copyfileobj(response,f)
            if p.stat().st_size!=part['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=part['sha256']:raise ValueError('Archive part hash mismatch')
            return p
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:parts=list(pool.map(part_file,release['archive']['parts']))
        with archive.open('wb') as f:
            for p in parts:
                with p.open('rb') as source:shutil.copyfileobj(source,f)
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=release['archive']['sha256']:raise ValueError('Archive hash mismatch')
        with zipfile.ZipFile(archive) as z:
            if set(z.namelist())!=set(manifest):raise ValueError('Archive file list mismatch')
            for info in z.infolist():
                name=info.filename
                if not name.startswith('media/stereo/20261106/') or '..' in PurePosixPath(name).parts or info.file_size!=manifest[name]['bytes']:raise ValueError('Unexpected archive path/size')
                data=z.read(name)
                if hashlib.sha256(data).hexdigest()!=manifest[name]['sha256']:raise ValueError('Sample hash mismatch: '+name)
                out=ROOT/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
    print('Stereo sample media ready:',len(manifest),'files')

if __name__=='__main__':fetch()
