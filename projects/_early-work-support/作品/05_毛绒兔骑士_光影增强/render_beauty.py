import bpy, sys, time, json
from pathlib import Path
root=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'05_毛绒兔骑士_光影增强.blend'))
scene=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX'
devices=pref.get_devices_for_type('OPTIX');selected=next(d for d in devices if d.type=='OPTIX' and '3080' in d.name)
for d in pref.devices:d.use=d.id==selected.id and d.type=='OPTIX'
scene.cycles.device='GPU';scene.render.use_compositing=False
preview='--preview' in sys.argv
scene.cycles.samples=64 if preview else 1024
scene.cycles.adaptive_threshold=.015 if preview else .003
scene.cycles.adaptive_min_samples=16 if preview else 64
scene.cycles.use_denoising=False
scene.render.resolution_x=810 if preview else 1000;scene.render.resolution_y=scene.render.resolution_x;scene.render.resolution_percentage=100
exr=root/('preview_linear.exr' if preview else 'beauty_linear.exr')
png=root/('preview_agx.png' if preview else 'beauty_agx.png')
settings=scene.render.image_settings;settings.file_format='OPEN_EXR';settings.color_mode='RGBA';settings.color_depth='16';settings.exr_codec='ZIP';scene.render.filepath=str(exr)
started=time.perf_counter();bpy.ops.render.render(write_still=True)
settings.file_format='PNG';settings.color_mode='RGB';settings.color_depth='8'
bpy.data.images['Render Result'].save_render(filepath=str(png),scene=scene)
settings.file_format='OPEN_EXR';settings.color_mode='RGBA';settings.color_depth='16';settings.exr_codec='ZIP'
if not preview:bpy.ops.wm.save_as_mainfile(filepath=str(root/'05_毛绒兔骑士_光影增强.blend'))
report={'status':'passed','device':selected.name,'backend':selected.type,'seconds':round(time.perf_counter()-started,2),'resolution':[scene.render.resolution_x,scene.render.resolution_y],'samples':scene.cycles.samples,'adaptive_threshold':scene.cycles.adaptive_threshold,'compositing':scene.render.use_compositing,'linear_rgba_half_exr':str(exr),'png_agx_neutral':str(png),'exr_bytes':exr.stat().st_size}
(root/('preview_report.json' if preview else 'beauty_report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('BEAUTY_RENDER_COMPLETE '+json.dumps(report,ensure_ascii=False),flush=True)
