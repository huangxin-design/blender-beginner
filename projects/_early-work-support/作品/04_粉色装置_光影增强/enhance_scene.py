"""Relight the existing sculpture and build editable layered material networks."""
import bpy, json, sys, time, hashlib
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent
SOURCE=OUT.parent/'01_粉色装置'/'01_粉色装置.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
s=bpy.context.scene
def geometry_signature():
    return {o.name:{'type':o.type,'matrix':[list(row) for row in o.matrix_world],'data':o.data.name if o.data else None} for o in s.objects if o.type!='LIGHT'}
before_geometry=geometry_signature()
changes=[]

class Layered:
    def __init__(self,name):
        self.m=bpy.data.materials[name];self.n=self.m.node_tree.nodes;self.n.clear();self.l=self.m.node_tree.links
        self.out=self.node('ShaderNodeOutputMaterial','Material output',(800,100))
        self.coord=self.node('ShaderNodeTexCoord','Local material coordinates',(-1000,100))
    def node(self,kind,name,pos):
        n=self.n.new(kind);n.name=name;n.label=name;n.location=pos;return n
    def link(self,a,b):self.l.new(a,b)
    def noise(self,name,scale,pos=(-780,100)):
        n=self.node('ShaderNodeTexNoise',name,pos);n.inputs['Scale'].default_value=scale;n.inputs['Detail'].default_value=2
        self.link(self.coord.outputs['Generated'],n.inputs['Vector']);return n
    def ramp(self,name,source,c0,c1,pos=(-550,100)):
        n=self.node('ShaderNodeValToRGB',name,pos);n.color_ramp.elements[0].color=(*c0,1);n.color_ramp.elements[1].color=(*c1,1)
        self.link(source,n.inputs[0]);return n.outputs['Color']
    def shader(self,name,color,rough,pos=(0,100),metal=0):
        p=self.node('ShaderNodeBsdfPrincipled',name,pos);p.inputs['Base Color'].default_value=(*color,1)
        p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return p
    def bump(self,name,source,strength,distance,pos=(-260,-220)):
        b=self.node('ShaderNodeBump',name,pos);b.inputs['Strength'].default_value=strength;b.inputs['Distance'].default_value=distance
        self.link(source,b.inputs['Height']);return b.outputs['Normal']
    def mix(self,name,a,b,factor):
        m=self.node('ShaderNodeMixShader',name,(560,100));self.link(a.outputs[0],m.inputs[1]);self.link(b.outputs[0],m.inputs[2])
        if isinstance(factor,(int,float)):m.inputs[0].default_value=factor
        else:self.link(factor,m.inputs[0])
        self.link(m.outputs[0],self.out.inputs['Surface']);return m
    def fresnel(self,lo,hi):
        f=self.node('ShaderNodeFresnel','Glaze grazing angle',(-520,520));f.inputs['IOR'].default_value=1.46
        return self.ramp('Editable layer thickness mask',f.outputs[0],(lo,)*3,(hi,)*3,(-270,520))

def ceramic(name,c0,c1,rough=.28,coat=.11,sss=.02):
    a=Layered(name);noise=a.noise('Subtle fired pigment variation',5)
    pigment=a.ramp('Two ceramic pigment tones',noise.outputs['Fac'],c0,c1)
    body=a.shader('Ceramic body / soft scattering',c0,rough,(0,120));body.inputs['Subsurface Weight'].default_value=sss
    body.inputs['Subsurface Scale'].default_value=.08
    glaze=a.shader('Clear fired glaze',c1,coat,(280,-180));glaze.inputs['Coat Weight'].default_value=.70;glaze.inputs['Coat Roughness'].default_value=.07
    for p in [body,glaze]:a.link(pigment,p.inputs['Base Color'])
    pores=a.noise('Microscopic glaze pores',280,(-780,-320));normal=a.bump('Sub-pixel ceramic relief',pores.outputs['Fac'],.10,.0018)
    a.link(normal,body.inputs['Normal'])
    a.mix('MIX ceramic body + angle weighted glaze',body,glaze,a.fresnel(.12,.58))
    changes.append({'material':name,'layers':['Pigment tones','Ceramic body','Angle weighted clear glaze','Microscopic pores']})

def silicone(name,c0,c1,gloss=.16):
    a=Layered(name);noise=a.noise('Soft pigment variation',4)
    dye=a.ramp('Deep and light silicone dye',noise.outputs['Fac'],c0,c1)
    body=a.shader('Pigmented silicone / subsurface body',c0,.36,(0,100));body.inputs['Subsurface Weight'].default_value=.075
    body.inputs['Subsurface Scale'].default_value=.09
    clear=a.shader('Thin clear soft-touch finish',c1,gloss,(260,-190));clear.inputs['Coat Weight'].default_value=.75;clear.inputs['Coat Roughness'].default_value=.065
    for p in [body,clear]:a.link(dye,p.inputs['Base Color'])
    pores=a.noise('Fine rubber micro-pores',230,(-780,-300));normal=a.bump('Soft micro-pore relief',pores.outputs[0],.14,.0020)
    a.link(normal,body.inputs['Normal'])
    a.mix('MIX subsurface silicone + clear finish',body,clear,a.fresnel(.12,.40))
    changes.append({'material':name,'layers':['Pigmented SSS silicone','Thin clear finish','Angle mask','Micro pores']})

def metal(name,color):
    a=Layered(name)
    clean=a.shader('Clean polished metal',color,.105,(0,100),1)
    brushed=a.shader('Directional brushed metal',color,.29,(250,-190),1);brushed.inputs['Anisotropic'].default_value=.60
    scale=a.node('ShaderNodeVectorMath','Longitudinal scratch direction',(-810,-280));scale.operation='MULTIPLY';scale.inputs[1].default_value=(900,900,3)
    a.link(a.coord.outputs['Generated'],scale.inputs[0])
    grain=a.noise('Fine elongated machining scratches',1,(-600,-280));a.link(scale.outputs[0],grain.inputs['Vector'])
    a.link(a.bump('Microscopic brushed relief',grain.outputs[0],.12,.0007,(-320,-230)),brushed.inputs['Normal'])
    wear=a.noise('Sparse polished and brushed patches',6,(-790,350))
    mask=a.ramp('Clean / brushed surface ratio',wear.outputs[0],(.18,)*3,(.48,)*3,(-480,350))
    a.mix('MIX polished + micro-scratched metal',clean,brushed,mask)
    changes.append({'material':name,'layers':['Clean polished metal','Directional brushed metal','Sparse finish mask','Micro scratches']})

silicone('Coral ribbed rubber',(.53,.045,.019),(.86,.13,.04),.23)
silicone('Glossy soft pink sculptural ring',(.69,.13,.24),(.98,.30,.45),.075)
ceramic('Powder blue lacquer',(.17,.35,.72),(.25,.47,.88))
ceramic('Sky blue eye helmets',(.11,.43,.81),(.22,.63,.98),.25,.085)
ceramic('Grey sage pearls',(.25,.37,.29),(.36,.49,.38),.22,.065,.06)
ceramic('Ivory glass ceramic',(.76,.85,.76),(.97,1,.95),.23,.09)
metal('Brushed warm silver',(.79,.82,.86))
metal('Satin champagne gold',(.79,.47,.16))
metal('Fine warm brass',(.58,.29,.055))

a=Layered('Peach velvet');grain=a.noise('Broad soft peach pigment',5)
dye=a.ramp('Deep peach and candy pink fibres',grain.outputs[0],(.86,.23,.24),(1.0,.41,.34))
body=a.shader('Dense velvet body / fine grain',(.9,.3,.3),.77,(0,100));body.inputs['Subsurface Weight'].default_value=.055;body.inputs['Sheen Weight'].default_value=.7
nap=a.shader('Fine raised velvet nap',(.96,.48,.38),.88,(260,-170));nap.inputs['Sheen Weight'].default_value=1
for p in [body,nap]:a.link(dye,p.inputs['Base Color'])
micro=a.noise('Fine felt grain',180,(-780,-300));a.link(a.bump('Velvet micro relief',micro.outputs[0],.22,.003),body.inputs['Normal'])
facing=a.node('ShaderNodeLayerWeight','Velvet grazing response',(-540,480))
mask=a.ramp('Fine nap over dense velvet',facing.outputs['Facing'],(.12,)*3,(.42,)*3,(-260,460))
a.mix('MIX dense velvet + fine raised nap',body,nap,mask)
changes.append({'material':'Peach velvet','layers':['Deep/light peach pigment','Dense velvet','Grazing fine nap','Fine felt grain']})
a=Layered('Peach fibres');grain=a.noise('Individual fibre tint variation',18)
color=a.ramp('Root peach / lit peach fibre blend',grain.outputs[0],(.81,.32,.28),(1,.56,.45))
p=a.shader('Actual short peach fibres',(.9,.4,.3),.9);p.inputs['Sheen Weight'].default_value=1;a.link(color,p.inputs['Base Color']);a.link(p.outputs[0],a.out.inputs['Surface'])
changes.append({'material':'Peach fibres','layers':['Fine / coarse colour variation on 23000 real strands']})

# Keep the saved plinth colour while replacing its self-lit front with softboxes.
stage=bpy.data.materials['Background | rose quartz'].node_tree.nodes.get('Principled BSDF')
stage.inputs['Emission Strength'].default_value=.025

# Directional soft illumination; the narrow cards are linked only to metal.
old_lights=[{'name':o.name,'power':o.data.energy,'size':o.data.size} for o in s.objects if o.type=='LIGHT']
for o in list(s.objects):
    if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
lighting=bpy.data.collections.new('04 Directional studio lighting');s.collection.children.link(lighting)
metal_receivers=bpy.data.collections.new('04 Metal reflection receivers')
for o in s.objects:
    if o.type in {'MESH','CURVE'} and any(m and m.name in ['Brushed warm silver','Satin champagne gold','Fine warm brass'] for m in o.data.materials):metal_receivers.objects.link(o)
stage_receivers=bpy.data.collections.new('04 Pink plinth receivers');stage_receivers.objects.link(s.objects['Large rose display plinth'])
light_report=[]
def area(name,loc,target,power,width,height,color=(1,1,1),receivers=None):
    data=bpy.data.lights.new(name,'AREA');data.shape='RECTANGLE';data.energy=power;data.size=width;data.size_y=height;data.color=color
    o=bpy.data.objects.new(name,data);lighting.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    if receivers:o.light_linking.receiver_collection=receivers
    light_report.append({'name':name,'location':loc,'power':power,'width':width,'height':height,'color':color,'receivers':receivers.name if receivers else 'scene'})
area('KEY - warm left window',(-4.8,-5.5,10.2),(.1,0,4.2),2250,3.6,4.5,(1,.90,.82))
area('FILL - restrained cool front',(5,-5,5.4),(.1,0,3.9),450,4.5,5,(.82,.89,1))
area('RIM - cool right separation',(4.4,2.4,7.5),(.2,0,4.2),1550,2.6,4,(.83,.91,1))
area('RIM - warm velvet edge',(-2.5,3.4,9.8),(-.2,0,3.7),1050,3.0,3.5,(1,.84,.70))
area('METAL - large left reflection strip',(-3.6,-6.2,3.8),(-.9,-1,2.5),1100,1.3,6,(1,1,1),metal_receivers)
area('METAL - narrow right highlight',(4.1,-4.9,4.6),(-.6,-1,3),650,.65,5,(.88,.94,1),metal_receivers)
area('STAGE - broad front card',(-1,-8,.9),(0,1,-.7),1200,5.8,5.5,(1,.94,.92),stage_receivers)
area('STAGE - right candy gradient',(5,-6,1.8),(3,0,-.5),1650,3.8,5,(1,.87,.89),stage_receivers)
s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.70,.77,.90,1)
s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.10

assert before_geometry==geometry_signature(),'Geometry or camera changed unexpectedly'
s.render.engine='CYCLES';s.cycles.device='GPU';s.cycles.samples=128;s.cycles.use_denoising=True
s.cycles.max_bounces=12;s.cycles.glossy_bounces=6;s.cycles.transmission_bounces=6
s.render.resolution_x=1080;s.render.resolution_y=1048;s.render.resolution_percentage=100
s.render.film_transparent=False;s.use_nodes=False
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=0;s.view_settings.gamma=1
s.render.image_settings.file_format='OPEN_EXR';s.render.image_settings.color_depth='32';s.render.image_settings.color_mode='RGBA';s.render.image_settings.exr_codec='ZIP'
s.render.filepath=str(OUT/'beauty_linear.exr')
s['enhancement']='Directional lighting and editable mixed material layers only; no geometry edits; no grading or glare baked into EXR.'
s['source_blend']=str(SOURCE)
mix_report=[]
for change in changes:
    nodes=bpy.data.materials[change['material']].node_tree.nodes
    change['mix_nodes']=[n.name for n in nodes if n.bl_idname in {'ShaderNodeMixShader','ShaderNodeMixRGB','ShaderNodeMix'}]
    change['node_count']=len(nodes)
    mix_report.extend(change['mix_nodes'])
report={'source':str(SOURCE),'geometry_and_camera_unchanged':True,'non_light_objects':len(before_geometry),'old_lights':old_lights,'new_lights':light_report,'environment_strength':.10,'plinth_emission_strength':.025,'materials':changes,'actual_mix_shader_count':len(mix_report),'view_settings':{'view_transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'exr':'32-bit linear RGBA beauty, ZIP; no compositing, grading or glare','blend':str(OUT/'04_粉色装置_光影增强.blend')}
(OUT/'lighting_material_changes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=report['blend'])
mode=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if 'preview' in mode or 'final' in mode:
    p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';devices=p.get_devices_for_type('OPTIX')
    if not any(d.type=='OPTIX' for d in devices):raise RuntimeError('No OptiX GPU available')
    for d in p.devices:d.use=d.type=='OPTIX'
    preview='preview' in mode
    if preview:s.render.resolution_percentage=75;s.cycles.samples=32
    exr=OUT/('preview_linear.exr' if preview else 'beauty_linear.exr')
    png=OUT/('preview.png' if preview else 'beauty_preview.png')
    s.render.filepath=str(exr);started=time.perf_counter();bpy.ops.render.render(write_still=True)
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_depth='8';s.render.image_settings.color_mode='RGBA'
    bpy.data.images['Render Result'].save_render(str(png),scene=s)
    report['last_render']={'preview':preview,'exr':str(exr),'png':str(png),'seconds':round(time.perf_counter()-started,2),'samples':s.cycles.samples,'resolution_percent':s.render.resolution_percentage,'devices':[d.name for d in devices if d.type=='OPTIX']}
    (OUT/'lighting_material_changes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('LAYERED_PINK_READY '+json.dumps({'blend':report['blend'],'mix_shaders':len(mix_report),'geometry_unchanged':True},ensure_ascii=False))
