from pathlib import Path
import numpy as np,json
from PIL import Image
ROOT=Path(__file__).resolve().parent
rng=np.random.default_rng(1107); n=67579
raw=np.array(Image.open(ROOT/'source/07_mask.png').convert('L'))
styled=np.array(Image.open(ROOT/'source/07_styled_mask.png').convert('L'))
edge=(styled>70);inside=(raw>200)&(styled<50)
coords=[];energy=[];part=[]
for which,num in [(edge,round(n*.95)),(inside,n-round(n*.95))]:
    yy,xx=np.where(which); weights=styled[yy,xx].astype(float);weights/=weights.sum()
    ids=rng.choice(len(xx),num,replace=True,p=weights)
    coords.append(np.column_stack((xx[ids]+rng.uniform(-.42,.42,num),yy[ids]+rng.uniform(-.42,.42,num))))
    is_edge=which is edge
    energy.extend(rng.uniform(.98,1.45,num) if is_edge else rng.uniform(.045,.08,num))
    part.extend([int(is_edge)]*num)
xy=np.concatenate(coords); energy=np.array(energy);part=np.array(part)
np.savez_compressed(ROOT/'source/title_targets.npz',pixels=xy,energy=energy,edge=part)
(ROOT/'qa/target-mask.json').write_text(json.dumps({'selected_direction':'07 璃光细线','text':'黄花鱼\nBLENDER','source_resolution':[3072,4096],'edge_particles':int(part.sum()),'interior_particles':int((part==0).sum()),'mask_bounds':Image.fromarray(raw).getbbox()},ensure_ascii=False,indent=2),encoding='utf-8')
print('OUTLINE_TARGETS_READY',n,flush=True)
