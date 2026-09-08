"""Layered material and light refinement of the existing editable rabbit project."""
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent
SOURCE=OUT.parent/'02_毛绒兔骑士'/'02_毛绒兔骑士.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
random.seed(50529)

def reset(name):
    m=bpy.data.materials[name];m.use_nodes=True;m.node_tree.nodes.clear()
    n=m.node_tree.nodes;l=m.node_tree.links
    out=n.new('ShaderNodeOutputMaterial');out.location=(1100,50)
    return m,n,l,out

def node(n,kind,label,x,y):
    q=n.new(kind);q.label=label;q.name=label;q.location=(x,y);return q

def link(l,a,b):l.new(a,b)

def mixcolor(n,l,label,factor,a,b,x,y,mode='MIX'):
    q=node(n,'ShaderNodeMixRGB',label,x,y);q.blend_type=mode
    for socket,value in [(q.inputs[0],factor),(q.inputs[1],a),(q.inputs[2],b)]:
        if hasattr(value,'node'):link(l,value,socket)
        else:socket.default_value=value
    return q.outputs[0]

def mixshader(n,l,label,factor,a,b,x,y):
    q=node(n,'ShaderNodeMixShader',label,x,y)
    if hasattr(factor,'node'):link(l,factor,q.inputs[0])
    else:q.inputs[0].default_value=factor
    link(l,a,q.inputs[1]);link(l,b,q.inputs[2]);return q.outputs[0]

def ramp(n,l,label,value,lo,hi,x,y,p0=0,p1=1):
    r=node(n,'ShaderNodeValToRGB',label,x,y);r.color_ramp.elements[0].position=p0;r.color_ramp.elements[0].color=(*lo,1);r.color_ramp.elements[1].position=p1;r.color_ramp.elements[1].color=(*hi,1);link(l,value,r.inputs[0]);return r.outputs[0]

def mapped_noise(n,l,label,scale,detail=3,x=-950,y=0,stretch=(1,1,1)):
    tex=node(n,'ShaderNodeTexCoord',label+' coordinates',x-400,y)
    mul=node(n,'ShaderNodeVectorMath',label+' directional stretch',x-200,y);mul.operation='MULTIPLY';mul.inputs[1].default_value=stretch;link(l,tex.outputs['Generated'],mul.inputs[0])
    noise=node(n,'ShaderNodeTexNoise',label,x,y);noise.inputs['Scale'].default_value=scale;noise.inputs['Detail'].default_value=detail;noise.inputs['Roughness'].default_value=.68;link(l,mul.outputs[0],noise.inputs['Vector']);return noise,mul.outputs[0]

def bsdf(n,label,color,rough,x,y,metal=0,coat=0):
    p=node(n,'ShaderNodeBsdfPrincipled',label,x,y);p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Coat Weight'].default_value=coat;return p

def blush_color(n,l,base,x=200,y=-600):
    geo=node(n,'ShaderNodeNewGeometry','World position for dyed cheek fibres',-650,y)
    masks=[]
    for i,center in enumerate([(-.79,-.685,3.64),(.70,-.720,3.65)]):
        d=node(n,'ShaderNodeVectorMath','Peach cheek dye falloff %d'%i,-420,y-i*180);d.operation='DISTANCE';d.inputs[1].default_value=center;link(l,geo.outputs['Position'],d.inputs[0])
        r=node(n,'ShaderNodeMapRange','Soft cheek edge %d'%i,-210,y-i*180);r.inputs['From Min'].default_value=.10;r.inputs['From Max'].default_value=.27;r.inputs['To Min'].default_value=.68;r.inputs['To Max'].default_value=0;link(l,d.outputs['Value'],r.inputs['Value']);masks.append(r.outputs['Result'])
    m=node(n,'ShaderNodeMath','Combine dyed cheek regions',0,y);m.operation='MAXIMUM';link(l,masks[0],m.inputs[0]);link(l,masks[1],m.inputs[1])
    return mixcolor(n,l,'MIX pink wool / peach cheek dye',m.outputs[0],base,(.90,.115,.012,1),x,y)

# True native strand shaders: separately controllable root colour, tip colour and rough fibres.
m,n,l,out=reset('Individual pastel pink fibres')
info=node(n,'ShaderNodeHairInfo','Actual strand root to tip and per strand random',-1100,500)
random_color=ramp(n,l,'Rose / raspberry individual strand colours',info.outputs['Random'],(.235,.015,.081),(.67,.100,.265),-820,600,.08,.95)
tips=ramp(n,l,'Natural pink root to tip dye',info.outputs['Intercept'],(.14,.014,.051),(.94,.285,.51),-820,330,.0,1)
fiber_color=mixcolor(n,l,'MIX per strand tone / root tip dye',.48,random_color,tips,-510,500)
noise,_=mapped_noise(n,l,'Subtle irregular dye density',5,3,-1120,-10)
fiber_color=mixcolor(n,l,'MIX fine dye variation',.08,fiber_color,noise.outputs['Color'],-220,470,'MULTIPLY')
fiber_color=blush_color(n,l,fiber_color,160,-700)
h1=node(n,'ShaderNodeBsdfHairPrincipled','Silky fine pink strands',430,560);h1.parametrization='COLOR';h1.inputs['Roughness'].default_value=.38;h1.inputs['Radial Roughness'].default_value=.43;h1.inputs['Coat'].default_value=.06;h1.inputs['Random Roughness'].default_value=.16;link(l,fiber_color,h1.inputs['Color'])
h2=node(n,'ShaderNodeBsdfHairPrincipled','Soft rough wool fibres',430,150);h2.parametrization='COLOR';h2.inputs['Roughness'].default_value=.62;h2.inputs['Radial Roughness'].default_value=.66;h2.inputs['Coat'].default_value=0;h2.inputs['Random Roughness'].default_value=.24;link(l,fiber_color,h2.inputs['Color'])
roughmask=ramp(n,l,'Random fine and rough fibre blend',info.outputs['Random'],(.30,.30,.30),(.76,.76,.76),-160,70)
link(l,mixshader(n,l,'MIX fine strand / fluffy rough strand',roughmask,h1.outputs[0],h2.outputs[0],820,350),out.inputs['Surface'])

# Woven undercoat remains deep pink beneath the fibres instead of pale chalky white.
m,n,l,out=reset('Rose pink woven plush undercoat')
noise,vec=mapped_noise(n,l,'Fine woven felt pores',155,2,-950,350)
color=ramp(n,l,'Dense raspberry woven base',noise.outputs['Fac'],(.28,.018,.089),(.57,.070,.21),-600,420,.15,.85)
color=blush_color(n,l,color,150,-400)
p1=bsdf(n,'Dense soft woven base',(1,1,1),.80,450,450);p1.inputs['Sheen Weight'].default_value=.12;link(l,color,p1.inputs['Base Color'])
p2=bsdf(n,'Softer scattered weave',(1,1,1),.93,450,40);p2.inputs['Sheen Weight'].default_value=.19;p2.inputs['Subsurface Weight'].default_value=.025;link(l,color,p2.inputs['Base Color'])
bump=node(n,'ShaderNodeBump','Tiny woven pore relief',-250,200);bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.004;link(l,noise.outputs['Fac'],bump.inputs['Height'])
for p in [p1,p2]:link(l,bump.outputs[0],p.inputs['Normal'])
link(l,mixshader(n,l,'MIX woven structure / soft fibre fill',noise.outputs['Fac'],p1.outputs[0],p2.outputs[0],820,300),out.inputs['Surface'])

# The additional geometric curls were responsible for the old white speckled coating.
# Their sheen is now pink, diffuse and tapered, with a thin translucent fibre layer.
for i,colors in enumerate([((.22,.015,.070),(.56,.065,.185)),((.34,.030,.110),(.69,.120,.290)),((.42,.047,.145),(.78,.175,.365)),((.56,.085,.220),(.87,.240,.460))]):
    m,n,l,out=reset('Loose soft curl fibre %d'%i)
    noise,_=mapped_noise(n,l,'Curl fibre dye variation',35,2,-900,300)
    color=ramp(n,l,'Deep rose / pink curled fibre dye',noise.outputs['Fac'],*colors,-600,400,.12,.87)
    color=blush_color(n,l,color,0,-420)
    p=bsdf(n,'Matte round dyed curl',(1,1,1),.71,380,420);p.inputs['Specular IOR Level'].default_value=.18;p.inputs['Sheen Weight'].default_value=.055;p.inputs['Subsurface Weight'].default_value=.015;link(l,color,p.inputs['Base Color'])
    trans=node(n,'ShaderNodeBsdfTranslucent','Small pink backlight through fine fibre',380,80);link(l,color,trans.inputs['Color'])
    mixed=mixshader(n,l,'MIX diffuse curl / coloured fibre transmission',.14,p.outputs[0],trans.outputs[0],650,330)
    transparent=node(n,'ShaderNodeBsdfTransparent','Fine air between flyaway fibres',650,30)
    link(l,mixshader(n,l,'MIX fibre / delicate open flyaway',.10,mixed,transparent.outputs[0],870,300),out.inputs['Surface'])

for obj in scene.objects:
    if obj.type=='CURVE' and 'irregular curled flyaways' in obj.name:
        obj.data.bevel_depth=.00125
        for spline in obj.data.splines:
            size=random.uniform(.63,1.08)
            for j,p in enumerate(spline.points):
                t=j/max(1,len(spline.points)-1);p.radius=size*(.64+.32*math.sin(math.pi*t))*(1-.60*t*t)
    for ps in obj.particle_systems:
        if ps.settings.material<=len(obj.data.materials) and obj.data.materials[ps.settings.material-1].name=='Individual pastel pink fibres':
            ps.settings.radius_scale=.0020;ps.settings.tip_radius=.11

def layered_wood(name,dark,light,paint=None,stretch=(10,5,.6),coatmix=.34):
    m,n,l,out=reset(name)
    grain,vec=mapped_noise(n,l,'Long natural timber grain',5,4,-1200,650,stretch)
    fine,_=mapped_noise(n,l,'Fine pores and longitudinal fibres',45,2,-1200,300,(4,3,.22))
    scratches,_=mapped_noise(n,l,'Thin scratches and dry surface marks',110,2,-1200,-70,(.35,8,22))
    woodcolor=ramp(n,l,'Honey heartwood / dark growth grain',grain.outputs['Fac'],dark,light,-860,700,.18,.82)
    porecolor=ramp(n,l,'Warm fine timber pores',fine.outputs['Fac'],(.11,.040,.014),(.78,.45,.16),-860,360,.25,.82)
    woodcolor=mixcolor(n,l,'MIX large wood grain / fine pores',.18,woodcolor,porecolor,-530,650,'MULTIPLY')
    scratchmask=ramp(n,l,'Rare fine scratched marks',scratches.outputs['Fac'],(0,0,0),(.7,.7,.7),-860,-50,.65,.83)
    woodcolor=mixcolor(n,l,'MIX timber / subtle rubbed highlights',.10,woodcolor,scratchmask,-230,610,'ADD')
    b1=node(n,'ShaderNodeBump','Long pore relief',-500,180);b1.inputs['Strength'].default_value=.26;b1.inputs['Distance'].default_value=.010;link(l,fine.outputs['Fac'],b1.inputs['Height'])
    b2=node(n,'ShaderNodeBump','Micro scratches layered over pores',-180,170);b2.inputs['Strength'].default_value=.13;b2.inputs['Distance'].default_value=.002;link(l,scratches.outputs['Fac'],b2.inputs['Height']);link(l,b1.outputs[0],b2.inputs['Normal'])
    raw=bsdf(n,'Warm raw timber substrate',(1,1,1),.66,130,570);link(l,woodcolor,raw.inputs['Base Color']);link(l,b2.outputs[0],raw.inputs['Normal'])
    polished=bsdf(n,'Thin warm hand rubbed varnish',(1,1,1),.35,130,150,coat=.22);link(l,woodcolor,polished.inputs['Base Color']);link(l,b2.outputs[0],polished.inputs['Normal']);polished.inputs['Coat Roughness'].default_value=.30
    woodshader=mixshader(n,l,'MIX raw timber / hand rubbed varnish',coatmix,raw.outputs[0],polished.outputs[0],500,450)
    if paint is not None:
        paintcolor=ramp(n,l,'Vermilion / saturated orange painted fibres',grain.outputs['Fac'],paint[0],paint[1],-420,-200,.10,.92)
        paintcolor=mixcolor(n,l,'MIX orange paint / visible timber pores',.055,paintcolor,woodcolor,-110,-150,'MULTIPLY')
        pp=bsdf(n,'Orange paint pigment layer',(1,1,1),.43,200,-270,coat=.12);link(l,paintcolor,pp.inputs['Base Color']);link(l,b2.outputs[0],pp.inputs['Normal'])
        worn=ramp(n,l,'Fine exposed wood through paint',fine.outputs['Fac'],(.025,.025,.025),(.24,.24,.24),-510,-440,.55,.83)
        link(l,mixshader(n,l,'MIX orange paint / gently exposed wood',worn,pp.outputs[0],woodshader,830,250),out.inputs['Surface'])
    else:link(l,woodshader,out.inputs['Surface'])

layered_wood('Carved russet shield frame',(.045,.007,.002),(.29,.073,.014),stretch=(9,3,.6),coatmix=.52)
layered_wood('Orange painted timber',(.16,.040,.008),(.58,.21,.025),paint=((.72,.024,.0015),(.98,.12,.007)),stretch=(8,3,.65))
layered_wood('Ochre oak cross bracing',(.17,.062,.009),(.56,.28,.040),stretch=(10,3,.7),coatmix=.35)
layered_wood('Honey timber bark and fibres',(.075,.019,.0045),(.40,.145,.033),stretch=(17,17,.55),coatmix=.20)
layered_wood('Pale freshly cut end grain',(.25,.099,.025),(.65,.37,.11),stretch=(1.4,1.4,1),coatmix=.15)

# Polished gold and very fine brushed gold are separate editable lobes.
m,n,l,out=reset('Soft polished golden metal')
brush,vec=mapped_noise(n,l,'Fine directional brushed micro surface',90,2,-1000,350,(.4,12,35))
alloy=ramp(n,l,'Warm gold alloy micro colour',brush.outputs['Fac'],(.54,.235,.026),(.85,.51,.12),-700,500,.08,.93)
polished=bsdf(n,'Polished round gold boss',(1,1,1),.16,-150,500,metal=1);link(l,alloy,polished.inputs['Base Color'])
brushed=bsdf(n,'Fine brushed golden alloy',(1,1,1),.29,-150,70,metal=1);link(l,alloy,brushed.inputs['Base Color'])
bump=node(n,'ShaderNodeBump','Microscopic brushed grooves',-500,100);bump.inputs['Strength'].default_value=.11;bump.inputs['Distance'].default_value=.00045;link(l,brush.outputs['Fac'],bump.inputs['Height']);link(l,bump.outputs[0],brushed.inputs['Normal'])
mask=ramp(n,l,'Polished / brushed surface distribution',brush.outputs['Fac'],(.14,.14,.14),(.40,.40,.40),200,220)
link(l,mixshader(n,l,'MIX polished metal / brushed micro surface',mask,polished.outputs[0],brushed.outputs[0],790,400),out.inputs['Surface'])

# Every closed blade facet now contains a real Glass BSDF and translucent glossy layer.
crystal_specs=[('Sunlit ivory crystal',(.97,.77,.27),.024,.19),('Lemon crystal face',(.99,.64,.080),.020,.22),('Honey crystal face',(.82,.39,.026),.036,.28),('White luminous crystal tip',(1,.90,.58),.019,.16)]
for name,col,emit,density in crystal_specs:
    m,n,l,out=reset(name)
    glass=node(n,'ShaderNodeBsdfGlass','Real golden optical glass',-80,530);glass.inputs['Color'].default_value=(*col,1);glass.inputs['Roughness'].default_value=.055;glass.inputs['IOR'].default_value=1.47
    skin=bsdf(n,'Polished translucent crystal face',col,.12,-80,150,coat=.36);skin.inputs['Transmission Weight'].default_value=.72;skin.inputs['IOR'].default_value=1.47;skin.inputs['Coat Roughness'].default_value=.11
    fres=node(n,'ShaderNodeFresnel','Crystal edge reflection',-620,300);fres.inputs['IOR'].default_value=1.47
    mixrange=node(n,'ShaderNodeMapRange','Face / edge optical mix',-350,300);mixrange.inputs['To Min'].default_value=.24;mixrange.inputs['To Max'].default_value=.70;link(l,fres.outputs[0],mixrange.inputs['Value'])
    optics=mixshader(n,l,'MIX clear glass / polished transmitting edge',mixrange.outputs['Result'],glass.outputs[0],skin.outputs[0],280,450)
    emission=node(n,'ShaderNodeEmission','Very faint warm internal crystal light',280,90);emission.inputs['Color'].default_value=(1,.49,.028,1);emission.inputs['Strength'].default_value=.35
    link(l,mixshader(n,l,'MIX optical crystal / trace golden emission',emit,optics,emission.outputs[0],730,400),out.inputs['Surface'])
    volume=node(n,'ShaderNodeVolumeAbsorption','Subtle golden depth absorption',600,-220);volume.inputs['Color'].default_value=(*col,1);volume.inputs['Density'].default_value=density;link(l,volume.outputs[0],out.inputs['Volume'])

m,n,l,out=reset('Crystal suspended golden flecks')
noise,_=mapped_noise(n,l,'Gold inclusion brightness variation',32,2,-600,400)
p=bsdf(n,'Reflective suspended golden grains',(.94,.52,.035),.24,-180,400,metal=.88)
e=node(n,'ShaderNodeEmission','Tiny light in crystal inclusions',-180,70);e.inputs['Color'].default_value=(1,.61,.085,1);e.inputs['Strength'].default_value=1.8
mask=ramp(n,l,'Rare luminous inclusions',noise.outputs['Fac'],(.025,.025,.025),(.17,.17,.17),160,190,.3,.8)
link(l,mixshader(n,l,'MIX golden inclusions / rare internal sparkle',mask,p.outputs[0],e.outputs[0],650,350),out.inputs['Surface'])

def leaf_material(name,dark,light):
    m,n,l,out=reset(name)
    noise,vec=mapped_noise(n,l,'Fine leaf tissue variations',14,3,-1100,450,(2,3,1))
    wave=node(n,'ShaderNodeTexWave','Delicate secondary leaf veins',-820,70);wave.wave_type='BANDS';wave.bands_direction='DIAGONAL';wave.inputs['Scale'].default_value=27;wave.inputs['Distortion'].default_value=3;wave.inputs['Detail'].default_value=3;link(l,vec,wave.inputs['Vector'])
    color=ramp(n,l,'Lemon leaf tissue shades',noise.outputs['Fac'],dark,light,-650,450,.15,.85)
    vein=ramp(n,l,'Thin soft secondary vein mask',wave.outputs['Fac'],(.40,.48,.06),(.96,.91,.22),-550,100,.43,.59)
    color=mixcolor(n,l,'MIX leaf tissue / delicate vein pigment',.15,color,vein,-220,460,'MULTIPLY')
    p=bsdf(n,'Soft waxy leaf surface',(1,1,1),.43,150,450,coat=.07);p.inputs['Subsurface Weight'].default_value=.045;link(l,color,p.inputs['Base Color'])
    rough=ramp(n,l,'Natural leaf roughness variation',noise.outputs['Fac'],(.35,.35,.35),(.58,.58,.58),-220,0);link(l,rough,p.inputs['Roughness'])
    bump=node(n,'ShaderNodeBump','Fine leaf vein relief',-200,190);bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.004;link(l,wave.outputs['Fac'],bump.inputs['Height']);link(l,bump.outputs[0],p.inputs['Normal'])
    translucent=node(n,'ShaderNodeBsdfTranslucent','Warm backlit leaf body',160,-100);link(l,color,translucent.inputs['Color'])
    link(l,mixshader(n,l,'MIX waxy leaf surface / thin transmitting tissue',.17,p.outputs[0],translucent.outputs[0],750,350),out.inputs['Surface'])

leaf_material('Lemon golden leaf',(.58,.41,.004),(.96,.81,.023))
leaf_material('Chartreuse young leaf',(.39,.50,.005),(.78,.90,.035))
leaf_material('Deep yellow ochre leaf',(.47,.21,.003),(.94,.59,.015))

# Woven scarlet cape, with a second velvet lobe mixed over the cloth weave.
m,n,l,out=reset('Deep coral red wool cape')
weave,vec=mapped_noise(n,l,'Cape fine woven thread',190,2,-850,330,(1.4,1.4,.7))
color=ramp(n,l,'Crimson thread / warm coral thread',weave.outputs['Fac'],(.22,.003,.008),(.54,.013,.023),-550,400,.15,.85)
p=bsdf(n,'Scarlet woven wool',(1,1,1),.78,-30,500);p.inputs['Sheen Weight'].default_value=.16;link(l,color,p.inputs['Base Color'])
p2=bsdf(n,'Soft coral velvet thread',(1,1,1),.91,-30,60);p2.inputs['Sheen Weight'].default_value=.26;link(l,color,p2.inputs['Base Color'])
bump=node(n,'ShaderNodeBump','Tiny cloth weave relief',-360,120);bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.003;link(l,weave.outputs['Fac'],bump.inputs['Height']);link(l,bump.outputs[0],p.inputs['Normal']);link(l,bump.outputs[0],p2.inputs['Normal'])
link(l,mixshader(n,l,'MIX woven wool / soft velvet fibres',.35,p.outputs[0],p2.outputs[0],740,360),out.inputs['Surface'])

# Dark eyes retain coloured highlights instead of chalky flat white spots.
m,n,l,out=reset('Glossy chestnut safety eyes')
p=bsdf(n,'Dark chocolate resin eye',(.018,.009,.006),.20,80,390,coat=.27);p.inputs['Coat Roughness'].default_value=.12
clear=bsdf(n,'Clear polished eye surface',(.026,.015,.010),.10,80,0,coat=.45);clear.inputs['Coat Roughness'].default_value=.07
f=node(n,'ShaderNodeFresnel','Gentle eye edge polish',-200,180);f.inputs['IOR'].default_value=1.47
link(l,mixshader(n,l,'MIX dark resin / polished eye surface',f.outputs[0],p.outputs[0],clear.outputs[0],730,320),out.inputs['Surface'])

# Lower broad chalky sheen on the meadow; use warmer orange-gold variation in its retained vertex colours.
gm=bpy.data.materials['Golden meadow fibres with light tips'];n=gm.node_tree.nodes;l=gm.node_tree.links;p=n.get('Principled BSDF')
base=p.inputs['Base Color'].links[0].from_socket
noise,_=mapped_noise(n,l,'Meadow small tonal patches',9,2,-850,700,(1,1,1))
tint=ramp(n,l,'Burnt orange / golden meadow tint',noise.outputs['Fac'],(.52,.17,.025),(.97,.62,.20),-500,700)
colored=mixcolor(n,l,'MIX meadow vertex colour / warm tonal patches',.16,base,tint,-150,650,'MULTIPLY');link(l,colored,p.inputs['Base Color'])
p.inputs['Roughness'].default_value=.87;p.inputs['Specular IOR Level'].default_value=.17;p.inputs['Sheen Weight'].default_value=.035

def point_at(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
lights=[('Large warm key',(-3.8,-4.0,7.2),1030,3.1,(1,.86,.67),(0,0,3.1)),('Soft creamy fill',(4,-3.0,4.6),280,4.5,(1,.89,.79),(0,0,3.0)),('Plush rim sunlight',(-2.9,2.2,6.6),650,2.7,(1,.73,.43),(0,0,3.2)),('Gentle warm front leaf fill',(0,-6.5,3.4),125,4.1,(1,.93,.68),(0,-4.5,1.4))]
for name,loc,energy,size,color,target in lights:
    o=bpy.data.objects[name];o.location=loc;o.data.energy=energy;o.data.size=size;o.data.color=color;point_at(o,target)
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.82,.77,.66,1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.18
bpy.data.objects['Small warm crystal glow'].data.energy=8

# No artistic grading or glow is baked into this native beauty pass.
scene.render.use_compositing=False
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.look='None';scene.view_settings.exposure=0
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.use_denoising=False
scene.cycles.samples=1024;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.003;scene.cycles.adaptive_min_samples=64
scene.cycles.max_bounces=10;scene.cycles.transmission_bounces=8;scene.cycles.transparent_max_bounces=12
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='OPEN_EXR';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='16';scene.render.image_settings.exr_codec='ZIP'
scene.render.filepath=str(OUT/'beauty_linear.exr')
scene['Enhancement']='Editable layered Mix materials and warm directional key/fill/rim; no final grade or glow baked into beauty'
scene['Source project']=str(SOURCE)
scene['Final settings']='1000 square, scene linear HALF RGBA EXR, Cycles OptiX, no denoising; compositor reserved for final art direction'
summary={m.name:[n.label or n.name for n in m.node_tree.nodes if n.type in {'MIX_RGB','MIX_SHADER','MIX'}] for m in bpy.data.materials if m.use_nodes and any(n.type in {'MIX_RGB','MIX_SHADER','MIX'} for n in m.node_tree.nodes)}
(OUT/'material_mix_layers.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'05_毛绒兔骑士_光影增强.blend'))
print('MATERIAL_ENHANCEMENT_SAVED '+json.dumps({'objects':len(scene.objects),'layered_materials':len(summary),'mix_nodes':sum(map(len,summary.values()))},ensure_ascii=False),flush=True)
