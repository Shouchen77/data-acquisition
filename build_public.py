"""Build a small standalone bundle for public website hosting."""

import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "output" / "public_site"
FILES = (
    "index.html", "market.html", "contact.html", "styles.css", "app.js", "site.js",
    "assets/shijiao-mark.png", "data/market_catalog.json",
)


def build():
    catalog = json.loads((ROOT / "data/market_catalog.json").read_text(encoding="utf-8"))
    if catalog["total"] != len(catalog["records"]) or not catalog["records"]:
        raise ValueError("Catalog is empty or incomplete")
    for dataset in json.loads((ROOT / "data/eyecatcher_stereo_datasets.json").read_text())["datasets"]:
        for relative in [dataset["sample_data_url"], dataset["poster"], *dataset["previews"].values()]:
            if not (ROOT / relative).is_file():
                raise FileNotFoundError("Run python3 fetch_stereo_samples.py first: " + relative)
    sample_manifest = json.loads((ROOT / "output/stereo_sample_manifest.json").read_text())["files"]
    public_files = FILES + tuple(sorted(sample_manifest))
    for relative, entry in sample_manifest.items():
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("Sample file differs from reviewed manifest: " + relative)
    for relative in public_files:
        if not (ROOT / relative).is_file():
            raise FileNotFoundError(relative)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    existing = {str(path.relative_to(PUBLIC)) for path in PUBLIC.rglob("*") if path.is_file()}
    if existing - set(public_files):
        raise ValueError("Unexpected files in public bundle; refusing to publish them")
    manifest = {"task_records": catalog["total"], "files": {}}
    for relative in public_files:
        destination = PUBLIC / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
        manifest["files"][relative] = hashlib.sha256(destination.read_bytes()).hexdigest()
    archive_path = ROOT / "output" / "website-public.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for relative in public_files:
            archive.write(PUBLIC / relative, relative)
    (ROOT / "output" / "public_build_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Public bundle: {PUBLIC}")
    print(f"Deployable archive: {archive_path}")
    print(f"{len(public_files)} website files, {catalog['total']} task records.")


if __name__ == "__main__":
    build()
