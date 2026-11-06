"""Prepare the user-provided stereo samples and a curated robot reference catalog."""
from pathlib import Path
from collections import Counter, defaultdict
import csv, hashlib, io, json, shutil, statistics, subprocess, zipfile

ROOT = Path(__file__).resolve().parent
SAMPLES = [('橘子采摘','orange-picking','agriculture','果园','第一视角记录橘子采摘过程中的观察、伸手与摘取。'),('树莓采摘','raspberry-picking','agriculture','果园','第一视角记录树莓采摘过程中的近距离观察与手部操作。'),('金桔采摘','kumquat-picking','agriculture','果园','第一视角记录金桔采摘过程中的目标选择与摘取动作。'),('汽修','auto-repair','factory','汽修工位','第一视角记录车辆维修场景中的工具使用与操作过程。')]
def write_json(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):
    with path.open() as f:return list(csv.DictReader(f))
def curate():
    p=ROOT/'data/maniformer_data_market.json'; source=json.loads(p.read_text())
    real=[r for r in source['records'] if r['data_type']!='仿真']
    if len(real)==60:return
    pools=defaultdict(list)
    for r in real:pools[r['primary_scene']].append(r)
    chosen=[]; features=Counter()
    for scene in sorted(pools):
        candidates=pools[scene][:]
        for _ in range(12):
            def score(r):
                fs=[('sub',r['primary_scene'],r['secondary_scene']),('arm',r['arm_type']),('hand',r['hand_type']),('robot',r['robot_body_type']),('tactile',r['tactile_info']),('task',r['task_name'])]
                return (sum(1/(1+features[f]) for f in fs)+(1 if r['tactile_info']=='有触觉' else 0),r['id'])
            r=max(candidates,key=score);candidates.remove(r);chosen.append(r)
            for f in [('sub',r['primary_scene'],r['secondary_scene']),('arm',r['arm_type']),('hand',r['hand_type']),('robot',r['robot_body_type']),('tactile',r['tactile_info']),('task',r['task_name'])]:features[f]+=1
    keep={r['id'] for r in chosen}; retained=[r for r in source['records'] if r['data_type']=='仿真' or r['id'] in keep]
    source['records']=retained;source['total']=len(retained)
    write_json(p,source)
    cp=ROOT/'data/maniformer_data_market.csv'
    with cp.open(encoding='utf-8-sig',newline='') as f: reader=csv.DictReader(f);fields=reader.fieldnames;old=list(reader)
    with cp.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(r for r in old if int(r['id']) in {x['id'] for x in retained})
    sp=ROOT/'data/maniformer_data_market_summary.json'; summary=json.loads(sp.read_text())
    summary.update(records=len(retained),api_total=len(retained),dimensions={k:dict(Counter(str(r.get(k,'')).strip() for r in retained).most_common()) for k in summary['dimensions']},action_step_count=sum(len(r.get('action_steps_parsed') or json.loads(r['action_steps'])) for r in retained))
    write_json(sp,summary)
    write_json(ROOT/'data/robot_curation.json',{'retained_real':60,'removed_real':len(real)-60,'retained_sim':55,'strategy':'每个已有应用场景保留12条，优先覆盖不同细分场景、臂型、手型、机器人型号与触觉配置。','retained_ids':sorted(keep)})

def prepare(source_dir, ffmpeg):
    datasets=[]
    for title,slug,scene,subscene,description in SAMPLES:
        src=source_dir/title; relative=Path('media/stereo/20261106')/slug; dest=ROOT/relative
        for p in src.rglob('*'):
            if p.is_file() and p.suffix in ('.mp4','.csv','.yaml') and not p.name.startswith('.'):
                out=dest/p.relative_to(src);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
        subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-y','-ss','3','-i',str(src/'preview/top_left.mp4'),'-frames:v','1','-vf','scale=960:-2','-q:v','3',str(dest/'poster.jpg')],check=True)
        left=rows(dest/'timestamps/top_left_camera.csv');right=rows(dest/'timestamps/top_right_camera.csv');imu=rows(dest/'imu/imu.csv')
        intr=json.loads((dest/'calibration/intrinsics.yaml').read_text());extr=json.loads((dest/'calibration/extrinsics.yaml').read_text());info=json.loads((dest/'imu/imu_info.yaml').read_text())
        delta=[(float(b['device_timestamp_unwrapped_us'])-float(a['device_timestamp_unwrapped_us']))/1e6 for a,b in zip(left,left[1:])]
        fps=1/statistics.median(delta);span=(float(left[-1]['device_timestamp_unwrapped_us'])-float(left[0]['device_timestamp_unwrapped_us']))/1e6
        imu_delta=[(float(b['device_timestamp_unwrapped_us'])-float(a['device_timestamp_unwrapped_us']))/1e6 for a,b in zip(imu,imu[1:])]
        imu_hz=1/statistics.median(imu_delta)
        keys=['gyro_x_counts','gyro_y_counts','gyro_z_counts','accel_x_counts','accel_y_counts','accel_z_counts']
        plot=[]
        for i in range(0,len(imu),max(1,len(imu)//180)):
            r=imu[i];plot.append({'t':round((float(r['device_timestamp_unwrapped_us'])-float(imu[0]['device_timestamp_unwrapped_us']))/1e6,4),**{k:int(r[k]) for k in keys}})
        files=[]
        for p in sorted(dest.rglob('*')):
            if p.is_file() and p.name not in ('summary.json','data-files.zip','poster.jpg'):
                files.append({'path':str(p.relative_to(dest)),'url':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)})
        with zipfile.ZipFile(dest/'data-files.zip','w',zipfile.ZIP_DEFLATED) as z:
            for f in files:
                if not f['path'].endswith('.mp4'):z.write(dest/f['path'],f['path'])
        summary={'dataset_id':slug,'title':title,'frames':{'left':len(left),'right':len(right)},'imu_samples':len(imu),'duration_seconds':round(span+statistics.median(delta),3),'fps':round(fps,3),'imu_hz':round(imu_hz,3),'paired_timestamp_max_delta_us':max(abs(float(a['device_timestamp_unwrapped_us'])-float(b['device_timestamp_unwrapped_us'])) for a,b in zip(left,right)),'timestamp_monotonic':all(d>0 for d in delta),'imu_monotonic':all(d>0 for d in imu_delta),'timestamp_status':'设备时钟；主机 Unix 时间为估计值，UTC 对齐待验证','imu_status':'原始 counts；SI 单位列为空，量程与坐标轴待验证','calibration_status':'候选标定，尚未验收','intrinsics':intr,'extrinsics':extr,'imu_info':info,'tables':{'timestamps':{'headers':list(left[0]),'rows':left[:8]},'imu':{'headers':list(imu[0]),'rows':imu[:8]}},'imu_plot':plot,'files':files,'data_archive':str(relative/'data-files.zip')}
        write_json(dest/'summary.json',summary)
        datasets.append({'dataset_id':slug,'title':title,'description':description,'scene_id':scene,'subscene':subscene,'availability':'available','episode_count':1,'duration_seconds':summary['duration_seconds'],'capture':{'width':1920,'height':1200,'fps':summary['fps'],'imu_hz':summary['imu_hz']},'previews':{eye:str(relative/f'preview/top_{eye}.mp4') for eye in ['left','right']},'poster':str(relative/'poster.jpg'),'sample_data_url':str(relative/'summary.json'),'quality_status':'engineering_sample','task_tags':['双目','第一视角','IMU',title],'delivery_contents':['左右目原始视频（HEVC）','左右目预览视频（H.264）','逐帧时间戳 CSV','IMU 原始 counts CSV','相机内外参候选文件','IMU 配置信息'],'sample_stats':{'frames_per_eye':len(left),'imu_samples':len(imu)}})
        print(title,summary['frames'],summary['imu_samples'],summary['duration_seconds'],summary['fps'],summary['imu_hz'])
    write_json(ROOT/'data/eyecatcher_stereo_datasets.json',{'schema_version':1,'datasets':datasets})

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('source_dir',type=Path);p.add_argument('--ffmpeg',required=True);a=p.parse_args()
    curate();prepare(a.source_dir,a.ffmpeg)
