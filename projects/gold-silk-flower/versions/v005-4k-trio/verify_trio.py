"""Check 4K metadata, fixed core geometry, and shared opening animation."""
import hashlib
import json
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT/'manifest.json').read_text())
reports = {}; fingerprints = []
for variant, info in manifest.items():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/info['project']))
    s = bpy.context.scene
    assert (s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage) == (2160,3840,100)
    assert (s.frame_start,s.frame_end,s.render.fps,s.render.fps_base) == (1,300,30,1)
    petals = [o for o in s.objects if o.name.startswith('Petal ')]
    fixed = [o for o in petals if o.get('Fixed inner core')]
    moving = [o for o in petals if not o.get('Fixed inner core')]
    assert len(fixed) == 3 and len(moving) == 48
    assert all(o.data.shape_keys.animation_data is None for o in fixed)
    assert all(o.data.shape_keys.animation_data is not None for o in moving)
    core = bpy.data.objects['CENTER | locked flower heart']
    head = bpy.data.objects['FLOWER | fixed position, orientation and scale']
    assert head.animation_data is None and s.camera.animation_data is None
    transforms = []; positions = []; pixels = []; values = []; core_vertices = []
    for frame in range(1,301):
        s.frame_set(frame)
        transforms.append([v for o in [head,s.camera] for row in o.matrix_world for v in row])
        positions.append(tuple(core.matrix_world.translation))
        graph = bpy.context.evaluated_depsgraph_get()
        projection = s.camera.calc_matrix_camera(graph,x=2160,y=3840) @ s.camera.matrix_world.inverted()
        clip = projection @ Vector((*positions[-1],1))
        pixels.append(((clip.x/clip.w*.5+.5)*2160,(.5-clip.y/clip.w*.5)*3840))
        values.append([key.value for o in sorted(petals,key=lambda ob:ob.name) for key in o.data.shape_keys.key_blocks])
        if frame in [1,61,121,181,217,271,300]:
            coords = []
            for o in fixed:
                ev = o.evaluated_get(graph)
                a = np.empty(len(ev.data.vertices)*3,dtype=np.float32)
                ev.data.vertices.foreach_get('co',a)
                a = np.column_stack((a.reshape(-1,3),np.ones(len(ev.data.vertices))))
                coords.append(a @ np.array(ev.matrix_world).T)
            core_vertices.append(np.concatenate(coords))
    assert np.ptp(np.array(transforms),axis=0).max() == 0
    assert np.ptp(np.array(positions),axis=0).max() == 0
    assert np.ptp(np.array(pixels),axis=0).max() == 0
    assert all(np.array_equal(core_vertices[0],a) for a in core_vertices)
    values = np.array(values,dtype=np.float32)
    assert not np.array_equal(values[0],values[216])
    assert all(np.array_equal(values[216],a) for a in values[216:])
    fingerprint = hashlib.sha256(values.tobytes()).hexdigest(); fingerprints.append(fingerprint)
    assert not [im for im in bpy.data.images if im.source in {'MOVIE','SEQUENCE'} or (im.source == 'FILE' and not im.packed_file)]
    reports[variant] = {'project':info['project'],'resolution':[2160,3840],'fps':30,'frames':300,
        'core_checked_frames':300,'core_position_pixel':pixels[0], 'core_drift_pixels':0,
        'fixed_core_geometry_unchanged':True,'animated_petals':48,'fixed_core_petals':3,
        'static_hold_verified':True,'static_hold_from_frame':217,'animation_sha256':fingerprint,
        'external_texture_dependencies':[]}
    print('VALIDATED',variant,flush=True)
assert len(set(fingerprints)) == 1
(ROOT/'Scene_Validation_4K.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
print('ALL_THREE_SCENES_VALIDATED',flush=True)
