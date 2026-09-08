"""Editable three dimensional reconstruction of the supplied pink still life."""
import bpy, math, random, sys, json, time
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi

OUT=Path(__file__).resolve().parent
OUT.mkdir(parents=True,exist_ok=True)
random.seed(11)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials): bpy.data.materials.remove(d)

def mat(name,color,rough=.36,metal=0,noise=0,trans=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    n=m.node_tree.nodes; p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    p.inputs['Transmission Weight'].default_value=trans
    if noise:
        t=n.new('ShaderNodeTexNoise'); t.inputs['Scale'].default_value=110
        t.inputs['Detail'].default_value=2
        b=n.new('ShaderNodeBump'); b.inputs['Strength'].default_value=noise
        b.inputs['Distance'].default_value=.025
        m.node_tree.links.new(t.outputs['Fac'],b.inputs['Height'])
        m.node_tree.links.new(b.outputs['Normal'],p.inputs['Normal'])
    return m

pink=mat('Background | rose quartz',(.84,.25,.30),.62)
pink.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(1.2,.16,.22,1)
pink.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.45
rose=mat('Glossy rose enamel',(.72,.32,.39),.23)
rose_light=mat('Rose porcelain',(.85,.34,.43),.22)
pillar_mat=mat('Fine peach stone',(.72,.29,.27),.49,noise=.12)
coral=mat('Coral ribbed rubber',(.64,.10,.046),.42)
blue=mat('Powder blue lacquer',(.30,.45,.76),.27)
lidblue=mat('Sky blue eye helmets',(.16,.45,.80),.23)
blue_edge=mat('Pale blue edge',(.72,.83,.92),.24)
purple=mat('Deep lavender',(.205,.18,.345),.31)
pearl=mat('Grey sage pearls',(.32,.39,.35),.17)
white=mat('Ivory glass ceramic',(.87,.91,.84),.19)
ivory=mat('Warm ivory grid capsule',(.86,.88,.75),.4)
gridmat=mat('Fine grid threads',(.50,.57,.40),.67)
gold=mat('Satin champagne gold',(.72,.48,.22),.24,.82)
brass=mat('Fine warm brass',(.55,.32,.12),.28,.82)
silver=mat('Brushed warm silver',(.78,.79,.77),.22,.94,noise=.04)
reddish=mat('Eye socket terracotta',(.49,.075,.045),.29)
iris=mat('Warm pale grey iris',(.39,.40,.34),.2)
black=mat('Bee charcoal plum',(.064,.048,.075),.37)
yellow=mat('Bee honey stripes',(1.0,.40,.03),.33)
wing=mat('Translucent opal wings',(.91,.85,.78),.28,trans=.20)
fuzzpink=mat('Peach velvet',(.94,.38,.34),.8,noise=.35)
fuzzpink.node_tree.nodes.get('Principled BSDF').inputs['Sheen Weight'].default_value=.6
hairmat=mat('Peach fibres',(.91,.63,.59),.9)
wood=mat('Pale golden wood',(.64,.43,.18),.52,noise=.13)
paper=mat('Cream paper',(.91,.84,.61),.74,noise=.08)
clothmat=mat('Warm cream folded paper',(.82,.78,.49),.78,noise=.12)
lilac=mat('Lilac book cloth',(.44,.38,.68),.48)
strapmat=mat('Warm grey silicone watchband',(.33,.34,.31),.57)
screenmat=mat('Black watch screen',(.045,.06,.06),.2)
glass=mat('Spectacle lens glass',(.98,.99,.98),.045,trans=1)
glass.node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=1.08
gn=glass.node_tree.nodes;gl=glass.node_tree.links
transparent=gn.new('ShaderNodeBsdfTransparent');gmix=gn.new('ShaderNodeMixShader');gmix.inputs[0].default_value=.94
gl.new(gn.get('Principled BSDF').outputs[0],gmix.inputs[1]);gl.new(transparent.outputs[0],gmix.inputs[2]);gl.new(gmix.outputs[0],gn.get('Material Output').inputs['Surface'])
tortoise=mat('Tortoiseshell spectacle frames',(.115,.10,.08),.3)
rose_light.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.32
rose_light.node_tree.nodes.get('Principled BSDF').inputs['Coat Roughness'].default_value=.13

def finish(o,name,m,smooth=False):
    o.name=name
    if m: o.data.materials.append(m)
    if smooth and o.type=='MESH':
        for p in o.data.polygons:p.use_smooth=True
    return o
def mesh(name,v,f,m,smooth=False):
    d=bpy.data.meshes.new(name);d.from_pydata(v,[],f);d.update()
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
    return finish(o,name,m,smooth)
def sphere(name,loc,scale,m,seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=32,location=loc)
    o=bpy.context.object;o.scale=scale;return finish(o,name,m,True)
def cube(name,loc,scale,m,bevel=.04):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object
    o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finish(o,name,m)
    if bevel:
        q=o.modifiers.new('Soft manufactured edges','BEVEL');q.width=bevel;q.segments=4
        q=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return o
def cyl(name,loc,r,depth,m,verts=96):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc)
    o=finish(bpy.context.object,name,m)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return o
def tube(name,pts,r,m,cyclic=False):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=12
    c.bevel_depth=r;c.bevel_resolution=3
    s=c.splines.new('POLY');s.points.add(len(pts)-1)
    for p,co in zip(s.points,pts):p.co=(*co,1)
    s.use_cyclic_u=cyclic
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);finish(o,name,m);return o
def lathe(name,profile,m,loc=(0,0,0),n=96):
    v=[(loc[0]+r*cos(a*2*pi/n),loc[1]+r*sin(a*2*pi/n),loc[2]+z) for r,z in profile for a in range(n)]
    f=[]
    for j in range(len(profile)-1):
        for i in range(n):a=j*n+i;b=j*n+(i+1)%n;f.append((a,b,b+n,a+n))
    return mesh(name,v,f,m,True)
def capsule(name,center,r,length,m,axis='Z'):
    body=length/2-r
    profile=[(r*cos(a),-body+r*sin(a)) for a in [-pi/2+pi/2*i/16 for i in range(17)]]
    profile += [(r,body)]
    profile += [(r*cos(a),body+r*sin(a)) for a in [pi/2*i/16 for i in range(1,17)]]
    o=lathe(name,profile,m)
    o.location=center
    if axis=='X':o.rotation_euler.y=pi/2
    return o
def hemisphere(name,center,r,m,upper=True,zscale=1):
    angles=[(0 if upper else pi/2)+pi/2*i/24 for i in range(25)]
    return lathe(name,[(r*sin(a),r*cos(a)*zscale) for a in reversed(angles)],m,center)
def extrude(name,points,depth,m,y=0,bevel=.025):
    n=len(points);v=[(x,y+d,z) for d in [-depth/2,depth/2] for x,z in points]
    f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=mesh(name,v,[tuple(reversed(face)) for face in f],m)
    if bevel:q=o.modifiers.new('Rounded perimeter','BEVEL');q.width=bevel;q.segments=3
    o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o
def roundedrect(w,h,r,n=16):
    pts=[]
    for cx,cz,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,pi/2),(-w/2+r,-h/2+r,pi),(w/2-r,-h/2+r,3*pi/2)]:
        pts += [(cx+r*cos(start+pi/2*i/n),cz+r*sin(start+pi/2*i/n)) for i in range(n)]
    return pts
def ringframe(name,center,w,h,r,iw,ih,ir,depth,m):
    raw_outer=roundedrect(w,h,r);raw_inner=roundedrect(iw,ih,ir)
    outer=[];inner=[]
    for i in range(len(raw_outer)):
        j=(i+1)%len(raw_outer)
        steps=max(1,math.ceil(max(math.dist(raw_outer[i],raw_outer[j]),math.dist(raw_inner[i],raw_inner[j]))/.07))
        for k in range(steps):
            t=k/steps
            outer.append(tuple(a+(b-a)*t for a,b in zip(raw_outer[i],raw_outer[j])))
            inner.append(tuple(a+(b-a)*t for a,b in zip(raw_inner[i],raw_inner[j])))
    n=len(outer)
    v=[(center[0]+x,center[1]+y,center[2]+z) for y in [-depth/2,depth/2] for outline in [outer,inner] for x,z in outline]
    f=[]
    for i in range(n):
        j=(i+1)%n
        f += [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)]
    o=mesh(name,v,f,m,True)
    for vertex in o.data.vertices:
        t=(vertex.co.x-center[0])/w;weight=max(0,(vertex.co.z-center[2])/(h/2))**2
        vertex.co.z += (.12*sin(t*8.5)+.025*sin(t*18))*weight
        vertex.co.y -= .14*cos(t*9)*weight
    q=o.modifiers.new('Soft glazed corners','BEVEL');q.width=.11;q.segments=5
    o.modifiers.new('Weighted glazed surface normals','WEIGHTED_NORMAL');return o
def point(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()

# Backdrop and the broad pink display pedestal.
cyl('Large rose display plinth',(0,2.3,-2.50),5.6,5.0,pink,192)
# World camera rays provide a perfectly even pink sweep behind the plinth.

# Rounded coral organ column, including individual continuous vertical ribs.
capsule('Coral central core',(-.45,.62,6.13),.67,3.85,coral)
for j in range(22):
    a=2*pi*j/22;pts=[]
    for k in range(20):pts.append((-.45+.655*cos(a),.62+.655*sin(a),4.2+(7.36-4.2)*k/19))
    for k in range(1,25):
        t=(pi/2-.07)*k/24;pts.append((-.45+.655*cos(t)*cos(a),.62+.655*cos(t)*sin(a),7.36+.655*sin(t)))
    tube('Coral flute %02d'%j,pts,.075,coral)

# Tall plates and small cylinder stacked above the pink central block.
arch=[(-.20,1.05),(1.93,1.05),(1.93,5.58)]
arch += [(.865+1.065*cos(a),5.58+1.065*sin(a)) for a in [pi*i/48 for i in range(49)]]
arch += [(-.20,1.05)]
extrude('Ivory edge of large arched panel',[(x+.075,z+.005) for x,z in arch],.32,blue_edge,y=.43)
extrude('Powder blue arched panel',arch,.28,blue,y=.20)
extrude('Deep purple curved inset',[(-.12,1.10),(1.38,1.10),(1.37,2.3),(1.32,3.0),(1.15,3.7),(.82,4.4),(.4,5.06),(-.03,5.7),(-.16,5.95)],.035,purple,y=.037,bevel=.012)
extrude('Slim left blue sail',[(-1.50,3.75),(-1.50,6.89),(-1.39,6.68),(-1.28,6.29),(-1.18,5.73),(-1.05,4.1)],.14,blue,y=.37)
cube('Rose stone rectangular pillar',(-.12,-.15,4.89),(1.23,.85,3.40),pillar_mat,.035)
cyl('Small warm wood cylinder',(.20,.24,6.76),.37,.58,wood)
cyl('Powder blue cylinder cap',(.20,.24,7.28),.40,.53,blue)
for j,z in enumerate([7.12,6.44,5.77,5.10]):sphere('Sage pearl %d'%(j+1),(.67,-.65,z),(.305,.305,.325),pearl)
tube('Architectural fine brass handle',[(.66,.52,6.65),(.96,.52,8.03),(1.35,.52,8.03),(1.88,.52,6.32)],.018,brass)

# Two half-lidded eyes, each made of an actual globe, socket and blue shell.
def eye(name,x,y,z,r):
    sphere(name+' terracotta socket',(x,y,z),(r,r*.72,r),reddish)
    sphere(name+' ivory eyeball',(x+.06,y-r*.39,z+.015),(r*.74,r*.62,r*.77),white)
    sphere(name+' pale iris',(x+r*.26,y-r*.93,z+r*.12),(r*.29,.045,r*.29),iris)
    hemisphere(name+' blue hemispherical eyelid',(x,y-.045,z+r*.25),r*1.08,lidblue,True,.75)
eye('Upper eye',-.72,-.69,5.50,.57)
eye('Lower eye',.84,-.64,4.15,.46)
tube('Pink elbow left',[(-.66,-.47,4.94),(-1.05,-.50,4.98),(-1.19,-.50,4.80),(-1.19,-.5,4.30)],.11,rose)
capsule('Small pink side peg',(.48,-.90,3.69),.105,.46,rose_light)

# Delicate gridded ivory capsule in front of the tall block.
cx,cy,cz,r,L=.00,-1.16,4.53,.325,1.98
capsule('Ivory gridded capsule',(cx,cy,cz),r,L,ivory)
straight=L/2-r
for k in range(11):
    z=-L/2+.075+k*(L-.15)/10
    rad=r if abs(z)<=straight else math.sqrt(max(0,r*r-(abs(z)-straight)**2))
    tube('Grid latitude %02d'%k,[(cx+(rad+.002)*cos(t),cy+(rad+.002)*sin(t),cz+z) for t in [2*pi*i/96 for i in range(96)]],.003,gridmat,True)
for k in range(16):
    a=2*pi*k/16;pts=[]
    for i in range(65):
        z=-L/2+.008+(L-.016)*i/64
        rad=r if abs(z)<=straight else math.sqrt(max(0,r*r-(abs(z)-straight)**2))
        pts.append((cx+(rad+.002)*cos(a),cy+(rad+.002)*sin(a),cz+z))
    tube('Grid meridian %02d'%k,pts,.003,gridmat)

# The suspended split ceramic / gold sphere and its fine rectangular frame.
hemisphere('White upper half of suspended globe',(-1.42,-.91,4.03),.76,white,True)
hemisphere('Gold lower half of suspended globe',(-1.42,-.91,4.03),.76,gold,False)
for k in range(7):
    a=2*pi*k/7
    tube('Fine meridian on white globe %d'%k,[(-1.42+.762*sin(t)*cos(a),-.91+.762*sin(t)*sin(a),4.03+.762*cos(t)) for t in [pi/2*i/40 for i in range(41)]],.0028,ivory)
tube('Brass suspension frame',[(-1.88,-1.01,2.22),(-1.88,-1.01,4.80),(-1.00,-1.01,4.80),(-1.,-1.01,2.22)],.018,brass,True)
tube('Suspension short cord',[(-1.42,-.91,4.77),(-1.42,-.91,4.55)],.012,brass)

# Soft pink open sculptural stool and the stacked pebbles seen through it.
for i in range(5):
    p=sphere('Stacked violet pebble %02d'%i,(.42,-.05,1.64+i*.40),(.56,.36,.245),purple)
    p.rotation_euler.y=(-.10 if i%2 else .09)
sphere('Small coral sphere in stool opening',(1.03,-.22,1.84),(.32,.32,.32),coral)
sphere('Upright rose pebble in lower opening',(.15,-.50,1.00),(.47,.39,.90),rose_light)
frame_mat=rose_light.copy();frame_mat.name='Glossy soft pink sculptural ring'
frame_shader=frame_mat.node_tree.nodes.get('Principled BSDF')
frame_shader.inputs['Roughness'].default_value=.18
frame_shader.inputs['Coat Weight'].default_value=.60
frame_shader.inputs['Coat Roughness'].default_value=.07
ringframe('Sculptural pink hollow stool',(.74,-.42,1.85),2.42,2.46,.46,1.43,1.54,.48,.52,frame_mat)
# Large pale discs behind the main arrangement.
sphere('Left pink background disc',(-2.22,.54,1.54),(1.2,.18,1.18),rose_light)
sphere('Upper right pink background disc',(1.93,.90,3.47),(.82,.12,.95),rose_light)
sphere('Lower right pink background disc',(1.91,.90,1.89),(.84,.12,.86),rose_light)

# Bees with ellipsoid stripe bands, distinct eyes, wings, antennae and feet.
def bee(name,loc,scale,tilt=0,reverse=False):
    before=set(bpy.data.objects)
    body=sphere(name+' body',(0,0,0),(.46,.235,.27),black)
    for k,x in enumerate([-.23,-.04,.15,.32]):
        rr=math.sqrt(1-(x/.48)**2)
        pts=[(x,.24*rr*cos(a),.275*rr*sin(a)) for a in [2*pi*i/64 for i in range(64)]]
        tube(name+' honey stripe %d'%k,pts,.033,yellow,True)
    sphere(name+' head',(-.46,-.015,-.015),(.19,.20,.19),black)
    for zz in [.06,-.075]:
        sphere(name+' white eye',(-.535,-.18,zz),(.081,.043,.086),white,32)
        sphere(name+' dark pupil',(-.559,-.216,zz+.005),(.037,.021,.043),black,24)
    for xx,angle in [(-.19,-.52),(.12,.60)]:
        w=sphere(name+' opal wing',(xx,.14,.27),(.18,.055,.27),wing)
        w.rotation_euler=(-.65,angle,0)
        vein=[Vector(w.location)+w.rotation_euler.to_matrix() @ Vector((0,-.045,zz)) for zz in [-.17,0,.20]]
        tube(name+' wing vein',vein,.006,white)
    for dy in [-.04,.10]:
        tube(name+' antenna',[(-.51,dy,.12),(-.60,dy,.30),(-.54,dy,.41)],.014,black)
    bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=.115,radius2=0,depth=.25,location=(.54,0,.035))
    o=finish(bpy.context.object,name+' pointed tail',black,True);o.rotation_euler.y=pi/2
    for x in [-.23,.02,.22]:tube(name+' little leg',[(x,-.12,-.17),(x+.05,-.20,-.28),(x+.13,-.20,-.26)],.012,black)
    parts=set(bpy.data.objects)-before
    root=bpy.data.objects.new(name+' assembly',None);bpy.context.collection.objects.link(root)
    for o in parts:o.parent=root
    root.location=loc;root.scale=(scale*.78,)*3;root.rotation_euler.y=tilt
    if reverse:root.rotation_euler.z=pi
bee('Flying bee',(2.20,-.42,5.79),.94,-.15)
bee('Bee resting above cup',(-1.36,-1.44,2.38),.88,.32,True)

# The metallic open cup; cross section includes both walls and a real inner floor.
cupx,cupy=-.97,-1.77
profile=[(0,.055),(.515,.055),(.54,.075),(.55,.22),(.56,1.83),(.555,1.88),(.529,1.88),(.525,1.81),(.509,.16),(0,.16)]
lathe('Hollow silver cup',profile,silver,(cupx,cupy,0))
tube('Cup rolled rim',[(cupx+.543*cos(t),cupy+.543*sin(t),1.874) for t in [2*pi*i/128 for i in range(128)]],.012,silver,True)
tube('Cup low seam',[(cupx+.548*cos(t),cupy+.548*sin(t),.24) for t in [2*pi*i/128 for i in range(128)]],.012,silver,True)

# Wooden layers below the central arrangement.
for i in range(3):cube('Thin stacked wooden plinth %d'%i,(-.17,-.48,.07+i*.115),(2.34,1.22,.11),wood,.012)
for i in range(14):tube('Wood grain %02d'%i,[(-1.28,-1.094,.025+i*.024),(.96,-1.094,.025+i*.024)],.002,paper)

# Plush peach capsules with real short fibre curves and silicone watch strap.
def furry_pill(name,loc,r,length,tilt=0,fibres=10000):
    before=set(bpy.data.objects)
    o=capsule(name+' velvet body',(0,0,0),r,length,fuzzpink,axis='X')
    c=bpy.data.curves.new(name+' short fibres','CURVE');c.dimensions='3D';c.resolution_u=1;c.bevel_depth=.0017;c.bevel_resolution=0
    half=length/2-r
    for i in range(fibres):
        x=random.uniform(-length/2,length/2);a=random.uniform(0,2*pi)
        if abs(x)<=half:rr=r;normal=Vector((0,cos(a),sin(a)))
        else:
            dx=abs(x)-half;rr=math.sqrt(max(0,r*r-dx*dx));normal=Vector((math.copysign(dx,x),rr*cos(a),rr*sin(a))).normalized()
        p=Vector((x,rr*cos(a),rr*sin(a)));q=p+normal*random.uniform(.009,.021)
        s=c.splines.new('POLY');s.points.add(1);s.points[0].co=(*p,1);s.points[1].co=(*q,1)
    ob=bpy.data.objects.new(name+' peach fuzz',c);bpy.context.collection.objects.link(ob);finish(ob,name+' peach fuzz',hairmat)
    root=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(root)
    for ob in set(bpy.data.objects)-before:
        if ob!=root:ob.parent=root
    root.location=loc;root.rotation_euler.y=tilt
furry_pill('Left peach cushion',(-2.35,-1.21,.65),.55,2.00,-.17,8000)
furry_pill('Watch cushion',(1.72,-1.91,.60),.57,3.20,0,15000)

# Closed silicone band, with a small rose-gold smartwatch facing the camera.
wx=1.25;wy=-1.91;wz=.60
prof=[(.566,-.17),(.599,-.17),(.599,.17),(.566,.17),(.566,-.17)]
band=lathe('Silicone wrist strap',prof,strapmat);band.rotation_euler.y=pi/2;band.location=(wx,wy,wz)
watchroot=bpy.data.objects.new('Watch assembly',None);bpy.context.collection.objects.link(watchroot)
frame=cube('Rose gold watch case',(0,0,0),(.50,.13,.59),gold,.065);frame.parent=watchroot
display=cube('Inset black glass watch screen',(0,-.075,0),(.40,.027,.48),screenmat,.05);display.parent=watchroot
disc=cyl('Watch minimalist round dial',(0,-.095,.015),.15,.008,strapmat,64);disc.rotation_euler.x=pi/2;disc.parent=watchroot
dot=sphere('Watch display indicator',(.04,-.104,.035),(.018,.008,.018),white,24);dot.parent=watchroot
watchroot.location=(wx,wy-.415,wz+.435);watchroot.rotation_euler.x=-.35
crown=cyl('Watch side crown',(wx+.272,wy-.40,wz+.43),.045,.055,gold,32);crown.rotation_euler.y=pi/2

# Diagonal yellow pencil with a graphite tip, wooden cone and purple eraser.
before=set(bpy.data.objects)
pencil=cyl('Yellow hexagonal pencil',(0,0,1.06),.096,1.84,yellow,6)
bpy.ops.mesh.primitive_cone_add(vertices=6,radius1=0,radius2=.096,depth=.28,location=(0,0,.0))
finish(bpy.context.object,'Sharpened wood pencil point',wood)
bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=0,radius2=.025,depth=.10,location=(0,0,-.11));finish(bpy.context.object,'Graphite point',black)
cyl('Lavender eraser',(0,0,2.035),.098,.20,lilac,6)
textcurve=bpy.data.curves.new('Pencil lettering','FONT');textcurve.body='CREATIVE';textcurve.size=.055;textcurve.extrude=.0004
ob=bpy.data.objects.new('Pencil lettering',textcurve);bpy.context.collection.objects.link(ob);finish(ob,'Pencil lettering',black)
ob.location=(.031,-.085,.46);ob.rotation_euler=(pi/2,0,pi/2)
parts=set(bpy.data.objects)-before;root=bpy.data.objects.new('Leaning pencil assembly',None);bpy.context.collection.objects.link(root)
for ob in parts:ob.parent=root
root.location=(.08,-2.14,.18);root.rotation_euler.y=.32

# Stack of small pastel books, a ribbon and the glasses on the top volume.
def book(name,x,y,z,w,d,h,cover):
    cube(name+' paper block',(x,y,z+h/2),(w-.08,d-.08,h-.09),paper,.012)
    for zz in [z+.025,z+h-.025]:cube(name+' cover',(x,y,zz),(w,d,.05),cover,.012)
    cube(name+' curved spine',(x-w/2+.04,y,z+h/2),(.10,d,h),cover,.04)
    for i in range(1,7):tube(name+' page line %02d'%i,[(x-w/2+.09,y-d/2+.035,z+.055+(h-.11)*i/7),(x+w/2-.055,y-d/2+.035,z+.055+(h-.11)*i/7)],.0018,wood)
book('Bottom grey book',3.44,-.80,.04,1.58,.95,.37,strapmat)
book('Cream middle book',3.47,-.77,.41,1.70,.98,.40,rose_light)
book('Rose middle book',3.45,-.78,.81,1.63,.94,.40,rose)
book('Top lavender book',3.36,-.73,1.21,1.89,1.04,.43,lilac)
extrude('Coral bookmark ribbon',[(3.43,.64),(3.59,.64),(3.59,.36),(3.515,.47),(3.43,.36)],.025,coral,y=-1.29,bevel=.003)
mesh('Cream folded corner drape',[(2.42,-1.27,1.66),(3.43,-1.27,1.66),(2.92,-1.31,1.28)],[(0,1,2)],paper)
def glasses():
    for i,x in enumerate([3.10,3.70]):
        pts=[(x+xx*(1+.35*zz),-.80,1.94+zz+xx*(.14 if i else -.14)) for xx,zz in roundedrect(.49,.48,.11)]
        tube('Spectacles lens rim %d'%i,pts,.028,tortoise,True)
        outline=roundedrect(.425,.413,.09)
        extrude('Spectacles glass lens %d'%i,[(x+xx*(1+.35*zz),1.94+zz+xx*(.14 if i else -.14)) for xx,zz in outline],.011,glass,y=-.80,bevel=.005)
        tube('Spectacles earpiece %d'%i,[(x+(-.245 if i==0 else .245),-.80,2.01),(x+(-.245 if i==0 else .245),-.23,1.87),(x+(-.17 if i==0 else .17),-.1,1.72)],.025,tortoise)
    tube('Spectacles curved bridge',[(3.34,-.80,1.92),(3.40,-.79,1.99),(3.46,-.80,1.92)],.026,tortoise)
glasses()

# Small metallic stationery in front and the pale folded cloth over the edge.
capsule('Rose gold pen',(-2.66,-2.27,.075),.055,1.6,gold,'X')
capsule('Cream pen',(-2.02,-2.38,.065),.042,1.08,white,'X')
for x in [-2.50,-1.70]:cyl('Pen metal ring',(x,-2.38,.067),.045,.025,silver).rotation_euler.y=pi/2
# One continuous sheet: the fold follows the cylinder's curved front edge.
# Dense front rows stay outside that curve rather than cutting a chord through it.
paper_vertices=[];paper_faces=[];nx=32;top_rows=6;drop_rows=14
paper_left,paper_right,paper_tip=-1.17,.73,.28
def plinth_front(x):return 2.3-math.sqrt(5.6**2-x*x)-.045
for j in range(top_rows+1):
    t=j/top_rows
    for i in range(nx+1):
        x=paper_left+(paper_right-paper_left)*i/nx
        paper_vertices.append((x,-1.55+(plinth_front(x)+1.55)*t,.035))
for j in range(1,drop_rows):
    t=j/drop_rows
    for i in range(nx+1):
        top_x=paper_left+(paper_right-paper_left)*i/nx
        x=top_x*(1-t)+paper_tip*t
        paper_vertices.append((x,plinth_front(x)-.01*sin(pi*t),.035-.78*t))
rows=top_rows+drop_rows
for j in range(rows-1):
    for i in range(nx):
        a=j*(nx+1)+i;b=a+nx+1
        paper_faces.append((a,b,b+1,a+1))
tip_index=len(paper_vertices)
paper_vertices.append((paper_tip,plinth_front(paper_tip),.035-.78))
last_row=(rows-1)*(nx+1)
for i in range(nx):paper_faces.append((last_row+i,tip_index,last_row+i+1))
folded_paper=mesh('Ivory folded paper over plinth',paper_vertices,paper_faces,clothmat,True)
solid=folded_paper.modifiers.new('Thin paper thickness','SOLIDIFY');solid.thickness=.006;solid.offset=0
folded_paper['continuous_fold']=True
folded_paper['front_width_world']=paper_right-paper_left

# Three little butter-yellow heart motifs at the left base.
def heart(x,y,z,s):
    outline=[]
    for i in range(64):
        t=2*pi*i/64;outline.append((x+s*16*sin(t)**3/17,z+s*(13*cos(t)-5*cos(2*t)-2*cos(3*t)-cos(4*t))/17))
    extrude('Little yellow heart',outline,.013,paper,y=y,bevel=.005)
for z in [.26,.50,.74]:heart(-2.85,-1.765,z,.12)
sphere('Cream pebble by hearts',(-2.61,-1.99,.13),(.11,.06,.135),paper)

# Soft product photography, fully three dimensional Cycles scene.
world=bpy.context.scene.world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.78,.80,.83,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.40
wn=world.node_tree.nodes;wl=world.node_tree.links
camera_bg=wn.new('ShaderNodeBackground');camera_bg.name='Camera pink calibrated under AgX';camera_bg.inputs['Color'].default_value=(4.5,.34,.80,1)
camera_bg.inputs['Strength'].default_value=1
path=wn.new('ShaderNodeLightPath');mix=wn.new('ShaderNodeMixShader')
wl.new(path.outputs['Is Camera Ray'],mix.inputs[0]);wl.new(wn['Background'].outputs[0],mix.inputs[1]);wl.new(camera_bg.outputs[0],mix.inputs[2]);wl.new(mix.outputs[0],wn['World Output'].inputs[0])
for name,loc,power,size,color in [('Large warm left softbox',(-5,-7,12),1900,7,(1,.87,.80)),('Right fill',(6,-4,8),650,6,(.87,.91,1)),('Top rim',(-1,4,11),1400,5,(1,.84,.79))]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=color;point(o,(0,0,3.5))
bpy.ops.object.light_add(type='AREA',location=(-2,-8,3.5));o=bpy.context.object;o.name='Tall white frontal reflection card';o.data.energy=700;o.data.shape='RECTANGLE';o.data.size=3;o.data.size_y=7;point(o,(0,0,2.4))
bpy.ops.object.camera_add(location=(-.13,-30,5.972));cam=bpy.context.object;cam.name='Reference matching orthographic camera';point(cam,(-.13,0,4.4));cam.data.type='ORTHO';cam.data.ortho_scale=13.45
scene=bpy.context.scene;scene.camera=cam;scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_denoising=True
scene.render.resolution_x=1080;scene.render.resolution_y=1048;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.render.film_transparent=False
scene.render.filepath=str(OUT/'01_粉色装置.png')
scene['reference']='01_粉色装置.png supplied by user; reconstructed as editable geometry'
scene['notes']='All visible objects are native geometry, materials and lighting. No reference image is used as a texture.'
groups={label:bpy.data.collections.new(label) for label in ['00 Stage and lighting','01 Architectural sculpture','02 Bees','03 Foreground objects']}
for collection in groups.values():scene.collection.children.link(collection)
for ob in list(scene.objects):
    name=ob.name.lower()
    if ob.type in {'CAMERA','LIGHT'} or 'display plinth' in name:label='00 Stage and lighting'
    elif 'bee' in name:label='02 Bees'
    elif any(word in name for word in ['cup','watch','cushion','fibres','fuzz','pencil','pen','book','spectacle','paper','heart','wood grain','wooden plinth']):label='03 Foreground objects'
    else:label='01 Architectural sculpture'
    for collection in list(ob.users_collection):collection.objects.unlink(ob)
    groups[label].objects.link(ob)
plinth_receivers=bpy.data.collections.new('Plinth only - lighting receivers')
plinth_receivers.objects.link(bpy.data.objects['Large rose display plinth'])
bpy.ops.object.light_add(type='AREA',location=(5,-7,1.5));o=bpy.context.object;o.name='Right pink plinth softbox';o.data.energy=1050;o.data.shape='RECTANGLE';o.data.size=3;o.data.size_y=6;point(o,(3,0,-.6))
o.light_linking.receiver_collection=plinth_receivers
for collection in list(o.users_collection):collection.objects.unlink(o)
groups['00 Stage and lighting'].objects.link(o)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.color_type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'01_粉色装置.blend'))
mode=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if 'preview' in mode:
    p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices_for_type('OPTIX')
    for d in p.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU';scene.cycles.samples=24
    scene.render.threads_mode='FIXED';scene.render.threads=6
    scene.render.resolution_percentage=75;scene.render.filepath=str(OUT/'preview.png')
    bpy.ops.render.render(write_still=True)
elif 'final' in mode:
    p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';devices=p.get_devices_for_type('OPTIX')
    gpu=[d for d in devices if d.type=='OPTIX']
    if not gpu:raise RuntimeError('No OptiX GPU')
    for d in p.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU';bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'01_粉色装置.blend'))
    started=time.perf_counter()
    bpy.ops.render.render(write_still=True)
    manifest={'blender':bpy.app.version_string,'render_engine':'Cycles','compute_backend':'OPTIX','devices':[d.name for d in gpu],'resolution':[scene.render.resolution_x,scene.render.resolution_y],'samples':scene.cycles.samples,'objects':len(scene.objects),'materials':len(bpy.data.materials),'external_image_textures':[i.filepath for i in bpy.data.images if i.source=='FILE'],'render_seconds':round(time.perf_counter()-started,2),'blend':str(OUT/'01_粉色装置.blend'),'png':scene.render.filepath}
    (OUT/'render_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('PINK_SCENE_READY',len(bpy.data.objects),str(OUT))
