"""Render a range from an archived scene with Blender 5.2.1; never modify the archive."""
import argparse
import json
from pathlib import Path
import sys
import time

import bpy

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--version', choices=('v004', 'v005'), required=True)
parser.add_argument('--start', type=int, default=1)
parser.add_argument('--end', type=int, default=450)
parser.add_argument('--device', choices=('CPU', 'OPTIX'), default='CPU')
parser.add_argument('--samples', type=int)
parser.add_argument('--scale', type=float, default=1, help='Resolution multiplier, e.g. 0.25 for a small preview')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
if not 1 <= args.start <= args.end <= 450:
    parser.error('Frame range must be within 1–450.')
if not 0 < args.scale <= 1 or (args.samples is not None and args.samples < 1):
    parser.error('Use 0 < scale <= 1 and positive samples.')
source = ROOT / 'versions' / args.version / 'scene.blend'
if not source.is_file():
    raise FileNotFoundError(f'Download the Release scene into {source}.')
bpy.ops.wm.open_mainfile(filepath=str(source))
scene = bpy.context.scene
width, height, default_samples = (720, 960, 128) if args.version == 'v004' else (2880, 3840, 64)
samples = args.samples or default_samples
scene.render.engine = 'CYCLES' if args.version == 'v004' else 'BLENDER_EEVEE'
scene.render.resolution_x = max(2, round(width * args.scale / 2) * 2)
scene.render.resolution_y = max(2, round(height * args.scale / 2) * 2)
scene.render.resolution_percentage = 100
scene.render.use_persistent_data = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '8'
scene.render.image_settings.compression = 15
if args.version == 'v004':
    scene.cycles.samples = samples
    scene.cycles.adaptive_min_samples = min(128, samples)
    scene.cycles.device = 'CPU'
    scene.render.compositor_device = 'CPU'
    if args.device == 'OPTIX':
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        devices = [device for device in prefs.devices if device.type == 'OPTIX']
        if not devices:
            raise RuntimeError('No OptiX device found; use --device CPU on this machine.')
        for device in prefs.devices:
            device.use = device.type == 'OPTIX'
        scene.cycles.device = 'GPU'
        scene.render.compositor_device = 'GPU'
else:
    # EEVEE uses the graphics device; the Cycles CPU/OPTIX option does not apply.
    scene.eevee.taa_render_samples = samples

out = ROOT / 'output' / args.version
frames = out / 'frames'
frames.mkdir(parents=True, exist_ok=True)
records = []
for frame in range(args.start, args.end + 1):
    scene.frame_set(frame)
    scene.render.filepath = str(frames / f'frame_{frame:04d}.png')
    started = time.monotonic()
    bpy.ops.render.render(write_still=True)
    record = {'frame': frame, 'seconds': round(time.monotonic() - started, 2), 'camera': scene.camera.name}
    records.append(record)
    (out / f'render_{args.start:04d}_{args.end:04d}.json').write_text(
        json.dumps({'resolution': [scene.render.resolution_x, scene.render.resolution_y],
                    'samples': samples, 'engine': scene.render.engine,
                    'persistent_data': False, 'frames': records}, indent=2), encoding='utf-8')
    print('FRAME_COMPLETE', record, flush=True)
