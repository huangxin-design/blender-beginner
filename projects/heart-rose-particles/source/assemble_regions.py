from pathlib import Path
import json,sys,shutil
from PIL import Image
ROOT=Path(__file__).resolve().parent;mode=sys.argv[1] if len(sys.argv)>1 else 'full'
records=json.loads((ROOT/'qa'/f'regions-{mode}.json').read_text(encoding='utf-8'))
if mode=='full':
    assert {r['frame'] for r in records}==set(range(381,470))|set(range(510,586))
for item in records:
    with Image.open(ROOT/'stills/native_600.png') as im:base=im.copy()
    with Image.open(ROOT/'regions'/f'bloom_{item["frame"]:04d}.png') as im:
        # Blender may floor the floating-point border to the previous integer pixel.
        x=item['x'];y=4096-item['y_from_bottom']-im.height
        base.paste(im,(x,y))
    dest=ROOT/('stills' if mode=='test' else 'frames')/f'bloom_{item["frame"]:04d}.png';base.save(dest,compress_level=2)
if mode=='full':
    assert (ROOT/'qa/prefix-state.json').exists()
    for f in range(470,510):shutil.copy2(ROOT/'stills/native_490.png',ROOT/'frames'/f'bloom_{f:04d}.png')
    for f in range(586,601):shutil.copy2(ROOT/'stills/native_600.png',ROOT/'frames'/f'bloom_{f:04d}.png')
print('REGIONS_ASSEMBLED',mode,len(records),flush=True)
