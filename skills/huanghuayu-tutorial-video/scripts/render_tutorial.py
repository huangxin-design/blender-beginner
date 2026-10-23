"""Render a local JSON lesson with the approved fixed-chassis tutorial design.

Requires Pillow, ffmpeg and ffprobe. No network access or voice synthesis occurs.
All media/font paths resolve relative to the config, independently of the CWD.
"""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

sys.dont_write_bytecode = True  # Keep a read-only installed skill free of local module caches.
from image_backdrop import fit_with_backdrop

ASSETS = Path(__file__).resolve().parents[1] / 'assets'
W, H = 1080, 1440
SCREEN = (75, 250, 930, 795)
CAPTION = (80, 1168, 970, 1348)
C = dict(background='#090C12', screen='#111923', panel='#1B2632',
         text='#F3F4EF', muted='#929FAE', accent='#A3EED5', amber='#C6A168')
SLOTS = {
    'single': [(92, 310, 896, 625)],
    'split': [(92, 310, 434, 625), (554, 310, 434, 625)],
    'grid': [(92, 310, 434, 275), (554, 310, 434, 275),
             (92, 650, 434, 275), (554, 650, 434, 275)],
    'card': [(92, 310, 360, 625)],
}
VIDEO_EXTS = {'.mp4', '.mov', '.mkv', '.webm', '.avi', '.m4v'}


def run(args, capture=False):
    return subprocess.run([str(a) for a in args], check=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None).stdout


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_streams',
                          '-show_format', '-of', 'json', path], True))


def resolve(base, value):
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def font_paths(config, base):
    """Find installed fonts; never distribute or silently substitute missing CJK."""
    roots = [Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts',
             Path.home() / 'AppData/Local/Microsoft/Windows/Fonts',
             Path('/usr/share/fonts'), Path('/usr/local/share/fonts'),
             Path.home() / '.local/share/fonts', Path.home() / '.fonts',
             Path('/System/Library/Fonts'), Path('/Library/Fonts'),
             Path.home() / 'Library/Fonts']
    files = {}
    for root in roots:
        if root.is_dir():
            for path in root.rglob('*'):
                if path.suffix.lower() in ('.ttf', '.otf', '.ttc'):
                    files.setdefault(path.name.lower(), path)
    fallback = ['MiSans-Regular.ttf', 'NotoSansCJKsc-Regular.otf',
                'NotoSansCJK-Regular.ttc', 'NotoSansSC-Regular.ttf',
                'SourceHanSansSC-Regular.otf', 'SourceHanSansCN-Regular.otf',
                'msyh.ttc', 'PingFang.ttc']
    choices = {
        'title': ['DouyinSansBold.otf', 'MiSans-Semibold.ttf'] + fallback,
        'regular': fallback,
        'bold': ['MiSans-Semibold.ttf', 'NotoSansCJKsc-Bold.otf', 'msyhbd.ttc'] + fallback,
        'mono': ['consola.ttf', 'DejaVuSansMono.ttf', 'Menlo.ttc'],
    }
    result = {}
    for role, names in choices.items():
        explicit = config.get('fonts', {}).get(role)
        candidates = [resolve(base, explicit)] if explicit else [files[n.lower()] for n in names if n.lower() in files]
        for path in candidates:
            if not path.is_file():
                continue
            f = ImageFont.truetype(str(path), 32)
            if role != 'mono' and bytes(f.getmask('中')) == bytes(f.getmask('\U0010ffff')):
                continue
            result[role] = path
            break
        if role not in result:
            raise ValueError(f'No usable {role} font. Set fonts.{role} to an installed font file'
                             ' (Chinese roles require MiSans, Noto Sans CJK/SC, Source Han Sans or Microsoft YaHei).')
    return result


class Design:
    def __init__(self, config, base):
        self.config = config
        self.paths = font_paths(config, base)
        self.font_cache = {}

    def font(self, size, role='regular'):
        key = size, role
        if key not in self.font_cache:
            self.font_cache[key] = ImageFont.truetype(str(self.paths[role]), size)
        return self.font_cache[key]

    def text(self, im, xy, value, size=34, color=None, width=960, role='regular'):
        f = self.font(size, role)
        if '\n' in value or f.getlength(value) > width:
            raise ValueError(f'Text exceeds its single-line safe area ({width}px): {value!r}')
        ImageDraw.Draw(im).text(xy, value, fill=color or C['text'], font=f)

    def background(self, chapter=0, active=None, total=1):
        im = Image.new('RGB', (W, H), C['background'])
        metal_panel(im, (18, 18, 1062, 1424), 30,
                    [(0, (64,59,76)), (.018,(31,34,43)), (.48,(21,25,33)), (.98,(18,21,29)), (1,(52,47,65))])
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((28,28,1052,1414), 24, outline='#14171F', width=2)
        for x,y in [(38,40),(1042,40),(38,1056),(1042,1056),(38,1401),(1042,1401)]:
            d.ellipse((x-5,y-5,x+5,y+5), fill='#10141A', outline='#646271')
            d.line((x-2,y+2,x+2,y-2), fill='#7B7782')
        brand = self.config.get('brand', '黄花鱼频道')
        self.text(im, (60,44), brand, 28, C['accent'], 650, 'title')
        self.text(im, (752,48), self.config.get('brand_tag','AI × CREATE'), 22, C['muted'], 230, 'mono')
        d.ellipse((1001,57,1015,71), fill='#376F63', outline='#6AB3A0')
        d.ellipse((976,60,984,68), fill='#B68D53')
        d.line((60,86,1017,86), fill='#3B3C48')
        chapters = self.config['chapters']
        for i,item in enumerate(chapters):
            x = 60 + i * (978 // len(chapters))
            width = 978 // len(chapters) - 48
            color = C['accent'] if i == chapter else '#5B6673'
            self.text(im, (x,184), item['code'], 18, color, 120, 'mono')
            self.text(im, (x+127,181), item['label'], 18, color, width-127)
            d.line((x,215,x+width,215), fill=color if i == chapter else '#30343F', width=2)
        metal_panel(im, (36,224,1044,1070), 20,
                    [(0,(74,67,88)), (.012,(38,42,52)), (.04,(19,23,31)), (.96,(20,24,31)), (1,(71,61,85))])
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((49,237,1031,1057),12,fill='#080C12',outline='#080A0F',width=3)
        d.rounded_rectangle((57,245,1023,1049),8,fill=C['screen'],outline='#293440')
        for y in range(249,1048,5): d.line((61,y,1019,y),fill='#121A23')
        for y in range(295,1000,45):
            d.line((42,y,42,y+19),fill='#737080')
            d.line((1038,y,1038,y+19),fill='#0A0D12',width=2)
        with Image.open(ASSETS/'graphics/tv_caption_blank_v1.png') as source:
            tv = source.convert('RGBA').crop((30,108,2088,672)).resize((1024,300),Image.Resampling.LANCZOS)
        im.paste(tv,(28,1084),tv)
        self.text(im,(88,1132),'// '+brand,23,C['accent'],700,'title')
        for i,line in enumerate(['01  prompt.read(context);','02  scene.build();','03  frame.render();']):
            self.text(im,(88,1183+i*30),line,18,'#2B323E',500,'mono')
        for i,line in enumerate(['// AI WORKFLOW','scene.ready();','}']):
            self.text(im,(795,1193+i*30),line,18,'#2B323E',180,'mono')
        self.text(im,(60,1391),self.config.get('footer','教程演示 · 可编辑素材'),16,C['muted'],310)
        if active is not None:
            self.text(im,(951,1390),f'{active+1:02}/{total:02}',18,C['muted'],90,'mono')
        step = min(39, 540 / total)
        for i in range(total):
            x = 390 + i * step
            d.rectangle((x,1399,x+step-10,1403), fill=C['accent'] if active is not None and i<=active else '#303B43')
        return im

    def captions(self, im, lines):
        if not lines: return
        size, line_height = (46,60) if len(lines)==3 else (48,66)
        f = self.font(size)
        d = ImageDraw.Draw(im)
        boxes = [d.textbbox((0,i*line_height),line,font=f) for i,line in enumerate(lines)]
        top, bottom = min(b[1] for b in boxes), max(b[3] for b in boxes)
        if len(lines)>3 or bottom-top>180 or any(b[2]-b[0]>870 for b in boxes):
            raise ValueError(f'Subtitle exceeds CRT safe area: {lines}')
        y = 1255-(bottom-top)/2-top
        for i,(line,b) in enumerate(zip(lines,boxes)):
            d.text((525-(b[2]-b[0])/2-b[0],y+i*line_height),line,fill=C['text'],font=f)

    def canvas(self, shot, index, total):
        im = self.background(shot['chapter'],index,total)
        self.text(im,(60,103),shot['title'],58,width=960,role='title')
        self.text(im,(92,264),shot.get('kicker',''),26,C['accent'],890)
        self.text(im,(92,1000),shot.get('note',''),25,C['muted'],896)
        d = ImageDraw.Draw(im)
        for item,(x,y,w,h) in zip(shot.get('media',[]),SLOTS[shot['layout']]):
            d.rounded_rectangle((x-3,y-3,x+w+3,y+h+3),8,fill='#131822',outline='#586175',width=2)
            self.text(im,(x+8,y+h+12),item.get('label',''),27,C['accent'],w-16)
        if shot['layout']=='card':
            card = shot.get('card',{})
            x = 488 if shot.get('media') else 92
            width = 988-x
            d.rounded_rectangle((x,310,988,935),12,fill=C['panel'],outline='#425664',width=2)
            eyebrow = card.get('eyebrow','')
            self.text(im,(x+26,344),eyebrow,25,C['accent'],width-52,'mono' if eyebrow.isascii() else 'regular')
            lines = card.get('lines',[])
            if len(lines)>5: raise ValueError('card.lines supports at most five lines')
            for i,line in enumerate(lines):
                self.text(im,(x+26,440+i*74),line,35,width=width-52,role='bold')
            self.text(im,(x+26,865),card.get('note',''),23,C['muted'],width-52)
        return im


def metal_panel(im, box, radius, stops):
    x0,y0,x1,y1 = box
    w,h = x1-x0,y1-y0
    surface = Image.new('RGB',(w,h)); d = ImageDraw.Draw(surface)
    for y in range(h):
        t = y/max(1,h-1)
        a,b = next((a,b) for a,b in zip(stops,stops[1:]) if a[0]<=t<=b[0])
        u = (t-a[0])/(b[0]-a[0])
        d.line((0,y,w,y),fill=tuple(round(a[1][j]*(1-u)+b[1][j]*u) for j in range(3)))
    mask = Image.new('L',(w,h))
    ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),radius,fill=255)
    im.paste(surface,(x0,y0),mask)
    ImageDraw.Draw(im).rounded_rectangle(box,radius,outline='#55515F')


def normalized_events(shot, duration):
    cues = shot.get('subtitle_events',[])
    if not cues: return []
    starts = [float(c['start']) for c in cues]
    if starts[0] != 0 or any(a>=b for a,b in zip(starts,starts[1:])) or starts[-1]>=duration:
        raise ValueError(f'{shot["id"]}: subtitle starts must increase from zero within the shot')
    if any(not c.get('lines') or any(not isinstance(line,str) or not line.strip() or '\n' in line for line in c['lines']) for c in cues):
        raise ValueError(f'{shot["id"]}: subtitle lines must be nonempty strings without newlines')
    return [dict(start=starts[i],end=starts[i+1] if i+1<len(cues) else duration,lines=c['lines']) for i,c in enumerate(cues)]


def media_source(item, base, cache, tag):
    path = resolve(base,item['file'])
    if not path.is_file(): raise FileNotFoundError(path)
    video = path.suffix.lower() in VIDEO_EXTS
    start = float(item.get('start_seconds',0))
    if start<0: raise ValueError('start_seconds must be nonnegative')
    if video:
        info = probe(path)
        stream = next(s for s in info['streams'] if s['codec_type']=='video')
        duration = float(info['format']['duration'])
        if start>=duration: raise ValueError(f'Video start lies beyond end: {path}')
        frame = cache/f'{tag}_source.png'
        run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',start,'-i',path,'-frames:v','1',frame])
        source = Image.open(frame).convert('RGB')
    else:
        source = Image.open(path).convert('RGB')
    crop = item.get('crop')
    if crop:
        if len(crop)!=4 or not (0<=crop[0]<crop[2]<=source.width and 0<=crop[1]<crop[3]<=source.height):
            raise ValueError(f'Invalid pixel crop for {path}: {crop}')
        source = source.crop(crop)
    fit = item.get('fit','contain')
    if fit not in ('contain','cover'): raise ValueError('fit must be contain or cover')
    return path,video,start,crop,fit,source


def movie_filter(layer, fps):
    _,_,w,h = layer['box']
    prefix = ''
    if layer['crop']:
        l,t,r,b = layer['crop']; prefix = f'crop={r-l}:{b-t}:{l}:{t},'
    return prefix+f'scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps={fps},tpad=stop_mode=clone:stop_duration=3600'


def stamp(t, ass=False):
    base = 100 if ass else 1000; value = round(t*base); sep = '.' if ass else ','
    return f'{value//(3600*base):02}:{value//(60*base)%60:02}:{value//base%60:02}{sep}{value%base:0{2 if ass else 3}}'


def write_subtitles(timeline, out, family):
    events = [dict(start=t['start']+c['start'],end=t['start']+c['end'],lines=c['lines']) for t in timeline for c in t['subtitle_events']]
    srt = '\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n'+'\n'.join(c['lines']) for i,c in enumerate(events))
    (out/'subtitles.srt').write_text(srt+'\n',encoding='utf-8')
    header = '[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1440\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n'
    header += f'Style: Default,{family},48,&H00EFF4F3,&H00EFF4F3,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,80,80,0,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
    rows = []
    for c in events:
        value = r'{\an5\pos(525,1255)\fs'+str(46 if len(c['lines'])==3 else 48)+'}'+r'\N'.join(c['lines'])
        rows.append(f'Dialogue: 0,{stamp(c["start"],True)},{stamp(c["end"],True)},Default,,0,0,0,,{value}')
    (out/'subtitles.ass').write_text(header+'\n'.join(rows)+'\n',encoding='utf-8-sig')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path,help='Output directory; contains tutorial.mp4, previews, timeline and subtitles')
    parser.add_argument('--prepare-only',action='store_true',help='Create frames/timeline/subtitles without encoding the video')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8-sig')); base = args.config.resolve().parent
    shots = config['shots']; video = config.get('video',{}); fps = int(video.get('fps',30))
    if not shots or len(shots)>40: raise ValueError('Use 1–40 shots')
    if (video.get('width',1080),video.get('height',1440))!=(1080,1440):
        raise ValueError('This approved layout renders at 1080×1440; resize the finished video separately if needed')
    if fps<=0 or fps>60: raise ValueError('fps must be 1–60')
    if not 1<=len(config['chapters'])<=3: raise ValueError('Use 1–3 chapter navigation labels')
    if len({s['id'] for s in shots})!=len(shots): raise ValueError('Shot ids must be unique')
    if any(not re.fullmatch(r'[A-Za-z0-9_-]+',s['id']) for s in shots): raise ValueError('Shot ids allow only ASCII letters, digits, _ and -')
    for tool in ['ffmpeg','ffprobe']:
        if not shutil.which(tool): raise RuntimeError(f'{tool} must be installed and on PATH')
    design = Design(config,base)
    out = args.output.resolve(); cache = out/'cache'; previews = out/'previews'
    for p in [out,cache,previews]: p.mkdir(parents=True,exist_ok=True)
    design.background().save(out/'background_blank.png')
    timeline = []; cursor_frames = 0; jobs = []
    for i,shot in enumerate(shots):
        sid = shot['id']; layout = shot['layout']
        if layout not in SLOTS: raise ValueError(f'Unknown layout: {layout}')
        if not isinstance(shot['chapter'],int) or not 0<=shot['chapter']<len(config['chapters']): raise ValueError(f'{sid}: invalid chapter index')
        count = len(shot.get('media',[]))
        if (layout!='card' and count!=len(SLOTS[layout])) or (layout=='card' and count>1): raise ValueError(f'{sid}: wrong media count for {layout}')
        audio = resolve(base,shot['audio_file']) if shot.get('audio_file') else None
        audio_length = float(probe(audio)['format']['duration']) if audio else 0
        duration = max(float(shot.get('duration_seconds',0)),audio_length)
        if duration<=0: raise ValueError(f'{sid}: supply positive duration_seconds or audio_file')
        tail = float(video.get('tail_seconds',.35))
        if tail<0: raise ValueError('tail_seconds cannot be negative')
        frames = math.ceil((duration+tail)*fps-1e-9); duration = frames/fps
        events = normalized_events(shot,duration)
        canvas = design.canvas(shot,i,len(shots)); layers = []
        for j,(item,box) in enumerate(zip(shot.get('media',[]),SLOTS[layout])):
            path,is_video,start,crop,fit,source = media_source(item,base,cache,f'{sid}_{j}')
            x,y,w,h = box
            fitted = fit_with_backdrop(source,(w,h)) if fit=='contain' else ImageOps.fit(source,(w,h),Image.Resampling.LANCZOS)
            canvas.paste(fitted,(x,y))
            if is_video:
                # A static same-source blurred backing surrounds a sharp moving contain image.
                # This keeps UI capture padding quiet and avoids mirroring/duplicating UI text.
                if fit=='contain':
                    contained = ImageOps.contain(source,(w,h))
                    fw,fh = contained.size; box=(x+(w-fw)//2,y+(h-fh)//2,fw,fh)
                layers.append(dict(file=str(path),start=start,crop=crop,box=box))
        canvas_path = cache/f'{sid}_canvas.png'; canvas.save(canvas_path)
        for ci,cue in enumerate(events):
            preview = canvas.copy(); design.captions(preview,cue['lines'])
            preview.save(previews/f'{sid}_cue_{ci+1}.png')
            overlay = Image.new('RGBA',(W,H)); design.captions(overlay,cue['lines'])
            overlay.crop(CAPTION).save(cache/f'{sid}_caption_{ci}.png')
        preview = canvas.copy()
        if events: design.captions(preview,events[0]['lines'])
        preview.save(previews/f'{sid}.png')
        transition = 0 if i==0 else max(1, round((12 if shot['chapter']!=shots[i-1]['chapter'] else 8)*fps/30))
        if frames<=transition: raise ValueError(f'{sid}: shot shorter than its transition')
        record = dict(id=sid,title=shot['title'],chapter=shot['chapter'],start=cursor_frames/fps,
                      duration=duration,end=(cursor_frames+frames)/fps,frames=frames,
                      screen_transition_frames=transition,subtitle_events=events,
                      audio_file=shot.get('audio_file'),audio_duration_seconds=audio_length)
        timeline.append(record); cursor_frames+=frames
        jobs.append((canvas_path,layers,audio))
    (out/'timeline.json').write_text(json.dumps(dict(duration_seconds=cursor_frames/fps,frames=cursor_frames,fps=fps,shots=timeline),ensure_ascii=False,indent=2),encoding='utf-8')
    write_subtitles(timeline,out,design.font(48).getname()[0])
    sheet = Image.new('RGB',(1080,math.ceil(len(shots)/4)*360),C['background'])
    for i,shot in enumerate(shots):
        with Image.open(previews/f'{shot["id"]}.png') as im: sheet.paste(im.resize((270,360)),((i%4)*270,(i//4)*360))
    sheet.save(previews/'contact_sheet.png')
    if args.prepare_only:
        print(f'PREPARED {len(shots)} shots: {out}',flush=True); return
    for i,(shot,record,job) in enumerate(zip(shots,timeline,jobs)):
        sid=shot['id']; canvas_path,layers,audio=job; duration=record['duration']
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-threads','2','-loop','1','-framerate',fps,'-i',canvas_path]
        filters=[]; previous='0:v'; next_input=1
        for j,layer in enumerate(layers):
            cmd+=['-ss',layer['start'],'-i',layer['file']]
            x,y,_,_=layer['box']
            filters += [f'[{next_input}:v]setpts=PTS-STARTPTS,{movie_filter(layer,fps)}[movie{j}]',f'[{previous}][movie{j}]overlay={x}:{y}:format=rgb[mix{j}]']
            previous=f'mix{j}';next_input+=1
        tf=record['screen_transition_frames']
        if tf:
            old=cache/f'{sid}_previous.png'; previous_frames=timeline[i-1]['frames']
            run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',cache/f'{i-1:03}.mp4','-vf',f'select=eq(n\\,{previous_frames-1}),format=rgb24,crop=930:795:75:250','-frames:v','1',old])
            cmd+=['-loop','1','-framerate',fps,'-i',old]; seconds=tf/fps
            filters += [f'[{next_input}:v]format=rgba,fade=t=out:st=0:d={seconds}:alpha=1[oldscreen]',f'[{previous}][oldscreen]overlay=75:250:format=rgb:enable=\'lt(t,{seconds})\'[transition]']
            previous='transition';next_input+=1
        for ci,cue in enumerate(record['subtitle_events']):
            cmd+=['-loop','1','-framerate',fps,'-i',cache/f'{sid}_caption_{ci}.png']
            filters += [f'[{previous}][{next_input}:v]overlay=80:1168:format=rgb:enable=\'gte(t,{cue["start"]})*lt(t,{cue["end"]})\'[caption{ci}]']
            previous=f'caption{ci}';next_input+=1
        cmd += ['-i',audio] if audio else ['-f','lavfi','-i','anullsrc=r=48000:cl=mono']
        filters += [f'[{previous}]null[v]']
        cmd += ['-filter_complex_threads','2','-filter_complex',';'.join(filters),'-map','[v]','-map',f'{next_input}:a:0','-af',f'apad=whole_dur={duration}','-frames:v',record['frames'],'-t',duration,'-r',fps,'-c:v','libx264','-preset','fast','-crf','18','-threads','4','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-ar','48000','-movflags','+faststart',cache/f'{i:03}.mp4']
        print(f'RENDER {i+1}/{len(shots)} {sid} {duration:.3f}s',flush=True);run(cmd)
    concat=cache/'concat.txt'
    concat.write_text('\n'.join(f"file '{i:03}.mp4'" for i in range(len(shots))),encoding='utf-8')
    destination=out/'tutorial.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',concat,'-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=9','-c:a','aac','-b:a','192k','-movflags','+faststart',destination])
    info=probe(destination);stream=next(s for s in info['streams'] if s['codec_type']=='video')
    decoded=subprocess.run(['ffmpeg','-hide_banner','-xerror','-i',str(destination),'-vf','blackdetect=d=0:pic_th=0.98:pix_th=0.02','-f','null','-'],capture_output=True,text=True,encoding='utf-8',errors='replace',check=True)
    checks=dict(resolution=(stream['width'],stream['height'])==(W,H),fps=float(Fraction(stream['avg_frame_rate']))==fps,
                frames=int(stream['nb_frames'])==cursor_frames,duration=abs(float(info['format']['duration'])-cursor_frames/fps)<.15,
                audio=any(s['codec_type']=='audio' for s in info['streams']),full_decode=True,no_black_frames='black_start:' not in decoded.stderr)
    report=dict(passed=all(checks.values()),checks=checks,frames=cursor_frames,seconds=float(info['format']['duration']),
                sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),bytes=destination.stat().st_size,
                fonts={k:str(v) for k,v in design.paths.items()})
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if not report['passed']: raise RuntimeError(report)
    print('VERIFIED '+str(destination),flush=True)


if __name__=='__main__':
    main()
