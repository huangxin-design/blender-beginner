"""Encode freshly rendered frames; archived videos under versions/ remain unchanged."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--version', choices=('v004', 'v005'), required=True)
parser.add_argument('--start', type=int, default=1)
parser.add_argument('--end', type=int, default=450)
args = parser.parse_args()
if not 1 <= args.start <= args.end <= 450:
    parser.error('Frame range must be within 1–450.')
out = ROOT / 'output' / args.version
for frame in range(args.start, args.end + 1):
    path = out / 'frames' / f'frame_{frame:04d}.png'
    if not path.is_file():
        raise FileNotFoundError(path)
count = args.end - args.start + 1
video = out / 'final.mp4'
subprocess.run(['ffmpeg', '-hide_banner', '-y', '-framerate', '30', '-start_number', str(args.start),
                '-i', str(out / 'frames/frame_%04d.png'), '-frames:v', str(count), '-an',
                '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart', str(video)], check=True)
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames',
    '-show_entries', 'stream=codec_name,width,height,r_frame_rate,nb_read_frames:format=duration,size',
    '-of', 'json', str(video)], text=True))
stream = probe['streams'][0]
if int(stream['nb_read_frames']) != count or stream['r_frame_rate'] != '30/1':
    raise RuntimeError('Encoded frame count or frame rate does not match.')
decoded = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-xerror', '-i', str(video),
    '-vf', 'blackdetect=d=0.01:pix_th=0.05:pic_th=0.95', '-an', '-f', 'null', '-'],
    capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)
(out / 'decode.log').write_text(decoded.stderr, encoding='utf-8')
if 'black_start:' in decoded.stderr:
    raise RuntimeError('Black interval detected; inspect output decode.log.')
probe.update(full_decode_passed=True, black_intervals=[])
(out / 'media_validation.json').write_text(json.dumps(probe, indent=2), encoding='utf-8')
print(video)
