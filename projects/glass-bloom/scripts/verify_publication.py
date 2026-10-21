"""Reopen both published projects, check their dependencies, and optionally render a small sample."""
import hashlib
import json
import re
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
SMOKE = '--render' in sys.argv
report = {'passed': True, 'versions': {}, 'scope': 'Reopen, packed dependencies, four animation samples; no new collision test.'}
for version in ('v008', 'v009'):
    source = ROOT / 'versions' / version / 'scene.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    flower = next(o for o in scene.objects if o.name.startswith('FLOWER'))
    petals = [o for o in scene.objects if o.type == 'MESH' and o.name.startswith(('OUTER ', 'INNER ', 'SEPAL '))]
    images = [im for im in bpy.data.images if im.source == 'FILE']
    missing = [im.name for im in images if not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
    assert not missing and not bpy.data.libraries
    assert len(petals) == 13
    assert (scene.render.resolution_x, scene.render.resolution_y, scene.render.fps, scene.frame_end) == (3072, 4096, 24, 360)
    samples = []
    for frame in (1, 73, 180, 360):
        scene.frame_set(frame)
        assert max(abs(float(x) - 1) for x in flower.scale) < 1e-6
        samples.append({'frame': frame, 'flower_scale': list(flower.scale), 'camera_matrix': [float(x) for row in scene.camera.matrix_world for x in row], 'petal_eval_time': [float(o.data.shape_keys.eval_time) for o in petals]})
    data = {
        'scene': f'versions/{version}/scene.blend',
        'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'petals': len(petals), 'file_images': len(images), 'packed_images': sum(bool(im.packed_file) for im in images),
        'missing_dependencies': missing, 'linked_libraries': len(bpy.data.libraries),
        'absolute_image_paths': [im.name for im in images if re.match(r'^[A-Za-z]:[/\\]', im.filepath)],
        'embedded_texts_with_local_paths': [t.name for t in bpy.data.texts if re.search(r'[A-Za-z]:[/\\]', t.as_string())],
        'samples': samples,
    }
    if SMOKE:
        scene.frame_set(180)
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for device in prefs.devices:
            device.use = device.type == 'OPTIX'
        scene.cycles.device = 'GPU'
        scene.cycles.samples = 32
        scene.render.resolution_percentage = 25
        scene.render.compositor_device = 'CPU'
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_depth = '8'
        scene.render.filepath = str(ROOT / 'qa' / f'{version}-reopen.png')
        bpy.ops.render.render(write_still=True)
        data['render_smoke'] = {'frame': 180, 'resolution': [768,1024], 'samples': 32, 'image': f'qa/{version}-reopen.png'}
    report['versions'][version] = data
assert report['versions']['v008']['samples'] == report['versions']['v009']['samples']
report['sampled_animation_and_camera_match'] = True
(ROOT / 'qa/publication-reopen.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('PUBLICATION_REOPEN_PASS', json.dumps({v:{k:d[k] for k in ('sha256','packed_images','missing_dependencies','embedded_texts_with_local_paths')} for v,d in report['versions'].items()}), flush=True)
