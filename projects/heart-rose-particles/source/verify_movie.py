import subprocess, json, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parent
ffmpeg=shutil.which('ffmpeg'); ffprobe=shutil.which('ffprobe')
movie=ROOT/'HuangHuaYu_Outline07_3072x4096_4K.mp4'
meta=json.loads(subprocess.check_output([ffprobe,'-v','error','-show_streams','-show_format','-of','json',str(movie)]))
stream=next(x for x in meta['streams'] if x['codec_type']=='video')
w,h=stream['width'],stream['height']; size=w*h*3//2
assert (w,h)==(3072,4096) and stream['r_frame_rate']=='30/1'
assert float(meta['format']['duration'])==20
logs=[open(ROOT/'qa'/f'{name}_decode.log','wb') for name in ('software','hardware')]
commands=[[ffmpeg,'-hide_banner','-loglevel','warning','-threads','4','-c:v',decoder,'-i',str(movie),'-an','-pix_fmt','yuv420p','-f','rawvideo','pipe:1'] for decoder in ('h264','h264_cuvid')]
processes=[subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=log) for cmd,log in zip(commands,logs)]
def frame(pipe):
    out=bytearray()
    while len(out)<size:
        block=pipe.read(size-len(out))
        if not block:break
        out.extend(block)
    return out
count=0; max_diff=0; sum_diff=0; different=0; stats=[]; black_frames=[]
while True:
    a,b=[frame(p.stdout) for p in processes]
    if not a and not b:break
    assert len(a)==len(b)==size
    aa=np.frombuffer(a,dtype=np.uint8); bb=np.frombuffer(b,dtype=np.uint8)
    delta=np.abs(aa.astype(np.int16)-bb.astype(np.int16))
    peak=int(delta.max()); max_diff=max(max_diff,peak); sum_diff+=int(delta.sum()); different+=int(peak>0)
    y=aa[:w*h].reshape(h,w); yy,xx=np.where(y>38); count+=1
    if count<=530:
        minimum=100 if 181<=count<=249 else 1000
        assert len(xx)>minimum,f'Unexpected blank frame {count}: {len(xx)}'
    near_black=y.max()<=20 and y.mean()<16.1
    if count>=588:
        assert near_black,f'Unexpected visible tail {count}'
        with Image.open(ROOT/'frames'/f'bloom_{count:04d}.png') as im:
            assert np.asarray(im).max()<=1,'Source tail must contain only black-level dithering'
    if near_black:black_frames.append(count)
    stats.append({'frame':count,'lit_pixels':len(xx),'luma_mean':float(y.mean()),'luma_max':int(y.max()),'bounds':[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())] if len(xx) else None})
    if count%60==0:print('DECODED_AND_COMPARED',count,flush=True)
codes=[p.wait() for p in processes]
for log in logs:log.close()
assert codes==[0,0] and count==600 and max_diff<=2
assert stats[559]['lit_pixels']<stats[529]['lit_pixels']*.5
files=sorted((ROOT/'frames').glob('bloom_*.png'))
assert len(files)==600
for p in files:
    with Image.open(p) as im:assert im.size==(w,h)
chosen=[1,105,185,215,240,261,290,367,490,530,560,600]
sheet=Image.new('RGB',(1200,1272),(7,7,9)); draw=ImageDraw.Draw(sheet)
for i,f in enumerate(chosen):
    with Image.open(ROOT/'frames'/f'bloom_{f:04d}.png') as im:im=im.resize((300,400))
    x=(i%4)*300; y=(i//4)*424
    sheet.paste(im,(x,y+24)); draw.text((x+9,y+5),f'{(f-1)/30:.2f}s / {f:03d}',fill='#c4a38f')
sheet=sheet.crop((0,0,1200,1272)); sheet.save(ROOT/'qa/full-film-contact.jpg',quality=94)
summary={'native_video':{'width':w,'height':h,'aspect':'3:4','fps':stream['r_frame_rate'],'frame_count':count,'duration_seconds':float(meta['format']['duration']),'codec':stream['codec_name'],'pixel_format':stream['pix_fmt'],'color_space':stream.get('color_space'),'audio':any(x['codec_type']=='audio' for x in meta['streams'])},'native_pngs':{'count':len(files),'dimensions_verified_for_all':True},'full_decode_comparison':{'software_decoder':'FFmpeg h264','hardware_decoder':'NVIDIA h264_cuvid','comparison':'Every native YUV420P sample at 3072x4096, all 600 frames','max_sample_difference_8bit':max_diff,'mean_absolute_sample_difference':sum_diff/(count*size),'different_frames':different,'unexpected_blank_frames_before_fade':0,'exit_codes':codes},'ending_check':{'type':'Wind fade to black, no loop','intentional_black_frames':black_frames,'last_frame_luma_max':stats[-1]['luma_max'],'black_tolerance_8bit_luma':{'reference_black':16,'maximum':20,'mean_below':16.1,'source_tail_rgb_maximum':1,'reason':'All 13 source tail frames are checked for RGB 0/1 dithering only; the video allows black-level PNG dithering and H.264 quantization.'}},'browser_playback':{'status':'pending'},'per_frame_luma_scan':stats}
(ROOT/'qa/video-check.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='per_frame_luma_scan'},ensure_ascii=False,indent=2),flush=True)
