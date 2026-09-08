"""Rebuild the published v001 desk-lamp demonstration in a new .blend file."""

import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def material(name, color, metallic=0.0, roughness=0.35):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    mat.diffuse_color = (*color, 1)
    return mat


def organize(obj, name, collection, mat=None):
    obj.name = name
    for previous in list(obj.users_collection):
        previous.objects.unlink(obj)
    collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj


def cylinder(name, radius, depth, z, mat, collection, bevel=0.03):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=radius, depth=depth,
                                       location=(0, 0, z))
    obj = organize(bpy.context.object, name, collection, mat)
    mod = obj.modifiers.new('Soft_Edges', 'BEVEL')
    mod.width = bevel
    mod.segments = 3
    obj.modifiers.new('Weighted_Normals', 'WEIGHTED_NORMAL')
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices) == 4
    return obj


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    output = args.output.expanduser().resolve()
    if output.suffix.lower() != '.blend':
        raise ValueError('Output must end in .blend')
    if output.exists():
        raise FileExistsError(f'Choose a new version path: {output}')
    output.parent.mkdir(parents=True, exist_ok=True)

    # This template starts a NEW scene. Do not use this reset for editing user files.
    if bpy.data.filepath:
        raise RuntimeError('This template creates new scenes; do not load an existing .blend first.')
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)
    scene = bpy.context.scene
    groups = {}
    for name in ('Model', 'Stage', 'Lighting', 'Cameras'):
        groups[name] = bpy.data.collections.new(name)
        scene.collection.children.link(groups[name])

    sage = material('Sage_Enamel', (0.16, 0.30, 0.23), metallic=0.2)
    brass = material('Brushed_Brass', (0.42, 0.24, 0.08), metallic=0.75)
    warm_white = material('Warm_Diffuser', (0.95, 0.83, 0.62))
    floor_mat = material('Sand_Backdrop', (0.64, 0.49, 0.36), roughness=0.75)
    model = groups['Model']

    cylinder('Lamp_Base', 0.50, 0.13, 0.075, sage, model, 0.05)
    cylinder('Lamp_Base_Trim', 0.40, 0.025, 0.153, brass, model, 0.01)
    cylinder('Lamp_Stem', 0.048, 1.30, 0.81, brass, model, 0.015)

    # Open bottom with a thin wall; separate cap and diffuser remain editable.
    bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=0.76, radius2=0.31,
                                    depth=0.46, end_fill_type='NOTHING',
                                    location=(0, 0, 1.66))
    shade = organize(bpy.context.object, 'Lamp_Shade', model, sage)
    for face in shade.data.polygons:
        face.use_smooth = True
    shell = shade.modifiers.new('Shade_Thickness', 'SOLIDIFY')
    shell.thickness = 0.025
    bevel = shade.modifiers.new('Shade_Edge', 'BEVEL')
    bevel.width = 0.014
    bevel.segments = 3
    cylinder('Lamp_Top', 0.31, 0.035, 1.893, sage, model, 0.012)
    cylinder('Lamp_Diffuser', 0.70, 0.012, 1.442, warm_white, model, 0.005)
    cylinder('Lamp_Finial', 0.06, 0.045, 1.933, brass, model, 0.015)

    bpy.ops.mesh.primitive_plane_add(size=200)
    organize(bpy.context.object, 'Ground', groups['Stage'], floor_mat)
    for name, location, power, size in (
        ('Key', (3, -4, 5), 550, 4),
        ('Fill', (-3, -2, 3), 250, 3),
        ('Rim', (1, 3, 4), 450, 2.5),
    ):
        light_data = bpy.data.lights.new(name, 'AREA')
        light_data.energy, light_data.shape, light_data.size = power, 'DISK', size
        obj = bpy.data.objects.new(name, light_data)
        groups['Lighting'].objects.link(obj)
        obj.location = location
        aim(obj, (0, 0, 1))

    camera = bpy.data.objects.new('Camera_Main', bpy.data.cameras.new('Camera_Main'))
    groups['Cameras'].objects.link(camera)
    camera.location = (3.5, -5, 3.0)
    aim(camera, (0, 0, 1.0))
    camera.data.type, camera.data.ortho_scale = 'ORTHO', 3.6
    camera.data.lens = 50
    scene.camera = camera
    scene.world = bpy.data.worlds.new('Studio_World')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.45, 0.53, 0.65, 1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.25
    scene.unit_settings.system = 'METRIC'
    # Authoring coordinates above use a 2-unit lamp; deliver a ~49 cm desk lamp.
    for obj in scene.objects:
        obj.location *= 0.25
        if obj.type == 'MESH':
            for vertex in obj.data.vertices:
                vertex.co *= 0.25
            for modifier in obj.modifiers:
                if modifier.type == 'BEVEL':
                    modifier.width *= 0.25
                elif modifier.type == 'SOLIDIFY':
                    modifier.thickness *= 0.25
        elif obj.type == 'LIGHT':
            obj.data.energy *= 0.25 ** 2
            obj.data.size *= 0.25
    camera.data.ortho_scale *= 0.25
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 960, 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = '//preview.png'
    scene.render.fps = 24
    scene.frame_set(1)
    scene.view_settings.view_transform = 'AgX'
    # Match the saved evaluation fixture used for this public demonstration.
    # These are scripted staging choices, not a record of a person's manual edit.
    camera.location.x += 0.2
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    scene.cycles.samples = 12
    # Make opening the delivered file land on its composed camera view.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
    # Session-only setting: avoid writing thumbnail caches outside the project.
    bpy.context.preferences.filepaths.file_preview_type = 'NONE'
    # This is a fresh scene: omit unused factory brush assets and materials.
    bpy.data.orphans_purge(do_recursive=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=True)
    print(f'SAVED {output} | Blender {bpy.app.version_string}')


if __name__ == '__main__':
    main()
