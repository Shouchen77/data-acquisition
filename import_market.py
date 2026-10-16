"""Import the collected public task records into the website's local catalog."""

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import math
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
SCENES = [
    {"id": "factory", "label": "工厂", "description": "装配、质检、设备操作", "subscenes": ["装配工位", "质检台", "产线"]},
    {"id": "medical", "label": "医疗", "description": "器械整理、物资准备、护理辅助", "subscenes": ["器械准备区", "物资间", "护理实训区"]},
    {"id": "home", "label": "家居", "description": "厨房操作、收纳、清洁", "subscenes": ["厨房", "客厅", "卧室"]},
    {"id": "logistics", "label": "仓储物流", "description": "拣选、分拣、打包", "subscenes": ["货架区", "分拣台", "打包区"]},
    {"id": "retail", "label": "商超", "description": "理货、补货、收银", "subscenes": ["货架区", "收银台"]},
    {"id": "office", "label": "办公", "description": "桌面操作、物品整理", "subscenes": ["工位", "会议室"]},
    {"id": "food", "label": "餐饮", "description": "备餐、饮品制作、餐具整理", "subscenes": ["备餐区", "吧台", "餐厅"]},
]
SCENE_IDS = {scene["id"] for scene in SCENES}
SOURCE_SCENES = {"工业": "factory", "家居": "home", "商超": "retail", "办公": "office", "餐饮": "food"}


def public_url(value):
    """Only publish intentional HTTPS previews/reports, never local file paths."""
    if not value:
        return ""
    if not isinstance(value, str):
        raise ValueError("Public preview/report URL must be a string")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Public preview/report URLs must use HTTPS without credentials")
    return value


def import_stereo_datasets(payload):
    """Whitelist public summaries; operator identity and raw delivery files stay private."""
    if payload.get("schema_version") != 1 or not isinstance(payload.get("datasets"), list):
        raise ValueError("Invalid stereo dataset source")
    records, seen = [], set()
    for dataset in payload["datasets"]:
        if not isinstance(dataset, dict):
            raise ValueError("Stereo dataset must be an object")
        dataset_id = dataset.get("dataset_id", "")
        if not isinstance(dataset_id, str) or not dataset_id or dataset_id in seen:
            raise ValueError("Missing or duplicate stereo dataset_id")
        seen.add(dataset_id)
        if dataset.get("scene_id") not in SCENE_IDS:
            raise ValueError("Unknown stereo scene_id: " + dataset_id)
        for field in ("title", "description", "subscene"):
            if not isinstance(dataset.get(field), str) or not dataset[field].strip():
                raise ValueError("Missing stereo " + field + ": " + dataset_id)
        availability = dataset.get("availability")
        if availability not in ("sampling", "available"):
            raise ValueError("Stereo availability must be sampling or available")
        for field in ("capture", "previews"):
            if not isinstance(dataset.get(field, {}), dict):
                raise ValueError("Stereo " + field + " must be an object")
        for field in ("task_tags", "delivery_contents"):
            if not isinstance(dataset.get(field, []), list) or not all(isinstance(value, str) for value in dataset.get(field, [])):
                raise ValueError("Stereo " + field + " must be a list of strings")
        capture = {}
        for field in ("width", "height", "fps", "imu_hz", "fov_h", "fov_v"):
            value = dataset.get("capture", {}).get(field)
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value <= 0):
                raise ValueError("Invalid measured capture parameter: " + field)
            capture[field] = value
        for field in ("episode_count", "duration_seconds"):
            value = dataset.get(field)
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
                raise ValueError("Invalid stereo " + field)
        episode_count = dataset.get("episode_count")
        if episode_count is not None and (type(episode_count) is not int):
            raise ValueError("episode_count must be an integer")
        if availability == "available" and not episode_count:
            raise ValueError("Available datasets require an actual episode_count")
        previews = {eye: public_url(dataset.get("previews", {}).get(eye, "")) for eye in ("left", "right")}
        if bool(previews["left"]) != bool(previews["right"]):
            raise ValueError("Stereo previews require both left and right views")
        qa_url = public_url(dataset.get("qa_report_url", ""))
        # A target standard never becomes a compliance claim during import.
        records.append({
            "id": dataset_id, "catalog_id": "ec:" + dataset_id, "dataset_kind": "human_stereo",
            "subject": "human", "source_id": "eyecatcher", "source_name": "视焦科技",
            "catalog_stage": "owned", "standard_basis": "V3", "availability": availability,
            "task_name": dataset["title"].strip(), "task_description": dataset["description"].strip(),
            "scene_id": dataset["scene_id"], "primary_scene": next(s["label"] for s in SCENES if s["id"] == dataset["scene_id"]),
            "secondary_scene": dataset["subscene"].strip(), "task_tags": [str(tag) for tag in dataset.get("task_tags", [])],
            "capture": capture, "episode_count": episode_count, "duration_seconds": dataset.get("duration_seconds"),
            "previews": previews, "qa_report_url": qa_url,
            "quality_status": "report_available" if qa_url else "pending",
            "delivery_contents": [str(item) for item in dataset.get("delivery_contents", [])],
            "action_steps": [],
        })
    return records


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
        record = {"id": record_id, "catalog_id": "mf:" + str(record_id), "episode_uuid": original["episode_uuid"]}
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
        if record["primary_scene"] not in SOURCE_SCENES:
            raise ValueError("Unknown reference scene: " + record["primary_scene"])
        record.update({
            "dataset_kind": "robot_sim" if record["data_type"] == "仿真" else "robot_real",
            "subject": "robot", "source_id": "maniformer", "source_name": "Maniformer",
            "catalog_stage": "reference", "availability": "reference", "standard_basis": None,
            "quality_status": "not_disclosed", "scene_id": SOURCE_SCENES[record["primary_scene"]],
        })
        records.append(record)

    records.sort(key=lambda record: record["id"], reverse=True)
    stereo_source = DATA / "eyecatcher_stereo_datasets.json"
    stereo_records = import_stereo_datasets(json.loads(stereo_source.read_text(encoding="utf-8")))
    reference_count = len(records)
    records = stereo_records + records
    dimensions = {
        field: dict(Counter(record.get(field, "") for record in records).most_common())
        for field in DIMENSIONS
    }
    total_steps = sum(len(record["action_steps"]) for record in records)
    catalog = {
        "schema_version": 2,
        "source_name": "Maniformer",
        "source_url": "https://www.maniformer.net/dataShop",
        "catalog_stage": "mixed",
        "scene_taxonomy": SCENES,
        "collections": {"human_stereo": len(stereo_records), "robot_real": sum(r["dataset_kind"] == "robot_real" for r in records), "robot_sim": sum(r["dataset_kind"] == "robot_sim" for r in records)},
        "reference_count": reference_count,
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
        "source_unavailable_count": max(0, source["total"] - reference_count),
        "stereo_datasets": len(stereo_records),
        "reference_records": reference_count,
        "duplicate_ids": 0,
        "video_links": sum(bool(record.get("video_url")) for record in records),
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
