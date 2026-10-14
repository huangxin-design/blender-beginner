"""Encode all 360 rendered frames and verify the complete 15-second video."""
import hashlib
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAMES = ROOT/'renders/frames_final'
MOVIE = ROOT/'film-15s.mp4'
for frame in range(1, 361):
    path = FRAMES/f'{frame:04d}.png'
    with path.open('rb') as f:
        header = f.read(24)
    assert header[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', header[16:24]) == (720, 960), path
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-xerror', '-y', '-framerate', '24',
                '-start_number', '1', '-i', str(FRAMES/'%04d.png'), '-frames:v', '360',
                '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p',
                '-vf', 'scale=in_range=pc:out_range=tv:out_color_matrix=bt709,setsar=1',
                '-movflags', '+faststart', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                '-colorspace', 'bt709', str(MOVIE)], check=True)
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(MOVIE)], text=True))
stream = probe['streams'][0]
assert (stream['width'], stream['height'], int(stream['nb_frames'])) == (720, 960, 360)
assert stream['avg_frame_rate'] == '24/1' and stream['display_aspect_ratio'] == '3:4'
assert abs(float(probe['format']['duration'])-15) < .001
subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(MOVIE), '-f', 'null', '-'], check=True)
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(MOVIE),
                '-vf', 'fps=1,scale=180:240,tile=5x3', '-frames:v', '1', str(ROOT/'renders/storyboard.jpg')], check=True)
report = {'passed': True, 'width': 720, 'height': 960, 'fps': 24, 'frames': 360,
          'duration_seconds': 15, 'complete_timeline': True, 'full_decode': 'PASS',
          'movie_bytes': MOVIE.stat().st_size, 'master_resolution': [1080, 1440],
          'master_sha256': hashlib.sha256((ROOT/'scene.blend').read_bytes()).hexdigest()}
(ROOT/'renders/media_verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('VIDEO_VERIFIED', json.dumps(report), flush=True)
