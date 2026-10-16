"""Package the complete GitHub-ready project without local runtime artifacts."""

import fnmatch
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
ARCHIVE = OUTPUT / "shijiao-data-website-github.zip"
MANIFEST = OUTPUT / "project-package-manifest.json"
PACKAGE_ROOT = "shijiao-data-website"
IGNORED_PARTS = {".git", ".tools", ".runtime", "__pycache__", ".DS_Store"}
IGNORED_PREFIXES = (
    "output/public_site/",
    "device_capture/captures/",
    "device_capture/sdk/vendor/",
    "device_capture/sdk/rendered/",
    "device_capture/sdk/extracted_text/",
)


def include(relative):
    name = relative.as_posix()
    if any(part in IGNORED_PARTS for part in relative.parts):
        return False
    if name.startswith(IGNORED_PREFIXES) or name.endswith(".pyc"):
        return False
    if relative.name.startswith(".env") and relative.name != ".env.example":
        return False
    if name in {"PROJECT_PACKAGE_MANIFEST.json", "output/project-package-manifest.json", "output/public_build_manifest.json"}:
        return False
    if fnmatch.fnmatch(name, "output/*.zip") or fnmatch.fnmatch(name, "device_capture/evidence/ui-*.jpg"):
        return False
    return True


def project_files():
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "."],
            cwd=ROOT, capture_output=True, check=True,
        )
        candidates = [Path(name) for name in result.stdout.decode("utf-8").split("\0") if name]
    except (FileNotFoundError, subprocess.CalledProcessError):
        # Also works after extracting the archive, before git init.
        candidates = []
        for directory, subdirectories, filenames in os.walk(ROOT, followlinks=False):
            base = Path(directory).relative_to(ROOT)
            subdirectories[:] = [name for name in subdirectories if include(base / name / "_")]
            candidates.extend(base / name for name in filenames)
    files = []
    for relative in sorted(set(candidates)):
        if not include(relative):
            continue
        path = ROOT / relative
        if not path.is_file():
            continue
        if path.is_symlink() or ROOT not in path.resolve().parents:
            raise ValueError(f"Refusing to include an external or symbolic file: {relative}")
        files.append(relative)
    return files


def package():
    files = project_files()
    required = {
        "index.html", "styles.css", "app.js", "data/market_catalog.json",
        "README.md", "GITHUB_PUBLISH.md", ".gitignore",
        ".github/workflows/deploy-pages.yml", "build_public.py", "package_project.py",
    }
    missing = required - {path.as_posix() for path in files}
    if missing:
        raise ValueError(f"Missing required project files: {sorted(missing)}")
    catalog = json.loads((ROOT / "data/market_catalog.json").read_text(encoding="utf-8"))
    if catalog["total"] != len(catalog["records"]):
        raise ValueError("Market catalog count mismatch")
    manifest = {
        "format_version": 1,
        "root_directory": PACKAGE_ROOT,
        "project_files": len(files),
        "catalog_records": catalog["total"],
        "source_bytes": 0,
        "files": {},
    }
    OUTPUT.mkdir(exist_ok=True)
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in files:
            content = (ROOT / relative).read_bytes()
            manifest["source_bytes"] += len(content)
            manifest["files"][relative.as_posix()] = hashlib.sha256(content).hexdigest()
            entry = zipfile.ZipInfo.from_file(ROOT / relative, f"{PACKAGE_ROOT}/{relative.as_posix()}")
            archive.writestr(entry, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        archive.writestr(f"{PACKAGE_ROOT}/PROJECT_PACKAGE_MANIFEST.json", manifest_text)
    MANIFEST.write_text(manifest_text, encoding="utf-8")
    print(f"GitHub project archive: {ARCHIVE}")
    print(f"Included {len(files)} project files and a SHA-256 manifest; {catalog['total']} market records.")
    print(f"Archive size: {ARCHIVE.stat().st_size:,} bytes")


if __name__ == "__main__":
    package()
