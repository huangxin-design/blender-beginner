"""Render the four approved portraits without saving scene or preference changes.

Open scene.blend in Blender background mode and pass arguments after --:
    --output-dir /absolute/new/output-directory [--preview] [--device OPTIX]
CPU is the portable default. OPTIX requires a compatible NVIDIA device.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path, required=True)
parser.add_argument('--preview', action='store_true', help='240 x 320, 8 samples; a quick readability check.')
parser.add_argument('--device', choices=['CPU', 'OPTIX'], default='CPU')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
output_dir = args.output_dir.expanduser()
if not output_dir.is_absolute() or output_dir.exists() or output_dir.is_symlink():
    parser.error('--output-dir must be an absolute, previously nonexistent directory.')
output_dir = output_dir.resolve()

ROOT = Path(__file__).resolve().parent
scene = bpy.context.scene
rows = json.loads((ROOT / 'atlas-orientations.json').read_text(encoding='utf-8'))
if [row['brand'] for row in rows] != ['openai', 'claude', 'deepseek', 'gemini']:
    raise RuntimeError('Use the included four-brand orientation data.')
camera = scene.camera
if not camera or scene.render.engine != 'CYCLES':
    raise RuntimeError('Open the included scene.blend before running this script.')
if args.device == 'OPTIX':
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    if not any(device.type == 'OPTIX' for device in prefs.devices):
        raise RuntimeError('No OPTIX device found. Re-run with --device CPU.')
    for device in prefs.devices:
        device.use = device.type == 'OPTIX'
scene.cycles.device = 'CPU' if args.device == 'CPU' else 'GPU'
scene.cycles.samples = 8 if args.preview else 128
scene.cycles.adaptive_threshold = .018
scene.cycles.use_denoising = True
scene.cycles.denoising_use_gpu = args.device == 'OPTIX'
scene.render.resolution_x = 240 if args.preview else 960
scene.render.resolution_y = 320 if args.preview else 1280
scene.render.resolution_percentage = 100
scene.render.use_motion_blur = False
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '8'
original_camera_location = camera.location.copy()
camera.data.sensor_fit = 'HORIZONTAL'
camera.data.lens = 85
for name in ['01 - 121 animated pink pins', '02 - Ground sockets', '05 - HUANGHUAYU signature']:
    bpy.data.collections[name].hide_render = True
balls = list(bpy.data.collections['03 - Rolling spheres'].objects)
output_dir.mkdir(parents=True, exist_ok=False)
outputs = []
for row in rows:
    scene.frame_set(row['frame'])
    ball = bpy.data.objects[row['object']]
    for other in balls:
        other.hide_render = other != ball
    target = ball.location + Vector((0, 0, -.012))
    direction = (original_camera_location - ball.location).normalized()
    camera.location = target + direction * 2.8
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    output = output_dir / f'{row["brand"]}_{scene.render.resolution_x}x{scene.render.resolution_y}.png'
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f'Render did not produce {output.name}.')
    outputs.append({'brand': row['brand'], 'frame': row['frame'], 'file': output.name})
    print('PORTRAIT COMPLETE', row['brand'], flush=True)
(output_dir / 'render-settings.json').write_text(json.dumps({
    'source_blend': Path(bpy.data.filepath).name,
    'resolution': [scene.render.resolution_x, scene.render.resolution_y],
    'format': 'PNG RGB 8-bit',
    'background': 'Original pink studio floor and lighting, opaque',
    'samples': scene.cycles.samples,
    'device': args.device,
    'preview': args.preview,
    'scene_saved': False,
    'preferences_saved': False,
    'outputs': outputs,
}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
