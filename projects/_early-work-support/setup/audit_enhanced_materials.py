"""Inspect connected, in-use material layers and editable finishing nodes."""
from pathlib import Path
import argparse,sys,json
import bpy
p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);bpy.ops.wm.open_mainfile(filepath=str(a.scene))
report={'blender':bpy.app.version_string,'scene':str(a.scene),'materials':[]}
for m in bpy.data.materials:
    if not m.use_nodes or not m.users:continue
    nt=m.node_tree
    starts=[n for n in nt.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output]
    seen=set();todo=list(starts)
    while todo:
        n=todo.pop()
        if n.name in seen:continue
        seen.add(n.name)
        for s in n.inputs:
            todo.extend(link.from_node for link in s.links)
    nodes=[nt.nodes[name] for name in seen]
    mixes=[n for n in nodes if n.bl_idname in {'ShaderNodeMixShader','ShaderNodeMix','ShaderNodeMixRGB'}]
    if mixes:
        report['materials'].append({'name':m.name,'users':m.users,'connected_mix_nodes':[n.name for n in mixes],
            'texture_nodes':sum(n.type.startswith('TEX_') for n in nodes),
            'bump_nodes':sum(n.type=='BUMP' for n in nodes),
            'mask_driven_mix_nodes':sum(any(s.is_linked for s in n.inputs if s.name in {'Fac','Factor'}) for n in mixes)})
scene=bpy.context.scene
nt=scene.compositing_node_group
report['compositor']=[{'type':n.bl_idname,'name':n.name} for n in nt.nodes] if nt else []
report['compositing_enabled']=scene.render.use_compositing
report['lights']=[{'name':o.name,'type':o.data.type,'energy':o.data.energy} for o in scene.objects if o.type=='LIGHT' and not o.hide_render]
report['external_images']=[i.filepath for i in bpy.data.images if i.source=='FILE' and i.users and not i.packed_file]
report['active_mix_materials']=len(report['materials'])
report['connected_mix_node_count']=sum(len(m['connected_mix_nodes']) for m in report['materials'])
report['resolution']=[scene.render.resolution_x,scene.render.resolution_y]
assert report['active_mix_materials']>=5,'Too few in-use layered materials'
assert scene.render.use_compositing,'Compositing disabled in the saved file'
assert any(n['type']=='CompositorNodeGlare' for n in report['compositor']),'Missing editable bloom'
assert any(n['type']=='CompositorNodeHueSat' for n in report['compositor']),'Missing editable saturation grade'
report['status']='passed'
a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in {'materials','lights','compositor'}},ensure_ascii=False))
