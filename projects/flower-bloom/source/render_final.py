"""Render the verified 4K scene at its saved quality; resume only complete PNGs."""
import bpy
import json
import time
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parent
scene=bpy.context.scene
assert (scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage)==(2160,3840,100)
assert (scene.frame_start,scene.frame_end,scene.render.fps)==(1,240,30)
assert scene.cycles.samples==64
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX'
prefs.get_devices()
for d in prefs.devices:
    d.use=d.type=='OPTIX'
scene.cycles.device='GPU'
scene.cycles.denoising_use_gpu=True
scene.render.image_settings.file_format='PNG'
scene.render.use_persistent_data=True
folder=ROOT/'frames'
folder.mkdir(exist_ok=True)
start=time.perf_counter()
rendered=0
for frame in range(1,241):
    scene.frame_set(frame)
    path=folder/f'frame_{frame:04}.png'
    complete=False
    if path.exists():
        with path.open('rb') as f:
            header=f.read(24)
            f.seek(-12,2)
            ending=f.read(12)
        complete=(header[:8]==b'\x89PNG\r\n\x1a\n'
                  and struct.unpack('>II',header[16:24])==(2160,3840)
                  and ending==b'\x00\x00\x00\x00IEND\xaeB`\x82')
    if not complete:
        scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        rendered+=1
    elapsed=time.perf_counter()-start
    progress={'done':frame,'total':240,'rendered_this_run':rendered,'elapsed_seconds':round(elapsed,1),
              'mean_seconds_per_rendered_frame':round(elapsed/max(rendered,1),2),
              'resolution':[2160,3840],'samples':64,'backend':'OPTIX'}
    (ROOT/'render-progress.json').write_text(json.dumps(progress,indent=2),encoding='utf-8')
    if frame==1 or frame%10==0:
        print('4K PROGRESS',json.dumps(progress),flush=True)
print('4K RENDER COMPLETE',round(time.perf_counter()-start,1),flush=True)
