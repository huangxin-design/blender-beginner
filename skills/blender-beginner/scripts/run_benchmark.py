"""Run one Blender frame in a separate process with a hard timeout."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender', required=True, type=Path)
    parser.add_argument('--blend', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--backend', default='AUTO', choices=('AUTO', 'CPU', 'OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL'))
    parser.add_argument('--width', type=int, default=960)
    parser.add_argument('--height', type=int, default=540)
    parser.add_argument('--samples', type=int, default=16)
    parser.add_argument('--frame', type=int)
    parser.add_argument('--timeout', type=float, default=90)
    args = parser.parse_args()
    if not 0 < args.timeout <= 300:
        parser.error('--timeout must be greater than 0 and no more than 300 seconds.')
    if not (1 <= args.width <= 8192 and 1 <= args.height <= 8192 and 1 <= args.samples <= 4096):
        parser.error('Invalid dimensions or sample count.')
    executable = args.blender.expanduser().resolve(strict=True)
    source = args.blend.expanduser().resolve(strict=True)
    if not executable.is_file() or not source.is_file() or source.suffix.lower() != '.blend':
        parser.error('Provide an existing Blender executable and .blend file.')
    if not args.output_dir.is_absolute():
        parser.error('--output-dir must be an absolute new directory.')
    output = args.output_dir.resolve()
    worker = Path(__file__).with_name('benchmark_frame.py')
    if not worker.is_file():
        parser.error('benchmark_frame.py is missing from the skill.')
    output.mkdir(parents=True, exist_ok=False)
    temp = output / 'temp'
    temp.mkdir()
    env = os.environ.copy()
    env.update(TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
    command = [str(executable), '--background', '--factory-startup', '--disable-autoexec',
               str(source), '--python-exit-code', '1', '--python', str(worker), '--',
               '--output-dir', str(output / 'render'), '--backend', args.backend,
               '--width', str(args.width), '--height', str(args.height), '--samples', str(args.samples)]
    if args.frame is not None:
        command.extend(['--frame', str(args.frame)])
    result = {'status': 'not_started', 'source': str(source), 'timeout_seconds': args.timeout,
              'report': str(output / 'render' / 'report.json'),
              'limitation': 'One bounded frame is not proof of 4K capacity or sustained animation performance.'}
    started = time.perf_counter()
    try:
        with (output / 'blender.log').open('w', encoding='utf-8') as log:
            process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                     timeout=args.timeout, env=env,
                                     creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        result['exit_code'] = process.returncode
        result['status'] = 'completed' if process.returncode == 0 else 'failed'
        report_path = output / 'render' / 'report.json'
        if process.returncode == 0:
            if not report_path.is_file():
                result.update(status='failed', error='Blender exited without a measurement report.')
            else:
                measured = json.loads(report_path.read_text(encoding='utf-8'))
                if not measured.get('ok'):
                    result.update(status='failed', error='Measurement report did not pass.')
    except subprocess.TimeoutExpired:
        result.update(status='timeout', error='This launched Blender process was killed at the time limit. Capacity is unproven.')
    except (OSError, ValueError) as error:
        result.update(status='failed', error=str(error))
    result['process_seconds'] = round(time.perf_counter() - started, 3)
    (output / 'run.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))
    return 0 if result['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
