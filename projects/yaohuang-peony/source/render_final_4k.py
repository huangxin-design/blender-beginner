"""Render approved native 4K frames with atomic files and resumable progress."""
import argparse
import json
import os
from pathlib import Path
import struct
import sys
import time
import bpy

ROOT = Path(__file__).resolve().parent
FRAMES = ROOT/'frames_4k'
FRAMES.mkdir(exist_ok=True)
p = argparse.ArgumentParser()
p.add_argument('--check',action='store_true',help='Render only frame 165 for full-resolution quality inspection.')
a = p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
s = bpy.context.scene
assert (s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage)==(2160,3840,100)
assert (s.frame_start,s.frame_end,s.render.fps)==(1,240,24)
assert s.render.engine=='CYCLES' and s.render.image_settings.color_depth=='16'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
for device in prefs.devices:
    device.use = device.type=='OPTIX'
assert any(d.use for d in prefs.devices)
s.cycles.device = 'GPU'
s.cycles.denoising_use_gpu = True
s.cycles.tile_size = 512
s.render.use_persistent_data = False
s.render.compositor_device = 'CPU'


def valid_frame(path):
    if not path.is_file() or path.stat().st_size < 64:
        return False
    with path.open('rb') as f:
        header = f.read(25)
        f.seek(-12,2)
        ending = f.read(12)
    return (header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',header[16:24])==(2160,3840)
            and header[24]==16 and ending==b'\x00\x00\x00\x00IEND\xaeB`\x82')


ready = {i for i in range(1,241) if valid_frame(FRAMES/f'{i:04d}.png')}
order = [165] if a.check else [1,107,240]+[i for i in range(1,241) if i not in [1,107,240]]
start = time.time()
rendered = 0
for frame in order:
    if frame in ready:
        continue
    s.frame_set(frame)
    temporary = FRAMES/f'_render_{frame:04d}.png'
    destination = FRAMES/f'{frame:04d}.png'
    s.render.filepath = str(temporary)
    before = time.time()
    bpy.ops.render.render(write_still=True)
    assert valid_frame(temporary),str(temporary)
    os.replace(temporary,destination)
    ready.add(frame)
    rendered += 1
    status = {'status':'rendering','completed':len(ready),'total':240,'last_frame':frame,
              'last_frame_seconds':round(time.time()-before,2),'session_seconds':round(time.time()-start,1),
              'session_frames':rendered,'native_resolution':[2160,3840]}
    (ROOT/'progress.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
    with (ROOT/'frame_timings.jsonl').open('a',encoding='utf-8') as log:
        log.write(json.dumps(status)+'\n')
    print('FINAL_4K_PROGRESS',json.dumps(status),flush=True)
print('FINAL_4K_CHECK_COMPLETE' if a.check else 'FINAL_4K_FRAMES_COMPLETE',len(ready),flush=True)
