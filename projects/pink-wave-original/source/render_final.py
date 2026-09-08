import bpy
import json
import time
from pathlib import Path

root = Path(__file__).resolve().parent
frames = root / 'frames'
frames.mkdir(exist_ok=True)
scene = bpy.context.scene
assert scene.render.resolution_x == scene.render.resolution_y == 3840
assert scene.frame_start == 1 and scene.frame_end == 200
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.compression = 15
scene.render.use_persistent_data = True
scene.cycles.denoising_use_gpu = True
start = time.perf_counter()
for frame in range(1, 201):
    scene.frame_set(frame)
    scene.render.filepath = str(frames / f'frame_{frame:04d}.png')
    if not Path(scene.render.filepath).exists():
        bpy.ops.render.render(write_still=True)
    if frame == 1 or frame % 10 == 0:
        progress = {'done': frame, 'total': 200, 'elapsed_seconds': round(time.perf_counter() - start, 1)}
        (root / 'render-progress.json').write_text(json.dumps(progress, indent=2), encoding='utf-8')
        print('PROGRESS', json.dumps(progress), flush=True)
scene.frame_set(201)
scene.render.filepath = str(root / 'loop-seam-frame201.png')
bpy.ops.render.render(write_still=True)
print('RENDER COMPLETE', round(time.perf_counter() - start, 1), flush=True)
