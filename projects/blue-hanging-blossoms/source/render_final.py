"""Portable render entry derived from the approved V8 UHD renderer."""
import struct
import sys
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['preview']
mode=args[0]
if mode not in ('preview','render'):
    raise ValueError('Use preview or render [first] [last].')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'scene.blend'))
s=bpy.context.scene
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX'
prefs.get_devices()
for device in prefs.devices:
    device.use=device.type=='OPTIX'
if not any(d.use and d.type=='OPTIX' for d in prefs.devices):
    raise RuntimeError('This renderer requires an NVIDIA OptiX device.')
s.render.engine='CYCLES'
s.cycles.device='GPU'
s.cycles.use_denoising=True
s.cycles.use_adaptive_sampling=True
s.cycles.samples=32 if mode=='preview' else 128
s.cycles.adaptive_threshold=.03 if mode=='preview' else .015
s.cycles.adaptive_min_samples=24
s.render.use_persistent_data=False
s.render.resolution_x,s.render.resolution_y=(360,640) if mode=='preview' else (2160,3840)
s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
s.render.image_settings.color_mode='RGB'
s.render.image_settings.color_depth='16'
s.render.image_settings.compression=25
frames=[360] if mode=='preview' else range(int(args[1]) if len(args)>1 else 1,(int(args[2]) if len(args)>2 else 384)+1)
folder=ROOT/'renders'/('preview' if mode=='preview' else 'frames')
folder.mkdir(parents=True,exist_ok=True)
for frame in frames:
    if not 1<=frame<=384:
        raise ValueError('Frame must be within 1–384.')
    dest=folder/f'{frame:04d}.png'
    if mode=='render' and dest.exists():
        data=dest.read_bytes()
        if data[:8]==b'\x89PNG\r\n\x1a\n' and data[-8:]==b'IEND\xaeB`\x82' and struct.unpack('>II',data[16:24])==(2160,3840) and data[24]==16:
            continue
    s.frame_set(frame)
    s.render.filepath=str(dest)
    bpy.ops.render.render(write_still=True)
    print(f'FRAME_DONE {frame}',flush=True)
