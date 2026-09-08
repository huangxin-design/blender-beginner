"""Five editable material looks for the suspended geometry animation.

Load the untouched base scene before each call. No keyframes are created.
Index: 0 white/multicolor; 1 black/gold; 2 icy iridescent; 3 original purple;
4 black/white. Original noise, pigment Mix and micro-normal nodes are retained.
"""
import bpy


STYLE_NAMES = ['白底彩色', '黑金', '冰蓝虹彩', '紫黄糖果', '黑白']
MATERIAL_NAMES = {
    'yellow': '08 | sun yellow satin plastic',
    'pink': '08 | candy pink soft lacquer',
    'lilac': '08 | pale lilac satin ceramic',
    'navy': '08 | deep blue coated resin',
    'white': '08 | lavender white porcelain',
    'gold': '08 | warm yellow satin alloy',
    'purple': '08 | violet molded resin',
    'dark': '08 | Midnight blue satin resin',
    'lemon': '08 | Lemon yellow flat enamel',
    'orb': '08 | Pleated yellow matte resin',
}


def col(value):
    value = value.lstrip('#')
    rgb = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb) + (1,)


def finish(mat, color, metallic, roughness, coat=.18):
    nt = mat.node_tree
    mix = nt.nodes.get('MIX neighboring pigment tones')
    base = col(color)
    mat.diffuse_color = base
    mix.inputs[1].default_value = tuple(v * .982 for v in base[:3]) + (1,)
    mix.inputs[2].default_value = tuple(min(1, v * 1.018) for v in base[:3]) + (1,)
    p = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Coat Weight'].default_value = coat
    p.inputs['Coat Roughness'].default_value = .23
    p.inputs['Subsurface Weight'].default_value = 0
    p.inputs['Specular IOR Level'].default_value = .36
    r = next(n for n in nt.nodes if n.type == 'MAP_RANGE')
    r.inputs['To Min'].default_value = roughness - .018
    r.inputs['To Max'].default_value = roughness + .018


def angular_color(mat, colors):
    nt = mat.node_tree
    layer = nt.nodes.new('ShaderNodeLayerWeight')
    layer.name = '09 | Viewing-angle iridescence'
    layer.label = 'Angle-dependent pearlescent pigment'
    layer.location = (-980, 620)
    layer.inputs['Blend'].default_value = .35
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.name = '09 | Cyan violet pearl angle colors'
    ramp.location = (-740, 620)
    ramp.color_ramp.interpolation = 'EASE'
    for i, color in enumerate(colors):
        e = ramp.color_ramp.elements[i] if i < 2 else ramp.color_ramp.elements.new(i / (len(colors) - 1))
        e.position = i / (len(colors) - 1)
        e.color = col(color)
    nt.links.new(layer.outputs['Facing'], ramp.inputs['Fac'])
    # Both neighboring pigments inherit angle color; a tiny second tone offset
    # retains the connected original noise-controlled pigment Mix.
    tint = nt.nodes.new('ShaderNodeMixRGB')
    tint.name = '09 | Neighboring pearl shade'
    tint.blend_type = 'MULTIPLY'
    tint.inputs[0].default_value = 1
    tint.inputs[2].default_value = (.95, .985, 1, 1)
    tint.location = (-430, 540)
    nt.links.new(ramp.outputs['Color'], tint.inputs[1])
    mix = nt.nodes.get('MIX neighboring pigment tones')
    nt.links.new(ramp.outputs['Color'], mix.inputs[1])
    nt.links.new(tint.outputs['Color'], mix.inputs[2])


def object_material(scene, prefixes, mat):
    for obj in scene.objects:
        if not obj.name.startswith(tuple(prefixes)):
            continue
        if obj.data and hasattr(obj.data, 'materials'):
            for i in range(len(obj.data.materials)):
                obj.data.materials[i] = mat
        for mod in obj.modifiers:
            if mod.type == 'NODES' and mod.node_group:
                for socket in mod.node_group.interface.items_tree:
                    if socket.item_type == 'SOCKET' and socket.in_out == 'INPUT' and socket.socket_type == 'NodeSocketMaterial':
                        socket.default_value = mat
                # A literal Set Material override keeps these uniquely owned
                # per-object node groups editable and avoids stale modifier
                # material-interface values after loading the 08 project.
                for node in mod.node_group.nodes:
                    if node.type == 'SET_MATERIAL':
                        inp = node.inputs['Material']
                        for link in list(inp.links):
                            mod.node_group.links.remove(link)
                        inp.default_value = mat


def stage(scene, bottom, top, floor_color, world_strength, light_powers):
    wall = bpy.data.materials['08 | lavender backdrop base']
    ramp = next(n for n in wall.node_tree.nodes if n.type == 'VALTORGB')
    factor = 2 ** (-scene.view_settings.exposure)
    for e, h in zip(ramp.color_ramp.elements, [bottom, top]):
        e.color = tuple(v * factor for v in col(h)[:3]) + (1,)
    floor = bpy.data.materials['08 | pale pink lavender floor']
    p = next(n for n in floor.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = col(floor_color)
    p.inputs['Roughness'].default_value = .62
    for n in floor.node_tree.nodes:
        if n.type == 'EMISSION':
            n.inputs['Color'].default_value = tuple(v * factor for v in col(floor_color)[:3]) + (1,)
    bg = scene.world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = (.8, .8, .8, 1)
    bg.inputs['Strength'].default_value = world_strength
    for obj in scene.objects:
        if obj.type == 'LIGHT':
            obj.data.color = (1, 1, 1)
            for key, power in zip(['KEY', 'FILL', 'RIM'], light_powers):
                if obj.name.startswith(key):
                    obj.data.energy = power
    # The inherited pink glow tint must not leak into neutral or gold styles.
    nt = scene.compositing_node_group
    if nt:
        for n in nt.nodes:
            if n.type == 'GLARE':
                n.inputs['Tint'].default_value = (1, 1, 1, 1)
                n.inputs['Strength'].default_value = .012
                n.inputs['Threshold'].default_value = 2.0


def apply_palette(scene, index):
    """Apply one static style to a newly loaded base scene; returns style name."""
    if index not in range(5):
        raise ValueError('Palette index must be 0 through 4')
    scene['09 palette index'] = index
    scene['09 palette name'] = STYLE_NAMES[index]
    if index == 3:
        return STYLE_NAMES[index]
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = -.2
    scene.view_settings.gamma = 1
    mats = {k: bpy.data.materials[v] for k, v in MATERIAL_NAMES.items()}
    if index == 0:
        colors = dict(yellow='FFD12B', pink='ED9ECC', lilac='DCE4E3', navy='168FBF', white='E1E7E5', gold='FDD34B', purple='D5DDD9', dark='424D49', lemon='E4E8E5', orb='ECA5D2')
        for key, mat in mats.items():
            finish(mat, colors[key], .02, .37, .16)
        special = {}
        for key, color in [('green','74BD86'), ('orange','EF7E19'), ('pink','E9A3D0'), ('black','29322D')]:
            mat = mats['white'].copy(); mat.name = '09 | Colorful accent ' + key
            finish(mat, color, .01, .39, .13); special[key] = mat
        object_material(scene, ['03 |', '32 |', '32 curled'], special['green'])
        object_material(scene, ['07 |', '09 |'], special['orange'])
        object_material(scene, ['10 |','04 |','31 |','31c |'], mats['white'])
        object_material(scene, ['21 |','21 stud','21 rounded','06c |','27 |'], mats['yellow'])
        object_material(scene, ['06 |','22 |','22 arrow','28 |','14 |'], mats['navy'])
        object_material(scene, ['06b |','23 |','29 |'], special['pink'])
        object_material(scene, ['24 |'], special['black'])
        object_material(scene, ['18 |'], special['green'])
        stage(scene, 'DDE2DF', 'C7CECA', 'DCE3E0', .35, (900, 150, 200))
    elif index == 1:
        colors = dict(yellow='BB8339', pink='D19B4A', lilac='E2C08A', navy='CAA064', white='E7D3A7', gold='F5CE88', purple='A06A31', dark='956027', lemon='DDC18C', orb='CF9A4D')
        for key, mat in mats.items():
            finish(mat, colors[key], .91, .28 if key != 'orb' else .34, .12)
        stage(scene, '050505', '020202', '171817', .32, (1000, 320, 420))
    elif index == 2:
        colors = dict(yellow='58BEE6', pink='DEB7ED', lilac='C0DCEE', navy='2689D2', white='E1EAF1', gold='B9DCEB', purple='514FCC', dark='7573BC', lemon='2BE0D9', orb='4C91CB')
        for key, mat in mats.items():
            finish(mat, colors[key], .56, .24 if key != 'orb' else .30, .32)
            if key in ('yellow','pink','lilac','white','gold','dark'):
                angular_color(mat, ['9B79CD','F0CCE9','E0F4F3','8BD9E9'])
            elif key == 'orb':
                angular_color(mat, ['668DBB','87CBDF','D9EDF2','A7DBE7'])
        stage(scene, 'DCEAF0', 'AABFCC', 'D6E5EE', .38, (820, 280, 260))
    else:
        colors = dict(yellow='D0D0D0', pink='313131', lilac='C3C3C3', navy='DFDFDF', white='454545', gold='DDDDDD', purple='242424', dark='BCBCBC', lemon='E0E0E0', orb='252525')
        for key, mat in mats.items():
            finish(mat, colors[key], .1 if key in ('gold','dark') else .025, .36, .18)
        stage(scene, '050505', '030303', '9A9A9A', .33, (930, 170, 300))
    return STYLE_NAMES[index]
