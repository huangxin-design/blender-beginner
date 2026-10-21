# Publication adaptation: relative scene name and configurable installation paths.
"""Resume native 4K frames, denoise within a memory budget, and encode."""
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time
import ctypes
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'scripts'
BLENDER=Path(os.environ.get('BLENDER_BINARY') or shutil.which('blender') or 'blender').resolve()
os.environ.setdefault('OIDN_LIBRARY_DIR', str(BLENDER.parent/'blender.shared'))
BLENDER_PYTHON=BLENDER.parent/'5.2'/'python'/'bin'/'python.exe'
BLEND=ROOT/'scene.blend'
CACHE=ROOT/'renders'/'cache'
for variable,folder in (('OPTIX_CACHE_PATH','optix'),('CUDA_CACHE_PATH','cuda')):
    directory=CACHE/folder
    directory.mkdir(parents=True,exist_ok=True)
    os.environ[variable]=str(directory)
LOGS=ROOT/'logs';LOGS.mkdir(exist_ok=True)
FRAMES=CACHE/'frames';FRAMES.mkdir(parents=True,exist_ok=True)
STILLS=ROOT/'renders'/'stills';STILLS.mkdir(parents=True,exist_ok=True)
FLAGS=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
START=time.monotonic()
HERO=(1,73,180)

class MemoryStatus(ctypes.Structure):
    _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[
        (name,ctypes.c_ulonglong) for name in
        ('physical','available_physical','pagefile','available_commit','virtual','available_virtual','extended')]

def wait_memory(frame):
    if os.name!='nt':return
    while True:
        memory=MemoryStatus();memory.length=ctypes.sizeof(memory)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
            raise OSError('Could not read Windows memory availability')
        if memory.available_commit>=6*1024**3 and memory.available_physical>=4*1024**3:
            return
        status('waiting_memory',frame)
        time.sleep(30)

def valid_frame(frame):
    path=FRAMES/f'{frame:04d}.png'
    if not path.exists() or path.stat().st_size<1000:return False
    with path.open('rb') as f:
        head=f.read(25);f.seek(-8,2);tail=f.read()
    return head[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',head[16:24])==(3072,4096) and head[24]==16 and tail==b'IEND\xaeB`\x82'

def status(state,frame=None,error=None):
    completed=[f for f in range(1,361) if valid_frame(f)]
    data={'state':state,'pid':os.getpid(),'completed_frames':len(completed),'total_frames':360,
          'active_frame':frame,'elapsed_seconds':round(time.monotonic()-START,1),
          'cache':str(FRAMES),'native_size':[3072,4096],'fps':24,'duration':15,
          'error':error,'updated_unix':time.time()}
    temp=ROOT/'pipeline_status.partial.json'
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(ROOT/'pipeline_status.json')
    print(json.dumps(data,ensure_ascii=False),flush=True)

def blender(script,frame,raw=False):
    wait_memory(frame)
    status('rendering',frame)
    logfile=LOGS/f'{frame:04d}_{"raw" if raw else "post"}.log'
    command=[str(BLENDER),'--background','--factory-startup']
    if raw:command.append(str(BLEND))
    command+=['--threads','8' if raw else '4','--python-exit-code','1','--python',str(SCRIPTS/script),'--']
    command+=['raw',str(frame)] if raw else [str(frame)]
    with logfile.open('w',encoding='utf-8') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,creationflags=FLAGS)
    text=logfile.read_text(encoding='utf-8',errors='replace')
    if result.returncode or re.search(r'\| ERROR|Traceback|Malloc returns null|Calloc returns null',text):
        raise RuntimeError(f'{script} frame {frame}: see {logfile}')

def valid_raw(frame):
    path=CACHE/'raw'/f'{frame:04d}.exr'
    if not path.is_file() or path.stat().st_size<1000:return False
    # Only retained raw frames need this independent check before reuse.
    wait_memory(frame)
    status('checking_raw',frame)
    logfile=LOGS/f'{frame:04d}_raw_check.log'
    with logfile.open('w',encoding='utf-8') as log:
        result=subprocess.run([str(BLENDER_PYTHON),str(SCRIPTS/'post_frame.py'),
                               '--check-exr',str(frame)],stdout=log,
                              stderr=subprocess.STDOUT,creationflags=FLAGS)
    return result.returncode==0

def post(frame):
    blender('post_frame.py',frame)
    if not valid_frame(frame):raise RuntimeError(f'Invalid postprocessed frame {frame}')
    if frame in HERO:shutil.copy2(FRAMES/f'{frame:04d}.png',STILLS/f'{frame:04d}.png')
    # These are this job's two per-frame intermediate files, not source assets.
    raw_root=(CACHE/'raw').resolve()
    for name in (f'{frame:04d}.exr',f'{frame:04d}_denoised.exr'):
        path=(raw_root/name).resolve()
        assert path.parent==raw_root
        if path.exists():path.unlink()

def main():
    status('rendering')
    sequence=list(HERO)+[f for f in range(1,361) if f not in HERO]
    # Native 4K guide buffers and CPU denoising must not overlap while other
    # projects render on this workstation; the parallel version exhausted RAM.
    for frame in sequence:
        if valid_frame(frame):
            if frame in HERO:shutil.copy2(FRAMES/f'{frame:04d}.png',STILLS/f'{frame:04d}.png')
            continue
        status('rendering',frame)
        if not valid_raw(frame):blender('render_4k.py',frame,True)
        post(frame)
    if not all(valid_frame(f) for f in range(1,361)):raise RuntimeError('Frame sequence is incomplete')
    status('encoding')
    with (LOGS/'encode.log').open('w',encoding='utf-8') as log:
        subprocess.run([sys.executable,str(SCRIPTS/'encode_video.py')],stdout=log,stderr=subprocess.STDOUT,creationflags=FLAGS,check=True)
    status('complete')

if __name__=='__main__':
    try:main()
    except Exception as e:
        status('failed',error=str(e))
        raise
