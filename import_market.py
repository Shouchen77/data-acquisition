"""Import the collected public task records into the website's local catalog."""

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
FIELDS = (
    "task_name", "task_description", "environment", "robot_body_type",
    "arm_model", "hand_type", "data_type", "collection_method",
    "primary_scene", "secondary_scene", "arm_type", "tactile_info", "theme",
)
DIMENSIONS = (
    "data_type", "primary_scene", "secondary_scene", "arm_type",
    "tactile_info", "collection_method", "robot_body_type", "arm_model", "hand_type",
)


def import_catalog():
    source = json.loads((DATA / "maniformer_data_market.json").read_text(encoding="utf-8"))
    collection = json.loads((DATA / "maniformer_data_market_summary.json").read_text(encoding="utf-8"))
    records = []
    seen = set()
    normalized_fields = 0
    for original in source["records"]:
        record_id = original["id"]
        if not isinstance(record_id, int) or record_id in seen:
            raise ValueError(f"Invalid or duplicate record ID: {record_id}")
        seen.add(record_id)
        record = {"id": record_id, "episode_uuid": original["episode_uuid"]}
        for field in FIELDS:
            value = str(original.get(field) or "").strip()
            if field == "arm_model" and value.lower() == "90d":
                value = "90D"
            normalized_fields += value != original.get(field)
            record[field] = value
        if not record["task_name"] or not record["task_description"]:
            raise ValueError(f"Missing task content: {record_id}")
        video_url = original.get("video_url", "")
        parsed_url = urlparse(video_url)
        if parsed_url.scheme != "https" or parsed_url.hostname != "www.maniformer.net":
            raise ValueError(f"Unexpected video URL: {record_id}")
        record["video_url"] = video_url
        steps = original.get("action_steps_parsed")
        if not isinstance(steps, list):
            steps = json.loads(original.get("action_steps") or "[]")
        for step in steps:
            start, end = step.get("start_frame"), step.get("end_frame")
            if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start <= end:
                raise ValueError(f"Invalid action frame range: {record_id}")
        record["action_steps"] = steps
        records.append(record)

    records.sort(key=lambda record: record["id"], reverse=True)
    dimensions = {
        field: dict(Counter(record[field] for record in records).most_common())
        for field in DIMENSIONS
    }
    total_steps = sum(len(record["action_steps"]) for record in records)
    catalog = {
        "schema_version": 1,
        "source_name": "Maniformer",
        "source_url": "https://www.maniformer.net/dataShop",
        "catalog_stage": "reference",
        "collected_at_utc": collection["collected_at_utc"],
        "imported_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_total": source["total"],
        "total": len(records),
        "action_step_count": total_steps,
        "dimensions": dimensions,
        "records": records,
    }
    report = {
        "source_file": "data/maniformer_data_market.json",
        "catalog_file": "data/market_catalog.json",
        "imported_at_utc": catalog["imported_at_utc"],
        "source_total": source["total"],
        "imported_records": len(records),
        "source_unavailable_count": max(0, source["total"] - len(records)),
        "duplicate_ids": 0,
        "video_links": sum(bool(record["video_url"]) for record in records),
        "action_steps": total_steps,
        "normalized_fields": normalized_fields,
        "dimensions": dimensions,
    }
    # Validation finishes before either output is replaced. Re-running never appends records.
    (DATA / "market_catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (DATA / "market_import_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(records)} tasks, {total_steps} action steps, {report['video_links']} video links.")
    print(f"Normalized {normalized_fields} fields; {report['source_unavailable_count']} source record unavailable.")


if __name__ == "__main__":
    import_catalog()
