# Publication adaptation: relative scene name and configurable installation paths.
"""Memory-capped HDR denoise, then native Blender color management without Bloom."""
import sys
import gc
import json
import time
from pathlib import Path
import numpy as np
import OpenImageIO as oiio

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'renders'/'cache'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from denoise_capped import denoise

def write_linear_exr(path,pixels):
    temporary=path.with_name(path.stem+'.partial.exr')
    spec=oiio.ImageSpec(pixels.shape[1],pixels.shape[0],3,oiio.FLOAT)
    spec.attribute('compression','zip')
    output=None;opened=False;stage='create'
    try:
        output=oiio.ImageOutput.create(str(temporary))
        if output is None:raise RuntimeError(oiio.geterror())
        stage='open'
        if not output.open(str(temporary),spec):raise RuntimeError(output.geterror())
        opened=True;stage='write'
        if not output.write_image(pixels):raise RuntimeError(output.geterror())
        stage='close'
        closed=output.close();opened=False
        if not closed:raise RuntimeError(output.geterror())
        stage='publish'
        temporary.replace(path)
    except Exception as error:
        print('EXR_WRITE_ERROR',json.dumps({'path':str(path),'stage':stage,
              'error_type':type(error).__name__,'message':str(error)},ensure_ascii=True),
              file=sys.stderr,flush=True)
        raise
    finally:
        if opened:output.close()

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
check_only=args[0]=='--check-exr'
frame=int(args[1] if check_only else args[0])
started=time.monotonic()
source=CACHE/'raw'/f'{frame:04d}.exr'
inp=oiio.ImageInput.open(str(source))
if not inp:raise RuntimeError(oiio.geterror())
layers={}
index=0
while inp.seek_subimage(index,0):
    layers[inp.spec().get_string_attribute('name')]=index
    index+=1
print('EXR_LAYERS',layers,flush=True)
def read_pass(name):
    index=next(i for n,i in layers.items() if n.endswith('.'+name))
    inp.seek_subimage(index,0)
    spec=inp.spec()
    if (spec.width,spec.height)!=(3072,4096) or spec.nchannels<3:
        raise ValueError(f'Invalid EXR pass dimensions: {name}')
    pixels=inp.read_image(subimage=index,miplevel=0,chbegin=0,chend=3,format=oiio.FLOAT)
    if pixels is None:raise ValueError(f'Unreadable EXR pass {name}: {inp.geterror()}')
    pixels=np.ascontiguousarray(pixels,dtype=np.float32)
    if pixels.shape!=(4096,3072,3):raise ValueError(f'Unexpected EXR pass shape: {name}')
    for row in range(0,4096,128):
        if not np.isfinite(pixels[row:row+128]).all():
            raise ValueError(f'Non-finite EXR pass pixels: {name}')
    return pixels
try:
    if check_only:
        for name in ('Combined','Denoising Albedo','Denoising Normal'):
            pixels=read_pass(name)
            del pixels
        print('EXR_VALIDATED',frame,flush=True)
        sys.exit(0)
    color=read_pass('Combined')
    albedo=read_pass('Denoising Albedo')
    normal=read_pass('Denoising Normal')
finally:
    inp.close()
height,width=color.shape[:2]
assert (width,height)==(3072,4096),(width,height)
clean=denoise(color,albedo,normal,max_memory_mb=512,threads=8)
assert np.isfinite(clean).all()
del color,albedo,normal;gc.collect()
linear_path=CACHE/'raw'/f'{frame:04d}_denoised.exr'
write_linear_exr(linear_path,clean)
del clean;gc.collect()

# A simple CPU render applies native color management at full resolution;
# all 3D geometry is hidden and the denoised linear image feeds the output directly.
import bpy
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'scene.blend'))
s=bpy.context.scene;s.frame_set(frame)
for ob in s.objects:
    if ob.type!='CAMERA':ob.hide_render=True
bpy.context.preferences.addons['cycles'].preferences.compute_device_type='NONE'
s.cycles.device='CPU';s.cycles.samples=1;s.cycles.use_adaptive_sampling=False
s.cycles.use_denoising=False
bpy.context.view_layer.cycles.denoising_store_passes=False
s.render.use_compositing=True;s.render.compositor_device='CPU'
g=s.compositing_node_group
output_node=next(n for n in g.nodes if n.type=='GROUP_OUTPUT')
for node in list(g.nodes):
    if node.type in {'R_LAYERS','GLARE'}:g.nodes.remove(node)
image_node=g.nodes.new('CompositorNodeImage')
image_node.image=bpy.data.images.load(str(linear_path),check_existing=False)
g.links.new(image_node.outputs['Image'],output_node.inputs['Image'])
s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG'
s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='16'
s.render.image_settings.compression=25
destination=CACHE/'frames'/f'{frame:04d}.png'
destination.parent.mkdir(parents=True,exist_ok=True)
temporary=destination.with_name(f'{frame:04d}.post.png')
s.render.filepath=str(temporary)
bpy.ops.render.render(write_still=True)
temporary.replace(destination)
record={'frame':frame,'post_seconds':round(time.monotonic()-started,3),'denoiser':'OIDN HIGH CPU / 512MB working target','threads':8,'bytes':destination.stat().st_size}
with (ROOT/'post_timings.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
print('POST_DONE',json.dumps(record),flush=True)
