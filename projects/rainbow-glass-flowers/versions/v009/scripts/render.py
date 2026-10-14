"""Render checks or every frame of the final 15-second film, resuming safely."""
import os
import sys
import time
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
cache = ROOT / 'renders/optix_cache'
cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('OPTIX_CACHE_PATH', str(cache))
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
for device in prefs.devices:
    device.use = device.type == 'OPTIX'
s = bpy.context.scene
args = sys.argv[sys.argv.index('--') + 1:]
mode = args[0]
frames = range(1, 361) if mode == 'film' else [int(f) for f in args[1:]]
s.render.resolution_x, s.render.resolution_y = (720, 960) if mode in ('film', 'repair') else (540, 720)
if mode == 'still':
    s.render.resolution_x, s.render.resolution_y = 1080, 1440
s.render.resolution_percentage = 100
s.cycles.samples = 64 if mode == 'still' else 32
s.cycles.adaptive_threshold = .05
s.cycles.adaptive_min_samples = 8
s.render.use_persistent_data = True
s.cycles.use_auto_tile = True
s.cycles.tile_size = 1024
s.cycles.denoising_use_gpu = False
out = ROOT / 'renders' / {'film': 'frames_final', 'repair': 'frames_final', 'still': 'full_checks', 'check': 'checks_final'}[mode]
out.mkdir(parents=True, exist_ok=True)
start = time.monotonic()
for frame in frames:
    if (ROOT / 'renders/STOP_RENDER').exists():
        raise SystemExit('Paused for scene revision')
    path = out / f'{frame:04d}.png'
    if mode == 'film' and path.exists():
        continue
    s.frame_set(frame)
    s.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print(f'FRAME_DONE {frame} elapsed={time.monotonic()-start:.2f}s', flush=True)
