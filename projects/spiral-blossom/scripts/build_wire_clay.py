"""Shaded white clay with the original petal quad layout; identical animation."""
import bpy
import hashlib
import json
from array import array
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def curves(owner):
    animation = owner.animation_data
    if not animation or not animation.action:
        return []
    return [fc for layer in animation.action.layers for strip in layer.strips
            for bag in strip.channelbags if bag.slot_handle == animation.action_slot.handle
            for fc in bag.fcurves]

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'versions'/'v013'/'scene.blend'))
scene=bpy.context.scene


def digest_collection(collection,prop,width,code='f'):
    values=array(code,[0])*(len(collection)*width)
    collection.foreach_get(prop,values)
    return hashlib.sha256(values.tobytes()).hexdigest()


def snapshot():
    result={'objects':{},'geometry':{},'animation':{}}
    for obj in sorted(scene.objects,key=lambda o:o.name):
        result['objects'][obj.name]={'parent':obj.parent.name if obj.parent else None,
            'matrix':list(v for row in obj.matrix_local for v in row),
            'hidden':[obj.hide_render,obj.hide_viewport],
            'modifiers':[(m.name,m.type,[(p,getattr(m,p)) for p in
                ('levels','render_levels','thickness','offset','uv_smooth') if hasattr(m,p)])
                for m in obj.modifiers]}
    for mesh in bpy.data.meshes:
        result['geometry'][mesh.name]={'co':digest_collection(mesh.vertices,'co',3),
            'indices':digest_collection(mesh.loops,'vertex_index',1,'i'),
            'uv':digest_collection(mesh.uv_layers.active.data,'uv',2) if mesh.uv_layers.active else None}
    for key in bpy.data.shape_keys:
        result['geometry']['shape:'+key.name]=[(k.name,digest_collection(k.data,'co',3)) for k in key.key_blocks]
    for curve in bpy.data.curves:
        result['geometry']['curve:'+curve.name]=[(s.type,
            digest_collection(s.points,'co',4) if s.type!='BEZIER' else digest_collection(s.bezier_points,'co',3))
            for s in curve.splines]
    owners=list(bpy.data.objects)+list(bpy.data.shape_keys)+list(bpy.data.curves)+list(bpy.data.cameras)+[scene]
    for owner in owners:
        result['animation'][owner.id_type+':'+owner.name]=[(c.data_path,c.array_index,
            digest_collection(c.keyframe_points,'co',2)) for c in curves(owner)]
    cam=scene.camera.data
    result['camera']={'object':scene.camera.name,'lens':cam.lens,'sensor_width':cam.sensor_width,
        'clip':[cam.clip_start,cam.clip_end],'dof':[cam.dof.use_dof,cam.dof.aperture_fstop,
        cam.dof.focus_object.name if cam.dof.focus_object else None,cam.dof.focus_distance]}
    result['render']={p:getattr(scene.render,p) for p in ('resolution_x','resolution_y',
        'resolution_percentage','fps','fps_base','use_motion_blur','motion_blur_shutter')}
    result['frames']=[scene.frame_start,scene.frame_end]
    return result


before=snapshot()


def clay(name,color):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    mat.diffuse_color=(*color,1)
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(*color,1)
    bsdf.inputs['Roughness'].default_value=.68
    bsdf.inputs['Specular IOR Level'].default_value=.28
    return mat,bsdf


wire,shader=clay('Clay | original 10 x 22 petal quad lines',(.66,.66,.66))
nodes,links=wire.node_tree.nodes,wire.node_tree.links
uv=nodes.new('ShaderNodeUVMap'); uv.uv_map='Petal UV'
sep=nodes.new('ShaderNodeSeparateXYZ'); links.new(uv.outputs['UV'],sep.inputs[0])


def grid_line(socket,count,inner,outer):
    scale=nodes.new('ShaderNodeMath'); scale.operation='MULTIPLY'
    scale.inputs[1].default_value=count; links.new(socket,scale.inputs[0])
    fract=nodes.new('ShaderNodeMath'); fract.operation='FRACT'; links.new(scale.outputs[0],fract.inputs[0])
    complement=nodes.new('ShaderNodeMath'); complement.operation='SUBTRACT'
    complement.inputs[0].default_value=1; links.new(fract.outputs[0],complement.inputs[1])
    distance=nodes.new('ShaderNodeMath'); distance.operation='MINIMUM'
    links.new(fract.outputs[0],distance.inputs[0]); links.new(complement.outputs[0],distance.inputs[1])
    edge=nodes.new('ShaderNodeMapRange'); edge.interpolation_type='SMOOTHSTEP'; edge.clamp=True
    edge.inputs['From Min'].default_value=inner; edge.inputs['From Max'].default_value=outer
    edge.inputs['To Min'].default_value=1; edge.inputs['To Max'].default_value=0
    links.new(distance.outputs[0],edge.inputs['Value'])
    return edge.outputs['Result']


u=grid_line(sep.outputs['X'],10,.025,.065)
v=grid_line(sep.outputs['Y'],22,.018,.045)
maximum=nodes.new('ShaderNodeMath'); maximum.operation='MAXIMUM'
links.new(u,maximum.inputs[0]); links.new(v,maximum.inputs[1])
mix=nodes.new('ShaderNodeMixRGB'); mix.blend_type='MIX'
mix.inputs[1].default_value=(.66,.66,.66,1)
mix.inputs[2].default_value=(.065,.065,.065,1)
links.new(maximum.outputs[0],mix.inputs[0]); links.new(mix.outputs[0],shader.inputs['Base Color'])
wire['Topology']='Original petal UV grid: 10 quad columns x 22 quad rows; follows native shape keys and subdivision.'
solid,_=clay('Clay | white stem and filaments',(.64,.64,.64))
fuzz,_=clay('Clay | pale trichomes',(.55,.55,.55))
flower_count=0
for obj in scene.objects:
    if not hasattr(obj.data,'materials') or obj.name=='Neutral seamless background':
        continue
    if 'Row' in obj:
        assert len(obj.data.vertices)==5*23*11
        uv_layer=obj.data.uv_layers.get('Petal UV')
        assert uv_layer is not None
        for loop in obj.data.loops:
            vertex=loop.vertex_index%253
            expected=((vertex%11)/10,(vertex//11)/22)
            assert max(abs(a-b) for a,b in zip(uv_layer.data[loop.index].uv,expected))<1e-6
        material=wire
        flower_count+=1
    else:
        material=fuzz if obj.name.startswith('Stem fuzz | band ') else solid
    obj.data.materials.clear(); obj.data.materials.append(material)


def luminance(color):
    return .2126*color[0]+.7152*color[1]+.0722*color[2]


# Neutralize hue while retaining the existing light placements and luminance.
for light in bpy.data.lights:
    y=luminance(light.color); light.color=(y,y,y)
for node in scene.world.node_tree.nodes:
    if node.type=='BACKGROUND':
        y=luminance(node.inputs['Color'].default_value)
        node.inputs['Color'].default_value=(y,y,y,1)
backdrop=bpy.data.objects['Neutral seamless background'].data.materials[0]
for node in backdrop.node_tree.nodes:
    if node.type=='VALTORGB':
        for stop in node.color_ramp.elements:
            y=luminance(stop.color); stop.color=(y,y,y,stop.color[3])

after=snapshot()
assert before==after,'The clay variant must not change geometry, framing or animation.'
scene['V14 appearance']='White clay with grey original petal quad lines and neutral lighting; frame-for-frame match to V13.'
scene.render.filepath='//output/frames/'
(ROOT/'output').mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'output'/'wire-clay-rebuilt.blend'))
(ROOT/'output'/'rebuilt-preservation.json').write_text(json.dumps({'passed':True,
    'matched':['object transforms and parenting','mesh and shape-key coordinates','curve control points',
        'native animation keys','mesh UVs and connectivity','geometry modifiers','camera and DOF',
        'resolution, frame range, fps and motion blur'],
    'flowers_with_verified_original_quad_grid':flower_count,'frames':900,'fps':60,
    'resolution':[1080,1440],'source':'versions/v013/scene.blend',
    'geometry_snapshot_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest()},indent=2),encoding='utf-8')
print('WIRE_CLAY_SAVED',flower_count,flush=True)
