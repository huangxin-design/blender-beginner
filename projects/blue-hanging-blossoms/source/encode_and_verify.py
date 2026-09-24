"""Encode a completed native PNG sequence; verify resolution, duration and decode."""
import json
import struct
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
folder=ROOT/'renders'
video=folder/'blue-hanging-blossoms-4k.mp4'
for frame in range(1,385):
    data=(folder/'frames'/f'{frame:04d}.png').read_bytes()
    assert data[:8]==b'\x89PNG\r\n\x1a\n' and data[-8:]==b'IEND\xaeB`\x82',frame
    assert struct.unpack('>II',data[16:24])==(2160,3840) and data[24]==16,frame
subprocess.run(['ffmpeg','-hide_banner','-y','-framerate','24','-start_number','1','-i',str(folder/'frames/%04d.png'),'-frames:v','384','-vf','scale=out_color_matrix=bt709:out_range=tv,format=yuv420p','-c:v','libx264','-preset','slow','-crf','16','-profile:v','high','-level:v','5.1','-colorspace','bt709','-color_primaries','bt709','-color_trc','iec61966-2-1','-movflags','+faststart','-an',str(video)],check=True)
probe=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(video)],capture_output=True,text=True,check=True)
info=json.loads(probe.stdout)['streams'][0]
assert (info['width'],info['height'])==(2160,3840),info
assert info['avg_frame_rate']=='24/1' and int(info['nb_read_frames'])==384,info
assert abs(float(info['duration'])-16)<.00001,info
decode=subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True,check=True)
assert not decode.stderr.strip(),decode.stderr
(folder/'verification.json').write_text(json.dumps({'movie':info,'full_decode_errors':False,'sequence_frames':384},indent=2),encoding='utf-8')
print(json.dumps(info,indent=2))
