# Publication adaptation: relative scene name and configurable installation paths.
"""Bounded, resumable native 4K PNG rendering; final encoding is separate."""
import bpy
import sys
import json
import time
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'renders'/'cache'/'frames'
s=bpy.context.scene
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='OPTIX'
s.cycles.device='GPU'
s.render.compositor_device='CPU'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['draft','73']
mode=args[0]
if mode=='draft':
    s.render.resolution_percentage=25;s.cycles.samples=48
    s.render.image_settings.color_depth='8'
    frames=[int(v) for v in args[1:]] or [1,73,180]
    output=ROOT/'previews'
elif mode=='benchmark':
    s.render.resolution_percentage=100
    frames=[int(args[1]) if len(args)>1 else 73]
    if len(args)>2:s.cycles.samples=int(args[2])
    output=ROOT/'previews'/'benchmark'
elif mode=='raw':
    frames=[int(args[1])]
    output=CACHE.parent/'raw'
    assert (s.render.resolution_x,s.render.resolution_y,s.render.fps,s.frame_start,s.frame_end)==(3072,4096,24,1,360)
    s.render.resolution_percentage=100
    s.cycles.samples=64
    s.cycles.use_denoising=False
    bpy.context.view_layer.cycles.denoising_store_passes=True
    s.render.use_compositing=False
    s.render.image_settings.media_type='MULTI_LAYER_IMAGE'
    s.render.image_settings.file_format='OPEN_EXR_MULTILAYER'
    s.render.image_settings.color_depth='32'
    s.render.image_settings.exr_codec='ZIP'
else:
    frames=range(int(args[1]),int(args[2])+1)
    output=CACHE
output.mkdir(parents=True,exist_ok=True)

def valid(path):
    if not path.is_file() or path.stat().st_size<57:return False
    with path.open('rb') as f:
        head=f.read(25);f.seek(-8,2);tail=f.read()
    return head[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',head[16:24])==(3072,4096) and head[24]==16 and tail==b'IEND\xaeB`\x82'

for frame in frames:
    dest=output/(f'{frame:04d}.exr' if mode=='raw' else f'{frame:04d}_s{s.cycles.samples}.png' if mode=='benchmark' else f'{frame:04d}.png')
    if mode=='final' and valid(dest):continue
    started=time.monotonic();s.frame_set(frame)
    temp=output/f'{frame:04d}.partial{dest.suffix}'
    s.render.filepath=str(temp)
    bpy.ops.render.render(write_still=True)
    temp.replace(dest)
    seconds=time.monotonic()-started
    progress={'mode':mode,'last_frame':frame,'seconds':round(seconds,3),'total_frames':360,'samples':s.cycles.samples,'cache':str(output)}
    (ROOT/'render_progress.json').write_text(json.dumps(progress,indent=2),encoding='utf-8')
    with (ROOT/'render_timings.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(progress)+'\n')
    print('FRAME_DONE',frame,round(seconds,2),flush=True)
