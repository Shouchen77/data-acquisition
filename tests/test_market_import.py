"""Check public catalog boundaries and the human stereo intake contract."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from import_market import import_stereo_datasets


def sample():
    return {
        "dataset_id": "467", "scene_id": "factory", "subscene": "装配工位",
        "title": "本地验证样例", "description": "仅用于验证接入，不进入正式目录",
        "availability": "available", "episode_count": 3, "duration_seconds": 180,
        "capture": {"width": 1920, "height": 1080, "fps": 30, "imu_hz": 200},
        "previews": {"left": "https://example.com/left.mp4", "right": "https://example.com/right.mp4"},
        "delivery_contents": ["左右目视频", "逐帧时间戳", "IMU"],
        "operator_name": "private", "gps": [30.1, 120.1], "local_path": "/private/session",
        "quality_status": "passed", "certified": True,
    }


class StereoIntakeTests(unittest.TestCase):
    def load(self, dataset):
        return import_stereo_datasets({"schema_version": 1, "datasets": [dataset]})[0]

    def test_namespace_and_private_fields(self):
        record = self.load(sample())
        self.assertEqual(record["catalog_id"], "ec:467")
        self.assertEqual(record["standard_basis"], "V3")
        self.assertEqual(record["quality_status"], "pending")
        for field in ("operator_name", "gps", "local_path", "certified"):
            self.assertNotIn(field, record)

    def test_report_presence_is_not_a_pass_claim(self):
        dataset = sample()
        dataset["qa_report_url"] = "https://example.com/qa.pdf"
        self.assertEqual(self.load(dataset)["quality_status"], "report_available")

    def test_invalid_intake_is_rejected(self):
        changes = [
            {"scene_id": "unknown"}, {"episode_count": 0}, {"episode_count": 1.5},
            {"capture": {"fps": float("nan")}}, {"capture": {"imu_hz": -1}},
            {"previews": {"left": "https://example.com/left.mp4"}},
            {"previews": {"left": "file:///private/left.mp4", "right": "file:///private/right.mp4"}},
            {"qa_report_url": "https://user:password@example.com/qa.pdf"},
            {"task_tags": "string is not a tag list"}, {"capture": []},
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                dataset = copy.deepcopy(sample())
                dataset.update(change)
                self.load(dataset)

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            import_stereo_datasets({"schema_version": 1, "datasets": [sample(), sample()]})

    def test_reference_catalog_keeps_source_and_quality_boundary(self):
        root = Path(__file__).resolve().parents[1]
        catalog = json.loads((root / "data/market_catalog.json").read_text())
        reference = [row for row in catalog["records"] if row["source_id"] == "maniformer"]
        self.assertEqual(len(reference), 466)
        self.assertEqual(sum(row["dataset_kind"] == "robot_real" for row in reference), 411)
        self.assertEqual(sum(row["dataset_kind"] == "robot_sim" for row in reference), 55)
        self.assertTrue(all(row["standard_basis"] is None and row["catalog_stage"] == "reference" for row in reference))
        self.assertEqual(len({row["catalog_id"] for row in catalog["records"]}), catalog["total"])
        self.assertTrue({"factory", "medical", "home"} <= {scene["id"] for scene in catalog["scene_taxonomy"]})


if __name__ == "__main__":
    unittest.main()
