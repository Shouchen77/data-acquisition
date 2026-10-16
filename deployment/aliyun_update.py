"""Update the existing static website atomically; keep prior releases for rollback.

Python 3.6+. Usage: python3 aliyun_update.py '<reviewed JSON configuration>'
Configuration keys: source_bases, files (path: SHA-256), total, collections.
The reviewed configuration is generated from the local public build manifest.
"""
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

SITE = Path('/srv/eyecatcher')
PUBLIC_FILES = {'index.html', 'styles.css', 'app.js', 'assets/shijiao-mark.png', 'data/market_catalog.json'}


def digest(content):
    return hashlib.sha256(content).hexdigest()


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'Eyecatcher-Deployment/2.0', 'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(request, timeout=25) as response:
        if response.status != 200:
            raise RuntimeError('Unexpected response: ' + str(response.status))
        content = response.read(8 * 1024 * 1024 + 1)
        if len(content) > 8 * 1024 * 1024:
            raise ValueError('File exceeds deployment limit')
        return content


def update(config):
    if os.geteuid() != 0:
        raise RuntimeError('Run on the existing server as root')
    expected = config['files']
    if set(expected) != PUBLIC_FILES:
        raise ValueError('Only the reviewed five website files can be deployed')
    bases = config['source_bases']
    if not bases or any(not base.startswith('https://') or not base.endswith('/') for base in bases):
        raise ValueError('Expected HTTPS source bases')
    current = SITE / 'current'
    if not current.is_symlink() or not current.resolve().is_dir():
        raise RuntimeError('Expected the existing managed release symlink')
    previous = os.readlink(str(current))
    caddy_path = Path('/etc/caddy/Caddyfile')
    caddy_before = caddy_path.read_bytes()
    if 'root * /srv/eyecatcher/current' not in caddy_before.decode('utf-8'):
        raise RuntimeError('Existing website route differs from the reviewed configuration')
    if 'PrintLink' not in fetch('http://127.0.0.1:8080/').decode('utf-8', 'replace'):
        raise RuntimeError('Existing PrintLink health check failed')
    stamp = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    release = SITE / 'releases' / stamp
    release.mkdir(mode=0o755)
    backup = Path('/var/backups/eyecatcher') / stamp
    backup.mkdir(mode=0o700)
    (backup / 'deployment-config.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')

    def download(name):
        errors = []
        for base in bases:
            try:
                content = fetch(base + name)
                if digest(content) != expected[name]:
                    raise ValueError('SHA-256 mismatch')
                destination = release / name
                destination.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
                destination.write_bytes(content)
                destination.chmod(0o644)
                return name
            except Exception as error:
                errors.append(str(error))
        raise RuntimeError('Download failed for {}: {}'.format(name, '; '.join(errors)))

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as workers:
        downloaded = sorted(workers.map(download, expected))
    catalog = json.loads((release / 'data/market_catalog.json').read_text(encoding='utf-8'))
    if catalog.get('schema_version') != 2 or catalog['total'] != config['total'] or len(catalog['records']) != config['total'] or catalog['collections'] != config['collections']:
        raise ValueError('Catalog schema/count validation failed')
    (backup / 'previous-release.txt').write_text(previous + '\n', encoding='utf-8')
    switched = False
    try:
        pending = SITE / ('current.' + stamp)
        pending.symlink_to(release, target_is_directory=True)
        os.replace(str(pending), str(current))
        switched = True

        def verify(name):
            content = fetch('https://eyecatcher.cn/' + name + '?release=' + stamp)
            if digest(content) != expected[name]:
                raise RuntimeError('Live verification failed: ' + name)
            return name
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as workers:
            verified = sorted(workers.map(verify, expected))
        if caddy_path.read_bytes() != caddy_before:
            raise RuntimeError('Caddy configuration changed during deployment')
        if 'PrintLink' not in fetch('http://127.0.0.1:8080/').decode('utf-8', 'replace'):
            raise RuntimeError('PrintLink health check failed after update')
    except Exception:
        if switched:
            restore = SITE / ('restore.' + stamp)
            restore.symlink_to(previous, target_is_directory=True)
            os.replace(str(restore), str(current))
        raise
    result = {'status': 'UPDATED', 'website': 'https://eyecatcher.cn/', 'release': str(release), 'previous_release': previous, 'backup': str(backup), 'total': catalog['total'], 'collections': catalog['collections'], 'verified_files': verified, 'caddy_unchanged': True, 'printlink_healthy': True}
    (backup / 'deployment.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('status', 'release', 'previous_release', 'total', 'collections', 'caddy_unchanged', 'printlink_healthy')}, separators=(',', ':')))


if __name__ == '__main__':
    update(json.loads(sys.argv[1]))
