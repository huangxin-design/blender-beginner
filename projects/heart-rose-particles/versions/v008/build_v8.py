import bpy, math, json, sys
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from rose_geometry import growing_rose
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/Heart_Text_Wind.blend'))
s=bpy.context.scene; s.frame_set(1)
s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage=3072,4096,100
s.render.pixel_aspect_x=s.render.pixel_aspect_y=1
s.frame_start,s.frame_end,s.render.fps=1,600,30
s.eevee.taa_render_samples=32; s.render.filepath='//frames/bloom_'
camera=s.camera; camera.animation_data_clear(); camera.data.animation_data_clear()
for f,scale in [(1,6.4),(28,6.4),(76,5.55),(600,5.55)]:
    camera.data.ortho_scale=scale; camera.data.keyframe_insert(data_path='ortho_scale',frame=f)
rotation=camera.rotation_euler.to_matrix()
right,up,depth=[np.array(rotation@Vector(v)) for v in ((1,0,0),(0,1,0),(0,0,1))]
center=np.array([.06,0,.48])
objects=[o for o in s.objects if o.name.startswith('POINTS /')]
heart=np.concatenate([np.array([p.co[:] for p in o.data.shape_keys.key_blocks[0].data]) for o in objects])
n=len(heart); rng=np.random.default_rng(810)
rose=growing_rose(n,center,right,up,depth)
print('SCULPTED_ROSE_SAMPLED',n,flush=True)

letters=bpy.data.collections['04 / Typography contours / hidden']
for o in list(letters.objects):bpy.data.objects.remove(o,do_unlink=True)
text_objects=[]
for name,font,width,cy in [('黄花鱼','C:/Windows/Fonts/msyhbd.ttc',3.30,.55),('BLENDER','C:/Windows/Fonts/arialbd.ttf',3.20,-.54)]:
    cu=bpy.data.curves.new(name,'FONT'); cu.body=name; cu.font=bpy.data.fonts.load(font); cu.size=1; cu.resolution_u=12; cu.fill_mode='BOTH'
    o=bpy.data.objects.new(name,cu); letters.objects.link(o)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.convert(target='MESH'); o=bpy.context.object
    a=np.array([v.co[:] for v in o.data.vertices]); low=a.min(axis=0); high=a.max(axis=0)
    factor=width/(high[0]-low[0]); mid=(low+high)*.5
    coords=center+((a[:,0]-mid[0])*factor)[:,None]*right+((a[:,1]-mid[1])*factor+cy)[:,None]*up
    o.data.vertices.foreach_set('co',coords.astype(np.float32).ravel())
    o.hide_render=True; o.hide_set(True); text_objects.append(o)
bpy.data.libraries.write(str(ROOT/'source/YellowCroaker_Text.blend'),set(text_objects),fake_user=True)
triangles=[]; areas=[]
for o in text_objects:
    o.data.calc_loop_triangles(); vv=np.array([v.co[:] for v in o.data.vertices])
    tri=vv[np.array([t.vertices[:] for t in o.data.loop_triangles])]
    triangles.extend(tri); areas.extend(np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)*.5)
triangles=np.asarray(triangles); areas=np.asarray(areas)
tri=triangles[rng.choice(len(triangles),n,p=areas/areas.sum())]
a=np.sqrt(rng.random(n))[:,None]; b=rng.random(n)[:,None]
text=(1-a)*tri[:,0]+a*(1-b)*tri[:,1]+a*b*tri[:,2]+rng.uniform(-.018,.018,(n,1))*depth
def order(points):
    uv=points@np.array([right,up]).T; uv=(uv-uv.min(axis=0))/(uv.max(axis=0)-uv.min(axis=0))
    q=np.minimum(1023,(uv*1023).astype(np.uint32)); code=np.zeros(len(q),np.uint32)
    for bit in range(10):
        code|=((q[:,0]>>bit)&1)<<(2*bit); code|=((q[:,1]>>bit)&1)<<(2*bit+1)
    return np.argsort(code,kind='stable')
mapping=np.empty(n,dtype=int); mapping[order(heart)]=order(rose['bud'])
for name in ('seed','bud','open','group','color','energy','birth','visibility'):rose[name]=rose[name][mapping]
mapped_text=np.empty_like(text); mapped_text[order(rose['open'])]=text[order(text)]
def key(sk,values):
    for f,v in values:sk.value=v; sk.keyframe_insert(data_path='value',frame=f)
def socket(sock,values):
    for f,v in values:sock.default_value=v; sock.keyframe_insert(data_path='default_value',frame=f)
def attribute(mesh,name,kind,values):
    a=mesh.attributes.new(name,kind,'POINT'); field={'FLOAT':'value','FLOAT_COLOR':'color','FLOAT_VECTOR':'vector'}[kind]
    a.data.foreach_set(field,np.asarray(values,np.float32).ravel())
offset=0; ends=[]; materials=set()
for o in objects:
    mesh=o.data; count=len(mesh.vertices); sl=slice(offset,offset+count); offset+=count
    keys=mesh.shape_keys; keys.animation_data_clear(); text_key=keys.key_blocks[1]; text_key.name='Text / 黄花鱼 / BLENDER'
    seed=o.shape_key_add(name='Growth / seed'); seed.data.foreach_set('co',rose['seed'][sl].astype(np.float32).ravel())
    bud=o.shape_key_add(name='Growth / stem and closed bud'); bud.relative_key=seed; bud.data.foreach_set('co',rose['bud'][sl].astype(np.float32).ravel())
    key(seed,[(1,0),(145,0),(167,.18),(187,.72),(207,1),(600,1)])
    key(bud,[(1,0),(185,0),(210,.22),(235,.69),(261,1),(600,1)])
    for group,start,end in [(0,214,280),(1,271,324),(2,287,343),(3,303,357),(4,313,364)]:
        opened=o.shape_key_add(name=f'Bloom / layer {group}')
        opened.relative_key=bud; coords=rose['bud'][sl].copy(); mask=rose['group'][sl]==group
        coords[mask]=rose['open'][sl][mask]; opened.data.foreach_set('co',coords.astype(np.float32).ravel())
        key(opened,[(1,0),(start,0),(end,1),(600,1)])
    reference=o.shape_key_add(name='REFERENCE / fully open rose'); reference.data.foreach_set('co',rose['open'][sl].astype(np.float32).ravel()); reference.value=0
    text_key.relative_key=reference; text_key.data.foreach_set('co',mapped_text[sl].astype(np.float32).ravel())
    key(text_key,[(1,0),(380,0),(403,.13),(431,.54),(457,.94),(470,1),(600,1)])
    attribute(mesh,'rose_color','FLOAT_COLOR',np.column_stack([rose['color'][sl],np.ones(count)]))
    attribute(mesh,'rose_energy','FLOAT',rose['energy'][sl])
    attribute(mesh,'rose_birth','FLOAT',rose['birth'][sl])
    for i in range(len(rose['pose_frames'])):attribute(mesh,f'rose_visible_{i}','FLOAT',rose['visibility'][sl,i])
    ng=o.modifiers[0].node_group; ng.animation_data_clear(); nodes=ng.nodes; links=ng.links
    socket(nodes['Dispersion'].outputs[0],[(1,.96),(22,1.1),(43,.73),(76,0),(145,0),(173,.28),(197,.17),(230,.016),(250,0),(380,0),(407,.25),(435,.29),(458,.02),(470,0),(600,0)])
    socket(nodes['Particle size envelope'].outputs[0],[(1,1.04),(76,1),(145,1),(180,.88),(215,.82),(270,1.03),(380,1.03),(420,1.02),(470,.82),(600,.82)])
    for nd in nodes:
        if nd.bl_idname=='ShaderNodeTexNoise':nd.inputs['W'].driver_add('default_value').driver.expression='.042*frame + .17*sin(frame*.065)'
        if nd.bl_idname=='GeometryNodeSetMaterial':materials.add(nd.inputs['Material'].default_value)
    def calc(op,a,b):
        nd=nodes.new('ShaderNodeMath'); nd.operation=op; nd.label='GROWTH / '+op
        for i,v in enumerate((a,b)):
            if isinstance(v,(float,int)):nd.inputs[i].default_value=v
            else:links.new(v,nd.inputs[i])
        return nd.outputs[0]
    birth=nodes.new('GeometryNodeInputNamedAttribute'); birth.data_type='FLOAT'; birth.inputs['Name'].default_value='rose_birth'
    time=nodes['WIND / scene time'].outputs['Frame']
    age=calc('MINIMUM',calc('MAXIMUM',calc('DIVIDE',calc('SUBTRACT',time,birth.outputs['Attribute']),12),0),1)
    visible=calc('MULTIPLY',calc('MULTIPLY',age,age),calc('SUBTRACT',3,calc('MULTIPLY',age,2)))
    presence=nodes.new('ShaderNodeValue'); presence.name='GROWTH / presence'
    socket(presence.outputs[0],[(1,0),(145,0),(190,.80),(215,1),(600,1)])
    fields=[]
    for i in range(len(rose['pose_frames'])):
        attr=nodes.new('GeometryNodeInputNamedAttribute'); attr.data_type='FLOAT'; attr.inputs['Name'].default_value=f'rose_visible_{i}'; fields.append(attr.outputs['Attribute'])
    occlusion=fields[0]
    for i in range(1,len(fields)):
        blend=nodes.new('ShaderNodeValue'); blend.name=f'PETALS / visibility blend {i}'
        socket(blend.outputs[0],[(1,0),(rose['pose_frames'][i-1],0),(rose['pose_frames'][i],1),(600,1)])
        occlusion=calc('ADD',occlusion,calc('MULTIPLY',calc('SUBTRACT',fields[i],fields[i-1]),blend.outputs[0]))
    # Restore every particle when the rose becomes text.
    release=nodes.new('ShaderNodeValue'); release.name='PETALS / release to text'
    socket(release.outputs[0],[(1,0),(380,0),(421,1),(600,1)])
    occlusion=calc('ADD',occlusion,calc('MULTIPLY',calc('SUBTRACT',1,occlusion),release.outputs[0]))
    visible=calc('MULTIPLY',visible,occlusion)
    factor=calc('ADD',calc('SUBTRACT',1,presence.outputs[0]),calc('MULTIPLY',presence.outputs[0],visible))
    inst=next(nd for nd in nodes if nd.bl_idname=='GeometryNodeInstanceOnPoints')
    original=inst.inputs['Scale'].links[0].from_socket; links.new(calc('MULTIPLY',original,factor),inst.inputs['Scale'])
    x=(mapped_text[sl]-center)@right
    onset=509+16*np.clip((x+1.75)/3.5,0,1)+rng.uniform(0,18,count); lifetime=rng.uniform(1.05,1.48,count)
    mesh.attributes['wind_onset'].data.foreach_set('value',onset.astype(np.float32)); mesh.attributes['wind_lifetime'].data.foreach_set('value',lifetime.astype(np.float32)); ends.extend(onset+30*lifetime)
    for name in ('wind_velocity','wind_flutter'):
        a=mesh.attributes[name]; values=np.array([v.vector[:] for v in a.data],np.float32); a.data.foreach_set('vector',(values*1.12).ravel())

for mat in materials:
    nodes=mat.node_tree.nodes; links=mat.node_tree.links
    for nd in nodes:
        if nd.type=='TEX_NOISE' and nd.noise_dimensions=='4D':nd.inputs['W'].driver_add('default_value').driver.expression='.010*frame+.09*sin(frame*.07)'
    out=next(nd for nd in nodes if nd.type=='OUTPUT_MATERIAL'); old=out.inputs['Surface'].links[0].from_socket
    color=nodes.new('ShaderNodeAttribute'); color.attribute_name='rose_color'; color.attribute_type='INSTANCER'
    strength=nodes.new('ShaderNodeAttribute'); strength.attribute_name='rose_energy'; strength.attribute_type='INSTANCER'
    emission=nodes.new('ShaderNodeEmission'); links.new(color.outputs['Color'],emission.inputs['Color']); links.new(strength.outputs['Fac'],emission.inputs['Strength'])
    mix=nodes.new('ShaderNodeMixShader'); mix.label='Rose shading / soft crimson and gold'
    socket(mix.inputs[0],[(1,0),(170,0),(235,1),(380,1),(443,0),(600,0)])
    links.new(old,mix.inputs[1]); links.new(emission.outputs[0],mix.inputs[2]); links.new(mix.outputs[0],out.inputs['Surface'])

def smooth(a,b,f):
    t=max(0,min(1,(f-a)/(b-a))); return t*t*(3-2*t)
root=bpy.data.objects['ANIMATION / heartbeat']; root.animation_data_clear()
for f in range(1,601):
    phase=((f-1)/24)%1; beat=math.exp(-((phase-.12)/.07)**2)+.56*math.exp(-((phase-.31)/.10)**2); weight=1-smooth(145,241,f)
    root.scale=(1+.061*beat*weight,1+.046*beat*weight,1-.031*beat*weight)
    root.rotation_euler=(.023*math.sin(f*.013)*weight,.045*math.sin(f*.017)*weight,(-.045+.12*math.sin(f*.014))*weight)
    root.location=(0,0,.028*math.sin(f*.025)*weight)
    for prop in ('scale','rotation_euler','location'):root.keyframe_insert(data_path=prop,frame=f)
s.timeline_markers.clear()
for name,f in [('Heart gathering',1),('Heart beat',76),('Heart becomes seed',145),('Stem grows',207),('Closed rose bud',261),('Petals unfold',281),('Rose fully open',364),('Rose to lettering',380),('黄花鱼 / BLENDER',470),('Wind fade',510),('Black ending',589)]:s.timeline_markers.new(name,frame=f)
s.name='黄花鱼 BLENDER / Growing rose / V08'
s['Design']='Anatomical heart to a growing stem, closed rose bud and sequentially opening cupped petals; two-line Chinese/English particle lettering, then wind fade.'
s['Typography']='黄花鱼\nBLENDER'; s['Particle count']=n
s['Playback']='3072x4096 native / 3:4 / 30 fps / 600 frames / 20 seconds / silent'
s.frame_set(367)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'HuangHuaYu_Growing_Rose_4K.blend'))
report={'resolution':[3072,4096],'aspect':'3:4','fps':30,'frames':600,'particles':n,'petals':rose['petals'],'text':'黄花鱼\nBLENDER','last_particle_end_frame':float(max(ends)),'growth':'Stem extends first; compound leaves unfold; closed bud opens in four staggered petal layers.','camera_visible_surface_sampling':True}
(ROOT/'qa/build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('V8_BUILD_COMPLETE',report,flush=True)
