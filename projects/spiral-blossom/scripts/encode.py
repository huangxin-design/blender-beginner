"""Encode and verify the completed 3:4 cinematic PNG sequence."""
import argparse
import json
import shutil
import struct
import subprocess
import zlib
from pathlib import Path

CASE = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--version', choices=['v013', 'v014'], required=True)
args = parser.parse_args()
ROOT = CASE/'output'/args.version
FRAMES = ROOT/'frames'
(ROOT/'renders').mkdir(parents=True, exist_ok=True)
STAGES = [181, 379, 505, 535, 690, 900]


def validate_png(path):
    data = path.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', path
    assert data[12:16] == b'IHDR' and struct.unpack('>II', data[16:24]) == (1080, 1440), path
    position, has_pixels = 8, False
    while position < len(data):
        size = struct.unpack('>I', data[position:position + 4])[0]
        end = position + 12 + size
        assert end <= len(data), path
        chunk = data[position + 4:position + 8]
        actual_crc = zlib.crc32(data[position + 4:end - 4]) & 0xffffffff
        assert actual_crc == struct.unpack('>I', data[end - 4:end])[0], path
        has_pixels |= chunk == b'IDAT'
        position = end
        if chunk == b'IEND':
            assert size == 0 and position == len(data) and has_pixels, path
            return
    raise AssertionError(f'Missing PNG end: {path}')


for number in range(1,901):
    validate_png(FRAMES / f'{number:04d}.png')
# Hash decoded RGB pixels, excluding PNG metadata such as the frame number.
hash_output = subprocess.check_output(['ffmpeg','-v','error','-threads','2',
    '-framerate','60','-start_number','1','-i',str(FRAMES/'%04d.png'),
    '-frames:v','900','-vf','format=rgb24','-threads','2','-f','framemd5','-'],text=True)
hashes = [line.rsplit(',',1)[-1].strip() for line in hash_output.splitlines()
          if line and not line.startswith('#')]
assert len(hashes)==900 and len(set(hashes[856:]))==1
repeated_in_action = [i+1 for i in range(120,720) if hashes[i]==hashes[i-1]]
assert not repeated_in_action, repeated_in_action
print('PNG_VALIDATION_PASSED 900 native frames', flush=True)

reports = []
for label,width,height,level,crf in [('Master',1080,1440,'4.2','17'),
                                    ('Preview',720,960,'4.0','18')]:
    video = ROOT/('final.mp4' if label=='Master' else 'preview.mp4')
    filters = f'scale={width}:{height}:flags=lanczos,' if width != 1080 else ''
    filters += 'format=gbrpf32le,zscale=primariesin=bt709:transferin=iec61966-2-1:matrixin=gbr:rangein=full:primaries=bt709:transfer=bt709:matrix=bt709:range=limited,format=yuv420p'
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-xerror',
        '-framerate','60','-start_number','1','-i',str(FRAMES/'%04d.png'),
        '-frames:v','900','-vf',filters,'-c:v','libx264','-threads','4',
        '-preset','medium','-tune','fastdecode','-crf',crf,'-profile:v','high',
        '-level:v',level,'-refs','2','-bf','0','-g','60','-keyint_min','60',
        '-sc_threshold','0','-pix_fmt','yuv420p','-colorspace','bt709',
        '-color_primaries','bt709','-color_trc','bt709','-color_range','tv',
        '-movflags','+faststart','-an',str(video)],check=True)
    info = json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames',
        '-show_streams','-show_format','-of','json',str(video)],text=True))
    stream = info['streams'][0]
    assert len(info['streams'])==1 and stream['codec_type']=='video'
    assert (stream['width'],stream['height'])==(width,height)
    assert stream['nb_frames']==stream['nb_read_frames']=='900'
    assert stream['r_frame_rate']==stream['avg_frame_rate']=='60/1'
    assert stream['codec_name']=='h264' and stream['pix_fmt']=='yuv420p'
    assert stream['color_space']==stream['color_primaries']==stream['color_transfer']=='bt709'
    assert abs(float(info['format']['duration'])-15)<.001
    assert stream['has_b_frames']==0 and stream['refs']<=2
    subprocess.run(['ffmpeg','-hide_banner','-v','error','-xerror','-threads','4',
        '-i',str(video),'-f','null','-'],check=True)
    frames = json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams',
        'v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time',
        '-of','json',str(video)],text=True))['frames']
    pts = [float(f['best_effort_timestamp_time']) for f in frames]
    max_pts_error = max(abs(b-a-1/60) for a,b in zip(pts,pts[1:]))
    assert len(pts)==900 and max_pts_error<2e-6
    reports.append({'label':label,'path':video.relative_to(CASE).as_posix(),'passed':True,'frames':900,
        'fps':60,'seconds':15,'resolution':[width,height],'full_decode':'passed',
        'max_timestamp_step_error':max_pts_error,'bytes':video.stat().st_size})
    print('VIDEO_VALIDATED',label,flush=True)

shutil.copy2(FRAMES/'0900.png',ROOT/'preview.png')
contact = ['ffmpeg','-y','-hide_banner','-loglevel','error']
for frame in STAGES:
    contact.extend(['-i',str(FRAMES/f'{frame:04d}.png')])
filters = ';'.join(f'[{i}:v]scale=180:240:flags=lanczos[v{i}]' for i in range(6))
filters += ';'+''.join(f'[v{i}]' for i in range(6))+'hstack=inputs=6[out]'
contact.extend(['-filter_complex',filters,'-map','[out]','-frames:v','1','-q:v','2',
                str(ROOT/'renders'/'animation_stages.jpg')])
subprocess.run(contact,check=True)
(ROOT/'renders'/'video_audit.json').write_text(json.dumps({
    'png_crc_validation':'900 passed','native_frame_render':True,
    'repeated_frames_in_2_to_12_seconds':repeated_in_action,
    'held_frames':'858..900 repeat 857; native scene verified constant',
    'versions':reports},indent=2),encoding='utf-8')
print(json.dumps(reports),flush=True)
