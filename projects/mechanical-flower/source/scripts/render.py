"""Render scene.blend with Blender 5.2; run after Blender's -- separator."""
from pathlib import Path
import argparse
import os
import struct
import sys
import bpy

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--frame', type=int, help='Render only this frame (1–393).')
parser.add_argument('--percentage', type=int, default=100, help='Resolution percentage; 100 is native 4K.')
parser.add_argument('--samples', type=int, default=64)
parser.add_argument('--cpu', action='store_true', help='Force CPU rendering.')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
if args.frame is not None and not 1 <= args.frame <= 393:
    parser.error('--frame must be between 1 and 393')
if not 1 <= args.percentage <= 100 or args.samples < 1:
    parser.error('--percentage must be 1–100 and --samples must be positive')

root = Path(__file__).resolve().parents[1]
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.render.resolution_x, scene.render.resolution_y = 3072, 4096
scene.render.resolution_percentage = args.percentage
scene.render.fps = 24
scene.render.fps_base = 1
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '8'
scene.render.image_settings.compression = 15
scene.render.use_sequencer = False
scene.cycles.samples = args.samples
scene.cycles.adaptive_threshold = .02
scene.cycles.adaptive_min_samples = min(24, args.samples)
scene.cycles.use_denoising = True
scene.cycles.device = 'CPU'
scene.cycles.denoiser = 'OPENIMAGEDENOISE'
if not args.cpu:
    preferences = bpy.context.preferences.addons['cycles'].preferences
    try:
        preferences.compute_device_type = 'OPTIX'
        preferences.get_devices()
        available = [device for device in preferences.devices if device.type == 'OPTIX']
        if available:
            for device in preferences.devices:
                device.use = device.type == 'OPTIX'
            scene.cycles.device = 'GPU'
            scene.cycles.denoiser = 'OPTIX'
    except (TypeError, RuntimeError):
        pass
scene.render.use_persistent_data = True
output = root / ('renders' if args.percentage == 100 else 'preview_renders')
output.mkdir(exist_ok=True)
dimensions = tuple(size * args.percentage // 100 for size in (3072, 4096))

def complete_png(path):
    if not path.is_file() or path.stat().st_size < 36:
        return False
    with path.open('rb') as file:
        header = file.read(24)
        file.seek(-12, 2)
        tail = file.read()
    return (header[:8] == b'\x89PNG\r\n\x1a\n'
            and struct.unpack('>II', header[16:24]) == dimensions
            and tail == b'\x00\x00\x00\x00IEND\xaeB`\x82')

frames = [args.frame] if args.frame is not None else range(1, 394)
for frame in frames:
    target = output / f'{frame:04d}.png'
    if complete_png(target):
        print(f'SKIP {frame:04d}: complete PNG', flush=True)
        continue
    temporary = output / f'_render_{frame:04d}.png'
    scene.frame_set(frame)
    scene.render.filepath = str(temporary)
    bpy.ops.render.render(write_still=True)
    os.replace(temporary, target)
    print(f'RENDERED {frame:04d}', flush=True)
