"""Render a saved V13/V14 scene without changing the archived .blend."""
import argparse
import sys
import time
from pathlib import Path

import bpy

CASE = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--start', type=int, default=1)
parser.add_argument('--end', type=int, default=900)
parser.add_argument('--device', choices=['CPU', 'OPTIX'], default='CPU')
parser.add_argument('--scale', type=int, default=100)
parser.add_argument('--samples', type=int, default=128)
parser.add_argument('--output', type=Path)
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
if not 1 <= args.start <= args.end <= 900 or not 1 <= args.scale <= 100 or args.samples < 1:
    parser.error('Require 1 <= start <= end <= 900, scale 1..100, samples >= 1.')

version = Path(bpy.data.filepath).parent.name
folder = args.output or CASE / 'output' / version / 'frames'
folder.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.cycles.device = args.device if args.device == 'CPU' else 'GPU'
scene.cycles.denoising_use_gpu = args.device != 'CPU'
if args.device == 'OPTIX':
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for device in prefs.devices:
        device.use = device.type == 'OPTIX'
    if not any(device.use for device in prefs.devices):
        raise RuntimeError('No OptiX device available; use --device CPU.')
scene.render.threads_mode, scene.render.threads = 'FIXED', 2
scene.render.resolution_percentage = args.scale
scene.cycles.samples = args.samples
scene.render.image_settings.file_format = 'PNG'

# These zero-amplitude petals never open. Remove runtime evaluation overhead;
# the original shape keys and all other animation remain in the saved file.
for obj in scene.objects:
    if 'Bloom amplitude' in obj and obj['Bloom amplitude'] == 0:
        obj.data.shape_keys.animation_data_clear()
        for key in obj.data.shape_keys.key_blocks[1:]:
            key.value = 0
fuzz_cached = False
started = time.monotonic()
for frame in range(args.start, args.end + 1):
    scene.frame_set(frame)
    if frame >= scene['V13 fuzz fully grown frame'] and not fuzz_cached:
        for obj in scene.objects:
            if obj.name.startswith('Stem fuzz | band '):
                obj.data.animation_data_clear()
                obj.data.bevel_factor_end = 1
        fuzz_cached = True
    scene.render.filepath = str(folder / f'{frame:04d}.png')
    bpy.ops.render.render(write_still=True)
    print(f'FRAME_DONE {frame} elapsed={time.monotonic()-started:.1f}s', flush=True)
