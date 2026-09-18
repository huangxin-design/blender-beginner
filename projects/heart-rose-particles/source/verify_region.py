from pathlib import Path
import json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
with Image.open(ROOT/'stills/native_490.png') as im:a=np.asarray(im.convert('RGB')).astype(np.int16)
with Image.open(ROOT/'stills/bloom_0490.png') as im:b=np.asarray(im.convert('RGB')).astype(np.int16)
scores=[]
for dy in range(-1,2):
    for dx in range(-1,2):
        ref=a[1250:2700,550:2550];crop=b[1250+dy:2700+dy,550+dx:2550+dx]
        scores.append({'dx':dx,'dy':dy,'mean_absolute_difference':float(np.abs(ref-crop).mean())})
best=min(scores,key=lambda x:x['mean_absolute_difference'])
assert best['dx']==best['dy']==0,scores
delta=np.abs(a-b)
assert delta.mean()<.15
report={'native_pixel_grid_alignment':best,'full_frame_mean_absolute_difference':float(delta.mean()),'maximum_difference':int(delta.max()),'native_canvas':[3072,4096],'render_region_is_not_upscaled':True,'method':'Same native camera grid, active-particle bounds plus 100 pixel overscan; assemble on a native black frame','comparison_frame':490,'offset_checks':scores}
(ROOT/'qa/region-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('REGION_NATIVE_GRID_PASS',report,flush=True)
