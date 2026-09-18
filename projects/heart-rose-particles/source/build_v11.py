import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/Heart_Rose_V8.blend'))
s=bpy.context.scene;s.frame_set(490)
data=np.load(ROOT/'source/title_targets.npz')
xy=data['pixels'];energy=data['energy'];edge=data['edge'];rng=np.random.default_rng(1107)
rotation=s.camera.rotation_euler.to_matrix()
right,up,depth=[np.array(rotation@Vector(v)) for v in ((1,0,0),(0,1,0),(0,0,1))]
center=np.array([.06,0,.48]);view=np.array([v[:] for v in s.camera.data.view_frame(scene=s)])
span=np.ptp(view[:,:2],axis=0)
target=center+((xy[:,0]+.5)/3072-.5)[:,None]*span[0]*right+(.5-(xy[:,1]+.5)/4096)[:,None]*span[1]*up+rng.uniform(-.0005,.0005,(len(xy),1))*depth
objects=[o for o in s.objects if o.name.startswith('POINTS /')]
rose=np.concatenate([np.array([v.co[:] for v in o.data.shape_keys.key_blocks['REFERENCE / fully open rose'].data]) for o in objects])
def order(points):
    uv=points@np.array([right,up]).T; uv=(uv-uv.min(axis=0))/np.ptp(uv,axis=0)
    q=np.minimum(1023,(uv*1023).astype(np.uint32));code=np.zeros(len(q),np.uint32)
    for bit in range(10):code|=((q[:,0]>>bit)&1)<<(2*bit);code|=((q[:,1]>>bit)&1)<<(2*bit+1)
    return np.argsort(code,kind='stable')
mapping=np.empty(len(target),int);mapping[order(rose)]=order(target)
target=target[mapping];energy=energy[mapping];edge=edge[mapping]
def animate(sock,values):
    for f,v in values:sock.default_value=v;sock.keyframe_insert(data_path='default_value',frame=f)
def attr(mesh,name,kind,values):
    a=mesh.attributes.new(name,kind,'POINT');a.data.foreach_set('value' if kind=='FLOAT' else 'color',np.asarray(values,np.float32).ravel())
offset=0;mats=set();ends=[]
for o in objects:
    n=len(o.data.vertices);sl=slice(offset,offset+n);offset+=n
    o.data.shape_keys.key_blocks['Text / 黄花鱼 / BLENDER'].data.foreach_set('co',target[sl].astype(np.float32).ravel())
    attr(o.data,'outline_energy','FLOAT',energy[sl]);attr(o.data,'outline_edge','FLOAT',edge[sl])
    colors=np.tile([.58,.40,.37,1.],(n,1));attr(o.data,'outline_color','FLOAT_COLOR',colors)
    ng=o.modifiers[0].node_group
    random=ng.nodes['Random Value'];low=random.inputs['Min'].default_value;high=random.inputs['Max'].default_value
    animate(random.inputs['Min'],[(1,low),(380,low),(470,.00125),(600,.00125)])
    animate(random.inputs['Max'],[(1,high),(380,high),(470,.00175),(600,.00175)])
    for nd in ng.nodes:
        if nd.bl_idname=='GeometryNodeSetMaterial':mats.add(nd.inputs['Material'].default_value)
    # Use the new text's horizontal position for the same left-to-right wind release.
    x=(target[sl]-center)@right
    onset=509+16*np.clip((x+1.3)/2.6,0,1)+rng.uniform(0,18,n)
    lifetime=rng.uniform(1.05,1.48,n)
    o.data.attributes['wind_onset'].data.foreach_set('value',onset.astype(np.float32))
    o.data.attributes['wind_lifetime'].data.foreach_set('value',lifetime.astype(np.float32))
    ends.extend(onset+30*lifetime)
for mat in mats:
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');old=output.inputs['Surface'].links[0].from_socket
    col=nodes.new('ShaderNodeAttribute');col.attribute_type='INSTANCER';col.attribute_name='outline_color'
    strength=nodes.new('ShaderNodeAttribute');strength.attribute_type='INSTANCER';strength.attribute_name='outline_energy'
    emission=nodes.new('ShaderNodeEmission');links.new(col.outputs['Color'],emission.inputs['Color']);links.new(strength.outputs['Fac'],emission.inputs['Strength'])
    mix=nodes.new('ShaderNodeMixShader');mix.name='TITLE / selected 07 fine outline'
    animate(mix.inputs[0],[(1,0),(380,0),(420,.45),(455,1),(600,1)])
    links.new(old,mix.inputs[1]);links.new(emission.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs['Surface'])
# The title is sampled from the approved raster masks; no replacement font dependency.
for o in list(bpy.data.collections['04 / Typography contours / hidden'].objects):bpy.data.objects.remove(o,do_unlink=True)
s.name='黄花鱼 BLENDER / 07 璃光细线 / V11'
s['Selected typography']='07 璃光细线 / approved raster mask / pink-champagne particle contours'
s['Typography']='黄花鱼\nBLENDER';s['Title revision']='Only text destinations, late particle size, late title shading, and wind-release order changed.'
s.frame_start=1;s.frame_end=600;s.render.resolution_percentage=100;s.render.filepath='//frames/bloom_'
s.frame_set(490)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'HuangHuaYu_Outline07_4K.blend'))
report={'selected_style':'07 璃光细线','resolution':[3072,4096],'fps':30,'frames':600,'duration':20,'particles':len(target),'last_particle_end_frame':float(max(ends)),'first_changed_frame':381,'title_fully_formed_frame':470,'source_mask':'source/07_styled_mask.png','new_font_files':0}
(ROOT/'qa/build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('V11_BUILD_COMPLETE',report,flush=True)
