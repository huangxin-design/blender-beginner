"""Three native 4K flower projects sharing the verified stationary-core animation."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent/'v4_fixed_center'/'Pink_Flower_Fixed_v4.blend'
SOFT = ROOT.parent/'v3_luminous'/'Pink_Flower_Luminous_v3.blend'
NAMES = {'rose': '01_Rose_Gold_4K', 'crystal': '02_Rose_Crystal_4K', 'clay_wire': '03_Clay_Wire_4K'}
LIGHTS = ['Upper right daylight', 'Warm transmitted rim | behind the petals', 'Soft cool fill | leaves and shaded folds']

def clay_material(name, grid=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (.72, .74, .77, 1)
    tree = mat.node_tree
    bs = tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (.72, .74, .77, 1)
    bs.inputs['Roughness'].default_value = .78
    bs.inputs['Specular IOR Level'].default_value = .25
    if grid is None:
        return mat
    uv = tree.nodes.new('ShaderNodeTexCoord')
    sep = tree.nodes.new('ShaderNodeSeparateXYZ')
    tree.links.new(uv.outputs['UV'], sep.inputs[0])
    def math_node(op, a, b):
        node = tree.nodes.new('ShaderNodeMath'); node.operation = op
        for i, value in enumerate([a,b]):
            if isinstance(value, (int,float)): node.inputs[i].default_value = value
            else: tree.links.new(value, node.inputs[i])
        return node.outputs[0]
    distances = []
    for axis, count in zip(['X','Y'],grid):
        phase = math_node('FRACT', math_node('MULTIPLY', sep.outputs[axis], count), 0)
        distances.append(math_node('MINIMUM', phase, math_node('SUBTRACT', 1, phase)))
    distance = math_node('MINIMUM', *distances)
    ramp = tree.nodes.new('ShaderNodeValToRGB')
    ramp.name = 'Quad topology lines | reduced UV edge density'
    ramp.color_ramp.elements[0].position = .011
    ramp.color_ramp.elements[0].color = (.023, .030, .040, 1)
    ramp.color_ramp.elements[1].position = .027
    ramp.color_ramp.elements[1].color = (.72, .74, .77, 1)
    tree.links.new(distance, ramp.inputs[0])
    tree.links.new(ramp.outputs[0], bs.inputs['Base Color'])
    mat['Quad divisions U / V'] = grid
    mat['Wire display'] = 'Thinned quad edge directions from the native regular UV mesh; follows all shape keys.'
    return mat

manifest = {}
for variant, name in NAMES.items():
    bpy.ops.wm.open_mainfile(filepath=str(BASE))
    s = bpy.context.scene
    petals = [o for o in s.objects if o.name.startswith('Petal ')]
    if variant == 'rose':
        with bpy.data.libraries.load(str(SOFT), link=False) as (source, target):
            target.materials = ['Petal | translucent rose silk + luminous gold filaments']
            target.objects = list(LIGHTS)
            target.worlds = source.worlds
        pink = target.materials[0]
        for ob in petals:
            ob.data.materials.clear(); ob.data.materials.append(pink)
            ob.modifiers['Living petal thickness'].thickness = .004
        for light_name, source_light in zip(LIGHTS,target.objects):
            light = bpy.data.objects[light_name]
            light.data = source_light.data
            light.location = source_light.location
            light.rotation_euler = source_light.rotation_euler
            light.scale = source_light.scale
            bpy.data.objects.remove(source_light, do_unlink=True)
        s.world = target.worlds[0]
        glow = s.compositing_node_group.nodes['Warm gold filament glow']
        glow.inputs['Strength'].default_value = .30
        glow.inputs['Threshold'].default_value = 1.05
        glow.inputs['Size'].default_value = .25
        s.cycles.max_bounces = 10; s.cycles.transmission_bounces = 8
        s.cycles.diffuse_bounces = 4
    elif variant == 'clay_wire':
        petal_mat = clay_material('Clay | petal quad wire 12 x 12', (12,12))
        leaf_mat = clay_material('Clay | leaf quad wire 6 x 13', (6,13))
        plain = clay_material('Clay | neutral white support')
        dark = clay_material('Clay | graphite topology edges')
        dark.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.023,.030,.040,1)
        for ob in list(s.objects):
            if ob.type not in {'MESH','CURVE'} or ob.name == 'Blue studio background': continue
            material = petal_mat if ob.name.startswith('Petal ') else leaf_mat if ob.name.startswith('Leaf ') and ob.type == 'MESH' else plain
            ob.data.materials.clear(); ob.data.materials.append(material)
            if ob.type == 'CURVE':
                ob.data.resolution_u = 16; ob.data.bevel_resolution = 2
                bpy.ops.object.select_all(action='DESELECT')
                ob.select_set(True); bpy.context.view_layer.objects.active = ob
                bpy.ops.object.convert(target='MESH')
                ob.data.materials.append(dark)
                wire = ob.modifiers.new('Visible support topology', 'WIREFRAME')
                wire.thickness = .0018; wire.use_replace = False; wire.material_offset = 1
        key = bpy.data.objects[LIGHTS[0]]
        key.location = (5,-7.5,8.6)
        key.rotation_euler = (Vector((0,0,3.5))-key.location).to_track_quat('-Z','Y').to_euler()
        key.data.shape = 'DISK'; key.data.size = 4.0; key.data.energy = 1700
        key.data.color = (1,1,1)
        fill = bpy.data.objects[LIGHTS[2]]
        fill.data.shape = 'DISK'; fill.data.size = 4.0; fill.data.energy = 400
        fill.data.color = (1,1,1)
        rim = bpy.data.objects[LIGHTS[1]]
        rim.data.energy = 600; rim.data.size = 3.0; rim.data.color = (1,1,1)
        s.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.8,.8,.8,1)
        s.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .20
        s.render.use_compositing = False
        s.cycles.max_bounces = 6; s.cycles.diffuse_bounces = 4
        s['Wireframe display'] = 'Petals and leaves: thinned native quad UV edges. Stem and petioles: geometric wireframe modifier.'
    s.name = name
    s.render.resolution_x = 2160; s.render.resolution_y = 3840
    s.render.resolution_percentage = 100
    s.render.fps = 30; s.render.fps_base = 1
    s.render.image_settings.file_format = 'PNG'; s.render.image_settings.color_mode = 'RGB'
    s.render.image_settings.color_depth = '8'; s.render.image_settings.compression = 15
    s.render.use_persistent_data = True
    s.cycles.use_auto_tile = True; s.cycles.tile_size = 512
    s.cycles.samples = 64; s.cycles.adaptive_threshold = .022
    s.cycles.use_denoising = True; s.cycles.denoising_use_gpu = False
    s.render.compositor_device = 'CPU'
    s.render.use_motion_blur = False
    s['Variant'] = variant
    s['Delivery'] = 'Native portrait UHD 2160 x 3840; 30 fps; 300 frames / 10 seconds'
    s['Render notes'] = 'Cycles / OptiX, native 2160 x 3840, fixed flower core. No resolution upscaling or frame interpolation.'
    s.frame_set(271)
    s.render.filepath = f'//frames/{variant}/0271.png'
    for old in list(bpy.data.texts):
        if old.name.startswith('使用说明'): bpy.data.texts.remove(old)
    note = bpy.data.texts.new('使用说明 | 三版 4K')
    note.write('三版均为 2160×3840、30 fps、300 帧。花心固定，外侧 48 片花瓣展开。第 217–300 帧为静止盛开段。\n白模花瓣与叶片按原始 U/V 四边形网格抽稀显示布线，花茎与叶柄使用几何线框。\n')
    dest = ROOT/f'{name}.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    manifest[variant] = {'project':dest.name,'video':f'{name}_10s_2160x3840.mp4','samples':s.cycles.samples}
    print('VARIANT_SAVED',variant,flush=True)
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
