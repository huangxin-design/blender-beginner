import bpy, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def growing_rose(count, center, right, up, depth):
    rng=np.random.default_rng(818)
    collection=bpy.data.collections.new('05 / Sculpted rose surfaces / hidden')
    bpy.context.scene.collection.children.link(collection)
    verts=[]; closed=[]; faces=[]; groups=[]; uv=[]; kinds=[]
    # The flower axis tilts toward the camera, revealing the cup and rolled center.
    ax=np.array([-.12,.63,.767]); ax/=np.linalg.norm(ax)
    ex=np.array([1.,0,0]); ex-=ax*np.dot(ex,ax); ex/=np.linalg.norm(ex)
    ey=np.cross(ax,ex)
    base=np.array([-.14,.31,-.12])
    def world(p):return center+right*p[0]+up*p[1]+depth*p[2]
    def head(x,y,z):return world(base+1.13*(ex*x+ey*y+ax*z))
    def surface(name, rows, cols, fn, group, kind):
        start=len(verts); local=[]; bud=[]
        for i in range(rows):
            for j in range(cols):
                t=i/(rows-1); v=j/(cols-1)
                a,b=fn(t,2*v-1); local.append(a); bud.append(b); uv.append((t,v))
        verts.extend(local); closed.extend(bud)
        fs=[]
        for i in range(rows-1):
            for j in range(cols-1):
                a=i*cols+j; b=a+1; c=a+cols; d=c+1
                for tri in ((a,b,d),(a,d,c)):
                    fs.append(tri); faces.append(tuple(start+k for k in tri)); groups.append(group); kinds.append(kind)
        mesh=bpy.data.meshes.new(name); mesh.from_pydata([p.tolist() for p in local],[],fs)
        o=bpy.data.objects.new(name,mesh); collection.objects.link(o)
        o.shape_key_add(name='Open'); sk=o.shape_key_add(name='Closed bud')
        sk.data.foreach_set('co',np.asarray(bud,np.float32).ravel())
        o.hide_render=True; o.hide_set(True)

    layers=[(7,1.18,1.02,1.32,.53),(6,.92,1.36,1.53,.43),(5,.62,1.58,1.64,.34),(3,.28,1.72,1.71,.23)]
    for layer,(petals,radius,lip,peak,bud_radius) in enumerate(layers):
        for p in range(petals):
            angle=2*math.pi*p/petals+layer*.71+rng.uniform(-.095,.095)
            rad=radius*rng.uniform(.94,1.045)
            half=math.pi/petals*1.58
            tilt=rng.uniform(-.07,.07)
            def petal(t,u,angle=angle,rad=rad,lip=lip,peak=peak,half=half,tilt=tilt,bud_radius=bud_radius,layer=layer):
                r=.055*(1-t)**3+3*(1-t)**2*t*.15+3*(1-t)*t*t*rad*.66+t**3*rad
                zbase=(0,.24,.56,.98)[layer]
                z=zbase*(1-t)**3+3*(1-t)**2*t*(zbase+.22)+3*(1-t)*t*t*peak+t**3*lip
                z-=.24*abs(u)**2.2*t**1.7
                z+=.055*math.sin(3*u+angle)*t*t+tilt*t
                a=angle+u*half*math.sin(t*math.pi/2)+(.95 if layer==3 else .22)*t*(1-u*u)
                if layer==3:r=.055+.23*math.sin(t*math.pi*.63)
                r*=1-.135*u*u+.025*math.sin(4*u+angle)*t
                opened=head(r*math.cos(a),r*math.sin(a),z)
                rb=.05+bud_radius*math.sin(math.pi*t)**.76+.085*t
                ab=angle+u*half*math.sin(t*math.pi/2)+.16*t
                zb=1.51*t-.11*u*u*t+layer*.035*t
                shut=head(rb*math.cos(ab),rb*math.sin(ab),zb)
                opened=shut+(opened-shut)*(1.,.72,.42,.22)[layer]
                return opened,shut
            surface(f'Rose / cupped petal {layer+1:02d}.{p+1:02d}',32,29,petal,layer+1,0)

    def stem_center(t):return np.array([.08-.22*t+.115*math.sin(math.pi*t),-2.19+2.5*t,-.12+.055*math.sin(math.pi*t)])
    def stem(t,u):
        a=(u+1)*math.pi; radius=.030-.007*t
        p=world(stem_center(t)+np.array([radius*math.cos(a),0,radius*math.sin(a)]))
        return p,p
    surface('Rose / growing stem',100,14,stem,5,1)
    # Two compound leaves sit below the flower, with a central ridge and fine teeth.
    for side,t0,length in [(-1,.34,1.12),(1,.57,1.03)]:
        start=stem_center(t0)
        direction=np.array([side*.93,.36,.03]); direction/=np.linalg.norm(direction)
        def branch(t,u,start=start,direction=direction,length=length):
            a=(u+1)*math.pi; p=start+direction*length*t
            p+=np.array([0,.012*math.cos(a),.012*math.sin(a)])
            full=world(p); shut=world(start+(p-start)*.18)
            return full,shut
        surface(f'Rose / leaf stem {side}',36,10,branch,0,1)
        for j,along,leaf_side in [(0,.76,0),(1,.46,-1),(2,.43,1)]:
            anchor=start+direction*length*along
            leaf_dir=direction if leaf_side==0 else np.array([side*.48,leaf_side*.82,.08])
            leaf_dir=leaf_dir/np.linalg.norm(leaf_dir)
            cross=np.array([-leaf_dir[1],leaf_dir[0],0])
            leaf_length=.61 if j==0 else .42
            def leaf(t,u,anchor=anchor,leaf_dir=leaf_dir,cross=cross,leaf_length=leaf_length,start=start):
                serration=1+.065*math.sin(t*26*math.pi)
                width=.21*math.sin(math.pi*t)**.95*serration*(leaf_length/.61)
                p=anchor+leaf_dir*leaf_length*t+cross*width*u
                p[2]+=.13*math.sin(math.pi*t)-.09*abs(u)*math.sin(math.pi*t)
                full=world(p); shut=world(start+(p-start)*.16+np.array([0,.13*t,0]))
                return full,shut
            surface(f'Rose / serrated leaflet {side}.{j}',48,19,leaf,0,2)
    # Small pointed sepals hold the bud at the top of the stem.
    for p in range(5):
        angle=p*2*math.pi/5
        def sepal(t,u,angle=angle):
            r=.08+.44*t; a=angle+u*.15*math.sin(math.pi*t)
            a1=head(r*math.cos(a),r*math.sin(a),.15-.22*t)
            a2=head(r*.72*math.cos(a),r*.72*math.sin(a),.52*t)
            return a1,a2
        surface(f'Rose / sepal {p}',25,13,sepal,1,2)

    vv=np.asarray(verts); bb=np.asarray(closed); ff=np.asarray(faces)
    tt=vv[ff]; cross=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0])
    areas=np.linalg.norm(cross,axis=1)/2
    probabilities=areas*np.where(np.asarray(kinds)==1,2.0,1.0); probabilities/=probabilities.sum()
    vertex_groups=np.empty(len(vv),dtype=int)
    for face,group in zip(ff,groups):vertex_groups[face]=group
    pose_frames=[261,295,320,345,367]
    poses=[]; bvhs=[]
    for frame in pose_frames:
        pose=bb.copy()
        for group,start,end in [(0,214,280),(1,271,324),(2,287,343),(3,303,357),(4,313,364)]:
            t=np.clip((frame-start)/(end-start),0,1); weight=t*t*(3-2*t)
            mask=vertex_groups==group; pose[mask]+=(vv[mask]-bb[mask])*weight
        poses.append(pose); bvhs.append(BVHTree.FromPolygons([Vector(p) for p in pose],faces,all_triangles=True))
    # Visibility is sampled throughout unfolding, avoiding torn petals during the bloom.
    picked=[]; coefficients=[]; visibility=[]; total=0
    ray=Vector(-depth)
    while total<count:
        batch=max(12000,(count-total)*5)
        indices=rng.choice(len(ff),batch,p=probabilities)
        a=np.sqrt(rng.random(batch)); b=rng.random(batch)
        coeff=np.column_stack([1-a,a*(1-b),a*b])
        vis=np.zeros((batch,len(poses)),dtype=np.float32)
        for k,(pose,bvh) in enumerate(zip(poses,bvhs)):
            pts=np.sum(pose[ff[indices]]*coeff[:,:,None],axis=1)
            for i,point in enumerate(pts):
                if kinds[indices[i]]!=0:vis[i,k]=1; continue
                hit=bvh.ray_cast(Vector(point+depth*8),ray,8.004)
                if hit[0] is not None and abs(hit[3]-8)<.003:vis[i,k]=1
        valid=np.flatnonzero(vis.max(axis=1)>0)[:count-total]
        picked.append(indices[valid]); coefficients.append(coeff[valid]); visibility.append(vis[valid]); total+=len(valid)
    picked=np.concatenate(picked); coeff=np.concatenate(coefficients)
    opened=np.sum(vv[ff[picked]]*coeff[:,:,None],axis=1)
    bud=np.sum(bb[ff[picked]]*coeff[:,:,None],axis=1)
    kinds=np.asarray(kinds)[picked]; groups=np.asarray(groups)[picked]
    tex=np.sum(np.asarray(uv)[ff[picked]]*coeff[:,:,None],axis=1)
    normals=cross[picked]/np.maximum(np.linalg.norm(cross[picked],axis=1)[:,None],1e-10)
    facing=np.abs(normals@depth)
    tip=tex[:,0]**1.4
    colors=np.array([.18,.002,.022])[None,:]*(1-tip[:,None])+np.array([.75,.035,.065])[None,:]*tip[:,None]
    colors[kinds==1]=np.array([.34,.16,.043])
    colors[kinds==2]=np.array([.28,.18,.055])
    energy=rng.uniform(2.2,4.8,count)*(.22+.78*facing**1.2)
    energy[kinds==0]*=.30+.70*tex[kinds==0,0]**1.8
    glints=rng.random(count)<.018
    colors[glints]=np.array([1.,.64,.32]); energy[glints]*=rng.uniform(2.2,4.8,np.count_nonzero(glints))
    height=(bud-center)@up
    birth=np.where(kinds==0,rng.uniform(251,270,count),181+np.clip((height+2.2)/2.8,0,1)*50)
    birth[(groups==0)&(kinds!=0)]=rng.uniform(218,246,np.count_nonzero((groups==0)&(kinds!=0)))
    birth[(groups==1)&(kinds==2)]=rng.uniform(244,255,np.count_nonzero((groups==1)&(kinds==2)))
    seed_origin=world(np.array([.08,-2.19,-.12]))
    seed=seed_origin+(bud-seed_origin)*.045
    return {'seed':seed,'bud':bud,'open':opened,'group':groups,'color':colors,'energy':energy,'birth':birth,'visibility':np.concatenate(visibility),'pose_frames':pose_frames,'petals':sum(x[0] for x in layers)}
