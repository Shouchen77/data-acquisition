"""Deploy the static site beside the existing PrintLink reverse proxy.

Run on the authorized Alibaba Cloud server as root with Python 3.6 or later.
Downloads are verified against the reviewed website build before Caddy changes.
"""

import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import time
import urllib.request


EXPECTED = {
    "index.html": "d2421b0f0975378a3f6430a03722d0c6cf8bbaeedf955c02b35b6e66adf867bc",
    "styles.css": "7cc5d3cdb2667de0381ee69d6d6150c477f496d41c7026fe05e29faf7ddccf93",
    "app.js": "0ec6324f4d318b038b7384a8af79e376e6d5737beba1476652645f8f6d84f92d",
    "assets/shijiao-mark.png": "395c750240fd1114964fcd246ef32cfc6692a2c702ca14b7a9ae6c0d22de1dc3",
    "data/market_catalog.json": "cfdde790103519c2019260967b1767e67b16d2cdbf648073fbdaff6a24d25339",
}
SOURCES = (
    "https://shouchen77.github.io/data-acquisition/",
    "https://raw.githubusercontent.com/Shouchen77/data-acquisition/fe5519818feec0b7d8e609e80522e8e23b916989/",
)
SITE = Path("/srv/eyecatcher")
CADDYFILE = Path("/etc/caddy/Caddyfile")


def execute(args):
    result = subprocess.run(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True, timeout=45,
    )
    if result.returncode:
        raise RuntimeError("{}: {}".format(args[0], result.stderr[-1000:]))
    return result.stdout + result.stderr


def deploy():
    if os.geteuid() != 0:
        raise RuntimeError("Run this deployment as root")
    original = CADDYFILE.read_bytes()
    original_stat = CADDYFILE.stat()
    original_text = original.decode("utf-8")
    if "127.0.0.1:8080" not in original_text or "printlink.tech" not in original_text:
        raise RuntimeError("Existing PrintLink configuration differs from the reviewed server")
    if "eyecatcher.cn" in original_text:
        raise RuntimeError("An eyecatcher.cn configuration already exists; review before updating")
    caddy = shutil.which("caddy")
    if not caddy:
        raise RuntimeError("Existing Caddy binary was not found")
    execute(["systemctl", "is-active", "caddy"])
    with urllib.request.urlopen("http://127.0.0.1:8080/", timeout=15) as response:
        existing_page = response.read(16384).decode("utf-8", "replace")
        if response.status != 200 or "PrintLink" not in existing_page:
            raise RuntimeError("Existing PrintLink application did not pass its preflight")

    stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    release = SITE / "releases" / stamp
    release.mkdir(parents=True, mode=0o755)
    for directory in (SITE, SITE / "releases", release):
        directory.chmod(0o755)

    def download(item):
        name, expected = item
        last_error = None
        for base in SOURCES:
            try:
                request = urllib.request.Request(
                    base + name, headers={"User-Agent": "Eyecatcher-Deployment/1.0"},
                )
                with urllib.request.urlopen(request, timeout=25) as response:
                    content = response.read(4 * 1024 * 1024)
                if hashlib.sha256(content).hexdigest() != expected:
                    raise ValueError("SHA-256 mismatch: " + name)
                destination = release / name
                destination.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
                destination.write_bytes(content)
                destination.chmod(0o644)
                return name
            except Exception as error:
                last_error = error
        raise RuntimeError("Download failed for {}: {}".format(name, last_error))

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as workers:
        downloaded = sorted(workers.map(download, EXPECTED.items()))
    catalog = json.loads((release / "data/market_catalog.json").read_text(encoding="utf-8"))
    if catalog["total"] != 466 or len(catalog["records"]) != 466:
        raise RuntimeError("Market catalog failed its 466-record validation")

    backup = Path("/var/backups/eyecatcher") / stamp
    backup.mkdir(parents=True, mode=0o700)
    backup.chmod(0o700)
    (backup / "Caddyfile.before").write_bytes(original)
    additions = """

# Eyecatcher corporate website and existing PrintLink application.
eyecatcher.cn {
    root * /srv/eyecatcher/current
    encode zstd gzip
    file_server
}

3d.eyecatcher.cn {
    reverse_proxy 127.0.0.1:8080
}
"""
    candidate = backup / "Caddyfile.candidate"
    candidate.write_text(original_text.rstrip() + "\n" + additions, encoding="utf-8")
    validation = execute([caddy, "validate", "--config", str(candidate), "--adapter", "caddyfile"])
    (backup / "validation.log").write_text(validation, encoding="utf-8")

    current = SITE / "current"
    if current.exists() and not current.is_symlink():
        raise RuntimeError("Refusing to replace an existing directory at the deployment symlink")
    previous_target = os.readlink(str(current)) if current.is_symlink() else None
    pending_link = SITE / ("current." + stamp)
    pending_link.symlink_to(release, target_is_directory=True)
    os.replace(str(pending_link), str(current))

    pending_config = CADDYFILE.with_name("Caddyfile.eyecatcher-pending")
    pending_config.write_bytes(candidate.read_bytes())
    pending_config.chmod(stat.S_IMODE(original_stat.st_mode))
    os.chown(str(pending_config), original_stat.st_uid, original_stat.st_gid)
    os.replace(str(pending_config), str(CADDYFILE))
    try:
        execute(["systemctl", "reload", "caddy"])
        execute(["systemctl", "is-active", "caddy"])
    except Exception:
        CADDYFILE.write_bytes(original)
        if previous_target is not None:
            restore_link = SITE / ("restore." + stamp)
            restore_link.symlink_to(previous_target, target_is_directory=True)
            os.replace(str(restore_link), str(current))
        execute(["systemctl", "reload", "caddy"])
        raise

    result = {
        "status": "DEPLOYED", "website": "https://eyecatcher.cn/",
        "printlink": "https://3d.eyecatcher.cn/", "records": 466,
        "files": downloaded, "release": str(release), "backup": str(backup),
        "previous_release": previous_target,
    }
    (backup / "deployment.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    deploy()
