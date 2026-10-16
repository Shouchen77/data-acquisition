"""Start, inspect or stop a temporary Cloudflare preview of this website."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tarfile
import time
import urllib.request

from build_public import ROOT, build

RUNTIME = ROOT / ".runtime"
STATE_FILE = RUNTIME / "public-preview.json"
BINARY = ROOT / ".tools" / "cloudflared"
SERVER_LOG = RUNTIME / "website-server.log"
TUNNEL_LOG = RUNTIME / "cloudflare-tunnel.log"


def read_state():
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}


def owns_process(pid, marker):
    if not isinstance(pid, int):
        return False
    result = subprocess.run(["ps", "-p", str(pid), "-o", "args="], capture_output=True, text=True)
    return result.returncode == 0 and str(marker) in result.stdout


def install_cloudflared():
    if BINARY.is_file():
        return
    print("Downloading cloudflared from Cloudflare's official GitHub release…", flush=True)
    request = urllib.request.Request("https://api.github.com/repos/cloudflare/cloudflared/releases/latest", headers={"User-Agent": "ShijiaoWebsitePreview", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        release = json.load(response)
    asset = next(item for item in release["assets"] if item["name"] == "cloudflared-darwin-arm64.tgz")
    with urllib.request.urlopen(asset["browser_download_url"], timeout=60) as response:
        archive_bytes = response.read()
    expected = asset.get("digest")
    if not expected or expected != "sha256:" + hashlib.sha256(archive_bytes).hexdigest():
        raise ValueError("Cloudflared download checksum mismatch")
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
        member = next(item for item in archive.getmembers() if item.isfile() and Path(item.name).name == "cloudflared")
        binary_bytes = archive.extractfile(member).read()
    BINARY.parent.mkdir(parents=True, exist_ok=True)
    BINARY.write_bytes(binary_bytes)
    BINARY.chmod(0o755)
    print(f"Installed cloudflared {release['tag_name']} (checksum verified).", flush=True)


def launch(command, log_path):
    with log_path.open("w") as logfile:
        return subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=logfile, stderr=subprocess.STDOUT, start_new_session=True)


def start():
    build()
    state = read_state()
    if owns_process(state.get("tunnel_pid"), BINARY) and owns_process(state.get("server_pid"), ROOT / "serve_public.py"):
        print(f"Preview is already running: {state.get('url') or 'URL is still being assigned'}", flush=True)
        return
    # A stopped tunnel can leave its website server running. Clean up only the
    # processes belonging to the saved preview before allocating its port again.
    for key, marker in [("tunnel_pid", BINARY), ("server_pid", ROOT / "serve_public.py")]:
        if owns_process(state.get(key), marker):
            os.kill(state[key], signal.SIGTERM)
            for _ in range(20):
                if not owns_process(state[key], marker):
                    break
                time.sleep(0.1)
    install_cloudflared()
    RUNTIME.mkdir(parents=True, exist_ok=True)
    server = launch([sys.executable, "-u", str(ROOT / "serve_public.py")], SERVER_LOG)
    try:
        for _ in range(30):
            if server.poll() is not None:
                raise RuntimeError("Public website server failed to start. See .runtime/website-server.log")
            try:
                with urllib.request.urlopen("http://127.0.0.1:8766/", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError("Public website server did not become ready")
        tunnel = launch([str(BINARY), "tunnel", "--url", "http://127.0.0.1:8766", "--protocol", "http2", "--no-autoupdate"], TUNNEL_LOG)
        state = {"server_pid": server.pid, "tunnel_pid": tunnel.pid, "url": None, "local_url": "http://127.0.0.1:8766"}
        STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")
        print("Requesting a temporary public HTTPS URL…", flush=True)
        for _ in range(120):
            if tunnel.poll() is not None:
                raise RuntimeError("Cloudflare tunnel stopped. See .runtime/cloudflare-tunnel.log")
            logs = TUNNEL_LOG.read_text()
            match = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", logs)
            if match and state["url"] != match.group():
                state["url"] = match.group()
                STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")
                print(f"Public URL: {state['url']}", flush=True)
            if state["url"] and "Registered tunnel connection" in logs:
                print("Tunnel connected. Keep this computer awake and online while sharing.", flush=True)
                return
            time.sleep(0.5)
        raise RuntimeError("Tunnel connection is still pending. Check status and .runtime/cloudflare-tunnel.log")
    except Exception:
        # Preserve the named processes if an assigned tunnel is still connecting;
        # status/stop can inspect or clean up this task's processes later.
        if not STATE_FILE.exists() and server.poll() is None:
            server.terminate()
        raise


def status():
    state = read_state()
    if not state:
        print("No public preview has been started.")
        return
    if not state.get("url") and TUNNEL_LOG.exists():
        match = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", TUNNEL_LOG.read_text())
        if match:
            state["url"] = match.group()
            STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")
    running = owns_process(state.get("server_pid"), ROOT / "serve_public.py") and owns_process(state.get("tunnel_pid"), BINARY)
    print("Processes: " + ("running" if running else "stopped"))
    print("Public URL: " + str(state.get("url") or "not assigned"))


def stop():
    state = read_state()
    for key, marker in [("tunnel_pid", BINARY), ("server_pid", ROOT / "serve_public.py")]:
        if owns_process(state.get(key), marker):
            os.kill(state[key], signal.SIGTERM)
    print("Stopped this website's public preview.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("start", "status", "stop"), nargs="?", default="start")
    command = parser.parse_args().command
    {"start": start, "status": status, "stop": stop}[command]()
