"""Read-only evaluated triangle audit between flowers; optional virtual depth shifts."""
import argparse
import heapq
import itertools
import json
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'scene.blend'
parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, default=SOURCE)
parser.add_argument('--output', type=Path, default=ROOT / 'renders/cross_audit.json')
parser.add_argument('--frames', default='1,43,67,85,120,193,240,409,433,456,697,720')
parser.add_argument('--bdepth', type=float, default=0)
parser.add_argument('--cdepth', type=float, default=0)
parser.add_argument('--clearance', action='store_true', help='Bound A-stem/C-head surface distance within .02 units.')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
SOURCE = args.source
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
camera = next(marker.camera for marker in scene.timeline_markers if marker.frame == 1)
depth_axis = camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
offsets = {letter: depth_axis * amount for letter, amount in [('A', 0), ('B', args.bdepth), ('C', args.cdepth)]}
heads = {letter: bpy.data.objects[f'{letter} | outer petal 01'].parent for letter in 'ABC'}
head_parts = {letter: [o for o in scene.objects if o.type == 'MESH' and o.parent == head]
              for letter, head in heads.items()}
stems = {letter: bpy.data.objects[f'{letter} | curved stem'] for letter in 'ABC'}
pairs = []
for first, second in itertools.combinations('ABC', 2):
    pairs.extend(('head-head', a, b) for a, b in itertools.product(head_parts[first], head_parts[second]))
    pairs.append(('stem-stem', stems[first], stems[second]))
for first, second in itertools.permutations('ABC', 2):
    pairs.extend(('head-foreign-stem', a, stems[second]) for a in head_parts[first])
objects = {o.name: o for _, a, b in pairs for o in (a, b)}


def box_overlap(a, b):
    return all(a[0][axis] <= b[1][axis] and b[0][axis] <= a[1][axis] for axis in range(3))


def bounds(points):
    return (tuple(min(p[axis] for p in points) for axis in range(3)),
            tuple(max(p[axis] for p in points) for axis in range(3)))


def box_distance(a, b):
    return sum(max(0, a[0][axis] - b[1][axis], b[0][axis] - a[1][axis]) ** 2 for axis in range(3)) ** .5


def evaluate_frame(frame):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    boxes, trees, evaluated, geometry = {}, {}, {}, {}
    for name, obj in objects.items():
        evaluated[name] = obj.evaluated_get(graph)
        ob = evaluated[name]
        points = [ob.matrix_world @ Vector(co) + offsets[name[0]] for co in ob.bound_box]
        boxes[name] = (tuple(min(p[axis] for p in points) for axis in range(3)),
                       tuple(max(p[axis] for p in points) for axis in range(3)))

    def mesh_data(name):
        if name not in geometry:
            ob = evaluated[name]
            mesh = ob.to_mesh()
            mesh.calc_loop_triangles()
            points = [ob.matrix_world @ v.co + offsets[name[0]] for v in mesh.vertices]
            triangles = [tuple(t.vertices) for t in mesh.loop_triangles]
            geometry[name] = (points, triangles)
            ob.to_mesh_clear()
        return geometry[name]

    def tree(name):
        if name not in trees:
            points, triangles = mesh_data(name)
            trees[name] = BVHTree.FromPolygons(points, triangles, all_triangles=True, epsilon=0)
        return trees[name]

    def clearance():
        # Distance-to-surface is 1-Lipschitz: d(center)-triangle_radius is a lower
        # bound on the entire triangle. Adaptively subdivide only near the minimum.
        stem_name = stems['A'].name
        points, triangles = mesh_data(stem_name)
        best, heap, serial = float('inf'), [], 0
        best_part = None

        def consider(name, vertices):
            nonlocal best, serial, best_part
            center = sum(vertices, Vector()) / 3
            distance = tree(name).find_nearest(center)[3]
            if distance < best:
                best, best_part = distance, name
            radius = max((vertex - center).length for vertex in vertices)
            lower = max(0, distance - radius)
            if lower < best - .02:
                serial += 1
                heapq.heappush(heap, (lower, serial, name, vertices))

        for part in sorted(head_parts['C'], key=lambda obj: box_distance(boxes[stem_name], boxes[obj.name])):
            if box_distance(boxes[stem_name], boxes[part.name]) >= best:
                continue
            for indices in triangles:
                vertices = tuple(points[index] for index in indices)
                if box_distance(bounds(vertices), boxes[part.name]) < best:
                    consider(part.name, vertices)
        while heap and heap[0][0] < best - .02:
            _, _, name, (a, b, c) = heapq.heappop(heap)
            ab, bc, ca = (a + b) / 2, (b + c) / 2, (c + a) / 2
            for vertices in ((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)):
                consider(name, vertices)
        return {'lower_bound': max(0, best - .02001), 'upper_bound': best,
                'nearest_part': best_part, 'method': 'Adaptive triangle subdivision with nearest-surface Lipschitz bounds.'}

    contacts, candidates = [], 0
    for category, a, b in pairs:
        if not box_overlap(boxes[a.name], boxes[b.name]):
            continue
        candidates += 1
        overlap = tree(a.name).overlap(tree(b.name))
        if overlap:
            contacts.append({'kind': category, 'a': a.name, 'b': b.name,
                             'triangle_pairs': len(overlap), 'triangle_examples': overlap[:4]})
    row = {'frame': frame, 'aabb_candidates': candidates, 'built_bvhs': len(trees),
           'contact_object_pairs': len(contacts), 'triangle_contact_pairs': sum(c['triangle_pairs'] for c in contacts),
           'contacts': contacts}
    if args.clearance:
        row['A_stem_C_head_clearance'] = clearance()
    print('CROSS_FRAME', frame, 'object_pairs', len(contacts), 'triangle_pairs', row['triangle_contact_pairs'], flush=True)
    return row


started = time.monotonic()
frame_numbers = []
for token in args.frames.split(','):
    if ':' in token:
        start, end = (int(value) for value in token.split(':'))
        frame_numbers.extend(range(start, end + 1))
    else:
        frame_numbers.append(int(token))
samples = [evaluate_frame(frame) for frame in sorted(set(frame_numbers))]
output = args.output
output.parent.mkdir(parents=True, exist_ok=True)
report = json.loads(output.read_text(encoding='utf-8')) if output.exists() else {}
report.update({'source': str(SOURCE), 'read_only': True, 'render_called': False,
               'method': 'Evaluated world-space meshes; AABB broad phase then native BVHTree triangle/triangle intersection, epsilon=0.',
               'excluded': 'All same-flower contacts, including intentional stem/receptacle attachments.',
               'limitation': 'Sampled surface intersections; not a complete swept collision or volume-containment proof.',
               'camera_1_depth_axis': list(depth_axis)})
key = f'B_depth={args.bdepth:g},C_depth={args.cdepth:g}'
trial = report.setdefault('trials', {}).setdefault(key, {'offsets': {letter: list(offset) for letter, offset in offsets.items()}, 'frames': {}})
trial['frames'].update({str(row['frame']): row for row in samples})
trial['sample_count'] = len(trial['frames'])
trial['total_triangle_contact_pairs'] = sum(row['triangle_contact_pairs'] for row in trial['frames'].values())
gaps = [(int(frame), row['A_stem_C_head_clearance']) for frame, row in trial['frames'].items()
        if 'A_stem_C_head_clearance' in row]
if gaps:
    trial['clearance_sample_count'] = len(gaps)
    trial['minimum_A_stem_C_head_gap'] = {'lower_bound': min(gap['lower_bound'] for _, gap in gaps),
                                         'upper_bound': min(gap['upper_bound'] for _, gap in gaps),
                                         'frame_with_lowest_upper_bound': min(gaps, key=lambda row: row[1]['upper_bound'])[0]}
trial['latest_run_seconds'] = round(time.monotonic() - started, 3)
output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('CROSS_AUDIT_DONE', key, 'triangles', trial['total_triangle_contact_pairs'], 'seconds', trial['latest_run_seconds'], flush=True)
