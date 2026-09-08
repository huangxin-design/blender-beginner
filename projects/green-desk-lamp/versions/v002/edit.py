"""Copy the green shade material, make it matte ceramic, and save a new version.

Run with Blender --python. Both --input and --output are explicit paths;
the source and any existing output file are never overwritten.
"""
import argparse
import sys
from pathlib import Path

import bpy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    source = args.input.expanduser().resolve(strict=True)
    target = args.output.expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != '.blend':
        raise ValueError('Input must be an existing .blend file.')
    if target.suffix.lower() != '.blend':
        raise ValueError('Output must end in .blend.')
    if target.exists():
        raise FileExistsError(f'Choose a new version path: {target}')
    target.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)

    original = bpy.data.materials['Sage_Enamel']
    shade_objects = [bpy.data.objects[name] for name in ('Lamp_Shade', 'Lamp_Top')]
    if not all(len(o.material_slots) == 1 and o.material_slots[0].material == original
               for o in shade_objects):
        raise ValueError('Expected v001 shade and top to share Sage_Enamel.')
    if any(n.type == 'GROUP' for n in original.node_tree.nodes):
        raise ValueError('This example expects a material without nested node groups.')

    # Detach only these two objects from the shared material. The base keeps it.
    ceramic = original.copy()
    ceramic.name = 'Sage_Matte_Ceramic'
    ceramic.metallic = 0.0
    ceramic.roughness = 0.66
    nodes, links = ceramic.node_tree.nodes, ceramic.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    if bsdf is None or bsdf.inputs['Base Color'].is_linked:
        raise ValueError('Expected an unlinked Principled BSDF Base Color.')
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.66
    bsdf.inputs['IOR'].default_value = 1.46
    bsdf.inputs['Specular IOR Level'].default_value = 0.42
    bsdf.inputs['Coat Weight'].default_value = 0.0
    bsdf.location = (200, 100)
    nodes.get('Material Output').location = (560, 100)

    coordinates = nodes.new('ShaderNodeTexCoord')
    coordinates.name = 'Ceramic_Object_Coordinates'
    coordinates.location = (-840, -120)
    texture = nodes.new('ShaderNodeTexNoise')
    texture.name = 'Fine_Ceramic_Grain'
    texture.label = 'Fine surface grain; no color mottling'
    texture.location = (-620, -120)
    texture.inputs['Scale'].default_value = 500.0
    texture.inputs['Detail'].default_value = 2.0
    texture.inputs['Roughness'].default_value = 0.55
    links.new(coordinates.outputs['Object'], texture.inputs['Vector'])
    roughness = nodes.new('ShaderNodeMapRange')
    roughness.name = 'Matte_Roughness_Range'
    roughness.location = (-340, 140)
    roughness.inputs['To Min'].default_value = 0.60
    roughness.inputs['To Max'].default_value = 0.72
    links.new(texture.outputs['Fac'], roughness.inputs['Value'])
    links.new(roughness.outputs['Result'], bsdf.inputs['Roughness'])
    bump = nodes.new('ShaderNodeBump')
    bump.name = 'Subtle_Ceramic_Surface'
    bump.location = (-100, -180)
    bump.inputs['Strength'].default_value = 0.16
    bump.inputs['Distance'].default_value = 0.00012
    links.new(texture.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    for obj in shade_objects:
        obj.material_slots[0].material = ceramic

    bpy.context.preferences.filepaths.file_preview_type = 'NONE'
    bpy.ops.wm.save_as_mainfile(filepath=str(target), check_existing=True,
                              relative_remap=False)
    print(f'SAVED {target} | Blender {bpy.app.version_string}')


if __name__ == '__main__':
    main()
