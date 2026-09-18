import bpy,json
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'HuangHuaYu_Outline07_4K.blend'))
s=bpy.context.scene
assert (s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage)==(3072,4096,100)
assert (s.frame_start,s.frame_end,s.render.fps)==(1,600,30)
assert s['Typography']=='黄花鱼\nBLENDER'
objects=[o for o in s.objects if o.name.startswith('POINTS /')]
assert sum(len(o.data.vertices) for o in objects)==67579
assert len([o for o in s.objects if o.name.startswith('Rose / cupped petal')])==21
assert not [o for o in s.objects if o.name.startswith(('FLOW /','STREAK /','SHOCK /','VORTEX /'))]
starts=np.concatenate([np.array([v.value for v in o.data.attributes['wind_onset'].data]) for o in objects])
lives=np.concatenate([np.array([v.value for v in o.data.attributes['wind_lifetime'].data]) for o in objects])
assert starts.min()>509 and (starts+30*lives).max()<588
framing=[]
for f,shape in [(105,'Heart'),(145,'Heart'),(367,'REFERENCE / fully open rose'),(490,'Text / 黄花鱼 / BLENDER')]:
    s.frame_set(f); bpy.context.view_layer.update()
    view=np.array([v[:] for v in s.camera.data.view_frame(scene=s)])
    cam=np.array(s.camera.matrix_world.inverted()); world=[]
    for o in objects:
        keys=o.data.shape_keys.key_blocks
        assert keys[1].relative_key==keys['REFERENCE / fully open rose']
        coords=np.array([v.co[:] for v in keys[shape].data]); m=np.array(o.matrix_world)
        world.append(coords@m[:3,:3].T+m[:3,3])
    local=np.concatenate(world)@cam[:3,:3].T+cam[:3,3]
    uv=(local[:,:2]-view[:,:2].min(axis=0))/(view[:,:2].max(axis=0)-view[:,:2].min(axis=0))
    assert uv.min()>.04 and uv.max()<.96
    if shape=='Heart':assert .70<np.ptp(uv[:,1])<.86
    framing.append({'frame':f,'shape':shape,'bounds_normalized':[uv.min(axis=0).tolist(),uv.max(axis=0).tolist()]})
# Check the evaluated shape before Geometry Nodes against each intended target.
for o in objects:o.modifiers[0].show_viewport=False
shape_checks=[]
for f,shape in [(367,'REFERENCE / fully open rose'),(490,'Text / 黄花鱼 / BLENDER')]:
    s.frame_set(f); bpy.context.view_layer.update(); errors=[]
    for o in objects:
        evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=evaluated.to_mesh()
        actual=np.array([v.co[:] for v in mesh.vertices]); expected=np.array([v.co[:] for v in o.data.shape_keys.key_blocks[shape].data])
        errors.append(float(np.abs(actual-expected).max())); evaluated.to_mesh_clear()
    assert max(errors)<1e-5
    shape_checks.append({'frame':f,'max_coordinate_error':max(errors)})
assert not [im for im in bpy.data.images if im.source=='FILE' and im.users]
report={'resolution':[3072,4096],'fps':30,'frames':600,'particles':67579,'rose_petals':21,'text':'黄花鱼\nBLENDER','framing':framing,'shape_checks':shape_checks,'wind_onset_range':[float(starts.min()),float(starts.max())],'last_particle_end_frame':float((starts+30*lives).max()),'external_bitmap_dependencies':0,'extra_orbits':0}
(ROOT/'qa/source-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('SOURCE_CHECK_PASS',report,flush=True)
