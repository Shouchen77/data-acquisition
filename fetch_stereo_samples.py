"""Fetch the reviewed public stereo release without storing binary media in Git."""
import hashlib,json,shutil,tempfile,urllib.request,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parent
BASE='https://github.com/Shouchen77/data-acquisition/releases/download/stereo-samples-20261106/'

def fetch():
    manifest=json.loads((ROOT/'output/stereo_sample_manifest.json').read_text())['files']
    if all((ROOT/n).is_file() and hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v['sha256'] for n,v in manifest.items()):return
    with tempfile.TemporaryDirectory() as temp:
        archive=Path(temp)/'samples.zip'
        with urllib.request.urlopen(BASE+'stereo-samples-20261106.zip',timeout=180) as response,archive.open('wb') as f:shutil.copyfileobj(response,f)
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
