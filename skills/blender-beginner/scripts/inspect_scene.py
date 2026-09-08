"""Inspect an already loaded .blend; optionally render one frame without saving it."""

import argparse
import json
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_guards import ensure_single_scene_render


def output_path(value, suffix, source):
    path = Path(value).expanduser()
    if not path.is_absolute() or path.suffix.lower() != suffix:
        raise ValueError(f"Output must be an absolute {suffix} path: {value}")
    path = path.resolve()
    if path == source or path.exists():
        raise ValueError(f"Refusing to overwrite an existing file or source: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def has_geometry(obj):
    if obj.hide_render:
        return False
    if obj.type == "MESH":
        return len(obj.data.polygons) > 0
    if obj.type in {"CURVE", "SURFACE"}:
        return any(len(s.points) or len(s.bezier_points) for s in obj.data.splines)
    if obj.type == "FONT":
        return bool(obj.data.body.strip())
    if obj.type == "META":
        return len(obj.data.elements) > 0
    return False


def dependencies(warnings):
    found = []
    for image in bpy.data.images:
        if not image.users or image.source in {"GENERATED", "VIEWER"}:
            continue
        if image.packed_file or len(image.packed_files):
            continue
        if image.source != "FILE":
            warnings.append(f"Image {image.name}: source {image.source} is not audited.")
            continue
        path = Path(bpy.path.abspath(image.filepath, library=image.library))
        found.append({"kind": "image", "name": image.name, "path": str(path),
                      "exists": bool(image.filepath) and path.is_file()})
    for library in bpy.data.libraries:
        if library.packed_file:
            continue
        path = Path(bpy.path.abspath(library.filepath, library=library.parent))
        found.append({"kind": "library", "name": library.name, "path": str(path),
                      "exists": bool(library.filepath) and path.is_file()})
    return found


def render_preview(scene, path):
    ensure_single_scene_render(scene)
    render = scene.render
    previous = (render.filepath, render.image_settings.file_format, render.use_file_extension)
    try:
        render.filepath = str(path)
        render.image_settings.file_format = "PNG"
        render.use_file_extension = True
        bpy.ops.render.render(write_still=True, scene=scene.name)
        if not path.is_file():
            raise RuntimeError("Render did not produce the requested PNG.")
        with path.open("rb") as stream:
            if stream.read(8) != b"\x89PNG\r\n\x1a\n":
                raise RuntimeError("Preview does not have a PNG signature.")
    finally:
        render.filepath, render.image_settings.file_format, render.use_file_extension = previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True)
    parser.add_argument("--preview")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    source = Path(bpy.data.filepath).resolve() if bpy.data.filepath else None
    report_path = output_path(args.report, ".json", source)
    scene = bpy.context.scene
    errors = []
    scope = ("Active scene structure; used FILE image datablocks and linked libraries "
             "throughout this .blend. Packed images/libraries need no external path check.")
    warnings = [
        "Not a full asset audit: UDIM, image sequences, movies, fonts, caches, "
        "Geometry Nodes dependencies are not checked. Requested previews refuse compositor "
        "File Output nodes, multiview and active video sequences; this is not a sandbox.",
        "Geometry checks inspect base data and object.hide_render only; collection/view-layer "
        "exclusion, modifiers, camera framing, visibility and appearance require visual review.",
    ]
    report = {"ok": False, "source": str(source) if source else None,
              "blender_version": bpy.app.version_string, "scene": scene.name,
              "engine": scene.render.engine, "object_count": len(scene.objects),
              "camera": scene.camera.name if scene.camera else None,
              "resolution": {"x": scene.render.resolution_x, "y": scene.render.resolution_y,
                             "percentage": scene.render.resolution_percentage},
              "materials": [material.name for material in bpy.data.materials],
              "frames": {"start": scene.frame_start, "end": scene.frame_end,
                         "current": scene.frame_current},
              "scope": scope, "preview": None, "errors": errors, "warnings": warnings}
    try:
        preview_path = output_path(args.preview, ".png", source) if args.preview else None
        if source is None or not source.is_file():
            errors.append("No existing saved .blend file is loaded.")
        if scene.camera is None or scene.camera.name not in scene.objects:
            errors.append("The active scene must contain its active camera.")
        geometry = [obj.name for obj in scene.objects if has_geometry(obj)]
        report["renderable_geometry"] = geometry
        if not geometry:
            errors.append("No nonempty render-enabled mesh, curve, surface, font or metaball found.")
        report["external_dependencies"] = dependencies(warnings)
        for item in report["external_dependencies"]:
            if not item["exists"]:
                errors.append(f"Missing {item['kind']}: {item['name']} ({item['path']})")
        if preview_path and not errors:
            render_preview(scene, preview_path)
            report["preview"] = str(preview_path)
        elif preview_path:
            warnings.append("Preview skipped because structural or dependency checks failed.")
        else:
            warnings.append("No preview requested; this report does not prove rendering succeeds.")
    except Exception as error:
        errors.append(f"{type(error).__name__}: {error}")
    report["ok"] = not errors
    with report_path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"Scene report: {report_path}")
    if errors:
        raise RuntimeError("Scene validation failed; see the JSON report.")


if __name__ == "__main__":
    main()
