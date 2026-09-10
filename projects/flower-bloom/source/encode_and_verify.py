"""Encode the completed native render and verify every frame of both MP4s.

Run after frames/frame_0001.png through frame_0240.png have finished rendering.
Existing MP4 outputs are preserved; FFmpeg refuses to overwrite them.
"""

import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
FRAME_COUNT = 240
FPS = 30
LOGS = ROOT / 'logs' / 'delivery'
REPORT = ROOT / 'delivery-verification.json'
VIDEOS = (
    ('HUANGHUAYU_Flower_4K.mp4', (2160, 3840), 17, 51, '40M', '80M'),
    ('HUANGHUAYU_Flower_Preview_1080.mp4', (1080, 1920), 19, 41, '12M', '24M'),
)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def check_frames():
    frames = sorted((ROOT / 'frames').glob('frame_*.png'))
    expected = [f'frame_{frame:04d}.png' for frame in range(1, FRAME_COUNT + 1)]
    require([path.name for path in frames] == expected,
            'The native render must contain exactly frame_0001.png through frame_0240.png.')
    for path in frames:
        with Image.open(path) as im:
            require(im.format == 'PNG' and im.size == (2160, 3840),
                    f'Invalid native frame format or dimensions: {path.name}, {im.size}')
            im.verify()
    print('NATIVE FRAMES PASSED: 240 PNGs at 2160 x 3840.', flush=True)


def encode(ffmpeg, name, size, crf, level, maxrate, bufsize):
    width, height = size
    command = [
        ffmpeg, '-hide_banner', '-loglevel', 'warning', '-nostdin', '-n',
        '-threads', '4', '-filter_threads', '4', '-framerate', str(FPS),
        '-start_number', '1', '-i', str(ROOT / 'frames' / 'frame_%04d.png'),
        '-map', '0:v:0', '-an', '-frames:v', str(FRAME_COUNT),
        '-vf', f'scale={width}:{height}:flags=lanczos:out_color_matrix=bt709:out_range=tv,setsar=1',
        '-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf), '-threads', '4',
        '-profile:v', 'high', '-level:v', f'{level // 10}.{level % 10}',
        '-refs', '3', '-bf', '2', '-g', '60', '-maxrate', maxrate, '-bufsize', bufsize,
        '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'iec61966-2-1',
        '-colorspace', 'bt709', '-color_range', 'tv', '-movflags', '+faststart',
        str(ROOT / name),
    ]
    print(f'ENCODING: {name}', flush=True)
    with (LOGS / f'{Path(name).stem}-encode.log').open('wb') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    require(result.returncode == 0, f'Encoding failed: {name}; see its encode log.')


def probe(ffprobe, entry, size, level):
    path = ROOT / entry['file']
    result = subprocess.run([
        ffprobe, '-v', 'error', '-count_frames', '-show_streams', '-show_format',
        '-of', 'json', str(path),
    ], capture_output=True, text=True, encoding='utf-8', check=True)
    info = json.loads(result.stdout)
    entry['ffprobe'] = info
    streams = info['streams']
    require(len(streams) == 1 and streams[0]['codec_type'] == 'video',
            f'Expected one video stream: {path.name}')
    stream = streams[0]
    require((stream['width'], stream['height']) == size, f'Wrong dimensions: {path.name}')
    require(stream['codec_name'] == 'h264' and stream['profile'] == 'High'
            and stream['pix_fmt'] == 'yuv420p' and stream['level'] == level,
            f'Wrong codec, profile, pixel format or level: {path.name}')
    require(Fraction(stream['r_frame_rate']) == FPS
            and Fraction(stream['avg_frame_rate']) == FPS,
            f'Wrong frame rate: {path.name}')
    require(int(stream['nb_frames']) == FRAME_COUNT
            and int(stream['nb_read_frames']) == FRAME_COUNT,
            f'Wrong declared or decoded frame count: {path.name}')
    require(int(stream['duration_ts']) * Fraction(stream['time_base']) == 8
            and Fraction(stream['duration']) == 8
            and Fraction(info['format']['duration']) == 8,
            f'Wrong duration: {path.name}')
    require(stream.get('sample_aspect_ratio') == '1:1'
            and all(stream.get(key) == 'bt709'
                    for key in ('color_primaries', 'color_space'))
            and stream.get('color_transfer') == 'iec61966-2-1'
            and stream.get('color_range') == 'tv',
            f'Wrong pixel aspect ratio or color tags: {path.name}')
    entry['bytes'] = path.stat().st_size
    entry['metadata_passed'] = True


def compare_decoders(ffmpeg, entry):
    stream = next(s for s in entry['ffprobe']['streams'] if s['codec_type'] == 'video')
    width, height = stream['width'], stream['height']
    frame_bytes = width * height * 3
    decoders = ('h264', 'h264_cuvid')
    stem = Path(entry['file']).stem
    metrics_path = LOGS / f'{stem}-native-frame-differences.json'
    processes, handles = [], []
    comparison = {
        'passed': False, 'software_decoder': 'h264', 'hardware_decoder': 'h264_cuvid',
        'comparison_resolution': [width, height], 'comparison_pixel_format': 'rgb24',
        'pixel_format_normalization': 'NV12/planar layout is unified as YUV420P before both '
                                      'paths use the same RGB conversion. No resizing, spatial '
                                      'filtering, denoising or change to comparison thresholds.',
        'frames_compared': 0, 'decoded_frame_counts': {decoder: 0 for decoder in decoders},
        'partial_frame_bytes': {decoder: 0 for decoder in decoders},
        'channel_difference_threshold': 5,
        'worst_frame_selection': 'Largest mean RGB difference, then largest channel difference.',
        'player_ui_verification': 'not_verified',
        'sample_visual_review': 'not_verified',
        'scope': 'Full native-resolution software and NVIDIA hardware frame comparison, without '
                 'spatial resizing. Tool comparison does not verify playback in a player UI.',
    }
    entry['decode_comparison'] = comparison
    difference_sum = 0
    worst_mean, maximum_difference = 0.0, 0
    worst_fraction_over_5 = 0.0
    frame_metrics, samples = [], {}
    worst_raw, worst_frame, worst_key = None, None, (-1.0, -1)
    log_paths = []

    def save_sample(blob, decoder, frame):
        images = samples.setdefault(str(frame), {})
        if decoder not in images:
            path = LOGS / f'{stem}-{decoder}-frame_{frame:04d}.png'
            with Image.frombytes('RGB', (width, height), blob) as im:
                im.save(path)
            images[decoder] = str(path.relative_to(ROOT))

    try:
        for decoder in decoders:
            label = 'software' if decoder == 'h264' else decoder
            log_path = LOGS / f"{Path(entry['file']).stem}-{label}-decode.log"
            log_paths.append(log_path)
            log = log_path.open('wb')
            handles.append(log)
            command = [
                ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostdin', '-xerror',
                '-threads', '4', '-c:v', decoder, '-i', str(ROOT / entry['file']),
                '-map', '0:v:0', '-an', '-filter_threads', '4',
                '-vf', 'format=yuv420p', '-pix_fmt', 'rgb24',
                '-fps_mode', 'passthrough', '-threads', '4', '-f', 'rawvideo', 'pipe:1',
            ]
            processes.append(subprocess.Popen(command, stdout=subprocess.PIPE, stderr=log))
        while True:
            raw = [process.stdout.read(frame_bytes) for process in processes]
            if not any(raw):
                break
            for decoder, blob in zip(decoders, raw):
                if len(blob) == frame_bytes:
                    comparison['decoded_frame_counts'][decoder] += 1
                    frame = comparison['decoded_frame_counts'][decoder]
                    if frame in (1, 120, 240):
                        save_sample(blob, decoder, frame)
                else:
                    comparison['partial_frame_bytes'][decoder] += len(blob)
            if not all(len(blob) == frame_bytes for blob in raw):
                continue  # Drain the other decoder to retain its actual full-film frame count.
            frame = comparison['decoded_frame_counts']['h264']
            difference = np.frombuffer(raw[0], dtype=np.uint8).astype(np.int16)
            np.subtract(difference, np.frombuffer(raw[1], dtype=np.uint8), out=difference)
            np.abs(difference, out=difference)
            mean, maximum = float(difference.mean()), int(difference.max())
            fraction_over_5 = float(np.mean(difference.reshape(-1, 3).max(axis=1) > 5))
            difference_sum += int(difference.sum())
            worst_mean = max(worst_mean, mean)
            maximum_difference = max(maximum_difference, maximum)
            worst_fraction_over_5 = max(worst_fraction_over_5, fraction_over_5)
            frame_metrics.append({'frame': frame, 'mean_rgb_difference': mean,
                                  'maximum_channel_difference': maximum,
                                  'fraction_pixels_over_threshold': fraction_over_5})
            if (mean, maximum) > worst_key:
                worst_key, worst_frame, worst_raw = (mean, maximum), frame, raw
            del difference  # Keep only the current pair and the worst pair of decoded frames.
            comparison['frames_compared'] += 1
        comparison['decoder_exit_codes'] = [process.wait() for process in processes]
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait()
            process.stdout.close()
        for handle in handles:
            handle.close()
        comparison['decoder_exit_codes'] = [process.returncode for process in processes]
        if worst_raw is not None:
            for decoder, blob in zip(decoders, worst_raw):
                save_sample(blob, decoder, worst_frame)
        metrics_path.write_text(json.dumps({
            'file': entry['file'], 'resolution': [width, height], 'pixel_format': 'rgb24',
            'decoders': list(decoders), 'channel_difference_threshold': 5,
            'frames': frame_metrics,
        }, indent=2), encoding='utf-8')
        count = comparison['frames_compared']
        comparison.update({
            'mean_rgb_difference_0_to_255': difference_sum / (count * frame_bytes) if count else None,
            'worst_frame_mean_rgb_difference': worst_mean if count else None,
            'maximum_channel_difference': maximum_difference if count else None,
            'worst_frame_fraction_pixels_difference_over_5': worst_fraction_over_5 if count else None,
            'worst_frame': worst_frame,
            'per_frame_metrics': str(metrics_path.relative_to(ROOT)),
            'native_sample_images': samples,
            'logs': [str(path.relative_to(ROOT)) for path in log_paths],
        })
    require(comparison['decoder_exit_codes'] == [0, 0]
            and all(count == FRAME_COUNT for count in comparison['decoded_frame_counts'].values())
            and not any(comparison['partial_frame_bytes'].values())
            and comparison['frames_compared'] == FRAME_COUNT
            and all(path.stat().st_size == 0 for path in log_paths)
            and worst_mean < 0.1 and worst_fraction_over_5 < 0.0001,
            f"Software/hardware decode comparison failed: {entry['file']}; see decode logs.")
    comparison['passed'] = True
    entry['passed'] = True
    print(f"VIDEO PASSED: {entry['file']} — 240 frames, both decoders agree.", flush=True)


def make_stills():
    poster = ROOT / 'HUANGHUAYU_Flower_Poster_4K.png'
    shutil.copyfile(ROOT / 'frames' / 'frame_0155.png', poster)
    selected = (1, 35, 69, 103, 137, 171, 205, 240)
    sheet = Image.new('RGB', (960, 854), '#131919')
    for index, frame in enumerate(selected):
        with Image.open(ROOT / 'frames' / f'frame_{frame:04d}.png') as source:
            tile = source.convert('RGB').resize((240, 427), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(tile)
        draw.rectangle((0, 407, 240, 427), fill='#131919')
        draw.text((8, 411), f'Frame {frame:03d}  |  {(frame - 1) / FPS:.2f}s', fill='#e7e6df')
        sheet.paste(tile, ((index % 4) * 240, (index // 4) * 427))
    contact = ROOT / 'HUANGHUAYU_Flower_Contact_Sheet.jpg'
    sheet.save(contact, quality=94, subsampling=0)
    return {'poster': poster.name, 'poster_frame': 155, 'poster_resolution': [2160, 3840],
            'contact_sheet': contact.name, 'contact_frames': list(selected),
            'contact_grid': [4, 2], 'contact_cell_size': [240, 427]}


def main():
    report = {'status': 'running', 'passed': False, 'videos': []}
    LOGS.mkdir(parents=True, exist_ok=True)
    try:
        ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
        require(ffmpeg and ffprobe, 'ffmpeg and ffprobe must be available on PATH.')
        check_frames()
        report['native_frames'] = {'passed': True, 'count': FRAME_COUNT,
                                   'resolution': [2160, 3840], 'fps': FPS, 'seconds': 8}
        require(not any((ROOT / spec[0]).exists() for spec in VIDEOS),
                'An MP4 output already exists; preserve it before starting a fresh encoding run.')
        for name, size, crf, level, maxrate, bufsize in VIDEOS:
            encode(ffmpeg, name, size, crf, level, maxrate, bufsize)
        report['stills'] = make_stills()
        for name, size, _, level, _, _ in VIDEOS:
            entry = {'file': name, 'passed': False}
            report['videos'].append(entry)
            probe(ffprobe, entry, size, level)
            compare_decoders(ffmpeg, entry)
        report.update(status='passed', passed=True)
    except Exception as error:
        report.update(status='failed', passed=False, error=f'{type(error).__name__}: {error}')
        raise
    finally:
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'status': report['status'], 'passed': report['passed'],
                          'report': str(REPORT)}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
