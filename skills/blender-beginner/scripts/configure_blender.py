"""Configure a NEW portable Blender copy; run with --background --factory-startup."""
import argparse
import json
import os
from pathlib import Path
import sys
import time

import bpy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    supplied_root = Path(args.root)
    if not supplied_root.is_absolute() or not bpy.app.background:
        raise RuntimeError("An absolute --root and a background Blender process are required.")
    root = supplied_root.resolve(strict=True)
    config_value = bpy.utils.user_resource("CONFIG", create=False)
    if not config_value:
        raise RuntimeError("Blender has no isolated CONFIG path; check the portable directory.")
    config = Path(config_value).resolve()
    directories = {name: (root / name).resolve() for name in ("projects", "renders", "temp", "verification")}
    directories["config"] = config
    outputs = {
        "preferences": config / "userpref.blend",
        "startup": config / "startup.blend",
        "project": directories["projects"] / "start.blend",
        "report": directories["verification"] / "setup.json",
        "preview": directories["verification"] / "setup-preview.png",
    }
    for path in [*directories.values(), *outputs.values()]:
        if not path.resolve().is_relative_to(root):
            raise RuntimeError(f"Refusing a path outside the installation root: {path}")
    for path in outputs.values():
        if path.exists() or path.is_symlink():
            raise FileExistsError(f"Refusing to overwrite an existing file: {path}")
    for path in directories.values():
        path.mkdir(parents=True, exist_ok=True)

    preferences = bpy.context.preferences
    preferences.view.language = "zh_HANS"
    preferences.view.use_translate_interface = True
    preferences.view.use_translate_tooltips = True
    preferences.view.use_translate_new_dataname = False
    preferences.filepaths.use_auto_save_temporary_files = True
    preferences.filepaths.auto_save_time = 2
    preferences.filepaths.save_version = 2
    preferences.filepaths.temporary_directory = str(directories["temp"]) + os.sep
    preferences.filepaths.render_output_directory = str(directories["renders"]) + os.sep
    preferences.filepaths.file_preview_type = "NONE"

    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "CYCLES"
    scene.render.fps = 30
    scene.render.fps_base = 1.0
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x, scene.render.resolution_y = 320, 240
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(outputs["preview"])
    scene.cycles.samples = 8
    scene.cycles.use_denoising = True
    warnings, attempts, devices = [], [], []
    backend = "CPU"
    cycles = preferences.addons["cycles"].preferences

    def render(candidate):
        started = time.monotonic()
        result = {"backend": candidate, "success": False}
        try:
            outputs["preview"].unlink(missing_ok=True)
            if "FINISHED" not in bpy.ops.render.render(write_still=True):
                raise RuntimeError("Blender cancelled the render.")
            header = outputs["preview"].read_bytes()[:24]
            width = int.from_bytes(header[16:20], "big")
            height = int.from_bytes(header[20:24], "big")
            if header[:8] != b"\x89PNG\r\n\x1a\n" or (width, height) != (320, 240):
                raise RuntimeError("Render did not produce a 320 x 240 PNG.")
            result.update(success=True, width=width, height=height)
        except Exception as error:
            result["error"] = str(error)
            warnings.append(f"{candidate} render failed: {error}")
        result["seconds"] = round(time.monotonic() - started, 3)
        attempts.append(result)
        return result["success"]

    for candidate in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            cycles.compute_device_type = candidate
            cycles.get_devices()
        except (TypeError, ValueError, RuntimeError):
            continue
        available = [device for device in cycles.devices if device.type == candidate]
        if not available:
            continue
        devices.extend({"name": device.name, "type": device.type, "id": device.id} for device in available)
        for device in cycles.devices:
            device.use = device.type == candidate
        scene.cycles.device = "GPU"
        if render(candidate):
            backend = candidate
            break
    if backend == "CPU":
        cycles.compute_device_type = "NONE"
        for device in cycles.devices:
            device.use = device.type == "CPU"
        scene.cycles.device = "CPU"
        if not render("CPU"):
            raise RuntimeError("CPU verification render failed; configuration was not saved.")

    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.render.filepath = str(directories["renders"]) + os.sep
    scene.cycles.samples = 64
    bpy.ops.wm.save_userpref()
    bpy.ops.wm.save_homefile()
    bpy.ops.wm.save_as_mainfile(filepath=str(outputs["project"]))
    report = {
        "blender_version": bpy.app.version_string,
        "executable": bpy.app.binary_path,
        "root": str(root),
        "paths": {name: str(path) for name, path in {**directories, **outputs}.items()},
        "backend": backend,
        "devices": devices,
        "warnings": warnings,
        "render": attempts[-1],
        "render_attempts": attempts,
        "settings": {"language": "zh_HANS", "translate_new_names": False, "autosave_minutes": 2,
                     "backup_versions": 2, "units": "METRIC", "resolution": [1920, 1080],
                     "fps": 30, "engine": "CYCLES", "samples": 64, "denoising": True},
    }
    with outputs["report"].open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(f"Portable Blender configured: {outputs['report']}")


if __name__ == "__main__":
    main()
