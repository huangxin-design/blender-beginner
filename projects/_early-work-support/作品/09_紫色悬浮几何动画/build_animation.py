"""Native six-second mechanical floating loop, reconstructed from reference motion."""
import bpy, math, json, os
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix

ROOT=Path(__file__).resolve().parent
WORK=ROOT.parents[1]
os.environ['OPTIX_CACHE_PATH']=str(WORK/'setup/cache/optix')
bpy.ops.wm.open_mainfile(filepath=str(WORK/'作品/08_紫色悬浮几何/08_紫色悬浮几何_调色成品.blend'))
s=bpy.context.scene
s.name='09 | Independent floating geometry loop'
s.frame_start=1;s.frame_end=180;s.render.fps=30;s.render.fps_base=1
s.render.resolution_x=720;s.render.resolution_y=1280;s.render.resolution_percentage=100
s.cycles.samples=64;s.cycles.adaptive_threshold=.022;s.cycles.adaptive_min_samples=16
s.cycles.use_denoising=True;s.cycles.use_adaptive_sampling=True
s.render.use_persistent_data=True;s.render.use_motion_blur=False
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8'
s.render.image_settings.compression=15
s['Animation notes']='Fixed camera; independently rotating and oscillating assemblies; six-second seamless motion loop. Motion reconstructed, not source keyframes.'
R=Vector((1,0,0));U=Vector((0,.242535625,.9701425));T=Vector((0,-.9701425,.242535625));Z=Vector((0,0,1))
data=json.loads((ROOT/'rig_inventory.json').read_text(encoding='utf8'))
groups=data['groups']
for g in groups:
    if g['id']=='yellow_washer':g['members'].append('Particle 12')
    if g['id']=='cage':
        extras=g['members'][1:];g['members']=g['members'][:1]
        for name in extras:
            ob=bpy.data.objects[name]
            groups.append({'id':name,'members':[name],'anchor':name,'pivot_world':list(ob.location),'local_axis_z_world':list(ob.matrix_world.to_3x3()@Z)})
groups=[g for g in groups if g['id']!='Particle 12']

def q(axis,angle):return Quaternion(axis,angle)
def sn(u,cycles=1,phase=0):return math.sin(math.tau*cycles*u+phase)-math.sin(phase)
def deg(a):return math.radians(a)

def pose(g,u):
    """All angular speeds are exact integer cycles; additive motions begin at zero."""
    name=g['id'];n=Vector(g['local_axis_z_world']).normalized()
    d=Vector((0,0,0));rot=Quaternion((1,0,0,0))
    if name=='core':
        rot=q(R,deg(8)*sn(u))@q(n,math.tau*2*u);d=U*(.055*sn(u,2))
    elif name=='yellow_washer':rot=q(n,math.tau*2*u)
    elif name=='cage':rot=q(U,math.tau*2*u)@q(T,deg(8)*sn(u))
    elif name.startswith('06b'):
        d=U*(.07*sn(u,2,.5))
    elif name.startswith('06c'):
        rot=q(U,deg(16)*sn(u,2));d=U*(.045*sn(u,2,1))
    elif name.startswith('06d'):rot=q(T,deg(18)*sn(u,2))
    elif name.startswith('03 |'):
        rot=q(Z,deg(28)*sn(u))@q(T,deg(7)*sn(u,2));d=U*(.025*(1-math.cos(math.tau*u)))
    elif name.startswith('04 |'):
        rot=q(U,deg(22)*sn(u,2))@q(T,deg(6)*sn(u));d=U*(.07*sn(u,2))
    elif name.startswith('05 |'):
        rot=q(U,deg(9)*sn(u))@q(T,deg(4)*sn(u,2))
    elif name.startswith('08 |'):
        rot=q(U,deg(18)*sn(u,2))@q(T,deg(6)*sn(u))
    elif name.startswith('09 |'):
        d=U*(.28*sn(u,2))-R*.10+T*.20;rot=q(T,deg(3)*sn(u,2))
    elif name.startswith('10 |'):
        d=U*(-.26*sn(u,2))+R*.06;rot=q(T,-deg(3)*sn(u,2))
    elif name.startswith('11 |'):rot=q(U,math.tau*2*u)
    elif name=='top_pink_pipe':d=R*(.22*sn(u,2));rot=q(U,deg(6)*sn(u,2))
    elif name.startswith('13 |'):d=R*(-.18*sn(u,2));rot=q(U,-deg(7)*sn(u,2))
    elif name.startswith('14 |'):
        rot=q(U,math.tau*u);d=U*(.04*sn(u,2))+T*.12
    elif name=='upper_sector':rot=q(T,deg(11)*sn(u,2))@q(U,deg(26)*sn(u,2))
    elif name.startswith('07 |'):
        rot=q(R,deg(16)*sn(u,2))@q(T,deg(5)*sn(u));d=U*(.065*sn(u,2))
    elif name=='gold_pipe':rot=q(T,deg(12)*sn(u,2))@q(U,deg(15)*sn(u,2))
    elif name=='blue_studded_button':rot=q(n,-math.tau*2*u)@q(R,deg(7)*sn(u,2))
    elif name=='arrow':d=U*(.11*sn(u,2))+R*(.065*sn(u,2))
    elif name=='lower_fan':rot=q(T,deg(24)*sn(u,2))@q(U,deg(18)*sn(u,2))
    elif name.startswith('24 |'):rot=q(T,-deg(20)*sn(u,2))@q(U,deg(12)*sn(u))
    elif name.startswith('25 |'):rot=q(T,math.tau*u);d=U*(.035*sn(u,2))
    elif name=='lower_pink_pipe':rot=q(U,deg(12)*sn(u,2))@q(T,deg(6)*sn(u,2))
    elif name.startswith('27 |'):rot=q(T,deg(9)*sn(u,2));d=U*(.06*sn(u,2))
    elif name.startswith('28 |'):rot=q(T,-deg(10)*sn(u,2));d=U*(-.04*sn(u,2))
    elif name.startswith('29 |'):rot=q(U,deg(13)*sn(u,2));d=U*(.10*sn(u,2))
    elif name.startswith('30 |'):rot=q(U,math.tau*2*u);d=U*(.075*sn(u,2))
    elif name=='gold_dish':rot=q(U,deg(18)*sn(u,2))@q(T,deg(10)*sn(u,2));d=U*(.04*sn(u,2))
    elif name=='pink_waffle':rot=q(n,math.tau*2*u)@q(U,deg(18)*sn(u,2));d=U*(.035*sn(u,2))
    elif name=='spindle':rot=q(U,math.tau*2*u)
    elif name.startswith('20 |'):rot=q(U,math.tau*2*u)
    elif name.startswith(('17 |','18 |','33 |')):rot=q(T,deg(5)*sn(u,2));d=R*(.04*sn(u,2))
    elif name.startswith('Particle'):
        k=int(name[-2:]);d=U*(.045*sn(u,1+(k%2),k*.7))+R*(.015*sn(u,1,k*.37))
    elif name.startswith('Faceted'):
        k=int(name[-2:]);rot=q(U,math.tau*(1+k%2)*u);d=U*(.035*sn(u,2,k))
    elif name.startswith('16 |'):d=U*(.045*sn(u,2))
    elif name in ('upper_outline',) or name.startswith(('36 |','37 |','38 |')):rot=q(T,deg(3)*sn(u))
    return d,rot

rigcol=bpy.data.collections.new('09 | Editable animation controls');s.collection.children.link(rigcol)
dg=bpy.context.evaluated_depsgraph_get()
report={'fps':30,'loop_frames':180,'groups':[],'constant_ground_lifts':{}}
for g in groups:
    center=Vector(g['pivot_world'])
    # Cache evaluated geometry once; rigid parent animation does not change topology.
    clouds=[]
    for name in g['members']:
        o=bpy.data.objects[name];e=o.evaluated_get(dg);m=e.to_mesh()
        if m is not None:
            v=np.empty((len(m.vertices),3),dtype=np.float64);m.vertices.foreach_get('co',v.ravel())
            mw=np.array(e.matrix_world);clouds.append(v@mw[:3,:3].T+mw[:3,3]-np.array(center))
            e.to_mesh_clear()
    points=np.concatenate(clouds) if clouds else np.zeros((1,3))
    lift=0.0
    # Full per-frame ground envelope, applied as one constant lift to preserve smoothness.
    for frame in range(181):
        d,rot=pose(g,frame/180)
        zmin=float((points@np.array(rot.to_matrix())[2,:]).min())+center.z+d.z
        lift=max(lift,.018-zmin)
    if lift>0:report['constant_ground_lifts'][g['id']]=round(lift,6)
    ctrl=bpy.data.objects.new('ANIM | '+g['id'],None);rigcol.objects.link(ctrl)
    ctrl.empty_display_type='PLAIN_AXES';ctrl.empty_display_size=.20;ctrl.location=center
    ctrl.rotation_mode='QUATERNION';ctrl['Loop seconds']=6;ctrl['Assembly members']='; '.join(g['members'])
    for name in g['members']:
        ob=bpy.data.objects[name];world=ob.matrix_world.copy();ob.parent=ctrl
        ob.matrix_parent_inverse=Matrix.Identity(4)
        ob.matrix_basis=Matrix.Translation(-center)@world
    previous=None
    for frame in range(181):
        d,rot=pose(g,frame/180)
        if previous is not None and rot.dot(previous)<0:rot.negate()
        previous=rot.copy();ctrl.location=center+d+Z*lift;ctrl.rotation_quaternion=rot
        ctrl.keyframe_insert('location',frame=frame+1);ctrl.keyframe_insert('rotation_quaternion',frame=frame+1)
    # Linear dense samples avoid Bezier overshoot and quaternion speed reversals.
    action=ctrl.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            bag=strip.channelbag(ctrl.animation_data.action_slot)
            if bag:
                for fc in bag.fcurves:
                    for kp in fc.keyframe_points:kp.interpolation='LINEAR'
                    fc.modifiers.new('CYCLES')
    report['groups'].append({'id':g['id'],'parent':ctrl.name,'members':g['members'],'ground_lift':lift})

pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for device in pref.devices:device.use=device.type=='OPTIX'
s.cycles.device='GPU';s.frame_set(1)
for a in bpy.data.screens:
    for area in a.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
s.render.filepath=str(WORK/'渲染/09_紫色悬浮几何动画/frames/purple/frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'09_基础循环.blend'))
(ROOT/'motion_build_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('ANIMATION_BUILT',len(groups),'assemblies',flush=True)
