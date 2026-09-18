import bpy, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'HuangHuaYu_Growing_Rose_4K.blend'))
s=bpy.context.scene
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'keys'
if mode=='draft':
    s.render.resolution_percentage=25; s.eevee.taa_render_samples=20; s.frame_step=2
    s.render.filepath=str(ROOT/'draft/bloom_'); bpy.ops.render.render(animation=True)
elif mode=='full':
    s.render.resolution_percentage=100; s.frame_step=1
    s.render.filepath=str(ROOT/'frames/bloom_'); bpy.ops.render.render(animation=True)
    print('NATIVE_4K_COMPLETE',flush=True)
else:
    s.render.resolution_percentage=100 if mode=='native' else 25
    frames=[105,145,261,367,490,600] if mode=='native' else [105,185,215,240,261,290,320,347,367,425,490,550,600]
    for f in frames:
        s.frame_set(f); s.render.filepath=str(ROOT/'stills'/f'{mode}_{f:03d}.png'); bpy.ops.render.render(write_still=True)
