"""Finalize native delivery profiles and pack the reference soundtrack; no renders."""
from pathlib import Path
import json
import bpy

ROOT = Path(__file__).resolve().parent
PROFILE = json.loads((ROOT / 'render_profile.json').read_text(encoding='utf8'))
ASSEMBLY = json.loads((ROOT / 'assembly_build_report.json').read_text(encoding='utf8'))
MASTER = Path(ASSEMBLY['master'])
AUDIO = ROOT / '参考音轨.m4a'
TITLES = ['白底彩色', '黑金', '冰蓝虹彩', '紫黄糖果', '黑白']


def profile(scene):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = PROFILE['samples']
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = PROFILE['adaptive_threshold']
    scene.cycles.adaptive_min_samples = PROFILE['min_samples']
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = PROFILE['denoiser']
    scene.cycles.denoising_use_gpu = PROFILE['denoising_use_gpu']
    scene.cycles.denoising_prefilter = 'ACCURATE'
    scene.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    scene.render.use_persistent_data = True
    scene.render.resolution_x, scene.render.resolution_y = PROFILE['resolution']
    scene.render.resolution_percentage = 100
    scene.render.fps = PROFILE['fps']
    scene.render.fps_base = 1
    scene['09 final render profile'] = json.dumps(PROFILE, ensure_ascii=False)
    scene['09 denoising detail'] = 'OpenImageDenoise GPU; ACCURATE prefilter; RGB_ALBEDO_NORMAL.'


def inspect(scene):
    c = scene.cycles
    values = dict(name=scene.name, samples=c.samples, min_samples=c.adaptive_min_samples,
                  adaptive_threshold=c.adaptive_threshold, use_adaptive_sampling=c.use_adaptive_sampling,
                  denoiser=c.denoiser, use_denoising=c.use_denoising,
                  denoising_use_gpu=c.denoising_use_gpu, denoising_prefilter=c.denoising_prefilter,
                  denoising_input_passes=c.denoising_input_passes, device=c.device,
                  resolution=[scene.render.resolution_x, scene.render.resolution_y],
                  fps=scene.render.fps, persistent=scene.render.use_persistent_data)
    assert values['samples'] == PROFILE['samples'] and values['min_samples'] == PROFILE['min_samples']
    assert abs(values['adaptive_threshold'] - PROFILE['adaptive_threshold']) < 1e-6
    assert values['denoiser'] == 'OPENIMAGEDENOISE' and values['denoising_use_gpu']
    assert values['denoising_prefilter'] == 'ACCURATE'
    assert values['denoising_input_passes'] == 'RGB_ALBEDO_NORMAL'
    assert values['resolution'] == PROFILE['resolution'] and values['fps'] == PROFILE['fps']
    assert values['persistent'] and values['device'] == 'GPU' and values['use_denoising']
    assert values['use_adaptive_sampling']
    return values


def main():
    assert AUDIO.is_file()
    report = {'profile': PROFILE, 'source_projects': [], 'master': str(MASTER),
              'audio_origin': 'User-supplied reference video, extracted original soundtrack.',
              'rendered_during_finalize': False}
    for path_text in ASSEMBLY['source_projects']:
        path = Path(path_text)
        bpy.ops.wm.open_mainfile(filepath=str(path))
        for scene in bpy.data.scenes:
            profile(scene)
            scene['09 soundtrack note'] = '本独立6秒工程不含音轨；用户参考视频的原始音轨已内嵌在30秒总工程「09_悬浮几何_五套配色动画.blend」。'
        bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
        bpy.ops.wm.open_mainfile(filepath=str(path))
        report['source_projects'].append({'path': str(path), 'scenes': [inspect(s) for s in bpy.data.scenes]})

    bpy.ops.wm.open_mainfile(filepath=str(MASTER))
    for scene in bpy.data.scenes:
        profile(scene)
        scene['09 soundtrack note'] = '用户提供参考视频的原始音轨已内嵌总工程：参考音轨.m4a；主时间线第1至900帧完整播放。'
    master = bpy.data.scenes['09_五套配色_30秒']
    bpy.context.window.scene = master
    editor = master.sequence_editor_create()
    for strip in list(editor.strips):
        if strip.type == 'SOUND' and strip.name == '参考视频原音轨 · 已内嵌':
            editor.strips.remove(strip)
    audio = editor.strips.new_sound('参考视频原音轨 · 已内嵌', str(AUDIO), channel=2, frame_start=1)
    audio.frame_final_end = 901
    audio.volume = 1
    audio.sound.pack()
    audio.sound.filepath = '//参考音轨.m4a'
    master['09 audio packed'] = True
    master['09 audio source filename'] = '127578601936631279.mp4'
    master['09 soundtrack note'] = '参考视频原音轨已打包在工程内，可随.blend文件移动；音条channel2，第1至900帧，音量1.0。'
    for marker in list(master.timeline_markers):
        if marker.name in TITLES:
            master.timeline_markers.remove(marker)
    for i, name in enumerate(TITLES):
        master.timeline_markers.new(name, frame=i * 180 + 1)
    master.frame_set(1)
    for screen in bpy.data.screens:
        if screen.name.startswith('Layout'):
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    area.type = 'SEQUENCE_EDITOR'
                    area.spaces.active.view_type = 'SEQUENCER_PREVIEW'
                    area.spaces.active.show_region_ui = False
    bpy.ops.wm.save_as_mainfile(filepath=str(MASTER), compress=True)

    bpy.ops.wm.open_mainfile(filepath=str(MASTER))
    master = bpy.data.scenes['09_五套配色_30秒']
    report['master_scenes'] = [inspect(s) for s in bpy.data.scenes]
    sounds = [s for s in master.sequence_editor.strips if s.type == 'SOUND']
    scene_strips = sorted([s for s in master.sequence_editor.strips if s.type == 'SCENE'], key=lambda s: s.frame_final_start)
    assert len(sounds) == 1 and len(scene_strips) == 5
    audio = sounds[0]
    assert (audio.frame_final_start, audio.frame_final_end, audio.frame_final_duration, audio.channel) == (1, 901, 900, 2)
    assert audio.sound.packed_file is not None
    assert audio.sound.packed_file.size == AUDIO.stat().st_size
    assert not audio.mute and audio.volume == 1
    for i, strip in enumerate(scene_strips):
        assert (strip.frame_final_start, strip.frame_final_end, strip.frame_final_duration) == (i * 180 + 1, (i + 1) * 180 + 1, 180)
        assert strip.scene_input == 'CAMERA'
    report['audio'] = {'name': audio.name, 'start': audio.frame_final_start,
                       'end_exclusive': audio.frame_final_end, 'frames': audio.frame_final_duration,
                       'channel': audio.channel, 'packed_bytes': audio.sound.packed_file.size,
                       'volume': audio.volume, 'packed': True}
    report['markers'] = [{'name': m.name, 'frame': m.frame} for m in master.timeline_markers]
    report['scene_strips_unchanged'] = True
    report['profile_and_packed_audio_reload_passed'] = True
    report['master_size_bytes'] = MASTER.stat().st_size
    (ROOT / 'final_project_check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print('FINAL_PROJECT_CHECK', json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
