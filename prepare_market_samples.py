"""Prepare the reviewed stereo sample packages used by the website."""
from collections import Counter, defaultdict
import argparse, csv, hashlib, json, shutil, statistics, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SAMPLES = [
    ("汽修", "auto-repair", "factory", "汽修工位", "第一视角记录车辆维修场景中的工具使用与操作过程。", False),
    ("裁缝", "tailoring", "factory", "缝纫工位", "第一视角记录裁缝工位中的布料整理、工具使用与手部操作。", True),
    ("树莓采摘", "raspberry-picking", "agriculture", "果园", "第一视角记录树莓采摘过程中的近距离观察与手部操作。", False),
    ("橘子采摘", "orange-picking", "agriculture", "果园", "第一视角记录橘子采摘过程中的观察、伸手与摘取。", False),
    ("金桔采摘", "kumquat-picking", "agriculture", "果园", "第一视角记录金桔采摘过程中的目标选择与摘取动作。", False),
    ("电焊", "welding", "factory", "焊接工位", "第一视角记录电焊工位中的工具操作、工件处理与连续动作。", True),
]
LANDMARKS = ["wrist","thumb_cmc","thumb_mcp","thumb_ip","thumb_tip","index_mcp","index_pip","index_dip","index_tip","middle_mcp","middle_pip","middle_dip","middle_tip","ring_mcp","ring_pip","ring_dip","ring_tip","pinky_mcp","pinky_pip","pinky_dip","pinky_tip"]
CONNECTIONS = [[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],[13,17],[0,17],[17,18],[18,19],[19,20]]

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def rows(path):
    with path.open(encoding="utf-8", newline="") as f: return list(csv.DictReader(f))

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def num(row, *keys):
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            try: return float(value)
            except ValueError: pass
    return None

def poster(path, title, subscene):
    from PIL import Image, ImageDraw
    image = Image.new("RGB", (960, 600), "#101114")
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 40, 920, 560), outline="#dfff4f", width=2)
    draw.text((82, 92), "EYECATCHER / EGO DATA", fill="#dfff4f")
    draw.text((82, 230), title, fill="#ffffff")
    draw.text((82, 330), subscene + " · 双目采集样例", fill="#a9aaa5")
    draw.text((82, 500), "REAL PERSON · STEREO CAPTURE", fill="#ff7048")
    image.save(path, quality=88, optimize=True)

def handpose_info(dest, relative):
    eyes, stats = {}, {}
    for eye in ("left", "right"):
        path = dest / "handpose" / ("top_" + eye + ".json")
        if not path.is_file(): continue
        value = json.loads(path.read_text(encoding="utf-8")); frames = value.get("frames") or []
        raw = value.get("stats") or {}; count = raw.get("frames_with_hands")
        if count is None: count = sum(bool(frame.get("hands")) for frame in frames)
        stats[eye] = {"frames": len(frames), "frames_with_hands": count, "hand_ratio": round(count / len(frames), 4) if frames else 0}
        eyes[eye] = str(relative / "handpose" / ("top_" + eye + ".json"))
    if not eyes: return {"available": False, "notes": "本样例包尚未提供手部关键点文件。"}
    return {"available": True, "model": "mediapipe_hand_landmarker", "landmarks": LANDMARKS, "connections": CONNECTIONS, "eyes": eyes, "stats": stats, "notes": "3D 位置使用关键点 world 坐标；不是相机坐标系中的绝对手位姿。"}

def source_and_mapping(title, source_dir, external):
    source = Path("/Users/sochy/Downloads") / title if external else source_dir / title
    if title == "电焊": return source, {"left":"headcam.mp4", "right":"headcam_view_b.mp4", "left_ts":"headcam_camera.csv", "right_ts":"headcam_view_b_camera.csv"}
    return source, {"left":"top_left.mp4", "right":"top_right.mp4", "left_ts":"top_left_camera.csv", "right_ts":"top_right_camera.csv"}

def prepare(title, slug, scene, subscene, description, external, source_dir):
    src, mapping = source_and_mapping(title, source_dir, external)
    if not src.is_dir(): raise FileNotFoundError(src)
    relative = Path("media/stereo/20261124") / slug; dest = ROOT / relative
    if dest.exists(): shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for folder in ("calibration", "imu", "videos", "timestamps", "handpose"):
        (dest / folder).mkdir(parents=True, exist_ok=True)
    for folder in ("calibration", "imu"):
        for path in (src / folder).glob("*"):
            if path.is_file(): shutil.copy2(path, dest / folder / path.name)
    shutil.copy2(src / "videos" / mapping["left"], dest / "videos/top_left.mp4")
    shutil.copy2(src / "videos" / mapping["right"], dest / "videos/top_right.mp4")
    shutil.copy2(src / "timestamps" / mapping["left_ts"], dest / "timestamps/top_left_camera.csv")
    shutil.copy2(src / "timestamps" / mapping["right_ts"], dest / "timestamps/top_right_camera.csv")
    legacy_preview = ROOT / "media/stereo/20261106" / slug / "preview"
    if legacy_preview.is_dir():
        for path in legacy_preview.glob("*.mp4"):
            (dest / "preview").mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest / "preview" / path.name)
    if (src / "handpose").is_dir():
        for eye in ("left", "right"):
            path = src / "handpose" / ("top_" + eye + ".json")
            if path.is_file(): shutil.copy2(path, dest / "handpose" / path.name)
    left, right, imu = rows(dest / "timestamps/top_left_camera.csv"), rows(dest / "timestamps/top_right_camera.csv"), rows(dest / "imu/imu.csv")
    lt = [num(row, "device_timestamp_unwrapped_us", "exposure_end_device_us", "driver_timestamp_us") for row in left]
    it = [num(row, "device_timestamp_unwrapped_us", "exposure_end_device_us", "driver_timestamp_us") for row in imu]
    lt, it = [x for x in lt if x is not None], [x for x in it if x is not None]
    vd = [b-a for a,b in zip(lt, lt[1:]) if b > a]; md = [b-a for a,b in zip(it, it[1:]) if b > a]
    fps = 1_000_000 / statistics.median(vd) if vd else None; imu_hz = 1_000_000 / statistics.median(md) if md else None
    duration = ((lt[-1]-lt[0]) + statistics.median(vd)) / 1_000_000 if vd else None
    for row, value in zip(left, lt): row.setdefault("device_timestamp_unwrapped_us", str(int(value)))
    for row in right:
        value = num(row, "device_timestamp_unwrapped_us", "exposure_end_device_us", "driver_timestamp_us")
        if value is not None: row.setdefault("device_timestamp_unwrapped_us", str(int(value)))
    for row, value in zip(imu, it): row.setdefault("device_timestamp_unwrapped_us", str(int(value)))
    intrinsics = json.loads((dest / "calibration/intrinsics.yaml").read_text(encoding="utf-8")); extrinsics = json.loads((dest / "calibration/extrinsics.yaml").read_text(encoding="utf-8"))
    info_path = dest / "imu/imu_info.yaml"; imu_info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.exists() else {}
    keys = ["gyro_x_counts","gyro_y_counts","gyro_z_counts","accel_x_counts","accel_y_counts","accel_z_counts"]; plot=[]; step=max(1,len(imu)//180)
    for index in range(0,len(imu),step):
        row=imu[index]; item={"t":round((num(row,"device_timestamp_unwrapped_us")-it[0])/1_000_000,4) if it else 0}
        for key in keys:
            try: item[key]=int(float(row.get(key,0) or 0))
            except ValueError: item[key]=0
        plot.append(item)
    if not (dest / "poster.jpg").exists(): poster(dest / "poster.jpg", title, subscene)
    handpose = handpose_info(dest, relative); files=[]
    for path in sorted(dest.rglob("*")):
        if path.is_file() and path.name not in ("summary.json","data-files.zip","poster.jpg"):
            files.append({"path":str(path.relative_to(dest)),"url":str(relative/path.relative_to(dest)),"bytes":path.stat().st_size,"sha256":sha(path)})
    with zipfile.ZipFile(dest / "data-files.zip","w",zipfile.ZIP_DEFLATED) as archive:
        for entry in files:
            if not entry["path"].endswith(".mp4"): archive.write(dest/entry["path"],entry["path"])
    summary={"dataset_id":slug,"title":title,"frames":{"left":len(left),"right":len(right)},"imu_samples":len(imu),"duration_seconds":round(duration,3) if duration else None,"fps":round(fps,3) if fps else None,"imu_hz":round(imu_hz,3) if imu_hz else None,"paired_timestamp_max_delta_us":max((abs(float(a.get("device_timestamp_unwrapped_us",0))-float(b.get("device_timestamp_unwrapped_us",0))) for a,b in zip(left,right)),default=0),"timestamp_monotonic":all(b>a for a,b in zip(lt,lt[1:])),"imu_monotonic":all(b>a for a,b in zip(it,it[1:])),"timestamp_status":"设备曝光计数；主机 Unix 时间为估计值，UTC 对齐待验证","imu_status":"原始 counts；SI 单位与坐标轴待验证","calibration_status":"候选标定，尚未验收","intrinsics":intrinsics,"extrinsics":extrinsics,"imu_info":imu_info,"tables":{"timestamps":{"headers":list(left[0]),"rows":left[:8]},"imu":{"headers":list(imu[0]),"rows":imu[:8]}},"imu_plot":plot,"handpose":handpose,"files":files,"data_archive":str(relative/"data-files.zip")}
    write_json(dest/"summary.json",summary)
    preview_left=str(relative/"preview/top_left.mp4") if (dest/"preview/top_left.mp4").exists() else str(relative/"videos/top_left.mp4"); preview_right=str(relative/"preview/top_right.mp4") if (dest/"preview/top_right.mp4").exists() else str(relative/"videos/top_right.mp4")
    return {"dataset_id":slug,"title":title,"description":description,"scene_id":scene,"subscene":subscene,"availability":"available","episode_count":1,"duration_seconds":summary["duration_seconds"],"capture":{"width":1920,"height":1200,"fps":summary["fps"],"imu_hz":summary["imu_hz"]},"previews":{"left":preview_left,"right":preview_right},"poster":str(relative/"poster.jpg"),"sample_data_url":str(relative/"summary.json"),"quality_status":"engineering_sample","task_tags":["双目","第一视角","IMU",title],"delivery_contents":["左右目原始视频（HEVC）","逐帧时间戳 CSV","IMU 原始 counts CSV","相机内外参候选文件","手部关键点 JSON（如有）"],"sample_stats":{"frames_per_eye":len(left),"imu_samples":len(imu),"handpose_available":handpose["available"]}}

def curate():
    path=ROOT/"data/maniformer_data_market.json"; source=json.loads(path.read_text(encoding="utf-8")); real=[r for r in source["records"] if r["data_type"]!="仿真"]
    if len(real)==60: return
    pools=defaultdict(list); chosen=[]; features=Counter()
    for record in real: pools[record["primary_scene"]].append(record)
    for scene in sorted(pools):
        candidates=pools[scene][:]
        for _ in range(min(12,len(candidates))):
            def score(r):
                keys=[("sub",r["primary_scene"],r["secondary_scene"]),("arm",r["arm_type"]),("hand",r["hand_type"]),("robot",r["robot_body_type"]),("tactile",r["tactile_info"]),("task",r["task_name"])]
                return (sum(1/(1+features[x]) for x in keys)+(1 if r["tactile_info"]=="有触觉" else 0),r["id"])
            record=max(candidates,key=score); candidates.remove(record); chosen.append(record)
            for key in [("sub",record["primary_scene"],record["secondary_scene"]),("arm",record["arm_type"]),("hand",record["hand_type"]),("robot",record["robot_body_type"]),("tactile",record["tactile_info"]),("task",record["task_name"])]: features[key]+=1
    keep={r["id"] for r in chosen}; source["records"]=[r for r in source["records"] if r["data_type"]=="仿真" or r["id"] in keep]; source["total"]=len(source["records"]); write_json(path,source)
    csv_path=ROOT/"data/maniformer_data_market.csv"
    with csv_path.open(encoding="utf-8-sig",newline="") as f: reader=csv.DictReader(f); fields=reader.fieldnames; old=list(reader)
    with csv_path.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader(); writer.writerows(row for row in old if int(row["id"]) in keep or next((r for r in source["records"] if r["id"]==int(row["id"])),None) and next(r for r in source["records"] if r["id"]==int(row["id"]))["data_type"]=="仿真")

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("source_dir",type=Path); parser.add_argument("--ffmpeg",default=""); args=parser.parse_args(); curate()
    datasets=[prepare(*sample,args.source_dir) for sample in SAMPLES]; write_json(ROOT/"data/eyecatcher_stereo_datasets.json",{"schema_version":1,"datasets":datasets})
    for item in datasets: print(item["title"],item["capture"],item["sample_stats"])

if __name__=="__main__": main()
