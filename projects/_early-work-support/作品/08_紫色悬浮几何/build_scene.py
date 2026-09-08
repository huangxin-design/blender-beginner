"""Reference-directed editable abstract sculpture; run with Blender in background."""
import bpy, math, os, sys, json, time
from pathlib import Path
from mathutils import Vector, Matrix, Euler
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
os.environ['OPTIX_CACHE_PATH']=str(ROOT.parents[1]/'setup/cache/optix')
from materials import build_materials,col
from hero_geometry import build_pleated_orb,build_ripple_sheet

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
M=build_materials()
M['navy_dark']=M['navy'].copy();M['navy_dark'].name='08 | Midnight blue satin resin'
mix=next(n for n in M['navy_dark'].node_tree.nodes if n.type=='MIX_RGB')
base=col('233761');mix.inputs[1].default_value=tuple(v*.982 for v in base[:3])+(1,);mix.inputs[2].default_value=tuple(v*1.018 for v in base[:3])+(1,)
M['lemon']=M['yellow'].copy();M['lemon'].name='08 | Lemon yellow flat enamel'
mix=next(n for n in M['lemon'].node_tree.nodes if n.type=='MIX_RGB');base=col('FFE000')
mix.inputs[1].default_value=tuple(v*.985 for v in base[:3])+(1,);mix.inputs[2].default_value=base
bs=next(n for n in M['lemon'].node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Coat Weight'].default_value=.04;bs.inputs['Specular IOR Level'].default_value=.24;bs.inputs['Subsurface Weight'].default_value=0
R=Vector((1,0,0)); U=Vector((0,.242535625,.9701425)); T=R.cross(U)
C=Vector((0,0,4.15)); BASIS=Matrix((R,U,T)).transposed()
def P(x,y,d=0):return C+R*((x-360)/80)+U*((640-y)/80)+T*d
def place(o,x,y,d=0,rot=(0,0,0)):
    o.location=P(x,y,d);o.rotation_euler=(BASIS@Euler(tuple(math.radians(v) for v in rot),'XYZ').to_matrix()).to_euler()
    o['reference_center_px']=[x,y];return o
def smooth(o):
    if o.type=='MESH':
        for p in o.data.polygons:p.use_smooth=True
    return o
def bevel(o,w=.025,segments=3):
    m=o.modifiers.new('Soft manufactured edge','BEVEL');m.width=w;m.segments=segments
    return o
def mesh(name,vs,fs,mat,bv=0):
    m=bpy.data.meshes.new(name);m.from_pydata(vs,[],fs);m.update()
    o=bpy.data.objects.new(name,m);bpy.context.scene.collection.objects.link(o);m.materials.append(mat)
    if bv:bevel(o,bv)
    return smooth(o)
def sphere(name,x,y,r,mat,d=0,scale=(1,1,1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=r)
    o=bpy.context.object;o.name=name;o.data.materials.append(mat);o.scale=scale;return place(smooth(o),x,y,d)
def cylinder(name,x,y,r,depth,mat,d=0,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=80,radius=r,depth=depth)
    o=bpy.context.object;o.name=name;o.data.materials.append(mat);bevel(o,.025);smooth(o);return place(o,x,y,d,rot)
def path(name,points,mat,width=.02,closed=False):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=16;c.bevel_depth=width;c.bevel_resolution=4
    s=c.splines.new('POLY');s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    s.use_cyclic_u=closed;o=bpy.data.objects.new(name,c);bpy.context.scene.collection.objects.link(o);c.materials.append(mat);return o
def rod(name,a,b,r,mat):
    v=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=r,depth=v.length,location=(Vector(a)+Vector(b))/2)
    o=bpy.context.object;o.name=name;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();o.data.materials.append(mat);smooth(o);bevel(o,r*.4);return o
def annulus(name,outer,inner,thickness,mat,n=128):
    vs=[];fs=[]
    for z,r in [(-thickness/2,outer),(thickness/2,outer),(thickness/2,inner),(-thickness/2,inner)]:
        vs.extend([(r*math.cos(i*2*math.pi/n),r*math.sin(i*2*math.pi/n),z) for i in range(n)])
    for ring in range(4):
        for i in range(n):j=(i+1)%n;fs.append((ring*n+i,ring*n+j,((ring+1)%4)*n+j,((ring+1)%4)*n+i))
    return mesh(name,vs,fs,mat,.025)
def torus(name,major,minor,mat,n=112,m=40):
    vs=[];fs=[]
    for i in range(n):
        a=2*math.pi*i/n
        for j in range(m):
            b=2*math.pi*j/m;r=major+minor*math.cos(b);vs.append((r*math.cos(a),r*math.sin(a),minor*math.sin(b)))
    for i in range(n):
        for j in range(m):fs.append((i*m+j,((i+1)%n)*m+j,((i+1)%n)*m+(j+1)%m,i*m+(j+1)%m))
    return mesh(name,vs,fs,mat)
def sector(name,radius,angle,thickness,mat,n=64):
    vs=[];fs=[]
    outline=[(0,0)]+[(radius*math.cos(-angle/2+angle*i/n),radius*math.sin(-angle/2+angle*i/n)) for i in range(n+1)]
    k=len(outline)
    for z in [-thickness/2,thickness/2]:vs.extend([(x,y,z) for x,y in outline])
    fs.extend([tuple(reversed(range(k))),tuple(range(k,2*k))])
    for i in range(k):j=(i+1)%k;fs.append((i,j,k+j,k+i))
    return mesh(name,vs,fs,mat,.02)
def node_group(name):
    g=bpy.data.node_groups.new(name,'GeometryNodeTree');g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    return g,g.nodes,g.links
def input_socket(g,name,kind,value):
    s=g.interface.new_socket(name=name,in_out='INPUT',socket_type=kind);s.default_value=value;return s
def modifier(o,g):m=o.modifiers.new(g.name,'NODES');m.node_group=g;return m
def empty_mesh(name):
    o=bpy.data.objects.new(name,bpy.data.meshes.new(name));bpy.context.scene.collection.objects.link(o);return o

# Hollow tubes: real difference of two node cylinders, not a painted dark cap.
def tube_group():
    g,n,l=node_group('GN | Hollow tube · radius wall length')
    for name,val in [('Radius',.3),('Wall',.055),('Length',1.0)]:input_socket(g,name,'NodeSocketFloat',val)
    input_socket(g,'Material','NodeSocketMaterial',M['pink'])
    gi=n.new('NodeGroupInput');gi.location=(-650,100)
    outer=n.new('GeometryNodeMeshCylinder');outer.location=(-380,180);outer.inputs['Vertices'].default_value=80
    inner=n.new('GeometryNodeMeshCylinder');inner.location=(-380,-100);inner.inputs['Vertices'].default_value=80
    sub=n.new('ShaderNodeMath');sub.operation='SUBTRACT';sub.location=(-600,-220)
    add=n.new('ShaderNodeMath');add.operation='ADD';add.inputs[1].default_value=.08;add.location=(-600,-380)
    l.new(gi.outputs['Radius'],outer.inputs['Radius']);l.new(gi.outputs['Length'],outer.inputs['Depth'])
    l.new(gi.outputs['Radius'],sub.inputs[0]);l.new(gi.outputs['Wall'],sub.inputs[1]);l.new(sub.outputs[0],inner.inputs['Radius'])
    l.new(gi.outputs['Length'],add.inputs[0]);l.new(add.outputs[0],inner.inputs['Depth'])
    bo=n.new('GeometryNodeMeshBoolean');bo.operation='DIFFERENCE';bo.solver='MANIFOLD';bo.location=(-100,130)
    l.new(outer.outputs['Mesh'],bo.inputs['Mesh 1']);l.new(inner.outputs['Mesh'],bo.inputs['Mesh 2'])
    sm=n.new('GeometryNodeSetShadeSmooth');sm.domain='FACE';sm.location=(110,130);l.new(bo.outputs['Mesh'],sm.inputs['Geometry'])
    mat=n.new('GeometryNodeSetMaterial');mat.location=(310,130);l.new(sm.outputs['Geometry'],mat.inputs['Geometry']);l.new(gi.outputs['Material'],mat.inputs['Material'])
    out=n.new('NodeGroupOutput');out.location=(510,130);l.new(mat.outputs['Geometry'],out.inputs['Geometry']);return g
TG=tube_group()
def tube(name,a,b,r,wall,mat):
    o=empty_mesh(name);g=TG.copy();g.name=name+' | tube parameters';v=Vector(b)-Vector(a)
    vals={'Radius':r,'Wall':wall,'Length':v.length,'Material':mat}
    for s in g.interface.items_tree:
        if s.item_type=='SOCKET' and s.in_out=='INPUT':s.default_value=vals[s.name]
    modifier(o,g)
    o.location=(Vector(a)+Vector(b))/2;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();bevel(o,.014,3);return o
def curve_solid_group(name,cube=False):
    g,n,l=node_group(name);gi=n.new('NodeGroupInput');gi.location=(-550,0)
    input_socket(g,'Radius','NodeSocketFloat',1.0);input_socket(g,'Wire','NodeSocketFloat',.018);input_socket(g,'Material','NodeSocketMaterial',M['lilac'])
    if cube:
        input_socket(g,'Size','NodeSocketVector',(1,1,1));src=n.new('GeometryNodeMeshCube');src.location=(-320,150);l.new(gi.outputs['Size'],src.inputs['Size'])
        mtc=n.new('GeometryNodeMeshToCurve');mtc.location=(-100,150);l.new(src.outputs['Mesh'],mtc.inputs['Mesh']);source=mtc.outputs['Curve']
    else:
        src=n.new('GeometryNodeCurvePrimitiveCircle');src.location=(-300,150);src.inputs['Resolution'].default_value=192;l.new(gi.outputs['Radius'],src.inputs['Radius']);source=src.outputs['Curve']
    profile=n.new('GeometryNodeCurvePrimitiveCircle');profile.location=(-120,-80);profile.inputs['Resolution'].default_value=12;l.new(gi.outputs['Wire'],profile.inputs['Radius'])
    ctm=n.new('GeometryNodeCurveToMesh');ctm.location=(120,140);l.new(source,ctm.inputs['Curve']);l.new(profile.outputs['Curve'],ctm.inputs['Profile Curve'])
    mat=n.new('GeometryNodeSetMaterial');mat.location=(340,140);l.new(ctm.outputs['Mesh'],mat.inputs['Geometry']);l.new(gi.outputs['Material'],mat.inputs['Material'])
    out=n.new('NodeGroupOutput');out.location=(560,140);l.new(mat.outputs['Geometry'],out.inputs['Geometry']);return g
RG=curve_solid_group('GN | Circular wire · path and profile')
WG=curve_solid_group('GN | Frame cube · edges to round rods',True)
def wire(name,x,y,r,mat,d=0,rot=(0,0,0),width=.018,size=None):
    g=(WG if size else RG).copy();g.name=name+' | frame parameters';o=empty_mesh(name)
    vals={'Radius':r,'Wire':width,'Material':mat,'Size':size}
    for s in g.interface.items_tree:
        if s.item_type=='SOCKET' and s.in_out=='INPUT':s.default_value=vals[s.name]
    modifier(o,g)
    return place(o,x,y,d,rot)

# Primary visual anchors.
M['orb']=M['yellow'].copy();M['orb'].name='08 | Pleated yellow matte resin'
bs=next(n for n in M['orb'].node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Coat Weight'].default_value=.03;bs.inputs['Specular IOR Level'].default_value=.22
rough=next(n for n in M['orb'].node_tree.nodes if n.type=='MAP_RANGE');rough.inputs['To Min'].default_value=.48;rough.inputs['To Max'].default_value=.52
hero=build_pleated_orb('01 | Yellow pleated orbital core',M['orb'],radius=1.08,ribs=48)
place(hero,381,474,.12,(-22,-18,0))
bpy.context.view_layer.update()
bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=.13)
cap=bpy.context.object;cap.name='01b | Soft recessed yellow dimple closure';cap.data.materials.append(M['orb']);cap.matrix_world=hero.matrix_world.copy();cap.location=hero.matrix_world@Vector((0,0,.65));cap.scale=(1,1,.7);smooth(cap)
washer=annulus('02 | Yellow broad recessed washer',1.34,.54,.18,M['lemon']);place(washer,260,710,-.45,(-10,-12,-10))
rim=annulus('02b | Raised annular lip',1.30,1.16,.075,M['lemon']);place(rim,260,710,-.32,(-10,-12,-10))
# Spherical ring with a real straight bore: its tilted opening appears off-center.
profile=[];rr=1.045;hole=.57;beta=math.asin(hole/rr)
for i in range(65):
    theta=beta+(math.pi-2*beta)*i/64;profile.append((rr*math.sin(theta),rr*math.cos(theta)))
vs=[];fs=[];nn=128;mm=len(profile)
for i in range(nn):
    a=2*math.pi*i/nn;vs.extend([(r*math.cos(a),r*math.sin(a),z) for r,z in profile])
for i in range(nn):
    for j in range(mm):fs.append((i*mm+j,((i+1)%nn)*mm+j,((i+1)%nn)*mm+(j+1)%mm,i*mm+(j+1)%mm))
bottomring=mesh('03 | White spherical ring with purple bore',vs,[tuple(reversed(f)) for f in fs],M['white']);bottomring.data.materials.append(M['purple'])
for i,p in enumerate(bottomring.data.polygons):
    if i%mm>=64:p.material_index=1
place(bottomring,145,878,-.85,(-3,32,0))
tube('04 | Large navy diagonal open tube',P(367,897,-.70),P(444,783,.90),.63,.14,M['navy_dark'])
wire('05 | Golden orbital hoop',500,650,1.72,M['gold'],1.15,(12,-8,-12),.025)
wire('06 | Spatial lilac cage',486,661,.8,M['purple'],.15,(20,-24,-1),.039,(1.65,1.52,1.32))
sphere('06b | Sphere inside cage',481,660,.40,M['navy'],.16)
rod('06c | Pink capsule inside cage',P(547,647,.05),P(520,631,.80),.27,M['lilac'])
rod('06d | Lilac lower cage pin',P(557,674,-.05),P(576,665,.20),.17,M['purple'])
sheet=build_ripple_sheet('07 | Pink corrugated floating ribbon',M['pink'],width=1.56,height=.64,depth=.14)
place(sheet,550,508,1.20,(14,-9,16))

# Upper-left tilted tube arrangement and frame.
wire('08 | Large open parallelogram frame',238,413,.9,M['lilac'],-.70,(30,13,21),.019,(1.90,1.02,.85))
tube('09 | Upper pink open cylinder',P(197,410,.02),P(217,347,.74),.27,.045,M['pink'])
tube('10 | Upper navy open cylinder',P(236,468,-.18),P(264,366,.84),.285,.070,M['navy'])
wire('11 | Tiny yellow cube',148,377,.3,M['gold'],.10,(19,-15,20),.014,(.30,.60,.32))
wire('12 | Top right horizontal lower pink tube ring',485,353,.055,M['white'],.21,(0,0,0),.013)
tube('12b | Top right pink long tube',P(486,353,.8),P(642,353,-.1),.090,.027,M['lilac'])
tube('13 | Top right blue long tube',P(549,326,.8),P(649,326,-.1),.100,.029,M['navy_dark'])

# Purple pointed polyhedron over the pleated core.
poly=mesh('14 | Faceted lavender kite',[(0,.68,0),(-.55,.16,.10),(-.32,-.51,.03),(.38,-.02,-.20),(0,.09,.29)],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,3,2,1)],M['lilac'])
poly.data.materials.append(M['purple']);poly.data.materials.append(M['white'])
for i,p in enumerate(poly.data.polygons):p.use_smooth=False;p.material_index=[0,2,1,1,0][i]
place(poly,405,405,1.23,(0,-5,-9))
sl=sector('15 | Upper purple circular sector',1.16,math.radians(62),.13,M['purple']);place(sl,505,475,-.4,(10,12,59))
rod('15b | Pale bevel line across sector',P(505,475,-.22),P(565,382,-.22),.025,M['white'])

# Central diagonal stems and smaller discs.
sphere('16 | Upper pale sphere',250,530,.54,M['white'],-.75)
rod('17 | Long lilac back rod',P(241,505,-.4),P(368,615,-.4),.11,M['lilac'])
tube('18 | Thin pink horizontal pipe',P(269,586,.47),P(443,573,.46),.095,.025,M['pink'])
tube('19 | Left diagonal golden tube',P(72,620,.85),P(153,542,.16),.265,.060,M['yellow'])
wire('19b | Navy open end detail',72,633,.25,M['navy'],1.22,(25,30,-5),.033)
wire('20 | Small lilac satellite loop',174,526,.19,M['lilac'],-.02,(4,20,0),.060)
disk=cylinder('21 | Blue studded circular button',195,627,.67,.10,M['navy'],1.08,(9,-13,16))
bpy.context.view_layer.update()
for i,(x,y) in enumerate([(-.23,.23),(.14,.37),(-.43,.04),(-.03,.10),(.35,.10),(-.26,-.20),(.16,-.18),(-.06,-.42)]):
    pos=disk.matrix_world@Vector((x,y,.12));v=disk.matrix_world.to_3x3()@Vector((0,0,.13))
    rod('21 stud %02d'%i,pos,pos+v,.09,M['navy']);bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=.09,location=pos+v)
    o=bpy.context.object;o.name='21 rounded stud cap';o.data.materials.append(M['navy']);smooth(o)
rod('22 | Arrow shaft',P(115,674,1.28),P(137,647,1.28),.070,M['lilac'])
v=P(152,628,1.28)-P(134,651,1.28)
bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=.18,radius2=.01,depth=v.length,location=(P(152,628,1.28)+P(134,651,1.28))/2)
o=bpy.context.object;o.name='22 arrow head';o.rotation_euler=v.to_track_quat('Z','Y').to_euler();o.data.materials.append(M['lilac']);bevel(o,.01);smooth(o)

# Lower fragmented discs, transparent-looking outlines, and foreground pipes.
lowsec=sector('23 | Left lower lavender fan',.94,math.radians(85),.13,M['purple']);place(lowsec,103,701,.35,(12,-16,-46))
rod('23b | Fan pale cut edge',P(102,700,.49),P(174,717,.49),.023,M['white'])
sec=sector('24 | Central pale arc shard',.79,math.pi,.13,M['lilac']);place(sec,334,716,1.0,(0,0,-62))
sec.data.materials.append(M['white'])
arrow=mesh('25 | Pale triangular shard',[(0,.25,.03),(-.13,-.16,.03),(.35,-.10,.03),(0,.25,-.06),(-.13,-.16,-.06),(.35,-.10,-.06)],[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)],M['white'],.012);place(arrow,373,731,1.55,(0,0,10))
tube('26 | Front lower pink hollow pipe',P(312,886,.2),P(199,832,1.25),.30,.047,M['pink'])
cylinder('26b | White collar plate',272,843,.43,.09,M['white'],.77,(18,-32,12))
rod('27 | Front pink diagonal rod',P(461,858,1.38),P(578,716,1.38),.105,M['pink'])
rod('28 | Short lilac bottom rod',P(389,943,1.16),P(438,887,1.16),.10,M['lilac'])
tube('29 | Right upright purple cup',P(627,823,.1),P(628,748,.75),.25,.075,M['purple'])
cylinder('30 | Lower blue coin',468,927,.34,.055,M['navy_dark'],.2,(14,38,-10))
profile=[(.001,-.12),(.2,-.10),(.4,-.03),(.61,.11),(.74,.25),(.79,.29),(.81,.25),(.79,.17),(.67,-.03),(.4,-.20),(.001,-.24)]
vs=[];fs=[];nn=128;mm=len(profile)
for i in range(nn):
    a=math.tau*i/nn;vs.extend([(r*math.cos(a),r*math.sin(a),z) for r,z in profile])
for i in range(nn):
    for j in range(mm):fs.append((i*mm+j,((i+1)%nn)*mm+j,((i+1)%nn)*mm+(j+1)%mm,i*mm+(j+1)%mm))
plate=mesh('31 | Gold curved shallow dish',vs,[tuple(reversed(f)) for f in fs],M['gold']);sub=plate.modifiers.new('Smooth dish curvature','SUBSURF');sub.levels=2
place(plate,589,909,.18,(31,-21,14));plate.scale=(1,.83,1)
rod('31c | Dish foot',P(613,942,-.15),P(617,953,-.15),.075,M['gold'])
sphere('31d | Purple ball over dish',569,900,.23,M['purple'],1.12)
perforated=cylinder('32 | Pink waffle disc',580,846,.45,.11,M['pink'],1.03,(22,20,-13))
bpy.context.view_layer.update()
for i,(x,y) in enumerate([(-.20,.19),(.02,.24),(.23,.13),(-.25,-.02),(-.03,.02),(.18,-.09),(-.15,-.22),(.06,-.23)]):
    # Real toroidal recess lips, with a dark material at their shallow centers.
    pos=perforated.matrix_world@Vector((x,y,.07))
    o=torus('32 curled lattice rim %02d'%i,.068,.033,M['pink'],32,12);o.matrix_world=perforated.matrix_world.copy();o.location=pos

# Decorative particles: deliberate reference positions, varied depth.
for i,(x,y,r,key,d) in enumerate([
    (80,336,.145,'navy',-.2),(79,369,.140,'pink',-.1),(80,400,.145,'yellow',-.1),(80,432,.14,'lilac',-.15),
    (87,545,.275,'pink',1.0),(398,351,.090,'yellow',.1),(495,399,.14,'navy',.3),(492,426,.135,'pink',.4),
    (638,395,.058,'gold',0),(644,530,.185,'lilac',.4),(598,577,.13,'pink',.2),(630,618,.18,'yellow',.7),
    (190,687,.18,'pink',.75),(352,815,.35,'lilac',1.2),(80,762,.12,'navy',.25),(80,795,.12,'yellow',.45),
    (548,789,.10,'lilac',.4),(503,747,.065,'yellow',.1)]):sphere('Particle %02d'%i,x,y,r,M[key],d)
for i,(x,y,r,key) in enumerate([(608,452,.21,'navy'),(484,497,.12,'gold'),(80,704,.20,'pink')]):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=r);o=bpy.context.object;o.name='Faceted fragment %02d'%i;o.data.materials.append(M[key]);place(o,x,y,.6,(10,24,15));bevel(o,.045)
rod('33 | Upper orange sliver',P(337,382,-.6),P(331,359,-.6),.045,M['gold'])
rod('34 | Small left spindle',P(98,471,-.3),P(150,490,-.3),.115,M['lilac'])
cylinder('34b | Spindle collar',119,467,.27,.11,M['lilac'],-.25,(0,70,-19))

# Hairline graphics are spatial curves with subtle physical thickness.
def screen_rect(name,x0,y0,x1,y1,d,mat,width=.005):return path(name,[P(x0,y0,d),P(x1,y0,d),P(x1,y1,d),P(x0,y1,d)],mat,width,True)
screen_rect('35 | Upper fine outline',359,329,449,420,-.88,M['lilac'])
screen_rect('36 | Left fine outline',51,505,195,649,-.85,M['lilac'])
screen_rect('37 | Lower peach fine outline',226,878,299,950,-.62,M['pink'])
path('38 | Lower tilted diamond',[P(241,718,-.92),P(333,666,-.92),P(529,880,-.92),P(437,934,-.92)],M['lilac'],.009,True)
for x in [359,449]:
    bpy.ops.mesh.primitive_cube_add(size=.12);o=bpy.context.object;o.name='Upper outline corner marker';o.data.materials.append(M['lilac']);place(o,x,329,-.87)

# Art-directed studio shadow selection keeps fine floating rods from drawing lines on the floor.
for o in bpy.context.scene.objects:
    if o.type=='CURVE' or o.name.startswith(('05 |','08 |','11 |','17 |','18 |','22 |','27 |','28 |','33 |','34 |','34b |','35 |','36 |','37 |','38 |')):
        o.visible_shadow=False
    if o.name.startswith(('19 |','21 |','21 stud','21 rounded','23 |','23b |','Particle','Faceted fragment 02')):
        o.visible_shadow=False

# Stage: reference's horizontal seam at y~854 and lighter foreground.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0));floor=bpy.context.object;floor.name='STAGE | Light lilac shadow floor';floor.data.materials.append(M['floor'])
wall=mesh('STAGE | Lavender gradient wall',[(-50,5.5,0),(50,5.5,0),(50,5.5,40),(-50,5.5,40)],[(0,1,2,3)],M['backdrop'])
nt=M['backdrop'].node_tree;n=nt.nodes;l=nt.links;bs=next(x for x in n if x.type=='BSDF_PRINCIPLED')
geo=n.new('ShaderNodeNewGeometry');geo.location=(-650,100);sep=n.new('ShaderNodeSeparateXYZ');sep.location=(-460,100);l.new(geo.outputs['Position'],sep.inputs[0])
mp=n.new('ShaderNodeMapRange');mp.location=(-270,100);mp.inputs['From Min'].default_value=0;mp.inputs['From Max'].default_value=9.73;l.new(sep.outputs['Z'],mp.inputs['Value'])
ramp=n.new('ShaderNodeValToRGB');ramp.location=(-50,100);ramp.color_ramp.elements[0].color=tuple(v*2**.2 for v in col('D6B8E5')[:3])+(1,);ramp.color_ramp.elements[1].color=tuple(v*2**.2 for v in col('A076C4')[:3])+(1,);l.new(mp.outputs[0],ramp.inputs[0]);l.new(ramp.outputs['Color'],bs.inputs['Base Color'])
em=n.new('ShaderNodeEmission');em.inputs['Strength'].default_value=1.0;em.location=(220,-130);l.new(ramp.outputs['Color'],em.inputs['Color'])
lp=n.new('ShaderNodeLightPath');lp.location=(200,-360)
mix=n.new('ShaderNodeMixShader');mix.location=(460,0);l.new(lp.outputs['Is Camera Ray'],mix.inputs[0]);l.new(bs.outputs['BSDF'],mix.inputs[1]);l.new(em.outputs['Emission'],mix.inputs[2]);out=next(x for x in n if x.type=='OUTPUT_MATERIAL');l.new(mix.outputs['Shader'],out.inputs['Surface'])
# Keep the distant foreground bright while leaving the sculpture's shadow region diffuse.
nt=M['floor'].node_tree;n=nt.nodes;l=nt.links;bs=next(x for x in n if x.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=col('F0D9F4')
geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],sep.inputs[0])
fade=n.new('ShaderNodeMapRange');fade.inputs['From Min'].default_value=-2.0;fade.inputs['From Max'].default_value=-7;fade.inputs['To Min'].default_value=0;fade.inputs['To Max'].default_value=1;l.new(sep.outputs['Y'],fade.inputs['Value'])
em=n.new('ShaderNodeEmission');em.inputs['Color'].default_value=tuple(v*2**.2 for v in col('ECD7F0')[:3])+(1,);em.inputs['Strength'].default_value=1.0
lp=n.new('ShaderNodeLightPath');mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(lp.outputs['Is Camera Ray'],mult.inputs[0]);l.new(fade.outputs[0],mult.inputs[1])
mix=n.new('ShaderNodeMixShader');l.new(mult.outputs[0],mix.inputs[0]);l.new(bs.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);out=next(x for x in n if x.type=='OUTPUT_MATERIAL');l.new(mix.outputs[0],out.inputs['Surface'])

scene=bpy.context.scene;scene.name='08 | Lavender floating geometry'
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=C+T*23);cam=bpy.context.object;cam.name='CAMERA | Fixed reference composition';aim(cam,C);cam.data.type='ORTHO';cam.data.ortho_scale=16;scene.camera=cam
def light(name,pos,power,size,color,target=(0,0,3.5)):
    d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;d.energy=power;d.shape='DISK';d.size=size;d.color=color;aim(o,target)
light('KEY | Large upper left softbox',(-4.8,-3.0,10),1000,2.8,(1,.94,.98))
light('FILL | Open cool right shadows',(5,-3,6),160,5,(.85,.87,1))
light('RIM | Soft back top highlight',(-1,3.5,10),180,3.0,(1,.91,.86))
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.66,.60,.80,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.32
scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.014;scene.cycles.adaptive_min_samples=16;scene.cycles.use_denoising=True
scene.cycles.max_bounces=8;scene.cycles.transparent_max_bounces=6
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.render.resolution_x=576;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=-.2
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='8'
scene.render.film_transparent=False;scene.render.use_compositing=False
scene['Reference']='08_紫色悬浮几何.png; single-frame native 3D reconstruction, no invented video motion'
scene['Workflow']='Reference anchors → geometry preview → material and lighting → native render → comparison'
scene['GeometryNodes']='Pleated core, ripple sheet, hollow tubes, cube frames and wire circles remain editable.'
for o in scene.objects:o.select_set(False)
cam.select_set(True);bpy.context.view_layer.objects.active=cam
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'08_紫色悬浮几何.blend'))
start=time.time()
clay=bpy.data.materials.new('CHECK | Neutral matte clay');clay.diffuse_color=(.55,.55,.55,1);clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.55,.55,.55,1);clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.65
scene.view_layers[0].material_override=clay;scene.render.filepath=str(ROOT/'clay_preview.png');bpy.ops.render.render(write_still=True);scene.view_layers[0].material_override=None
scene.render.filepath=str(ROOT/'preview.png');bpy.ops.render.render(write_still=True)
(ROOT/'preview_report.json').write_text(json.dumps({'objects':len(scene.objects),'geometry_node_groups':[g.name for g in bpy.data.node_groups if g.type=='GEOMETRY'],'seconds':time.time()-start},ensure_ascii=False,indent=2),encoding='utf8')
print('PREVIEW_COMPLETE',flush=True)
