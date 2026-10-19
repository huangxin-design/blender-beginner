"""Render V004 in fresh 10-frame processes, or V005 in fresh 30-frame processes."""
import argparse
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--version', choices=('v004', 'v005'), required=True)
parser.add_argument('--blender', default='blender', help='Blender 5.2.1 executable or full path')
parser.add_argument('--start', type=int, default=1)
parser.add_argument('--end', type=int, default=450)
parser.add_argument('--device', choices=('CPU', 'OPTIX'), default='CPU', help='Cycles only; ignored for EEVEE')
parser.add_argument('--samples', type=int)
parser.add_argument('--scale', type=float, default=1)
args = parser.parse_args()
if not 1 <= args.start <= args.end <= 450:
    parser.error('Frame range must be within 1–450.')
if not 0 < args.scale <= 1 or (args.samples is not None and args.samples < 1):
    parser.error('Use 0 < scale <= 1 and positive samples.')
source = ROOT / 'versions' / args.version / 'scene.blend'
if not source.is_file():
    raise FileNotFoundError(f'Download the Release scene into {source}.')
width, height, batch_size = (720, 960, 10) if args.version == 'v004' else (2880, 3840, 30)
expected = tuple(max(2, round(value * args.scale / 2) * 2) for value in (width, height))
out = ROOT / 'output' / args.version
logs = out / 'logs'
logs.mkdir(parents=True, exist_ok=True)
for start in range(args.start, args.end + 1, batch_size):
    end = min(start + batch_size - 1, args.end)
    command = [args.blender, '--background', '--threads', '6', '--python-exit-code', '1',
               '--python', str(ROOT / 'scripts/render.py'), '--', '--version', args.version,
               '--start', str(start), '--end', str(end), '--device', args.device, '--scale', str(args.scale)]
    if args.samples is not None:
        command += ['--samples', str(args.samples)]
    log_path = logs / f'batch_{start:04d}_{end:04d}.log'
    print(f'Rendering {start}–{end}; log: {log_path}', flush=True)
    with log_path.open('w', encoding='utf-8') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    for frame in range(start, end + 1):
        path = out / 'frames' / f'frame_{frame:04d}.png'
        with path.open('rb') as image:
            header = image.read(24)
        if header[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack('>II', header[16:24]) != expected:
            raise RuntimeError(f'Unexpected PNG dimensions or header: {path}')
    print(f'BATCH_COMPLETE {start}–{end}', flush=True)
