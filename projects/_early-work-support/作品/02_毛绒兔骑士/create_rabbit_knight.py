"""Editable geometry reconstruction of the supplied plush rabbit knight reference."""
import bpy, math, random, json, sys, bisect
from mathutils import Vector
from pathlib import Path

OUT = Path(__file__).resolve().parent
random.seed(22091)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials):
    bpy.data.materials.remove(d)
scene = bpy.context.scene
collections = {}
for name in ['01 Rabbit plush', '02 Face and ears', '03 Crystal sword', '04 Wooden shield', '05 Cape', '06 Tree stump', '07 Golden meadow', '08 Paper scenery', '09 Foreground leaves', '10 Studio']:
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    collections[name] = c
CURRENT = collections['01 Rabbit plush']

def put(obj, name, mat=None):
    obj.name = name
    for c in list(obj.users_collection): c.objects.unlink(obj)
    CURRENT.objects.link(obj)
    if mat: obj.data.materials.append(mat)
    return obj

def material(name, color, rough=.55, metal=0, emission=0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metal
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1)
        p.inputs['Emission Strength'].default_value=emission
    return m

def plush_material(name, a, b, hair=False):
    m=material(name,a,.65)
    n=m.node_tree.nodes; l=m.node_tree.links; p=n.get('Principled BSDF')
    if hair:
        n.remove(p);p=n.new('ShaderNodeBsdfHairPrincipled');p.parametrization='COLOR'
        p.inputs['Roughness'].default_value=.36;p.inputs['Radial Roughness'].default_value=.43
        p.inputs['Coat'].default_value=.25;p.inputs['Random Roughness'].default_value=.28
        l.new(p.outputs[0],n.get('Material Output').inputs['Surface'])
    color_input='Color' if hair else 'Base Color'
    noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=105 if not hair else 8
    noise.inputs['Detail'].default_value=2
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position=.20; ramp.color_ramp.elements[0].color=(*a,1)
    ramp.color_ramp.elements[1].position=.82; ramp.color_ramp.elements[1].color=(*b,1)
    if hair:
        strand=n.new('ShaderNodeHairInfo');l.new(strand.outputs['Random'],ramp.inputs[0])
    else:l.new(noise.outputs['Fac'],ramp.inputs[0])
    l.new(ramp.outputs[0],p.inputs[color_input])
    if not hair:
        p.inputs['Sheen Weight'].default_value=.38;p.inputs['Sheen Roughness'].default_value=.6
        bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.18; bump.inputs['Distance'].default_value=.011
        l.new(noise.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m

def wood(name, dark, light, scale=(6,6,1), rough=.48):
    m=material(name,light,rough); n=m.node_tree.nodes; l=m.node_tree.links; p=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexCoord'); mapping=n.new('ShaderNodeVectorMath'); mapping.operation='MULTIPLY'; mapping.inputs[1].default_value=scale
    noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=4; noise.inputs['Detail'].default_value=3.5; noise.inputs['Roughness'].default_value=.72
    l.new(tex.outputs['Generated'],mapping.inputs[0]); l.new(mapping.outputs[0],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.24; ramp.color_ramp.elements[0].color=(*dark,1); ramp.color_ramp.elements[1].position=.79; ramp.color_ramp.elements[1].color=(*light,1)
    l.new(noise.outputs['Fac'],ramp.inputs[0]); l.new(ramp.outputs[0],p.inputs['Base Color'])
    bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.28; bump.inputs['Distance'].default_value=.035
    l.new(noise.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs[0],p.inputs['Normal'])
    return m

pink=plush_material('Rose pink woven plush undercoat',(.53,.075,.22),(.82,.24,.43))
furmat=plush_material('Individual pastel pink fibres',(.35,.027,.095),(.76,.21,.43),True)
cream=plush_material('Warm ivory short pile velvet',(.80,.62,.44),(.97,.84,.65))
creamfur=plush_material('Ivory fine fuzz',(.89,.73,.56),(1,.93,.8),True)
blush=plush_material('Peach blush woven fibres',(.95,.19,.075),(1,.43,.20))
blushfur=plush_material('Peach blush fine fuzz',(.97,.24,.11),(1,.48,.25),True)
white=material('Warm porcelain eye whites',(1,.94,.82),.27)
brown=material('Glossy chestnut safety eyes',(.029,.017,.013),.23)
nosemat=material('Cocoa embroidered nose',(.12,.026,.018),.31)
mouthmat=material('Tiny open embroidered mouth',(.19,.037,.024),.52)
gold=material('Soft polished golden metal',(.78,.39,.065),.22,.82)
framewood=wood('Carved russet shield frame',(.062,.012,.004),(.25,.062,.015),(2,5,55))
orangewood=wood('Orange painted timber',(.63,.074,.009),(.95,.23,.035),(8,3,.7),.55)
strapwood=wood('Ochre oak cross bracing',(.29,.14,.025),(.68,.41,.10),(12,3,1))
stumpwood=wood('Honey timber bark and fibres',(.13,.037,.012),(.42,.19,.068),(22,22,.55))
endwood=wood('Pale freshly cut end grain',(.58,.31,.10),(.85,.62,.31),(2,2,1))
grainmat=material('Dark warm wood growth lines',(.235,.09,.026),.69)
graingold=material('Light timber growth lines',(.63,.37,.15),.7)
papermat=material('Cream paper backdrop',(.84,.755,.58),.95)
cloudmat=material('Soft ivory paper clouds',(.98,.93,.83),.9)
starmat=material('Faded golden storybook sunburst',(.94,.77,.44),1)
fencemat=material('Warm off white picket fence',(.92,.85,.68),.72)
red=material('Deep coral red wool cape',(.55,.035,.025),.78)
red.node_tree.nodes.get('Principled BSDF').inputs['Sheen Weight'].default_value=.35

def sphere(name, loc, scl, mat, seg=56, rings=36):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o=put(bpy.context.object,name,mat); o.scale=scl
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    return o

def cube(name,loc,dims,mat,bevel=.04):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=put(bpy.context.object,name,mat); o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        m=o.modifiers.new('Soft hand made edges','BEVEL'); m.width=bevel;m.segments=4
        o.modifiers.new('Weighted face normals','WEIGHTED_NORMAL')
    return o

def curve(name,pts,radius,mat,cyclic=False):
    c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D';c.resolution_u=1;c.bevel_depth=radius;c.bevel_resolution=2
    sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,co in zip(sp.points,pts):p.co=(*co,1)
    sp.use_cyclic_u=cyclic
    o=bpy.data.objects.new(name,c);CURRENT.objects.link(o);c.materials.append(mat)
    return o

def mesh(name,verts,faces,mat,bevel=0):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);CURRENT.objects.link(o);me.materials.append(mat)
    if bevel:
        m=o.modifiers.new('Rounded crafted edges','BEVEL');m.width=bevel;m.segments=4
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o

def hair(obj,name,count,length,children=20,mat=furmat):
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    bpy.ops.object.particle_system_add()
    ps=obj.particle_systems[-1]; ps.seed=random.randint(1,99999)
    length*=1.55
    s=ps.settings;s.name=name;s.type='HAIR';s.count=count;s.hair_length=length;s.hair_step=4
    s.child_type='INTERPOLATED';s.child_percent=5;s.rendered_child_count=children
    s.child_length=.94;s.child_length_threshold=.1
    s.clump_factor=.035;s.clump_shape=.25
    s.roughness_1=length*.35;s.roughness_1_size=.3
    s.roughness_2=length*.28;s.roughness_2_size=.22
    s.roughness_endpoint=length*.35
    s.kink='CURL';s.kink_amplitude=length*.23;s.kink_frequency=2.7;s.kink_shape=.4
    s.root_radius=.70;s.tip_radius=.17;s.radius_scale=.0023
    obj.data.materials.append(mat);s.material=len(obj.data.materials)
    obj.select_set(False)
    return ps

def rod(name,start,end,radius,mat,vertices=32):
    d=Vector(end)-Vector(start)
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=d.length,location=(Vector(start)+Vector(end))/2)
    o=put(bpy.context.object,name,mat);o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    b=o.modifiers.new('Rounded rod ends','BEVEL');b.width=min(.025,radius*.2);b.segments=3
    for f in o.data.polygons:f.use_smooth=True
    return o

# Chunky sewn toy silhouette, with real short curly hair on every exposed surface.
head=sphere('Large round plush head',(0,0,3.43),(1.22,.86,.90),pink)
hair(head,'Dense curly head pile 286k fibres',13000,.033,22)
body=sphere('Small pear shaped plush body',(0,.045,2.20),(.88,.63,.78),pink)
for v in body.data.vertices:
    factor=1-.19*(v.co.z/.78);v.co.x*=factor;v.co.y*=factor
hair(body,'Dense body plush fibres',7000,.032,20)
leftfoot=sphere('Lifted left foot',(-.70,-.04,1.56),(.34,.46,.48),pink)
leftfoot.rotation_euler.y=.92
hair(leftfoot,'Left foot fibres',2300,.030,20)
rightfoot=sphere('Grounded right foot',(.43,-.075,1.34),(.40,.46,.32),pink)
hair(rightfoot,'Right foot fibres',2300,.030,20)
leftarm=sphere('Raised sword paw',(-1.10,-.08,3.12),(.43,.41,.47),pink)
hair(leftarm,'Sword hand fibres',2300,.035,20)
rightarm=sphere('Shield paw',(.91,-.025,2.73),(.35,.40,.49),pink)
hair(rightarm,'Shield hand fibres',1800,.032,20)
tail=sphere('Peek of round rabbit tail',(.61,.57,1.91),(.29,.29,.29),pink)
hair(tail,'Tail pom pom',800,.033,18)

CURRENT=collections['02 Face and ears']
def ring_ear(name,center,rx,rz,tilt):
    verts=[];faces=[];major=80;minor=16
    for i in range(major):
        t=2*math.pi*i/major
        cx=rx*math.cos(t);cz=rz*math.sin(t)
        nx=math.cos(t);nz=math.sin(t)
        for j in range(minor):
            q=2*math.pi*j/minor
            x=cx+.145*math.cos(q)*nx
            z=cz+.145*math.cos(q)*nz
            y=.145*math.sin(q)
            xx=x*math.cos(tilt)+z*math.sin(tilt)
            zz=-x*math.sin(tilt)+z*math.cos(tilt)
            verts.append((center[0]+xx,center[1]+y,center[2]+zz))
    for i in range(major):
        for j in range(minor):faces.append((i*minor+j,i*minor+(j+1)%minor,((i+1)%major)*minor+(j+1)%minor,((i+1)%major)*minor+j))
    o=mesh(name,verts,faces,pink)
    for p in o.data.polygons:p.use_smooth=True
    hair(o,name+' dense soft rim fibres',2500,.028,20)
    insert=sphere(name+' recessed ivory inner lining',(center[0],center[1]+.06,center[2]),(rx-.055,.05,rz+.015),cream)
    insert.rotation_euler.y=tilt;hair(insert,name+' inner lining fuzz',650,.012,12,creamfur)

ring_ear('Left long loop ear',(-.24,.045,4.43),.245,.43,.23)
ring_ear('Right long loop ear',(.62,.08,4.43),.245,.41,.22)

for side,x,y,z in [('Left',-.435,-.782,3.78),('Right',.20,-.825,3.80)]:
    eye=sphere(side+' cream eye white',(x,y,z),(.17,.090,.200),white)
    eye.rotation_euler.z=-.05
    pupil=sphere(side+' chestnut glossy pupil',(x-.029,y-.080,z+.025),(.120,.060,.156),brown)
    # A tiny physical reflective glint is supplied by the area lights.

muzzle=sphere('Small cream oval muzzle',(-.055,-.908,3.64),(.147,.100,.138),cream)
hair(muzzle,'Velvety muzzle nap',700,.009,10,creamfur)
sphere('Tiny horizontal cocoa nose',(-.06,-1.008,3.779),(.059,.025,.029),nosemat,40,24)
sphere('O shaped embroidered mouth',(-.039,-1.009,3.651),(.039,.018,.047),mouthmat,40,24)
sphere('Soft mouth inner highlight',(-.039,-1.030,3.654),(.019,.005,.026),cream,32,20)
# Blush is dyed into the head fabric and individual fibres, never a raised disc.
for m in [pink,furmat]:
    n=m.node_tree.nodes;l=m.node_tree.links;p=next(node for node in n if node.type in {'BSDF_PRINCIPLED','BSDF_HAIR_PRINCIPLED'});color_input='Color' if p.type=='BSDF_HAIR_PRINCIPLED' else 'Base Color';base=p.inputs[color_input].links[0].from_socket
    geo=n.new('ShaderNodeNewGeometry');masks=[]
    for center in [(-.79,-.685,3.64),(.70,-.720,3.65)]:
        dist=n.new('ShaderNodeVectorMath');dist.operation='DISTANCE';dist.inputs[1].default_value=center;l.new(geo.outputs['Position'],dist.inputs[0])
        remap=n.new('ShaderNodeMapRange');remap.inputs['From Min'].default_value=.11;remap.inputs['From Max'].default_value=.255;remap.inputs['To Min'].default_value=.92;remap.inputs['To Max'].default_value=0;l.new(dist.outputs['Value'],remap.inputs['Value']);masks.append(remap.outputs['Result'])
    maximum=n.new('ShaderNodeMath');maximum.operation='MAXIMUM';l.new(masks[0],maximum.inputs[0]);l.new(masks[1],maximum.inputs[1])
    mix=n.new('ShaderNodeMixRGB');l.new(maximum.outputs[0],mix.inputs[0]);l.new(base,mix.inputs[1]);mix.inputs[2].default_value=(.98,.23,.065,1);l.new(mix.outputs[0],p.inputs[color_input])

# Fine, independently editable curled pile fibres add irregular flyaways above the dense groom.
CURRENT=collections['01 Rabbit plush']
loopmats=[]
for i,col in enumerate([(.45,.065,.20),(.71,.18,.37),(.89,.30,.50),(.95,.44,.60)]):
    m=material('Loose soft curl fibre %d'%i,col,.46);m.node_tree.nodes.get('Principled BSDF').inputs['Sheen Weight'].default_value=.48;loopmats.append(m)
bpy.context.view_layer.update()
for source,num in [(head,42000),(body,16000),(leftarm,5000),(rightarm,3000),(leftfoot,5000),(rightfoot,5000)]:
    source.data.calc_loop_triangles();triangles=list(source.data.loop_triangles);cdf=[];area=0
    for tri in triangles:area+=tri.area;cdf.append(area)
    c=bpy.data.curves.new(source.name+' irregular curled flyaways','CURVE');c.dimensions='3D';c.resolution_u=1;c.bevel_depth=.00165;c.bevel_resolution=0
    for m in loopmats:c.materials.append(m)
    for i in range(num):
        tri=triangles[bisect.bisect_left(cdf,random.random()*area)];v=[source.data.vertices[k] for k in tri.vertices]
        a=math.sqrt(random.random());b=random.random();weights=(1-a,a*(1-b),a*b)
        pos=sum((q.co*w for q,w in zip(v,weights)),Vector());normal=sum((q.normal*w for q,w in zip(v,weights)),Vector()).normalized()
        pos=source.matrix_world@pos;normal=(source.matrix_world.to_3x3()@normal).normalized()
        tangent=normal.cross(Vector((0,0,1)))
        if tangent.length<.01:tangent=normal.cross(Vector((0,1,0)))
        tangent.normalize();bitangent=normal.cross(tangent).normalized()
        length=random.uniform(.045,.075);curl=random.uniform(.006,.012);turns=random.uniform(1.0,1.75);phase=random.random()*math.tau
        sp=c.splines.new('POLY');sp.points.add(12);sp.material_index=random.randrange(len(loopmats))
        for j,p in enumerate(sp.points):
            t=j/12;angle=phase+t*turns*math.tau
            q=pos+normal*(.008+length*t*.76)+tangent*(math.cos(angle)-math.cos(phase))*curl*t+bitangent*(math.sin(angle)-math.sin(phase))*curl*t
            p.co=(*q,1);p.radius=.70+.30*math.sin(math.pi*t)
    o=bpy.data.objects.new(c.name,c);CURRENT.objects.link(o)

CURRENT=collections['05 Cape']
verts=[];faces=[];cols=36;rows=22
for j in range(rows+1):
    t=j/rows
    for i in range(cols+1):
        u=i/cols*2-1
        width=.45+.62*t
        x=u*width
        z=3.09-1.73*t+.10*math.cos(u*2.4)*t+.045*math.sin(u*12)*t
        y=.46+.19*t+.12*math.cos(u*7)*t
        verts.append((x,y,z))
for j in range(rows):
    for i in range(cols):
        a=j*(cols+1)+i;faces.append((a,a+1,a+cols+2,a+cols+1))
cape=mesh('Draped scarlet cape with curved hem',verts,faces,red)
for p in cape.data.polygons:p.use_smooth=True
so=cape.modifiers.new('Actual fabric thickness','SOLIDIFY');so.thickness=.025
sub=cape.modifiers.new('Soft cloth folds','SUBSURF');sub.levels=2
curve('Stitched cape hem',[verts[rows*(cols+1)+i] for i in range(cols+1)],.009,material('Coral seam thread',(.69,.065,.027),.8))

CURRENT=collections['04 Wooden shield']
shieldroot=bpy.data.objects.new('SHIELD assembly - editable parts',None);CURRENT.objects.link(shieldroot)
shieldroot.location=(1.00,-.72,2.54);shieldroot.rotation_euler=(0,.07,-.055)
def shieldpoly(name,outline,depth,mat,y=0,bevel=.025):
    n=len(outline);v=[(x,y+d,z) for d in [-depth/2,depth/2] for x,z in outline]
    f=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]
    for i in range(n):f.append((i,(i+1)%n,(i+1)%n+n,i+n))
    o=mesh(name,v,f,mat,bevel);o.parent=shieldroot;return o

outline=[(-.54,.65),(.54,.65),(.55,-.38),(0,-.69),(-.55,-.38)]
shieldpoly('Thick dark wooden shield border',outline,.20,framewood,0,.065)
shieldpoly('Recessed orange shield panel',[(x*.79,z*.80) for x,z in outline],.065,orangewood,-.137,.035)
for x in [-.19,.17]:
    o=curve('Carved shield plank joint',[(x,-.181,.49),(x-.01,-.183,.14),(x+.008,-.185,-.25),(x,-.181,-.39)],.0055,framewood);o.parent=shieldroot
o=cube('Golden oak horizontal crossbar',(0,-.212,.025),(.90,.068,.135),strapwood,.018);o.parent=shieldroot
o=cube('Golden oak vertical crossbar',(0,-.210,.015),(.13,.070,1.085),strapwood,.017);o.parent=shieldroot;o.rotation_euler.y=.05
o=sphere('Dark metal boss mounting collar',(0,-.249,.012),(.169,.047,.169),framewood);o.parent=shieldroot
o=sphere('Polished golden round shield boss',(0,-.289,.018),(.109,.080,.109),gold);o.parent=shieldroot
for x,z in [(-.36,.025),(.36,.025),(0,.45),(0,-.42)]:
    o=sphere('Small brass shield rivet',(x,-.255,z),(.018,.01,.018),gold,20,12);o.parent=shieldroot

CURRENT=collections['03 Crystal sword']
swordroot=bpy.data.objects.new('SWORD assembly - faceted golden crystal',None);CURRENT.objects.link(swordroot)
swordroot.location=(-1.27,-.25,3.44);swordroot.rotation_euler=(.015,-.15,.05)
crystals=[]
for name,c,metal,trans,em in [('Sunlit ivory crystal',(1,.85,.34),.02,.20,.10),('Lemon crystal face',(.98,.73,.12),.13,.27,.10),('Honey crystal face',(.75,.42,.042),.16,.22,.05),('White luminous crystal tip',(1,.92,.56),.02,.12,.15)]:
    m=material(name,c,.18,metal,em);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=trans;p.inputs['IOR'].default_value=1.48;crystals.append(m)
v=[(-.19,0,.09),(.19,0,.09),(-.45,0,1.08),(.38,0,1.08),(-.10,0,1.74),(-.015,-.21,.92),(-.015,.15,.92)]
f=[(0,1,5),(0,5,2),(1,3,5),(2,5,4),(5,3,4),(1,0,6),(0,2,6),(2,4,6),(4,3,6),(3,1,6)]
blade=mesh('Solid triangular faceted golden crystal blade',v,f,crystals[0]);blade.parent=swordroot
blade.scale=(1.20,1,.9)
for m in crystals[1:]:blade.data.materials.append(m)
for i,p in enumerate(blade.data.polygons):p.material_index=[2,1,0,1,3,2,1,0,3,0][i]
guard=cube('Warm wooden sword crossguard',(0,-.015,.02),(.88,.24,.19),strapwood,.041);guard.parent=swordroot
handle=rod('Short wooden sword grip',(0,0,-.40),(0,0,-.05),.09,framewood);handle.parent=swordroot
for z in [-.29,-.23,-.17,-.11]:
    pts=[(.094*math.cos(t*math.tau/28),.094*math.sin(t*math.tau/28),z) for t in range(28)]
    o=curve('Copper grip winding',pts,.009,strapwood,True);o.parent=swordroot
o=sphere('Golden pommel',(0,0,-.4),(.112,.112,.077),gold);o.parent=swordroot
# Tiny suspended three-dimensional metallic inclusions, not an image texture.
sparklemat=material('Crystal suspended golden flecks',(1,.83,.24),.25,.56,.3)
verts=[];faces=[]
for i in range(270):
    z=random.uniform(.16,1.08);x=random.uniform(-.16-z*.22,.16+z*.16);y=random.uniform(-.17,-.01);r=random.uniform(.004,.012)
    a=len(verts);verts.extend([(x-r,y,z-r),(x+r,y,z-r),(x,y-r,z+r)]);faces.append((a,a+1,a+2))
o=mesh('Hundreds of gold crystal inclusions',verts,faces,sparklemat);o.parent=swordroot;o.scale=(1.20,1,.9)
starwhite=material('Brilliant sword tip star',(1,.96,.64),.3,0,14)
cx,cy,cz=-.120,-.13,1.566
for i,(a,b) in enumerate([(.04,.32),(.19,.028),(.10,.015)]):
    angle=[0,0,.72][i]
    pts=[(-a,0),(0,b),(a,0),(0,-b)]
    vv=[(cx+x*math.cos(angle)+z*math.sin(angle),cy-.02*i,cz-x*math.sin(angle)+z*math.cos(angle)) for x,z in pts]
    o=mesh('Physical four pointed luminous sparkle',vv,[(0,1,2,3)],starwhite);o.parent=swordroot

CURRENT=collections['06 Tree stump']
n=120;levels=[(.08,1.61),(.20,1.58),(.73,1.40),(.84,1.35)];verts=[]
for j,(z,r) in enumerate(levels):
    for i in range(n):
        t=math.tau*i/n;rr=r+.032*math.sin(t*5)+.027*math.sin(t*9+.5)
        verts.append((rr*math.cos(t),rr*math.sin(t),z+.012*math.sin(t*4)))
faces=[]
for j in range(len(levels)-1):
    for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
faces.append(tuple(range((len(levels)-1)*n,len(levels)*n)))
stump=mesh('Slightly irregular tapered honey wood stump',verts,faces,stumpwood,.025)
stump.data.materials.append(endwood);stump.data.polygons[-1].material_index=1
for p in stump.data.polygons[:-1]:p.use_smooth=True
for j in range(1,24):
    rr=j/24*1.31
    pts=[]
    for i in range(160):
        t=math.tau*i/160;r=rr*(1+.028*math.sin(t*3+j*.12)+.016*math.sin(t*7))
        pts.append((-.09+r*math.cos(t),.04+r*.94*math.sin(t),.857+.012*math.sin(t*4)))
    curve('Visible concentric annual growth ring %02d'%j,pts,.006 if j%3 else .013,grainmat if j%3 else graingold,True)
for j in range(110):
    t=math.tau*j/110+random.uniform(-.008,.008);pts=[]
    for i in range(18):
        u=i/17;z=.12+.67*u;r=1.61-.26*u+.031*math.sin(t*5)+.027*math.sin(t*9+.5)
        a=t+.014*math.sin(u*6+j*.7)+.018*u
        pts.append(((r+.006)*math.cos(a),(r+.006)*math.sin(a),z))
    curve('Fine vertical bark grain',pts,random.uniform(.002,.007),grainmat if j%4 else graingold)
for angle,zmid in [(-1.08,.57),(-2.1,.61),(.05,.50)]:
    for j in range(4):
        pts=[]
        for i in range(90):
            a=math.tau*i/90;z=zmid+(.035+j*.030)*math.sin(a);t=angle+(.18+j*.065)*math.cos(a)+.55*(z-zmid)
            r=1.61-.26*((z-.12)/.67)+.033*math.sin(t*5)+.027*math.sin(t*9+.5)
            pts.append(((r+.010)*math.cos(t),(r+.010)*math.sin(t),z))
        curve('Large organic oval bark knot contour',pts,.009,grainmat,True)
for j in range(5):
    pts=[]
    for i in range(120):
        t=-2.95+2.9*i/119;z=.19+j*.09+.055*math.sin(t*3.1+j*.42)
        r=1.61-.26*((z-.12)/.67)+.032*math.sin(t*5)+.027*math.sin(t*9+.5)
        pts.append(((r+.013)*math.cos(t),(r+.013)*math.sin(t),z))
    curve('Broad flowing grain around the timber',pts,.008,grainmat)
for angle in [-2.38,-.31,.96]:
    pts=[]
    for i in range(16):
        r=.97+.37*i/15;t=angle+.012*math.sin(i*2)
        pts.append((r*math.cos(t),r*math.sin(t),.865))
    curve('Natural radial crack in cut timber',pts,.010,grainmat)
branch=rod('Small sawn side branch',(1.33,.23,.35),(1.84,.34,.74),.185,stumpwood,48)
end=Vector((1.84,.34,.74));direction=(end-Vector((1.33,.23,.35))).normalized()
cap=sphere('Pale branch endgrain',end+direction*.008,(.182,.182,.016),endwood,48,24);cap.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
for o in CURRENT.objects:o.location.z+=.18

CURRENT=collections['07 Golden meadow']
groundmat=material('Ochre meadow soil',(.30,.091,.010),.95)
cube('Warm earth beneath the grass',(0,0,-.055),(200,200,.1),groundmat,0)
# A small grassy rise conceals the lower stump and brings the meadow into the foreground.
verts=[];faces=[];grid=70
for j in range(grid+1):
    y=-5+10*j/grid
    for i in range(grid+1):
        x=-5+10*i/grid;verts.append((x,y,.85*math.exp(-(x*x+y*y)/8)))
for j in range(grid):
    for i in range(grid):
        a=j*(grid+1)+i;faces.append((a,a+1,a+grid+2,a+grid+1))
mound=mesh('Low warm grassy hill',verts,faces,groundmat)
for p in mound.data.polygons:p.use_smooth=True
grassmat=material('Golden meadow fibres with light tips',(.68,.22,.028),.80)
n=grassmat.node_tree.nodes;l=grassmat.node_tree.links;p=n.get('Principled BSDF')
attr=n.new('ShaderNodeVertexColor');attr.layer_name='MeadowColour';l.new(attr.outputs['Color'],p.inputs['Base Color']);p.inputs['Sheen Weight'].default_value=.055;p.inputs['Specular IOR Level'].default_value=.18;p.inputs['Roughness'].default_value=.88
verts=[];faces=[];colors=[]
palette=[(.70,.18,.016),(.95,.36,.03),(.61,.12,.007),(.83,.25,.022),(.97,.45,.07),(.49,.085,.004),(.83,.29,.025)]
for j in range(96000):
    x=random.uniform(-5,5);y=random.uniform(-4,4)
    if x*x+y*y<1.48**2:continue
    z=.005+.85*math.exp(-(x*x+y*y)/8);h=random.uniform(.06,.15);width=random.uniform(.004,.009);theta=random.random()*math.tau
    dx=math.cos(theta);dy=math.sin(theta);lean=random.uniform(.03,.12);leanangle=random.random()*math.tau
    col=random.choice(palette);a=len(verts)
    for k in range(4):
        t=k/3;cx=x+lean*math.cos(leanangle)*t*t;cy=y+lean*math.sin(leanangle)*t*t;w=width*(1-t*.94)
        verts.extend([(cx-dx*w,cy-dy*w,z+h*t),(cx+dx*w,cy+dy*w,z+h*t)])
        colors.extend([tuple(min(v*(.55+.52*t),1) for v in col)+(1,)]*2)
    for k in range(3):faces.append((a+k*2,a+k*2+1,a+k*2+3,a+k*2+2))
grass=mesh('Tens of thousands of individual curved golden grass blades',verts,faces,grassmat)
vc=grass.data.color_attributes.new(name='MeadowColour',type='FLOAT_COLOR',domain='POINT')
flat=[v for c in colors for v in c];vc.data.foreach_set('color',flat)

CURRENT=collections['08 Paper scenery']
cube('Vertical warm cream seamless backdrop',(0,4.0,4.5),(200,.1,20),papermat,0)
# A physical flat cut-out starburst behind the subject.
pts=[];radii=[3.7,2.9,3.8,3.1,3.6,3.5,3.2,3.4,3.9,3.5]
for i in range(20):
    t=math.tau*i/20+.08;r=.90 if i%2 else radii[i//2]
    pts.append((r*math.cos(t),3.80,3.14+r*math.sin(t)))
star=mesh('Ten ray pale gold paper sunburst',pts,[tuple(range(20))],starmat);star.visible_shadow=False
def cloud(name,loc,width,height):
    # Overlapping soft volume lobes create a cloud silhouette in real geometry.
    parts=[]
    for i,(dx,dz,sc) in enumerate([(-.34,-.03,.34),(-.16,.13,.35),(.07,.19,.38),(.31,.035,.31)]):
        parts.append(sphere(name+' rounded lobe', (loc[0]+dx*width,loc[1],loc[2]+dz*height),(width*sc,.19,height*sc*.95),cloudmat,40,24))
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=parts[0];o.name=name+' seamless sculpted cloud'
    rem=o.modifiers.new('Unified round cloud silhouette','REMESH');rem.mode='VOXEL';rem.voxel_size=.04;rem.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=rem.name)
    sm=o.modifiers.new('Soft cotton paper cloud edges','SMOOTH');sm.factor=.7;sm.iterations=5
    o.visible_shadow=False;o.select_set(False)
cloud('High drifting ivory cloud',(1.11,3.49,5.31),1.85,1.35)
cloud('Left low paper cloud',(-3.16,3.48,3.94),2.35,1.35)
cloud('Right middle paper cloud',(3.36,3.45,2.65),2.5,1.30)
for i in range(8):
    x=-4.0+i*1.14;z=1.55+.21*math.sin(i*1.6);w=.42
    outline=[(-w/2,0),(w/2,0),(w/2,z-.19),(0,z),(-w/2,z-.19)]
    vv=[(x+a,2.70+y,b) for y in [-.055,.055] for a,b in outline]
    ff=[(4,3,2,1,0),(5,6,7,8,9)]+[(j,(j+1)%5,(j+1)%5+5,j+5) for j in range(5)]
    o=mesh('Pointed ivory fence picket %02d'%i,vv,ff,fencemat,.035);o.rotation_euler.y=.015*math.sin(i*4)
cube('Low ivory horizontal fence rail',(0,2.79,.52),(8.9,.10,.18),fencemat,.025)

CURRENT=collections['09 Foreground leaves']
stemmat=material('Golden ochre plant stems',(.28,.15,.015),.63)
leafmats=[material('Lemon golden leaf',(1,.86,.030),.5),material('Chartreuse young leaf',(.75,.86,.050),.49),material('Deep yellow ochre leaf',(.95,.64,.035),.60)]
def leaf(name,base,tip,width,mat,twist=0):
    start=Vector(base);end=Vector(tip);axis=end-start;side=Vector((axis.z,0,-axis.x)).normalized();verts=[];faces=[]
    rows=12;cols=8
    for j in range(rows+1):
        t=j/rows;mid=start+axis*t;ww=width*math.sin(math.pi*t)**.72
        for i in range(cols+1):
            u=i/cols*2-1;v=mid+side*ww*u;v.y-=.105*math.sin(math.pi*t)*(1-u*u);v.y+=twist*u*t
            verts.append(v[:])
    for j in range(rows):
        for i in range(cols):
            a=j*(cols+1)+i;faces.append((a,a+1,a+cols+2,a+cols+1))
    o=mesh(name,verts,faces,mat)
    for p in o.data.polygons:p.use_smooth=True
    s=o.modifiers.new('Paper leaf body thickness','SOLIDIFY');s.thickness=.025
    s=o.modifiers.new('Soft leaf edge','SUBSURF');s.levels=1
    curve(name+' raised central vein',[(start+axis*t+Vector((0,-.11*math.sin(math.pi*t),0)))[:] for t in [k/20 for k in range(21)]],.009,stemmat)

for plant,base,height,lean in [('Left near plant',(-1.48,-5.05,0),2.93,.36),('Right near plant',(2.73,-4.79,0),2.90,-.22),('Left low leaves',(-1.0,-5.15,0),1.64,-.26),('Right low leaves',(1.90,-5.0,0),1.65,.13)]:
    bx,by,bz=base;top=(bx+lean,by+.1,height)
    curve(plant+' arched stem',[(bx+lean*(t*t),by+.1*t,height*t) for t in [i/18 for i in range(19)]],.022,stemmat)
    for j in range(4):
        t=.25+j*.18;start=(bx+lean*t*t,by+.1*t,height*t)
        sign=(-1 if j%2 else 1)
        tip=(start[0]+sign*random.uniform(.30,.63),by-.10-random.uniform(0,.22),start[2]+random.uniform(.40,.75))
        leaf(plant+' sculpted oval leaf',start,tip,random.uniform(.28,.40),leafmats[j%3],random.uniform(-.08,.08))

CURRENT=collections['10 Studio']
def point_at(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(2.6,-15.0,4.80));camera=put(bpy.context.object,'Portrait camera - focus on rabbit face');scene.camera=camera
camera.data.lens=80;point_at(camera,(0,0,2.86))
focus=bpy.data.objects.new('Focus at front of plush face',None);CURRENT.objects.link(focus);focus.location=(0,-.55,3.45)
camera.data.dof.use_dof=True;camera.data.dof.focus_object=focus;camera.data.dof.aperture_fstop=.50;camera.data.dof.aperture_blades=7
for name,loc,energy,size,col,target in [('Large warm key',(-3.5,-4.5,8.0),1150,4.0,(1,.88,.70),(0,0,2.8)),('Soft creamy fill',(4.0,-2.5,5.5),500,5,(1,.86,.70),(0,0,3)),('Plush rim sunlight',(-3.2,2.4,7),1450,3,(1,.88,.58),(0,0,3.1))]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=put(bpy.context.object,name);o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.data.color=col;point_at(o,target)
bpy.ops.object.light_add(type='POINT',location=(-1.85,-.1,5.30));o=put(bpy.context.object,'Small warm crystal glow');o.data.energy=12;o.data.color=(1,.80,.28);o.data.shadow_soft_size=.38
bpy.ops.object.light_add(type='AREA',location=(0,-6.5,3.4));o=put(bpy.context.object,'Gentle warm front leaf fill');o.data.energy=115;o.data.shape='DISK';o.data.size=4;o.data.color=(1,.94,.65);point_at(o,(0,-4.5,1.4))
scene.world.use_nodes=True;world=scene.world.node_tree.nodes.get('Background');world.inputs['Color'].default_value=(.82,.73,.55,1);world.inputs['Strength'].default_value=.38
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=128;scene.cycles.use_denoising=True
scene.cycles.max_bounces=8;scene.cycles.transparent_max_bounces=8
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='8'
scene.render.filepath=str(OUT/'02_毛绒兔骑士.png')
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.30
nt=bpy.data.node_groups.new('Gentle golden crystal bloom','CompositorNodeTree');scene.compositing_node_group=nt
nt.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
rl=nt.nodes.new('CompositorNodeRLayers');glare=nt.nodes.new('CompositorNodeGlare');glare.inputs['Type'].default_value='Fog Glow';glare.inputs['Quality'].default_value='High';glare.inputs['Threshold'].default_value=2.0;glare.inputs['Strength'].default_value=.30;glare.inputs['Size'].default_value=.22
comp=nt.nodes.new('NodeGroupOutput');nt.links.new(rl.outputs['Image'],glare.inputs['Image']);nt.links.new(glare.outputs['Image'],comp.inputs['Image'])
scene.render.threads_mode='FIXED';scene.render.threads=8
scene['Reference']='02_毛绒兔骑士.png - reconstruction using fully editable 3D geometry and real short curly fibres'
scene['Design notes']='Pink plush knight, golden crystal sword, ochre timber shield, red cape, tree-ring stump and golden meadow. No reference image planes.'
scene['Final settings']='1000 square, Cycles OptiX, 128 samples, denoised'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'02_毛绒兔骑士.blend'))
report={'objects':len(scene.objects),'particle_systems':sum(len(o.particle_systems) for o in scene.objects),'blend':str(OUT/'02_毛绒兔骑士.blend')}
(OUT/'scene_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('RABBIT_BUILD_COMPLETE '+json.dumps(report,ensure_ascii=False),flush=True)
if '--preview' in sys.argv:
    pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';dev=pref.get_devices_for_type('OPTIX')
    for d in pref.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
    scene.render.resolution_percentage=100;scene.cycles.samples=32;scene.render.filepath=str(OUT/'preview.png')
    bpy.ops.render.render(write_still=True)
    print('RABBIT_PREVIEW_COMPLETE',flush=True)
