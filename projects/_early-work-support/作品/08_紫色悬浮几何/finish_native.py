"""Editable Blender color grade and highlight bloom, using the new linear beauty passes."""
from pathlib import Path
import argparse, sys, json, time
import bpy

p=argparse.ArgumentParser()
p.add_argument('--scene',type=Path,required=True)
p.add_argument('--beauty',type=Path,required=True)
p.add_argument('--profile',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--save-scene',type=Path)
args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
cfg=json.loads(args.profile.read_text(encoding='utf8'))
bpy.ops.wm.open_mainfile(filepath=str(args.scene))
original=bpy.context.scene

def sock(node,name,kind=None):
    return next(s for s in node.inputs if s.name==name and (kind is None or s.type==kind))

def set_grade(scene,image=None):
    nt=bpy.data.node_groups.new('FINISH · 饱和色彩与高光辉光','CompositorNodeTree')
    nt.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    scene.compositing_node_group=nt
    scene.render.use_compositing=True
    n,l=nt.nodes,nt.links
    src=n.new('CompositorNodeImage' if image else 'CompositorNodeRLayers')
    src.name='01 · Linear beauty / 线性渲染';src.label=src.name;src.location=(-1080,0)
    if image:src.image=image
    exp=n.new('CompositorNodeExposure');exp.name='02 · 整体曝光';exp.label=exp.name;exp.location=(-860,0)
    exp.inputs['Exposure'].default_value=cfg.get('exposure',0)
    percept=n.new('CompositorNodeConvertColorSpace');percept.name='03 · 感知色彩空间';percept.label=percept.name;percept.location=(-650,0)
    percept.from_color_space='scene_linear';percept.to_color_space='sRGB'
    bal=n.new('CompositorNodeColorBalance');bal.name='04 · 阴影 中间调 高光配色';bal.label=bal.name;bal.location=(-420,0)
    # Use the COLOR sockets; Blender 5.2 also has scalar sockets with these names.
    for key,name in [('lift','Lift'),('gamma','Gamma'),('gain','Gain')]:
        if key in cfg:sock(bal,name,'RGBA').default_value=(*cfg[key],1)
    sat=n.new('CompositorNodeHueSat');sat.name='05 · 糖果色饱和度';sat.label=sat.name;sat.location=(-170,0)
    sat.inputs['Saturation'].default_value=cfg['saturation']
    sat.inputs['Hue'].default_value=cfg.get('hue',.5)
    sat.inputs['Value'].default_value=1
    linear=n.new('CompositorNodeConvertColorSpace');linear.name='06 · 返回线性高光';linear.label=linear.name;linear.location=(60,0)
    linear.from_color_space='sRGB';linear.to_color_space='scene_linear'
    glow=n.new('CompositorNodeGlare');glow.name='07 · 局部高光辉光';glow.label=glow.name;glow.location=(290,0)
    for key,value in {'Type':'Fog Glow','Quality':'High','Threshold':cfg['glow_threshold'],
                      'Smoothness':cfg.get('glow_smoothness',.25),'Strength':cfg['glow_strength'],
                      'Size':cfg['glow_size'],'Saturation':cfg.get('glow_saturation',1.1)}.items():
        glow.inputs[key].default_value=value
    glow.inputs['Tint'].default_value=(*cfg.get('glow_tint',[1,1,1]),1)
    dst=n.new('NodeGroupOutput');dst.location=(550,0);dst.name='08 · 最终成品'
    chain=[src,exp,percept,bal,sat,linear,glow,dst]
    for a,b in zip(chain,chain[1:]):l.new(a.outputs['Image'],b.inputs['Image'])
    scene.view_settings.view_transform=cfg.get('view_transform','AgX')
    scene.view_settings.look=cfg.get('look','AgX - Medium High Contrast')
    scene.view_settings.exposure=cfg.get('view_exposure',0)
    scene.view_settings.gamma=1
    scene.render.compositor_device='CPU'
    scene['Final color grade']=json.dumps(cfg,ensure_ascii=False)
    return nt

set_grade(original)
original.render.image_settings.file_format='PNG'
original.render.image_settings.color_mode='RGB'
original.render.image_settings.color_depth='8'
original.render.filepath=str(args.output)
if args.save_scene:
    args.save_scene.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.save_scene))

beauty=bpy.data.images.load(str(args.beauty),check_existing=False)
w,h=beauty.size[:]
assert w>0 and h>0
try:
    import numpy as np
    px=np.empty(w*h*4,dtype=np.float32);beauty.pixels.foreach_get(px)
    rgb=px.reshape(-1,4)[:,:3];lum=rgb@np.array([.2126,.7152,.0722])
    print('BEAUTY_LUMINANCE',json.dumps({str(q):float(np.percentile(lum,q)) for q in [50,90,95,99,99.5,99.9,100]}),flush=True)
except Exception as exc:print('STATS_SKIPPED',str(exc),flush=True)

# A tiny empty CPU scene triggers only compositing of the full-sized beauty image.
post=bpy.data.scenes.new('POST · CPU beauty grading')
camera_data=bpy.data.cameras.new('POST camera')
camera=bpy.data.objects.new('POST camera',camera_data);post.collection.objects.link(camera);post.camera=camera
post.render.engine='CYCLES';post.cycles.device='CPU';post.cycles.samples=1
post.render.threads_mode='FIXED';post.render.threads=2
post.render.resolution_x=w;post.render.resolution_y=h;post.render.resolution_percentage=100
post.render.image_settings.file_format='PNG';post.render.image_settings.color_mode='RGB'
post.render.image_settings.color_depth='8';post.render.filepath=str(args.output)
set_grade(post,beauty)
args.output.parent.mkdir(parents=True,exist_ok=True)
start=time.perf_counter();bpy.ops.render.render(scene=post.name,write_still=True)
assert args.output.is_file()
print('FINISH_COMPLETE',json.dumps({'file':str(args.output),'size':[w,h],'seconds':round(time.perf_counter()-start,2),'profile':cfg},ensure_ascii=False),flush=True)
