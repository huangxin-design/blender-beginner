"""Render one cold preview in a fresh background process; never save the loaded file."""
import argparse
import json
from pathlib import Path
import platform
import sys
import time

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_guards import ensure_single_scene_render


def settings(scene):
    render = scene.render
    cycles = scene.cycles if render.engine == "CYCLES" else None
    eevee = getattr(scene, "eevee", None)
    return {"engine": render.engine, "frame": scene.frame_current,
            "resolution": [render.resolution_x, render.resolution_y],
            "percentage": render.resolution_percentage, "border": render.use_border,
            "samples": cycles.samples if cycles else getattr(eevee, "taa_render_samples", None),
            "adaptive_sampling": cycles.use_adaptive_sampling if cycles else None,
            "noise_threshold": cycles.adaptive_threshold if cycles else None,
            "denoising": cycles.use_denoising if cycles else None,
            "cycles_device": cycles.device if cycles else None,
            "compositing": render.use_compositing, "sequencer": render.use_sequencer}


def select_backend(scene, requested, report):
    if scene.render.engine != "CYCLES":
        if requested != "AUTO":
            raise RuntimeError("Explicit backends are Cycles-only; keep AUTO for the original engine.")
        report["backend"] = "ENGINE_MANAGED"
        report["warnings"].append("The original engine manages its GPU; device identity is unverified.")
        return
    preferences = bpy.context.preferences.addons["cycles"].preferences
    candidates = (["METAL"] if platform.system() == "Darwin" else
                  ["OPTIX", "CUDA", "HIP", "ONEAPI"])
    if requested != "AUTO":
        candidates = [] if requested == "CPU" else [requested]
    for candidate in candidates:
        try:
            preferences.compute_device_type = candidate
            preferences.get_devices()
            devices = [device for device in preferences.devices if device.type == candidate]
        except (TypeError, ValueError, RuntimeError) as error:
            report["enumeration_notes"].append(f"{candidate}: {error}")
            continue
        if not devices:
            report["enumeration_notes"].append(f"{candidate}: no matching devices")
            continue
        for device in preferences.devices:
            device.use = device.type == candidate
        scene.cycles.device = "GPU"
        report["backend"] = candidate
        report["selected_devices"] = [{"name": d.name, "type": d.type} for d in devices]
        return
    if requested not in {"AUTO", "CPU"}:
        raise RuntimeError(f"Requested GPU backend {requested} is unavailable; no CPU fallback.")
    preferences.compute_device_type = "NONE"
    scene.cycles.device = "CPU"
    report["backend"] = "CPU"
    report["selected_devices"] = [{"name": platform.processor() or "CPU", "type": "CPU"}]
    if requested == "AUTO":
        report["warnings"].append("No matching GPU was enumerated; AUTO selected CPU.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--backend", choices=["AUTO", "CPU", "OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"], default="AUTO")
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--samples", type=int, default=16)
    parser.add_argument("--frame", type=int)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    output = Path(args.output_dir).expanduser()
    if not output.is_absolute() or output.exists() or output.is_symlink():
        raise ValueError("--output-dir must be an absolute, previously nonexistent directory.")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    scene = bpy.context.scene
    report = {"schema_version": 1, "ok": False, "status": "failed",
              "source": bpy.data.filepath, "blender_version": bpy.app.version_string,
              "original": settings(scene), "test": None, "requested_backend": args.backend,
              "backend": None, "selected_devices": [], "backend_render_verified": False,
              "enumeration_notes": [], "warnings": [], "errors": [], "preview": None,
              "scene": {"name": scene.name, "objects": len(scene.objects),
                        "base_mesh_polygons": sum(len(o.data.polygons) for o in scene.objects if o.type == "MESH"),
                        "materials": len(bpy.data.materials), "images": len(bpy.data.images),
                        "camera": scene.camera.name if scene.camera else None},
              "render": {"completed": False, "kind": "cold_single_frame", "wall_seconds": None},
              "limitations": [
                  "Not Blender Benchmark or proof of 4K/animation capability; no linear time extrapolation.",
                  "Timed render includes render initialization, kernel/shader compilation, denoising, compositing and PNG writing when applicable; excludes process launch, .blend loading and device enumeration.",
                  "Fresh-process cold frame may reuse disk caches; not a guaranteed empty-cache benchmark.",
                  "No peak RAM/VRAM or sustained thermal measurement; base polygons exclude evaluated modifiers/instances.",
                  "One frame does not validate animation, simulation caches or worst-case frames; adaptive sampling may stop below the sample cap.",
                  "Run with --disable-autoexec in a fresh background process. The caller must enforce a hard timeout and record process failure/crash; this script cannot contain arbitrary installed add-ons.",
              ]}
    try:
        if not bpy.app.background or not bpy.data.filepath or not Path(bpy.data.filepath).is_file():
            raise RuntimeError("Load an existing .blend in a fresh background process first.")
        if min(args.width, args.height, args.samples) < 1:
            raise ValueError("Width, height and samples must be positive.")
        ensure_single_scene_render(scene)
        if scene.render.engine not in {"CYCLES", "BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"}:
            raise RuntimeError(f"Unsupported probe engine: {scene.render.engine}; engine was not changed.")
        select_backend(scene, args.backend, report)
        if args.frame is not None:
            scene.frame_set(args.frame)
        render = scene.render
        render.resolution_x, render.resolution_y = args.width, args.height
        render.resolution_percentage, render.use_border = 100, False
        if render.engine == "CYCLES":
            scene.cycles.samples = args.samples
        elif hasattr(getattr(scene, "eevee", None), "taa_render_samples"):
            scene.eevee.taa_render_samples = args.samples
        else:
            report["warnings"].append("This engine/version exposes no supported sample setting; samples unchanged.")
        preview = output / "preview.png"
        render.filepath, render.image_settings.file_format = str(preview), "PNG"
        render.use_file_extension = True
        report["test"] = settings(scene)
        started = time.perf_counter()
        try:
            result = bpy.ops.render.render(write_still=True, scene=scene.name)
        finally:
            report["render"]["wall_seconds"] = round(time.perf_counter() - started, 4)
        if "FINISHED" not in result or not preview.is_file():
            raise RuntimeError("Rendering did not complete with the requested PNG.")
        with preview.open("rb") as stream:
            header = stream.read(24)
        dimensions = [int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")]
        if header[:8] != b"\x89PNG\r\n\x1a\n" or dimensions != [args.width, args.height]:
            raise RuntimeError(f"Preview dimensions/signature failed validation: {dimensions}")
        report.update(ok=True, status="completed", preview=str(preview),
                      backend_render_verified=render.engine == "CYCLES")
        report["render"]["completed"] = True
    except Exception as error:
        report["errors"].append(f"{type(error).__name__}: {error}")
        raise
    finally:
        with (output / "report.json").open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(f"Frame probe report: {output / 'report.json'}")


if __name__ == "__main__":
    main()
