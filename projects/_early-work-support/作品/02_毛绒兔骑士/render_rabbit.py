import bpy, sys, time, json
from pathlib import Path
root=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'02_毛绒兔骑士.blend'))
scene=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences
pref.compute_device_type='OPTIX';devices=pref.get_devices_for_type('OPTIX')
selected=next(d for d in devices if d.type=='OPTIX' and '3080' in d.name)
for d in pref.devices:d.use=d.id==selected.id and d.type=='OPTIX'
scene.render.engine='CYCLES';scene.cycles.device='GPU'
final='--final' in sys.argv
scene.cycles.samples=1024 if final else 128
scene.cycles.use_denoising=False
scene.cycles.use_adaptive_sampling=True
scene.cycles.adaptive_threshold=.003 if final else .01
scene.cycles.adaptive_min_samples=64 if final else 16
scene['Final settings']='1000 square, Cycles OptiX, max 1024 samples, 0.003 adaptive threshold, denoising disabled to retain individual curls'
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.filepath=str(root/('02_毛绒兔骑士.png' if final else 'preview.png'))
scene.frame_set(1)
if final:bpy.ops.wm.save_as_mainfile(filepath=str(root/'02_毛绒兔骑士.blend'))
started=time.perf_counter();bpy.ops.render.render(write_still=True)
report={'device':selected.name,'backend':selected.type,'resolution':[1000,1000],'samples':scene.cycles.samples,'denoising':scene.cycles.use_denoising,'seconds':round(time.perf_counter()-started,2),'output':scene.render.filepath,'objects':len(scene.objects),'real_hair_systems':sum(len(o.particle_systems) for o in scene.objects),'native_render_fibres':sum(p.settings.count*(1+p.settings.rendered_child_count) for o in scene.objects for p in o.particle_systems),'explicit_curled_fibres':sum(len(o.data.splines) for o in scene.objects if o.type=='CURVE' and 'irregular curled flyaways' in o.name),'curve_objects':sum(o.type=='CURVE' for o in scene.objects)}
(root/('final_report.json' if final else 'preview_report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('RABBIT_RENDER_COMPLETE '+json.dumps(report,ensure_ascii=False),flush=True)
