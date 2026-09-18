import bpy,json
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def samples(path,frames):
    bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene
    objects=[o for o in s.objects if o.name.startswith('POINTS /')]
    for o in objects:
        ng=o.modifiers[0].node_group;inst=next(n for n in ng.nodes if n.bl_idname=='GeometryNodeInstanceOnPoints')
        save=ng.nodes.new('GeometryNodeStoreNamedAttribute');save.data_type='FLOAT';save.inputs['Name'].default_value='qa_radius'
        ng.links.new(inst.inputs['Points'].links[0].from_socket,save.inputs['Geometry'])
        ng.links.new(inst.inputs['Scale'].links[0].from_socket,save.inputs['Value'])
        ng.links.new(save.outputs[0],next(n for n in ng.nodes if n.type=='GROUP_OUTPUT').inputs['Geometry'])
    out={}
    for f in frames:
        s.frame_set(f);bpy.context.view_layer.update();positions=[];radii=[]
        for o in objects:
            e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
            positions.extend([tuple(o.matrix_world@v.co) for v in m.vertices]);radii.extend([a.value for a in m.attributes['qa_radius'].data]);e.to_mesh_clear()
        out[f]=(np.array(positions),np.array(radii),np.array(s.camera.matrix_world),s.camera.data.ortho_scale)
    return out
old=samples(ROOT/'source/Heart_Rose_V8.blend',[105,367,380])
new=samples(ROOT/'HuangHuaYu_Outline07_4K.blend',[105,367,380,470,490,509,586,588,600])
checks=[]
for f in old:
    pos=np.max(np.abs(old[f][0]-new[f][0]));rad=np.max(np.abs(old[f][1]-new[f][1]))
    assert pos<1e-7 and rad<1e-8 and np.array_equal(old[f][2],new[f][2]) and old[f][3]==new[f][3]
    checks.append({'frame':f,'max_world_position_difference':float(pos),'max_radius_difference':float(rad),'camera_identical':True})
for f in (470,509):
    assert np.max(np.abs(new[f][0]-new[490][0]))<1e-7
    assert np.max(np.abs(new[f][1]-new[490][1]))<1e-8
for f in (586,588,600):assert new[f][1].max()==0
(ROOT/'qa/prefix-state.json').write_text(json.dumps({'pre_title_state_checks':checks,'title_static_frames':[470,509],'verified_zero_radius_frames':[586,588,600]},indent=2),encoding='utf-8')
print('PREFIX_AND_STATIC_HOLDS_VERIFIED',checks,flush=True)
