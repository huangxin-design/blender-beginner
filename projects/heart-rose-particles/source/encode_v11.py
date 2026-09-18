import subprocess, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ffmpeg=shutil.which('ffmpeg')
mode=sys.argv[1] if len(sys.argv)>1 else 'full'
if mode=='draft':
    paths=sorted((ROOT/'draft').glob('bloom_*.png'))
    assert len(paths)==300
    (ROOT/'draft/concat.txt').write_text(''.join("file '"+p.name+"'\nduration 0.066666667\n" for p in paths),encoding='utf-8')
    subprocess.run([ffmpeg,'-y','-loglevel','warning','-f','concat','-safe','0','-i',str(ROOT/'draft/concat.txt'),'-r','15','-frames:v','300','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-refs','1','-bf','0','-movflags','+faststart',str(ROOT/'draft.mp4')],check=True)
else:
    movie=ROOT/'HuangHuaYu_Outline07_3072x4096_4K.mp4'
    subprocess.run([ffmpeg,'-y','-loglevel','warning','-framerate','30','-start_number','1','-i',str(ROOT/'frames/bloom_%04d.png'),'-frames:v','600','-an','-vf','scale=out_color_matrix=bt709:out_range=tv,format=yuv420p','-c:v','libx264','-threads','12','-preset','slow','-crf','17','-pix_fmt','yuv420p','-refs','1','-bf','0','-g','30','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-movflags','+faststart',str(movie)],check=True)
    subprocess.run([ffmpeg,'-y','-loglevel','warning','-i',str(movie),'-an','-vf','scale=1080:1440:flags=lanczos','-c:v','libx264','-preset','slow','-crf','18','-pix_fmt','yuv420p','-refs','1','-bf','0','-g','30','-movflags','+faststart',str(ROOT/'HuangHuaYu_Outline07_Preview_1080.mp4')],check=True)
    for name,f in [('Heart',105),('Rose',367),('Text',490)]:
        shutil.copy2(ROOT/'frames'/f'bloom_{f:04d}.png', ROOT/f'HuangHuaYu_{name}_4K.png')
print('ENCODE_COMPLETE',mode,flush=True)
