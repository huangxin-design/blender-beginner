"""Save the five editable looks and assemble their native 30-second VSE master."""
from pathlib import Path
import argparse
import json
import sys
import bpy

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from palette_animation import apply_palette, STYLE_NAMES

BASE = ROOT / '09_基础循环.blend'
MASTER = ROOT / '09_悬浮几何_五套配色动画.blend'
WIDTH, HEIGHT, FPS, DURATION = 720, 1280, 30, 180


def settings(scene, total=DURATION):
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = .035
    scene.cycles.adaptive_min_samples = 12
    scene.cycles.use_denoising = True
    scene.cycles.device = 'GPU'
    scene.render.use_persistent_data = True
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.render.fps_base = 1
    scene.frame_start = 1
    scene.frame_end = total
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = -.2
    scene.view_settings.gamma = 1


def gpu():
    p = bpy.context.preferences.addons['cycles'].preferences
    p.compute_device_type = 'OPTIX'
    p.get_devices()
    for d in p.devices:
        d.use = d.type == 'OPTIX'


def bind_compositor(scene):
    if scene.compositing_node_group:
        for node in scene.compositing_node_group.nodes:
            if node.type == 'R_LAYERS':
                node.scene = scene


def render_check(master, sources):
    """Matched native source and VSE camera renders, without altering saved files."""
    result = []
    for scene in [master] + sources:
        scene.render.resolution_x = 180
        scene.render.resolution_y = 320
        scene.cycles.samples = 16
        scene.cycles.adaptive_min_samples = 8
        scene.cycles.adaptive_threshold = .06
    for i in [0, 2]:
        source = sources[i]
        source.frame_set(45)
        source.render.filepath = str(ROOT / ('assembly_check_source_%02d.png' % i))
        bpy.context.window.scene = source
        bpy.ops.render.render(scene=source.name, write_still=True)
        main_frame = i * DURATION + 45
        master.frame_set(main_frame)
        master.render.filepath = str(ROOT / ('assembly_check_master_%02d.png' % i))
        bpy.context.window.scene = master
        bpy.ops.render.render(scene=master.name, write_still=True)
        result.append({'source_index': i, 'source_frame': 45, 'master_frame': main_frame,
                       'source_image': source.render.filepath, 'master_image': master.render.filepath})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--render-check', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    assert BASE.is_file(), 'The approved final base animation must be saved first.'
    paths = []
    scene_names = []
    for i, name in enumerate(STYLE_NAMES):
        bpy.ops.wm.open_mainfile(filepath=str(BASE))
        scene = bpy.context.scene
        scene.name = '09_%02d_%s_6秒' % (i + 1, name)
        apply_palette(scene, i)
        settings(scene)
        bind_compositor(scene)
        scene.frame_set(1)
        scene['09 delivery note'] = 'Editable 180-frame geometry loop; static materials for this look.'
        target = ROOT / ('09_%02d_%s.blend' % (i + 1, name))
        bpy.ops.wm.save_as_mainfile(filepath=str(target), compress=True)
        paths.append(target)
        scene_names.append(scene.name)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    master = bpy.context.scene
    master.name = '09_五套配色_30秒'
    settings(master, 5 * DURATION)
    master.render.use_compositing = False
    master.render.use_sequencer = True
    sources = []
    for path, name in zip(paths, scene_names):
        with bpy.data.libraries.load(str(path), link=False) as (data_from, data_to):
            assert name in data_from.scenes
            data_to.scenes = [name]
        scene = data_to.scenes[0]
        sources.append(scene)
        bind_compositor(scene)
    editor = master.sequence_editor_create()
    strips = []
    for i, source in enumerate(sources):
        strip = editor.strips.new_scene(STYLE_NAMES[i], source, channel=1, frame_start=i * DURATION + 1)
        strip.scene_input = 'CAMERA'
        strip.frame_final_duration = DURATION
        strips.append(strip)
    master.frame_set(1)
    master['09 delivery note'] = 'Five editable native source scenes, each 180 frames; consecutive hard cuts at 181, 361, 541, 721.'
    bpy.context.window.scene = master
    gpu()
    bpy.ops.wm.save_as_mainfile(filepath=str(MASTER), compress=True)

    # Verify the saved master, rather than only the in-memory construction.
    bpy.ops.wm.open_mainfile(filepath=str(MASTER))
    master = bpy.data.scenes['09_五套配色_30秒']
    bpy.context.window.scene = master
    strips = sorted(master.sequence_editor.strips, key=lambda s: s.frame_final_start)
    assert len(strips) == 5
    source_scenes = []
    for i, strip in enumerate(strips):
        assert strip.type == 'SCENE' and strip.scene_input == 'CAMERA'
        assert strip.frame_final_start == i * DURATION + 1
        assert strip.frame_final_end == (i + 1) * DURATION + 1
        assert strip.frame_final_duration == DURATION
        assert strip.scene.camera is not None
        assert (strip.scene.frame_start, strip.scene.frame_end) == (1, DURATION)
        source_scenes.append(strip.scene)
    report = {
        'master': str(MASTER), 'source_projects': [str(p) for p in paths],
        'source_base': str(BASE), 'resolution': [WIDTH, HEIGHT], 'fps': FPS,
        'frames': [1, 5 * DURATION], 'duration_seconds': 30,
        'source_scenes': [s.name for s in source_scenes],
        'strips': [{'name': s.name, 'source_scene': s.scene.name, 'start': s.frame_final_start,
                    'end_exclusive': s.frame_final_end, 'duration': s.frame_final_duration,
                    'input': s.scene_input} for s in strips],
        'reload_and_timing_passed': True,
    }
    if args.render_check:
        report['render_checks'] = render_check(master, source_scenes)
    (ROOT / 'assembly_build_report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf8')
    print('ASSEMBLY_COMPLETE', json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
