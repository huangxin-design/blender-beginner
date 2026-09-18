import bpy,sys,json
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'HuangHuaYu_Outline07_4K.blend'))
s=bpy.context.scene;objects=[o for o in s.objects if o.name.startswith('POINTS /')]
outputs=[]
for o in objects:
    ng=o.modifiers[0].node_group;inst=next(n for n in ng.nodes if n.bl_idname=='GeometryNodeInstanceOnPoints')
    out=next(n for n in ng.nodes if n.type=='GROUP_OUTPUT');original=out.inputs['Geometry'].links[0].from_socket
    store=ng.nodes.new('GeometryNodeStoreNamedAttribute');store.data_type='FLOAT';store.inputs['Name'].default_value='qa_radius'
    ng.links.new(inst.inputs['Points'].links[0].from_socket,store.inputs['Geometry']);ng.links.new(inst.inputs['Scale'].links[0].from_socket,store.inputs['Value'])
    outputs.append((o,ng,out,original,store.outputs[0]))
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'test'
frames=[490] if mode=='test' else list(range(381,470))+list(range(510,586))
records=[];(ROOT/'regions').mkdir(exist_ok=True)
s.render.resolution_percentage=100;s.render.use_border=True;s.render.use_crop_to_border=True
for f in frames:
    s.frame_set(f)
    for o,ng,out,original,point in outputs:ng.links.new(point,out.inputs['Geometry'])
    bpy.context.view_layer.update();coords=[]
    for o,ng,out,original,point in outputs:
        e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
        a=np.array([v.co[:] for v in m.vertices]);r=np.array([v.value for v in m.attributes['qa_radius'].data]);mat=np.array(o.matrix_world)
        coords.append(a[r>1e-8]@mat[:3,:3].T+mat[:3,3]);e.to_mesh_clear()
    world=np.concatenate(coords);cam=np.array(s.camera.matrix_world.inverted());p=world@cam[:3,:3].T+cam[:3,3]
    view=np.array([v[:] for v in s.camera.data.view_frame(scene=s)]);uv=(p[:,:2]-view[:,:2].min(axis=0))/np.ptp(view[:,:2],axis=0)
    # Border uses the original native camera pixel grid; generous overscan retains glow.
    lo=np.maximum(0,np.floor(uv.min(axis=0)*[3072,4096]-100)).astype(int)
    hi=np.minimum([3072,4096],np.ceil(uv.max(axis=0)*[3072,4096]+100)).astype(int)
    lo[0]=(lo[0]//3)*3;hi[0]=min(3072,((hi[0]+2)//3)*3)
    s.render.border_min_x=lo[0]/3072;s.render.border_max_x=hi[0]/3072
    s.render.border_min_y=lo[1]/4096;s.render.border_max_y=hi[1]/4096
    for o,ng,out,original,point in outputs:ng.links.new(original,out.inputs['Geometry'])
    bpy.context.view_layer.update();s.render.filepath=str(ROOT/'regions'/f'bloom_{f:04d}.png')
    bpy.ops.render.render(write_still=True)
    records.append({'frame':f,'x':int(lo[0]),'y_from_bottom':int(lo[1]),'right':int(hi[0]),'top_from_bottom':int(hi[1])})
    (ROOT/'qa'/f'regions-{mode}.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    print('REGION_COMPLETE',f,hi-lo,flush=True)
print('REGION_RENDER_FINISHED',mode,flush=True)
