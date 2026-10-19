"""Derive the clay look from archived V004; this is not the original modeling script.
Run with Blender 5.2.1: blender --background --python scripts/build_wire_clay.py
"""
import json
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'output'
OUTPUT.mkdir(parents=True, exist_ok=True)
source = ROOT / 'versions/v004/scene.blend'
if not source.is_file():
    raise FileNotFoundError('Download V004 scene.blend from the project Release into versions/v004/.')
bpy.ops.wm.open_mainfile(filepath=str(source))
scene = bpy.context.scene
scene.name = '白模布线 · Lit clay topology / 4K'

def clay(name, value=.72):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (value, value, value, 1)
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = mat.diffuse_color
    bs.inputs['Roughness'].default_value = .62
    bs.inputs['Specular IOR Level'].default_value = .24
    return mat, bs

def quad_material(name, x_cells, y_cells):
    mat, bs = clay(name)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'Wire topology UV'
    uv.location = (-900, 150)
    sep = nodes.new('ShaderNodeSeparateXYZ')
    links.new(uv.outputs['UV'], sep.inputs[0])
    edge_masks = []
    for axis, cells in enumerate((x_cells, y_cells)):
        mult = nodes.new('ShaderNodeMath'); mult.operation = 'MULTIPLY'
        links.new(sep.outputs[axis], mult.inputs[0]); mult.inputs[1].default_value = cells
        frac = nodes.new('ShaderNodeMath'); frac.operation = 'FRACT'
        links.new(mult.outputs[0], frac.inputs[0])
        invert = nodes.new('ShaderNodeMath'); invert.operation = 'SUBTRACT'
        invert.inputs[0].default_value = 1; links.new(frac.outputs[0], invert.inputs[1])
        distance = nodes.new('ShaderNodeMath'); distance.operation = 'MINIMUM'
        links.new(frac.outputs[0], distance.inputs[0]); links.new(invert.outputs[0], distance.inputs[1])
        ramp = nodes.new('ShaderNodeMapRange'); ramp.clamp = True
        ramp.inputs['From Min'].default_value = .018
        ramp.inputs['From Max'].default_value = .045
        ramp.inputs['To Min'].default_value = 1
        ramp.inputs['To Max'].default_value = 0
        links.new(distance.outputs[0], ramp.inputs['Value'])
        edge_masks.append(ramp.outputs['Result'])
        for column, node in enumerate((mult, frac, invert, distance, ramp)):
            node.location = (-720 + 175 * column, 300 - axis * 370)
    combine = nodes.new('ShaderNodeMath'); combine.operation = 'MAXIMUM'
    links.new(edge_masks[0], combine.inputs[0]); links.new(edge_masks[1], combine.inputs[1])
    mix = nodes.new('ShaderNodeMixRGB'); mix.location = (400, 150)
    mix.inputs[1].default_value = (.72, .72, .72, 1)
    mix.inputs[2].default_value = (.115, .125, .14, 1)
    links.new(combine.outputs[0], mix.inputs[0]); links.new(mix.outputs[0], bs.inputs['Base Color'])
    bs.location = (620, 150)
    mat['Topology'] = f'Original quad surface grid: {x_cells} x {y_cells}; follows animated UVs, no triangles or extra subdivision lines'
    return mat

def grid_uv(ob, cols, rows):
    layer = ob.data.uv_layers.new(name='Wire topology UV')
    for loop in ob.data.loops:
        vertex = loop.vertex_index
        layer.data[loop.index].uv = (vertex % cols / (cols - 1), vertex // cols / (rows - 1))

white, _ = clay('Clay · matte ivory white')
fiber, _ = clay('Clay · fine white fibers', .60)
petal_mat = quad_material('Clay topology · petal 40 x 56 quads', 40, 56)
sepal_mat = quad_material('Clay topology · sepal 8 x 24 quads', 8, 24)
stem_mat = quad_material('Clay topology · stem 16 x 140 quads', 16, 140)
sphere_mat = quad_material('Clay topology · core meridians', 48, 24)

for ob in scene.objects:
    if ob.type != 'MESH' or ob.name.startswith('Backdrop'):
        continue
    mat = white
    if ob.name.startswith('Petal '):
        grid_uv(ob, 41, 57); mat = petal_mat
    elif ob.name.startswith('Sepal '):
        grid_uv(ob, 9, 25); mat = sepal_mat
    elif ob.name.startswith('Stem '):
        layer = ob.data.uv_layers.new(name='Wire topology UV')
        for face in ob.data.polygons:
            row, col = divmod(face.index, 16)
            for loop, uv in zip(face.loop_indices, ((col/16, row/140), ((col+1)/16, row/140),
                                                   ((col+1)/16, (row+1)/140), (col/16, (row+1)/140))):
                layer.data[loop].uv = uv
        mat = stem_mat
    elif ob.name.startswith(('Core ', 'Receptacle ')):
        ob.data.uv_layers.active.name = 'Wire topology UV'; mat = sphere_mat
    elif ob.name.startswith('Fuzz '):
        mat = fiber
    ob.data.materials.clear(); ob.data.materials.append(mat)
    for face in ob.data.polygons:
        face.material_index = 0

# Retain the stable photographic backdrop, neutralized for topology presentation.
background = next(ob for ob in scene.objects if ob.name.startswith('Backdrop'))
background.active_material = background.active_material.copy()
background.active_material.name = 'Studio · neutral charcoal gradient'
for node in background.active_material.node_tree.nodes:
    if node.type == 'VALTORGB':
        for element in node.color_ramp.elements:
            r, g, b, a = element.color
            gray = .2126*r + .7152*g + .0722*b
            element.color = (gray*.65, gray*.65, gray*.65, a)
bn, bl = background.active_material.node_tree.nodes, background.active_material.node_tree.links
emission = next(node for node in bn if node.type == 'EMISSION')
source = emission.inputs['Color'].links[0].from_socket
floor = bn.new('ShaderNodeMixRGB'); floor.blend_type = 'ADD'
floor.inputs[0].default_value = 1; floor.inputs[2].default_value = (.012, .012, .012, 1)
bl.new(source, floor.inputs[1]); bl.new(floor.outputs[0], emission.inputs['Color'])
world = scene.world.node_tree.nodes['Background']
world.inputs['Color'].default_value = (.40, .40, .40, 1)
world.inputs['Strength'].default_value = .22
energies = {'Key': 690, 'Strip': 260, 'Rim': 1050, 'Fill': 105}
for ob in scene.objects:
    if ob.type == 'LIGHT':
        ob.data.color = (1, 1, 1)
        ob.data.energy = energies[ob.name.split(' · ')[0]]
        ob.data.use_shadow_jitter = ob.name.startswith(('Key', 'Rim'))
    if ob.type == 'CAMERA':
        ob.data.dof.use_dof = False
for node in scene.compositing_node_group.nodes:
    if node.type == 'GLARE':
        node.mute = True

scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 64
scene.eevee.use_raytracing = True
scene.eevee.use_fast_gi = True
scene.eevee.fast_gi_method = 'AMBIENT_OCCLUSION_ONLY'
scene.eevee.fast_gi_distance = .45
scene.eevee.fast_gi_thickness_near = .035
scene.eevee.fast_gi_quality = .75
scene.eevee.fast_gi_step_count = 16
scene.eevee.fast_gi_ray_count = 4
scene.eevee.fast_gi_resolution = '2'
scene.eevee.shadow_ray_count = 2
scene.eevee.shadow_step_count = 8
scene.render.resolution_x = 2880; scene.render.resolution_y = 3840
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '8'
scene.render.image_settings.compression = 15
scene.render.use_persistent_data = False
scene.render.use_compositing = True
scene.render.compositor_device = 'GPU'
scene.render.filepath = '//v005/frames/frame_'
scene['Wireframe version'] = 'Lit white clay / original quad grid / 2880x3840 / 450 frames at 30fps'
scene['Wire display'] = 'Quad grid coordinates follow original petal vertices and shape keys; no added diagonals'
scene.frame_set(330)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / 'wire-clay-rebuilt.blend'))
(OUTPUT / 'wire-clay-build.json').write_text(json.dumps({'resolution':[2880,3840], 'frames':450,
    'engine':scene.render.engine, 'samples':scene.eevee.taa_render_samples,
    'new_materials':[mat.name for mat in (white,fiber,petal_mat,sepal_mat,stem_mat,sphere_mat)],
    'light_energy':energies, 'dof':False, 'persistent_data':False}, indent=2), encoding='utf-8')
