"""Native resolution render with atomic frame output and resumable sequences."""
import argparse
import json
import sys
import time
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--variant', choices=['rose','crystal','clay_wire','all'], required=True)
p.add_argument('--mode', choices=['preview','check','movie'], required=True)
p.add_argument('--frames')
p.add_argument('--force',action='store_true')
args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
manifest = json.loads((ROOT/'manifest.json').read_text())
variants = list(manifest) if args.variant == 'all' else [args.variant]

def complete_png(path, size):
    if not path.exists() or path.stat().st_size < 100: return False
    with path.open('rb') as f:
        header = f.read(24); f.seek(-12,2); end = f.read()
    return header[:8] == b'\x89PNG\r\n\x1a\n' and int.from_bytes(header[16:20],'big') == size[0] and int.from_bytes(header[20:24],'big') == size[1] and end[4:8] == b'IEND'

for variant in variants:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/manifest[variant]['project']))
    s = bpy.context.scene
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    for device in prefs.devices: device.use = device.type == 'OPTIX'
    assert any(d.use and d.type == 'OPTIX' for d in prefs.devices)
    s.cycles.device = 'GPU'
    s.render.resolution_percentage = 100
    if args.mode == 'preview':
        s.render.resolution_x, s.render.resolution_y = 414,736
        s.cycles.samples = 32; s.cycles.adaptive_threshold = .035
        frames = [1,121,217]
        folder = ROOT/'previews'/variant
    else:
        assert (s.render.resolution_x,s.render.resolution_y) == (2160,3840)
        frames = [1,121,217] if args.mode == 'check' else list(range(1,218))
        folder = ROOT/'frames'/variant
    if args.frames: frames = [int(f) for f in args.frames.split(',')]
    folder.mkdir(parents=True,exist_ok=True)
    started = time.monotonic(); rendered = 0
    for frame in frames:
        target = folder/f'{frame:04d}.png'
        if not args.force and complete_png(target,(s.render.resolution_x,s.render.resolution_y)): continue
        s.frame_set(frame)
        temp = folder/f'{frame:04d}.tmp.png'
        s.render.filepath = str(temp)
        bpy.ops.render.render(write_still=True)
        assert complete_png(temp,(s.render.resolution_x,s.render.resolution_y))
        temp.replace(target)
        rendered += 1
        progress = {'variant':variant,'mode':args.mode,'frame':frame,'frames_needed':217,
            'rendered_this_run':rendered,'elapsed_seconds':round(time.monotonic()-started,1),
            'resolution':[s.render.resolution_x,s.render.resolution_y]}
        status = ROOT/f'{variant}_progress.json'
        temporary = status.with_suffix('.tmp')
        temporary.write_text(json.dumps(progress,indent=2),encoding='utf-8'); temporary.replace(status)
        print('FRAME_DONE',json.dumps(progress),flush=True)
    print('RENDER_COMPLETE',variant,args.mode,flush=True)
