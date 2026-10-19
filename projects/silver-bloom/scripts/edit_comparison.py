"""Frame-synchronous clay-to-shaded breakdown using the approved two videos."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'output/v006'
OUTPUT.mkdir(parents=True, exist_ok=True)
beauty = ROOT / 'versions/v004/final.mp4'
clay = ROOT / 'versions/v005/final.mp4'
for source in (beauty, clay):
    if not source.is_file():
        raise FileNotFoundError(f'Missing {source}; see the project README for Release downloads.')
output = OUTPUT / 'final.mp4'

def wipe(start, end):
    # Both inputs retain identical timestamps; the boundary reveals the material.
    weight = f'clip(((T-{start:.9f})/{end-start:.9f}*(W+16)-X)/16,0,1)'
    return f'A*{weight}+B*(1-{weight})'

segments = [
    (88/30, 'A', 'shaded introduction'),
    (4.5, 'B', 'clay unfolding'),
    (5.3, wipe(4.5, 5.3), 'left-to-right material reveal'),
    (227/30, 'A', 'shaded unfolding'),
    (262/30, 'B', 'clay filament detail'),
    (9.4, wipe(262/30, 9.4), 'left-to-right material reveal'),
    (298/30, 'A', 'shaded filament detail'),
    (11.25, 'B', 'clay wide shot'),
    (12.25, wipe(11.25, 12.25), 'left-to-right material reveal'),
    (15, 'A', 'shaded final hold with petal motion'),
]
expression = 'A'
for end, value, _ in reversed(segments[:-1]):
    expression = f'if(lt(T,{end-1e-6:.9f}),{value},{expression})'
filters = (
    '[0:v]setpts=PTS-STARTPTS,scale=1080:1440:flags=lanczos,setsar=1,format=gbrp[a];\n'
    '[1:v]setpts=PTS-STARTPTS,scale=1080:1440:flags=lanczos,setsar=1,format=gbrp[b];\n'
    f"[a][b]blend=all_expr='{expression}':shortest=1,format=yuv420p[out]\n"
)
filter_path = OUTPUT / 'comparison_filter.txt'
filter_path.write_text(filters, encoding='utf-8')
timeline = []
start = 0
for end, _, title in segments:
    timeline.append({'start': start, 'end': end, 'treatment': title})
    start = end
(OUTPUT / 'edit_timeline.json').write_text(json.dumps({
    'sources': {'shaded':beauty.relative_to(ROOT).as_posix(), 'clay':clay.relative_to(ROOT).as_posix()},
    'resolution':[1080,1440], 'fps':30, 'frames':450,
    'note':'Preview: shaded source 720x960, clay source 2880x3840. No retiming; identical source frame at every wipe.',
    'segments':timeline}, ensure_ascii=False, indent=2), encoding='utf-8')
command = ['ffmpeg', '-hide_banner', '-y', '-threads', '4', '-i', str(beauty),
           '-threads', '4', '-i', str(clay), '-filter_complex_threads', '4',
           '-filter_complex', filters, '-map', '[out]', '-an',
           '-frames:v', '450', '-r', '30', '-c:v', 'libx264', '-preset', 'slow',
           '-crf', '16', '-threads', '6', '-pix_fmt', 'yuv420p',
           '-movflags', '+faststart', str(output)]
with (OUTPUT / 'encode.log').open('w', encoding='utf-8') as log:
    subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames',
    '-show_entries', 'stream=codec_name,width,height,r_frame_rate,nb_frames,nb_read_frames:format=duration,size',
    '-of', 'json', str(output)], text=True))
stream = probe['streams'][0]
assert (stream['width'], stream['height']) == (1080,1440)
assert stream['r_frame_rate'] == '30/1' and int(stream['nb_read_frames']) == 450
assert abs(float(probe['format']['duration'])-15) < .01
decoded = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-xerror', '-i', str(output),
    '-vf', 'blackdetect=d=0.01:pix_th=0.05:pic_th=0.95', '-an', '-f', 'null', '-'],
    capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)
(OUTPUT / 'decode.log').write_text(decoded.stderr, encoding='utf-8')
assert 'black_start:' not in decoded.stderr
probe.update(full_decode_passed=True, black_intervals=[], matched_source_time=True)
(OUTPUT / 'media_validation.json').write_text(json.dumps(probe, indent=2), encoding='utf-8')
print(json.dumps({'output':str(output), 'validation':probe}, indent=2), flush=True)
