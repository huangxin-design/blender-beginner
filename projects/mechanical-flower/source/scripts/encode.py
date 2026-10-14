"""Encode rendered frames with FFmpeg; Python 3 standard library only."""
from pathlib import Path
import argparse
import json
import struct
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--codec', choices=['vp9', 'hevc'], default='vp9')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
frames = root / 'renders'
audio = root / 'assets/audio/Mix_SciFi.wav'
for frame in range(1, 394):
    path = frames / f'{frame:04d}.png'
    if not path.is_file():
        raise SystemExit(f'Missing render: renders/{path.name}')
    with path.open('rb') as file:
        header = file.read(24)
    if header[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack('>II', header[16:24]) != (3072, 4096):
        raise SystemExit(f'Expected native 3072×4096 PNG: renders/{path.name}')
if not audio.is_file():
    raise SystemExit('Missing assets/audio/Mix_SciFi.wav')
output = root / 'exports'
output.mkdir(exist_ok=True)
color = ['-colorspace', 'bt709', '-color_primaries', 'bt709',
         '-color_trc', 'iec61966-2-1', '-color_range', 'tv']
if args.codec == 'vp9':
    target = output / 'Mechanical_Flower_4K_SciFi.webm'
    pixel = 'yuv420p'
    options = ['-c:v', 'libvpx-vp9', '-crf', '18', '-b:v', '0', '-cpu-used', '4',
               '-row-mt', '1', '-tile-columns', '2', '-threads', '12', '-g', '48',
               '-c:a', 'libopus', '-b:a', '192k']
else:
    target = output / 'Mechanical_Flower_4K_SciFi_HEVC.mp4'
    pixel = 'yuv420p10le'
    options = ['-c:v', 'libx265', '-preset', 'medium', '-crf', '18', '-g', '48',
               '-bf', '0', '-profile:v', 'main10', '-x265-params', 'pools=12:frame-threads=3',
               '-tag:v', 'hvc1', '-c:a', 'aac', '-b:a', '320k', '-movflags', '+faststart']
subprocess.run(['ffmpeg', '-y', '-hide_banner', '-xerror', '-framerate', '24',
    '-start_number', '1', '-i', str(frames / '%04d.png'), '-i', str(audio),
    '-map', '0:v:0', '-map', '1:a:0', '-frames:v', '393',
    '-vf', f'scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format={pixel}',
    *options, *color, '-ar', '48000', '-ac', '2', '-t', '16.375', str(target)], check=True)
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames',
    '-show_streams', '-show_format', '-of', 'json', str(target)]))
video = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
assert (video['width'], video['height'], video['r_frame_rate'], video['nb_read_frames']) == (3072, 4096, '24/1', '393')
subprocess.run(['ffmpeg', '-hide_banner', '-v', 'error', '-xerror', '-i', str(target),
                '-f', 'null', '-'], check=True)
print(f'Exported {target.name}: 3072×4096, 24 fps, 393 frames; full software decode passed.')
