"""Clean candy finishes for the suspended geometric composition, Blender 5.2.

No external images: quiet pigment variation, minute surface grain, and distinct
roughness/coat responses. These are new molded objects, without weathering.
"""
import bpy


def col(hex_color):
    """Convert an sRGB #RRGGBB color into scene-linear RGBA."""
    h = hex_color.lstrip('#')
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
                 for v in srgb) + (1.0,)


def _node(tree, node_type, label, location):
    node = tree.nodes.new(node_type)
    node.name = label
    node.label = label
    node.location = location
    return node


def _candy(name, color, roughness, coat, metal=0.0, subsurface=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = col(color)
    tree = mat.node_tree
    tree.nodes.clear()
    link = tree.links.new

    coord = _node(tree, 'ShaderNodeTexCoord', 'Object-space fine finish', (-1000, 0))
    pigment = _node(tree, 'ShaderNodeTexNoise', 'Very quiet pigment variation', (-790, 260))
    pigment.inputs['Scale'].default_value = 12.0
    pigment.inputs['Detail'].default_value = 2.0
    pigment.inputs['Roughness'].default_value = 0.48
    link(coord.outputs['Object'], pigment.inputs['Vector'])

    mask = _node(tree, 'ShaderNodeValToRGB', 'Soft pigment blend mask', (-550, 260))
    mask.color_ramp.elements[0].position = 0.18
    mask.color_ramp.elements[0].color = (0.12, 0.12, 0.12, 1)
    mask.color_ramp.elements[1].position = 0.82
    mask.color_ramp.elements[1].color = (0.88, 0.88, 0.88, 1)
    link(pigment.outputs['Fac'], mask.inputs['Fac'])

    mix = _node(tree, 'ShaderNodeMixRGB', 'MIX neighboring pigment tones', (-290, 250))
    mix.blend_type = 'MIX'
    base = col(color)
    mix.inputs[1].default_value = tuple(v * 0.982 for v in base[:3]) + (1,)
    mix.inputs[2].default_value = tuple(min(1.0, v * 1.018) for v in base[:3]) + (1,)
    link(mask.outputs['Color'], mix.inputs[0])

    grain = _node(tree, 'ShaderNodeTexNoise', 'Minute molded surface grain', (-790, -100))
    grain.inputs['Scale'].default_value = 210.0
    grain.inputs['Detail'].default_value = 2.0
    grain.inputs['Roughness'].default_value = 0.52
    link(coord.outputs['Object'], grain.inputs['Vector'])

    rough = _node(tree, 'ShaderNodeMapRange', 'Narrow roughness variation', (-530, -90))
    rough.inputs['From Min'].default_value = 0.0
    rough.inputs['From Max'].default_value = 1.0
    rough.inputs['To Min'].default_value = roughness - 0.018
    rough.inputs['To Max'].default_value = roughness + 0.018
    link(grain.outputs['Fac'], rough.inputs['Value'])

    bump = _node(tree, 'ShaderNodeBump', 'Subpixel satin micro-normal', (-280, -190))
    bump.inputs['Strength'].default_value = 0.035
    bump.inputs['Distance'].default_value = 0.0007
    link(grain.outputs['Fac'], bump.inputs['Height'])

    surface = _node(tree, 'ShaderNodeBsdfPrincipled', 'Pigmented satin with thin clear coat', (10, 180))
    surface.inputs['Metallic'].default_value = metal
    surface.inputs['IOR'].default_value = 1.46
    surface.inputs['Specular IOR Level'].default_value = 0.36
    surface.inputs['Coat Weight'].default_value = coat
    surface.inputs['Coat Roughness'].default_value = 0.3 if metal < 0.1 else 0.25
    surface.inputs['Subsurface Weight'].default_value = subsurface
    surface.inputs['Subsurface Radius'].default_value = (1.0, 0.35, 0.2)
    surface.inputs['Subsurface Scale'].default_value = 0.025
    link(mix.outputs['Color'], surface.inputs['Base Color'])
    link(rough.outputs['Result'], surface.inputs['Roughness'])
    link(bump.outputs['Normal'], surface.inputs['Normal'])
    out = _node(tree, 'ShaderNodeOutputMaterial', 'Material output', (360, 180))
    link(surface.outputs['BSDF'], out.inputs['Surface'])
    mat['finish_note'] = 'Clean satin pigment; connected noise-mask color Mix; subtle roughness and micro-normal.'
    return mat


def _matte(name, color, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = col(color)
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = col(color)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Specular IOR Level'].default_value = 0.18
    return mat


def build_materials():
    """Return all nine named scene finishes; color and shader nodes stay editable."""
    return {
        'yellow': _candy('08 | sun yellow satin plastic', '#FFCC0A', .38, .15, subsurface=.022),
        'pink': _candy('08 | candy pink soft lacquer', '#F5A6D2', .36, .19, subsurface=.018),
        'lilac': _candy('08 | pale lilac satin ceramic', '#CAA4E9', .43, .11),
        'navy': _candy('08 | deep blue coated resin', '#315582', .32, .24, metal=.025),
        'white': _candy('08 | lavender white porcelain', '#F3DFF7', .37, .17, subsurface=.018),
        'gold': _candy('08 | warm yellow satin alloy', '#F5CB49', .34, .12, metal=.38),
        'purple': _candy('08 | violet molded resin', '#9250BE', .40, .14),
        'floor': _matte('08 | pale pink lavender floor', '#DEC3E5', .72),
        'backdrop': _matte('08 | lavender backdrop base', '#A679C3', .82),
    }
