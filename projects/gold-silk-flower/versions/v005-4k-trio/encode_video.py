"""Portable archive entry point for the original 4K H.264 encoding settings."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--variant', choices=['rose','crystal','clay_wire'], required=True)
args = p.parse_args()
manifest = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
validation = json.loads((ROOT/'Scene_Validation_4K.json').read_text(encoding='utf-8'))[args.variant]
assert validation['static_hold_verified'] and validation['static_hold_from_frame'] == 217
folder = ROOT/'frames'/args.variant
assert all((folder/f'{i:04d}.png').is_file() for i in range(1,218)), 'Render all 217 source frames first.'
output = ROOT/manifest[args.variant]['video']
temp = output.with_name(output.stem+'.encoding.mp4')
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','30','-start_number','1',
    '-i',str(folder/'%04d.png'),'-vf','tpad=stop_mode=clone:stop=83','-frames:v','300','-an',
    '-c:v','libx264','-preset','slow','-crf','16','-profile:v','high','-level:v','5.1','-pix_fmt','yuv420p',
    '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-movflags','+faststart',str(temp)],check=True)
probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries',
    'stream=codec_name,width,height,r_frame_rate,nb_read_frames,pix_fmt:format=duration,size','-of','json',str(temp)],text=True))
s = probe['streams'][0]
assert (s['width'],s['height'],s['r_frame_rate'],int(s['nb_read_frames'])) == (2160,3840,'30/1',300)
assert abs(float(probe['format']['duration'])-10)<.01
subprocess.run(['ffmpeg','-hide_banner','-v','error','-i',str(temp),'-f','null','-'],check=True)
temp.replace(output)
probe['complete_software_decode_passed'] = True
probe['hardware_and_player_checks'] = 'Not performed by this encoder; verify separately.'
(ROOT/f'{args.variant}_Media_Validation.json').write_text(json.dumps(probe,indent=2),encoding='utf-8')
print(output.name)
