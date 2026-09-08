"""Refuse known extra-output paths before a single scene preview; not a sandbox."""
import bpy


def file_outputs():
    found, visited = [], set()

    def visit(tree):
        if tree is None or tree.as_pointer() in visited:
            return
        visited.add(tree.as_pointer())
        for node in tree.nodes:
            if node.type == "OUTPUT_FILE" or node.bl_idname == "CompositorNodeOutputFile":
                found.append(f"{tree.name}/{node.name}")
            visit(getattr(node, "node_tree", None))

    for scene in bpy.data.scenes:
        visit(getattr(scene, "node_tree", None))
        visit(getattr(scene, "compositing_node_group", None))
    for tree in bpy.data.node_groups:
        if tree.bl_idname == "CompositorNodeTree":
            visit(tree)
    return found


def ensure_single_scene_render(scene):
    outputs = file_outputs()
    if outputs:
        raise RuntimeError("Isolate compositor File Output destinations before rendering: " + ", ".join(outputs))
    if scene.render.use_multiview:
        raise RuntimeError("Isolate multiview output before this single-PNG render.")
    editor = scene.sequence_editor
    strips = getattr(editor, "strips", getattr(editor, "sequences", ())) if editor else ()
    if scene.render.use_sequencer and len(strips):
        raise RuntimeError("An active video sequence can bypass scene rendering; isolate the 3D scene first.")
