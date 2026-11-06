"""Deploy the reviewed multipage website and stereo media, with atomic rollback."""
import concurrent.futures,datetime,hashlib,json,os,shutil,sys,urllib.request
from pathlib import Path,PurePosixPath
SITE=Path('/srv/eyecatcher')
CORE={'index.html','market.html','contact.html','styles.css','app.js','site.js','assets/shijiao-mark.png','data/market_catalog.json'}
def digest_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def get(url,limit=8*1024*1024,headers=None):
    req=urllib.request.Request(url,headers=dict({'User-Agent':'Eyecatcher-Deployment/3.0','Cache-Control':'no-cache'},**(headers or {})))
    with urllib.request.urlopen(req,timeout=120) as r:
        data=r.read(limit+1)
        if len(data)>limit:raise ValueError('Response too large')
        return data

def update(c):
    if os.geteuid()!=0 or set(c['core'])!=CORE:raise ValueError('Invalid deployment configuration')
    current=SITE/'current'
    if not current.is_symlink():raise ValueError('Expected current release symlink')
    previous=os.readlink(str(current));caddy=Path('/etc/caddy/Caddyfile').read_bytes()
    if 'root * /srv/eyecatcher/current' not in caddy.decode():raise ValueError('Unexpected website route')
    if b'PrintLink' not in get('http://127.0.0.1:8080/'):raise ValueError('PrintLink health check failed')
    stamp=datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ');release=SITE/'releases'/stamp
    backup=Path('/var/backups/eyecatcher')/stamp;backup.mkdir(mode=0o700)
    release.mkdir(mode=0o755)
    (backup/'deployment-config.json').write_text(json.dumps(c,indent=2))
    (backup/'previous-release.txt').write_text(previous+'\n')
    def core_file(name):
        errors=[]
        for base in c['source_bases']:
            try:
                data=get(base+name)
                if hashlib.sha256(data).hexdigest()!=c['core'][name]:raise ValueError('Hash mismatch')
                p=release/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);p.chmod(0o644);return
            except Exception as e:errors.append(str(e))
        raise RuntimeError('Cannot download '+name+': '+'; '.join(errors))
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:list(pool.map(core_file,CORE))
    catalog=json.loads((release/'data/market_catalog.json').read_text())
    if catalog['collections']!={'human_stereo':4,'robot_real':60,'robot_sim':55} or catalog['total']!=119 or len(catalog['records'])!=119:raise ValueError('Catalog count mismatch')
    shared=SITE/'shared'/('stereo-20261106-'+c['archive_sha256'][:12])
    shared.mkdir(parents=True,exist_ok=True)
    manifest=c['media']
    ready=all((shared/n).is_file() and digest_file(shared/n)==entry['sha256'] for n,entry in manifest.items())
    if not ready:
        def media_file(item):
            name,entry=item
            if not name.startswith('media/stereo/20261106/') or '..' in PurePosixPath(name).parts or entry['bytes']>80*1024*1024:raise ValueError('Invalid media file')
            path=shared/name
            if path.is_file() and digest_file(path)==entry['sha256']:return
            path.parent.mkdir(parents=True,exist_ok=True);pending=path.with_name(path.name+'.partial');errors=[]
            for base in c['media_bases']:
                try:
                    req=urllib.request.Request(base+name,headers={'User-Agent':'Eyecatcher-Deployment/3.0'})
                    with urllib.request.urlopen(req,timeout=180) as response,pending.open('wb') as out:
                        copied=0
                        while True:
                            block=response.read(1024*1024)
                            if not block:break
                            copied+=len(block)
                            if copied>entry['bytes']:raise ValueError('Media file exceeds expected size')
                            out.write(block)
                    if pending.stat().st_size!=entry['bytes'] or digest_file(pending)!=entry['sha256']:raise ValueError('Media file hash mismatch')
                    pending.chmod(0o644);os.replace(str(pending),str(path));return
                except Exception as e:errors.append(str(e))
            raise RuntimeError('Cannot download '+name+': '+'; '.join(errors))
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(media_file,manifest.items()))
        print('MEDIA_FILES_VERIFIED',len(manifest),flush=True)
    (release/'media').symlink_to(shared/'media',target_is_directory=True)
    switched=False
    try:
        pending=SITE/('current.'+stamp);pending.symlink_to(release,target_is_directory=True);os.replace(str(pending),str(current));switched=True
        def verify(name):
            if hashlib.sha256(get('https://eyecatcher.cn/'+name+'?release='+stamp)).hexdigest()!=c['core'][name]:raise ValueError('Live file hash mismatch: '+name)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:list(pool.map(verify,CORE))
        for n in manifest:
            if n.endswith('.mp4'):
                req=urllib.request.Request('https://eyecatcher.cn/'+n,headers={'Range':'bytes=0-1023'})
                with urllib.request.urlopen(req,timeout=30) as r:
                    if r.status!=206 or len(r.read(1025))!=1024:raise ValueError('Media range request failed: '+n)
            else:
                if hashlib.sha256(get('https://eyecatcher.cn/'+n)).hexdigest()!=manifest[n]['sha256']:raise ValueError('Sample data live verification failed: '+n)
        if Path('/etc/caddy/Caddyfile').read_bytes()!=caddy or b'PrintLink' not in get('http://127.0.0.1:8080/'):raise ValueError('Existing service verification failed')
    except Exception:
        if switched:
            restore=SITE/('restore.'+stamp);restore.symlink_to(previous,target_is_directory=True);os.replace(str(restore),str(current))
        raise
    result={'status':'UPDATED','release':str(release),'previous_release':previous,'backup':str(backup),'collections':catalog['collections'],'total':119,'core_files_verified':len(CORE),'media_files_verified':len(manifest),'media_range_requests_verified':16,'caddy_unchanged':True,'printlink_healthy':True}
    (backup/'deployment.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
if __name__=='__main__':update(json.loads(sys.argv[1]))
