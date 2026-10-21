# Publication adaptation: relative scene name and configurable installation paths.
"""Encode the completed native 3:4 sequence and verify both 15-second videos."""
import argparse
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FRAMES = ROOT/'renders'/'cache'/'frames'
NATIVE_SIZE = (3072, 4096)
FRAME_COUNT = 360
FPS = 24


def validate_frames(folder):
    invalid = []
    bit_depths = set()
    for frame in range(1, FRAME_COUNT + 1):
        path = folder / f'{frame:04d}.png'
        if not path.is_file() or path.stat().st_size < 57:
            invalid.append(path.name)
            continue
        with path.open('rb') as source:
            header = source.read(25)
            source.seek(-12, 2)
            ending = source.read(12)
        if (header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR'
                or struct.unpack('>II', header[16:24]) != NATIVE_SIZE
                or ending != b'\x00\x00\x00\x00IEND\xaeB`\x82'):
            invalid.append(path.name)
        else:
            bit_depths.add(header[24])
    if invalid:
        raise ValueError(f'{len(invalid)} missing/incomplete/non-native frames: {invalid[:12]}')
    return sorted(bit_depths)


def encode_and_verify(frames, movie, size, level):
    temporary = movie.with_name(movie.stem + '.encoding.mp4')
    conversion = (f'scale={size[0]}:{size[1]}:flags=lanczos+accurate_rnd:'
                  'in_range=pc:out_range=tv:out_color_matrix=bt709,setsar=1,'
                  'setparams=range=limited:color_primaries=bt709:'
                  'color_trc=iec61966-2-1:colorspace=bt709')
    command = [
        'ffmpeg', '-hide_banner', '-loglevel', 'warning', '-stats', '-xerror', '-y',
        '-threads', '2', '-framerate', str(FPS), '-start_number', '1',
        '-i', str(frames / '%04d.png'), '-frames:v', str(FRAME_COUNT), '-an',
        '-filter_threads', '2', '-vf', conversion, '-c:v', 'libx264',
        '-preset', 'slow', '-crf', '17', '-threads', '4', '-refs', '3',
        '-profile:v', 'high', '-level:v', level, '-pix_fmt', 'yuv420p',
        '-r', str(FPS), '-fps_mode', 'cfr', '-movflags', '+faststart',
        '-color_range', 'tv', '-color_primaries', 'bt709', '-color_trc', 'iec61966-2-1',
        '-colorspace', 'bt709', str(temporary),
    ]
    subprocess.run(command, check=True)
    probe = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json',
        str(temporary),
    ], text=True, encoding='utf-8'))
    stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    checks = {
        'resolution': (stream['width'], stream['height']) == size,
        'frame_count': int(stream.get('nb_frames', 0)) == FRAME_COUNT,
        'fps': stream['avg_frame_rate'] == '24/1' and stream['r_frame_rate'] == '24/1',
        'duration': abs(float(probe['format']['duration']) - 15) < 0.001,
        'aspect_ratio': stream['display_aspect_ratio'] == '3:4',
        'codec': stream['codec_name'] == 'h264' and stream['profile'] == 'High',
        'level': stream['level'] == round(float(level) * 10),
        'pixel_format': stream['pix_fmt'] == 'yuv420p',
        # The Blender PNGs use sRGB transfer; scale changes the YUV matrix and range only.
        'color': all(stream.get(k) == v for k, v in {
            'color_space': 'bt709', 'color_transfer': 'iec61966-2-1',
            'color_primaries': 'bt709', 'color_range': 'tv'}.items()),
    }
    if not all(checks.values()):
        raise ValueError(f'Media verification failed: {checks}')
    subprocess.run([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-xerror', '-threads', '2',
        '-i', str(temporary), '-map', '0:v:0', '-an', '-f', 'null', '-',
    ], check=True)
    temporary.replace(movie)
    return {'file': str(movie), 'checks': checks, 'full_decode': 'PASS',
            'color_encoding': {k: stream[k] for k in
                ('color_space', 'color_transfer', 'color_primaries', 'color_range')},
            'width': size[0], 'height': size[1], 'fps': FPS, 'frames': FRAME_COUNT,
            'duration_seconds': 15, 'h264_level': level, 'bytes': movie.stat().st_size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames-dir', type=Path, default=DEFAULT_FRAMES)
    args = parser.parse_args()
    bit_depths = validate_frames(args.frames_dir)
    print('SOURCE_SEQUENCE_VALIDATED', FRAME_COUNT, NATIVE_SIZE, flush=True)
    # 3072 x 4096 is 49,152 macroblocks: Level 5.2's 36,864 limit is insufficient.
    master = encode_and_verify(args.frames_dir, ROOT / 'Glass_Bloom_Direct_Wireclay_3x4_4K_15s.mp4',
                               NATIVE_SIZE, '6.0')
    preview_dir = ROOT / 'previews'
    preview_dir.mkdir(exist_ok=True)
    preview = encode_and_verify(args.frames_dir, preview_dir / 'Glass_Bloom_Direct_Wireclay_3x4_15s_preview.mp4',
                                (1152, 1536), '5.1')
    report = {'passed': True, 'source_frames': str(args.frames_dir.resolve()),
              'source_resolution': list(NATIVE_SIZE), 'source_bit_depths': bit_depths,
              'native_render_frames': FRAME_COUNT, 'frame_interpolation': False,
              'master': master, 'preview': preview}
    (ROOT / 'media_verification.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('MEDIA_VERIFICATION_PASS', json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
