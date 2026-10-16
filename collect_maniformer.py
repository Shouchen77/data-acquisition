#!/usr/bin/env python3
"""Collect the public metadata exposed by Maniformer Data Market.

The site currently serves the data-market list from /api/data.  This script
uses the documented-by-observation pagination response and deliberately keeps
the request rate low.  It stores the raw API records and a flat CSV suitable
for analysis.
"""
from __future__ import annotations

import csv
import json
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "https://www.maniformer.net"
API = f"{BASE}/api/data"
OUT = Path("data")
PAGE_SIZE = 12  # the site's public page size; larger pages can hit a NULL-row API bug


def get_page(page: int, page_size: int = PAGE_SIZE) -> dict:
    query = urlencode({"pageNum": page, "pageSize": page_size, "lang": "zh"})
    req = Request(f"{API}?{query}", headers={"User-Agent": "maniformer-public-data-research/1.0"})
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    first = get_page(1)
    total = int(first["total"])
    records = list(first["list"])
    pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    for page in range(2, pages + 1):
        time.sleep(0.25)
        try:
            records.extend(get_page(page)["list"])
        except HTTPError:
            # A few public rows currently have NULL action_steps and make a
            # multi-row response fail. Retry that page one row at a time.
            start = (page - 1) * PAGE_SIZE + 1
            for offset in range(PAGE_SIZE):
                time.sleep(0.08)
                try:
                    records.extend(get_page(start + offset, 1)["list"])
                except HTTPError:
                    # Keep the run usable when the server cannot serialize a
                    # single malformed public row; its id is reported by the
                    # API total but cannot be recovered through this endpoint.
                    continue
    # Keep one record per id if the API changes page boundaries during a run.
    records = list({int(row["id"]): row for row in records}.values())
    records.sort(key=lambda row: int(row["id"]), reverse=True)
    for row in records:
        try:
            row["action_steps_parsed"] = json.loads(row.get("action_steps") or "[]")
        except json.JSONDecodeError:
            row["action_steps_parsed"] = []
        row["video_url"] = f"{BASE}/{row['episode_url'].lstrip('/')}"

    (OUT / "maniformer_data_market.json").write_text(
        json.dumps({"source": API, "total": total, "records": records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    fields = [
        "id", "episode_uuid", "episode_url", "video_url", "environment", "task_name",
        "task_description", "robot_body_type", "arm_model", "hand_type", "data_type",
        "collection_method", "primary_scene", "secondary_scene", "arm_type",
        "tactile_info", "theme", "action_steps", "action_steps_parsed",
    ]
    with (OUT / "maniformer_data_market.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in records:
            out = dict(row)
            out["action_steps_parsed"] = json.dumps(out["action_steps_parsed"], ensure_ascii=False)
            writer.writerow(out)

    summary = {
        "source": API,
        "collected_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "records": len(records),
        "api_total": total,
        "dimensions": {
            key: dict(Counter(row.get(key) or "" for row in records).most_common())
            for key in ["data_type", "collection_method", "primary_scene", "secondary_scene", "arm_type", "tactile_info", "theme", "robot_body_type", "arm_model", "hand_type"]
        },
        "action_step_count": sum(len(row["action_steps_parsed"]) for row in records),
    }
    (OUT / "maniformer_data_market_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Collected {len(records)} records from {API}")


if __name__ == "__main__":
    main()
