"""Render an explicit PNG frame plan to a new directory; never save the source .blend."""
import argparse
import json
from pathlib import Path
import sys
import time
import uuid

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_guards import ensure_single_scene_render


EVENT_PREFIX = "BLENDER_RENDER_EVENT "


def render_settings(scene):
    settings = {
        "scene": scene.name,
        "engine": scene.render.engine,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y,
                       scene.render.resolution_percentage],
        "format": scene.render.image_settings.file_format,
        "camera": scene.camera.name if scene.camera else None,
        "blender_version": bpy.app.version_string,
    }
    if scene.render.engine == "CYCLES":
        settings["cycles"] = {key: getattr(scene.cycles, key) for key in
                              ("device", "samples", "use_denoising", "use_adaptive_sampling")}
    elif hasattr(scene, "eevee"):
        settings["eevee"] = {key: getattr(scene.eevee, key) for key in
                             ("taa_render_samples", "use_raytracing") if hasattr(scene.eevee, key)}
    return settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--frames", required=True, help="Explicit comma-separated frame numbers, e.g. 1,3,5.")
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(arguments)
    try:
        frames = [int(value.strip()) for value in args.frames.split(",")]
    except ValueError:
        parser.error("--frames must be comma-separated integers.")
    scene = bpy.context.scene
    limits = scene.bl_rna.properties["frame_current"]
    if not frames or len(frames) != len(set(frames)):
        parser.error("Provide a nonempty frame plan without duplicates.")
    if any(frame < limits.hard_min or frame > limits.hard_max for frame in frames):
        parser.error("A planned frame is outside Blender's supported range.")
    if not bpy.data.filepath:
        parser.error("Open an existing reviewed .blend via run_blender --blend before using this worker.")
    if not scene.camera or scene.camera.type != "CAMERA":
        parser.error("The active scene needs a render camera.")
    if scene.render.image_settings.file_format != "PNG":
        parser.error("This worker supports PNG only. Prepare an explicitly requested copy for other formats.")
    ensure_single_scene_render(scene)
    directory = args.output_dir.expanduser()
    if not directory.is_absolute() or directory.exists() or directory.is_symlink():
        parser.error("--output-dir must be an absolute, previously nonexistent directory.")
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    run_id = str(uuid.uuid4())

    def emit(event, **fields):
        print(EVENT_PREFIX + json.dumps({"v": 1, "run_id": run_id, "event": event,
              "emitted_at_unix": time.time(), **fields}, ensure_ascii=False), flush=True)

    settings = render_settings(scene)
    emit("plan", frames=frames, settings=settings, scope="frame_outputs_only")
    for frame in frames:
        output = directory / f"frame_{frame:06d}.png"
        emit("frame_started", frame=frame)
        started = time.perf_counter()
        scene.frame_set(frame)
        if render_settings(scene) != settings:
            raise RuntimeError("Render settings changed within this plan; split it into separately measured runs.")
        ensure_single_scene_render(scene)
        scene.render.filepath = str(output)
        result = bpy.ops.render.render(write_still=True)
        duration = time.perf_counter() - started
        if result != {"FINISHED"} or not output.is_file() or output.stat().st_size <= 0:
            raise RuntimeError(f"Frame {frame} did not return successfully with its planned PNG file.")
        emit("frame_completed", frame=frame, duration_seconds=duration,
             output=str(output), bytes=output.stat().st_size)
    emit("job_frames_complete", output_count=len(frames))


if __name__ == "__main__":
    main()
