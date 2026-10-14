"""Check every final frame using evaluated subdivided triangles, including petal roots."""
import hashlib
import json
import math
import time
from pathlib import Path
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'scene.blend'
OUT = ROOT / 'renders/petal_audit.json'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
s = bpy.context.scene
petals = sorted([o for o in s.objects if o.type == 'MESH' and any(' | '+tier+' petal ' in o.name for tier in ('outer', 'middle', 'inner'))], key=lambda o: o.name)
assert len(petals) == 192
for obj in petals:
    attr = obj.data.attributes.new('_clearance_u', 'FLOAT', 'POINT')
    assert len(obj.data.vertices) == 582
    for i in range(582):
        attr.data[i].value = 0 if i == 0 else 1 if i == 581 else (1-math.cos(math.pi*((i-1)//20+1)/30))/2

def snapshot(obj, graph, inverse):
    ev = obj.evaluated_get(graph)
    mesh = ev.to_mesh()
    mesh.calc_loop_triangles()
    tris = np.empty((len(mesh.loop_triangles), 3), dtype=np.int32)
    mesh.loop_triangles.foreach_get('vertices', tris.ravel())
    points = np.empty((len(mesh.vertices), 3), dtype=np.float32)
    mesh.vertices.foreach_get('co', points.ravel())
    matrix = np.array(inverse @ ev.matrix_world, dtype=np.float64)
    points = points @ matrix[:3, :3].T + matrix[:3, 3]
    attr = mesh.attributes.get('_clearance_u')
    us = np.ones(len(mesh.vertices), dtype=np.float32)
    if attr:
        attr.data.foreach_get('value', us)
    result = {'name': obj.name, 'low': points.min(axis=0), 'high': points.max(axis=0),
              'u': us[tris].mean(axis=1),
              'bvh': BVHTree.FromPolygons(points.tolist(), tris.tolist(), all_triangles=True, epsilon=0)}
    ev.to_mesh_clear()
    return result

rows = []
started = time.monotonic()
for frame in range(1, 361):
    s.frame_set(frame)
    graph = bpy.context.evaluated_depsgraph_get()
    for letter in 'ABC':
        selected = [o for o in petals if o.name.startswith(letter+' | ')]
        inverse = selected[0].parent.matrix_world.inverted()
        meshes = [snapshot(o, graph, inverse) for o in selected]
        targets = [snapshot(bpy.data.objects[letter+' | '+name], graph, inverse)
                   for name in ('spherical flower center', 'rounded petal support')]
        pairs, exposed_attachments = [], []
        attachment_u = 0
        for i, a in enumerate(meshes):
            for b in meshes[i+1:] + targets:
                if np.any(a['low'] > b['high']) or np.any(b['low'] > a['high']):
                    continue
                hits = a['bvh'].overlap(b['bvh'])
                if not hits:
                    continue
                maximum_u = float(max(a['u'][x] for x, _ in hits))
                row = {'a': a['name'], 'b': b['name'], 'triangles': len(hits), 'max_u': maximum_u}
                if any(b is target for target in targets):
                    attachment_u = max(attachment_u, maximum_u)
                    if maximum_u >= .25:
                        exposed_attachments.append(row)
                else:
                    pairs.append(row)
        rows.append({'frame': frame, 'flower': letter, 'petal_pairs': pairs,
                     'exposed_attachments': exposed_attachments, 'max_attachment_u': attachment_u})
    if frame % 24 == 0:
        print('AUDIT_PROGRESS', frame, 'petal_pairs', sum(len(r['petal_pairs']) for r in rows),
              'free_core_pairs', sum(len(r['exposed_attachments']) for r in rows), flush=True)
report = {'source': str(SOURCE), 'sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'frames': 360, 'flower_frame_checks': len(rows),
          'petal_pair_contacts': sum(len(r['petal_pairs']) for r in rows),
          'exposed_core_support_contacts': sum(len(r['exposed_attachments']) for r in rows),
          'maximum_attachment_u': max(r['max_attachment_u'] for r in rows),
          'method': 'Evaluated subdivided triangle intersection at all 360 integer frames. Petal pairs include entire roots; core/support contacts allowed only below longitudinal u=.25.',
          'seconds': time.monotonic()-started, 'rows': rows}
report['passed'] = report['petal_pair_contacts'] == report['exposed_core_support_contacts'] == 0
OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('AUDIT_DONE', report['passed'], report['seconds'], flush=True)
