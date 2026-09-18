import bpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'HuangHuaYu_Outline07_4K.blend'))
s=bpy.context.scene;mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'keys'
if mode in ('draft','full','all'):
    s.frame_start=381 if mode!='all' else 1;s.frame_end=600
    s.frame_step=2 if mode=='draft' else 1
    s.render.resolution_percentage=25 if mode=='draft' else 100
    if mode=='draft':s.eevee.taa_render_samples=20
    s.render.filepath=str(ROOT/('draft' if mode=='draft' else 'frames')/'bloom_')
    bpy.ops.render.render(animation=True)
    print('RENDER_COMPLETE',mode,flush=True)
else:
    s.render.resolution_percentage=100 if mode=='native' else 25
    frames=[367,380,490,550,600] if mode=='native' else [380,407,431,455,470,490,509,530,560,600]
    for f in frames:
        s.frame_set(f);s.render.filepath=str(ROOT/'stills'/f'{mode}_{f:03d}.png');bpy.ops.render.render(write_still=True)
