"""Render all 900 native frames; resume only complete existing PNG files."""
import bpy,os,json,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parents[1]
os.environ['OPTIX_CACHE_PATH']=str(WORK/'setup/cache/optix')
out=WORK/'渲染/09_紫色悬浮几何动画/frames';out.mkdir(parents=True,exist_ok=True)
files=json.loads((ROOT/'assembly_build_report.json').read_text(encoding='utf8'))['source_projects']
start=time.time();completed=0;times=[]
profile=json.loads((ROOT/'render_profile.json').read_text(encoding='utf8'))
for index,path in enumerate(files):
    bpy.ops.wm.open_mainfile(filepath=path)
    s=bpy.context.scene
    p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
    for d in p.devices:d.use=d.type=='OPTIX'
    s.cycles.device='GPU';s.cycles.samples=profile['samples']
    s.cycles.denoiser=profile['denoiser'];s.cycles.denoising_use_gpu=profile['denoising_use_gpu']
    s.cycles.adaptive_threshold=profile['adaptive_threshold'];s.cycles.adaptive_min_samples=profile['min_samples']
    s.render.use_persistent_data=True;s.render.image_settings.compression=15
    for frame in range(1,181):
        global_frame=index*180+frame;target=out/f'frame_{global_frame:04d}.png'
        if target.is_file() and target.stat().st_size>20000:
            completed+=1;continue
        s.frame_set(frame);s.render.filepath=str(target)
        t=time.time();bpy.ops.render.render(write_still=True);times.append(time.time()-t);completed+=1
        report={'complete':completed==900,'completed_frames':completed,'total_frames':900,
                'palette':index,'local_frame':frame,'last_frame':str(target),'elapsed_seconds':time.time()-start,
                'recent_seconds_per_frame':sum(times[-20:])/len(times[-20:]),'profile':profile}
        tmp=ROOT/'render_progress.tmp';tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');tmp.replace(ROOT/'render_progress.json')
        if frame%30==0:print('RENDER_PROGRESS',json.dumps(report,ensure_ascii=False),flush=True)
print('ALL_900_FRAMES_COMPLETE',time.time()-start,flush=True)
