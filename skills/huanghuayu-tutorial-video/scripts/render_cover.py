"""Render the approved cover style from a completed poster or a new artwork image.

Only Pillow and the local skill helpers are required. No network, Blender session,
font distribution or generation of a replacement artwork takes place.
"""
import argparse
import base64
import hashlib
import html
import io
import json
import math
from pathlib import Path
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

sys.dont_write_bytecode = True
from render_tutorial import font_paths, resolve
from image_backdrop import fit_with_backdrop

SKILL = Path(__file__).resolve().parents[1]
ASSETS = SKILL / 'assets' / 'cover'
SIZE = (1080, 1440)
ACCENT, INK, IVORY = '#E9FF24', '#07141D', '#F5F0DE'
FOOTER = (64, 1294, 1016, 1390)


def image_uri(image):
    data = io.BytesIO()
    image.save(data, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(data.getvalue()).decode('ascii')


def required_text(value, field):
    if not isinstance(value, str) or not value.strip() or '\n' in value or '\r' in value:
        raise ValueError(f'{field} must be a nonempty single line. Use title.lines for an explicit title break.')
    return value


def solve(matrix, values):
    """Solve the eight projective coefficients without adding a NumPy dependency."""
    rows = [list(a) + [b] for a, b in zip(matrix, values)]
    for col in range(len(values)):
        pivot = max(range(col, len(rows)), key=lambda r: abs(rows[r][col]))
        rows[col], rows[pivot] = rows[pivot], rows[col]
        divisor = rows[col][col]
        if abs(divisor) < 1e-10:
            raise ValueError('screen.quad is degenerate; use four distinct convex screen corners.')
        rows[col] = [n/divisor for n in rows[col]]
        for r in range(len(rows)):
            if r != col:
                multiplier = rows[r][col]
                rows[r] = [a-multiplier*b for a, b in zip(rows[r], rows[col])]
    return [r[-1] for r in rows]


def artwork_composite(base, artwork, screen, config_base, artwork_crop=None):
    quad = screen['quad']
    if len(quad) != 4 or any(len(p) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in p) for p in quad):
        raise ValueError('screen.quad needs [top-left, top-right, bottom-right, bottom-left] canvas coordinates.')
    if any(not (0 <= x <= SIZE[0] and 0 <= y <= SIZE[1]) for x, y in quad):
        raise ValueError('screen.quad is outside the 1080×1440 canvas.')
    turns = [(quad[(i+1)%4][0]-quad[i][0])*(quad[(i+2)%4][1]-quad[(i+1)%4][1])
             -(quad[(i+1)%4][1]-quad[i][1])*(quad[(i+2)%4][0]-quad[(i+1)%4][0]) for i in range(4)]
    if min(turns) <= 0:
        raise ValueError('screen.quad must be convex and ordered top-left, top-right, bottom-right, bottom-left.')
    plane_size = screen.get('plane_size', [round((math.dist(quad[0], quad[1])+math.dist(quad[3], quad[2]))/2),
                                           round((math.dist(quad[0], quad[3])+math.dist(quad[1], quad[2]))/2)])
    if len(plane_size) != 2 or any(not isinstance(v, int) or v < 32 or v > 4096 for v in plane_size):
        raise ValueError('screen.plane_size must contain two integers between 32 and 4096.')
    source = ImageOps.exif_transpose(Image.open(artwork)).convert('RGBA')
    flattened = Image.new('RGBA', source.size, INK)
    flattened.alpha_composite(source)
    crop = artwork_crop if artwork_crop is not None else [0, 0, source.width, source.height]
    if (not isinstance(crop, list) or len(crop) != 4
            or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in crop)
            or not (0 <= crop[0] < crop[2] <= source.width and 0 <= crop[1] < crop[3] <= source.height)):
        raise ValueError('artwork_crop must be [left, top, right, bottom] in source pixels, inside the oriented source image.')
    fit = screen.get('fit', 'cover')
    centering = screen.get('centering', [0.5, 0.5])
    if (not isinstance(centering, list) or len(centering) != 2
            or any(not isinstance(v, (int, float)) or not 0 <= v <= 1 for v in centering)):
        raise ValueError('screen.centering needs two values between zero and one.')
    # Cover uses one uniform scale. The selected core may exclude empty space or a long stem.
    effective_crop = list(crop)
    if fit == 'cover':
        width, height = crop[2]-crop[0], crop[3]-crop[1]
        ratio = plane_size[0]/plane_size[1]
        cw, ch = min(width, height*ratio), min(height, width/ratio)
        left, top = crop[0]+(width-cw)*centering[0], crop[1]+(height-ch)*centering[1]
        effective_crop = [left, top, left+cw, top+ch]
        fitted = flattened.resize(tuple(plane_size), Image.Resampling.LANCZOS, box=effective_crop)
    elif fit == 'contain':
        fitted = fit_with_backdrop(flattened.crop(crop).convert('RGB'), tuple(plane_size)).convert('RGBA')
    else:
        raise ValueError('screen.fit must be cover or contain; cover fills the screen without blurred side padding.')
    pw, ph = plane_size
    matrix, values = [], []
    for (u, v), (x, y) in zip(quad, [(0, 0), (pw, 0), (pw, ph), (0, ph)]):
        matrix.extend([[u, v, 1, 0, 0, 0, -x*u, -x*v], [0, 0, 0, u, v, 1, -y*u, -y*v]])
        values.extend([x, y])
    coefficients = solve(matrix, values)
    mask = Image.new('L', (pw, ph), 0)
    radius = screen.get('corner_radius', 0.05)
    if not isinstance(radius, (int, float)) or not 0 <= radius <= 0.25:
        raise ValueError('screen.corner_radius must be between 0 and 0.25 of the shorter plane dimension.')
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, pw-1, ph-1), radius=round(min(pw, ph)*radius), fill=255)
    warped = fitted.transform(SIZE, Image.Transform.PERSPECTIVE, coefficients, Image.Resampling.BICUBIC)
    alpha = mask.transform(SIZE, Image.Transform.PERSPECTIVE, coefficients, Image.Resampling.BICUBIC)
    if screen.get('mask'):
        custom_mask = Image.open(resolve(config_base, screen['mask'])).convert('L')
        if custom_mask.size != SIZE:
            raise ValueError('screen.mask must be a 1080×1440 grayscale mask; white reveals the artwork.')
        alpha = ImageChops.multiply(alpha, custom_mask)
    result = base.copy()
    result.paste(warped, (0, 0), alpha)
    return result, {'quad': quad, 'plane_size': plane_size, 'corner_radius': radius,
                    'fit': fit, 'centering': centering, 'artwork_source_size': list(source.size),
                    'artwork_crop': list(crop), 'effective_crop': effective_crop,
                    'mask_name': Path(screen['mask']).name if screen.get('mask') else None}


def prepare_background(c, config_base):
    mode = c.get('mode')
    if mode not in ['background', 'artwork']:
        raise ValueError('mode must be background (a completed poster) or artwork (a 2D CRT composite).')
    if mode == 'background' and not c.get('background'):
        raise ValueError('background mode requires the current case’s completed background image.')
    if mode == 'background' and c.get('artwork'):
        raise ValueError('background mode does not replace screen content. Use artwork mode to place artwork into a blank CRT.')
    if mode == 'background' and c.get('artwork_crop') is not None:
        raise ValueError('artwork_crop requires artwork mode; background mode preserves the completed poster.')
    default_screen = mode == 'artwork' and not c.get('background')
    path = ASSETS/'crt_blank.png' if default_screen else resolve(config_base, c['background'])
    source = ImageOps.exif_transpose(Image.open(path)).convert('RGBA')
    if abs(source.width/source.height - 0.75) > 0.002:
        raise ValueError('The poster background must be 3:4. Prepare the composition explicitly; this renderer will not crop it.')
    base = source.resize(SIZE, Image.Resampling.LANCZOS)
    provenance = {'mode': mode, 'background_name': path.name, 'background_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'background_source_size': list(source.size), 'source_note': c.get('source_note', ''),
                  'representation': 'User-provided completed poster, with native typography overlaid; source rendering provenance is not inferred.'}
    if mode == 'artwork':
        if not c.get('artwork'):
            raise ValueError('artwork mode requires artwork: the current case’s image. No example flower is substituted.')
        artwork = resolve(config_base, c['artwork'])
        if default_screen:
            screen = json.loads((ASSETS/'screen.json').read_text(encoding='utf-8'))
            # Bundled geometry/mask remain available when a case changes only its crop centering.
            if screen.get('mask'):
                screen['mask'] = str(ASSETS/screen['mask'])
            overrides = c.get('screen', {})
            if not isinstance(overrides, dict):
                raise ValueError('screen must be an object of mapping or fit settings.')
            screen.update(overrides)
        else:
            if not isinstance(c.get('screen'), dict) or 'quad' not in c['screen']:
                raise ValueError('A custom blank CRT background requires screen.quad coordinates; the default geometry cannot be assumed.')
            screen = c['screen']
        base, placement = artwork_composite(base, artwork, screen, config_base, c.get('artwork_crop'))
        provenance.update({'artwork_name': artwork.name, 'artwork_sha256': hashlib.sha256(artwork.read_bytes()).hexdigest(),
                           'representation': '2D image composite: supplied artwork fitted and projected into a CRT screen. This is not a native Blender scene render.',
                           'screen': placement})
    return base, provenance


class Cover:
    def __init__(self, config, config_base):
        self.paths = font_paths(config, config_base)
        self.layer = Image.new('RGBA', SIZE)
        self.draw = ImageDraw.Draw(self.layer)
        self.svg, self.positions = [], []

    def measure(self, value, size, tracking, role):
        f = ImageFont.truetype(str(self.paths[role]), size)
        missing = bytes(f.getmask('\U0010ffff'))
        for char in set(value)-set(' \t'):
            if bytes(f.getmask(char)) == missing:
                raise ValueError(f'The selected {role} font lacks {char!r}; configure a suitable installed font.')
        width = math.ceil(sum(f.getlength(ch) for ch in value)+max(0,len(value)-1)*tracking+32)
        ascent, descent = f.getmetrics()
        mask = Image.new('L', (width, ascent+descent+32))
        d = ImageDraw.Draw(mask)
        x, baseline, xs = 16.0, ascent+16, []
        for ch in value:
            xs.append(x)
            d.text((x,baseline),ch,font=f,fill=255,anchor='ls')
            x += f.getlength(ch)+tracking
        bounds = mask.getbbox()
        if bounds is None:
            raise ValueError('The text contains no visible glyphs.')
        return f, bounds, xs, baseline

    def rect(self, box, colour):
        x1,y1,x2,y2 = box
        if not (0 <= x1 < x2 <= SIZE[0] and 0 <= y1 < y2 <= SIZE[1]):
            raise ValueError(f'A text carrier exceeds the canvas: {box}')
        self.draw.rectangle((x1,y1,x2-1,y2-1),fill=colour)
        self.svg.append(f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{y2-y1}" fill="{colour}"/>')

    def text(self, value, box, size, tracking, colour, role='title', align='left'):
        required_text(value, 'text')
        f,b,xs,baseline = self.measure(value,size,tracking,role)
        w,h = b[2]-b[0],b[3]-b[1]
        x1,y1,x2,y2 = box
        if w > x2-x1 or h > y2-y1:
            raise ValueError(f'Text {value!r} is {w}×{h}px, exceeding {x2-x1:g}×{y2-y1:g}px. '
                             'Shorten the copy or explicitly adjust title.lines/title.size; glyphs are never squeezed or discarded.')
        px = x1 if align=='left' else x2-w if align=='right' else x1+(x2-x1-w)/2
        py = y1+(y2-y1-h)/2
        xs,baseline = [x+px-b[0] for x in xs],baseline+py-b[1]
        for ch,x in zip(value,xs):
            self.draw.text((x,baseline),ch,font=f,fill=colour,anchor='ls')
        family,style = f.getname()
        weight = 600 if 'semi' in style.lower() else 700 if 'bold' in style.lower() else 400
        self.svg.append(f'<text x="{" ".join(f"{x:.3f}" for x in xs)}" y="{baseline:.3f}" '
                        f'font-family="{html.escape(family,quote=True)}" font-size="{size}" font-weight="{weight}" '
                        f'fill="{colour}" xml:space="preserve">{html.escape(value)}</text>')
        self.positions.append({'text':value,'pixel_bbox':[px,py,px+w,py+h], 'size':size,'tracking':tracking,'font_role':role})
        return w


def typography(c):
    title = c['title']
    if not isinstance(title,dict):
        raise ValueError('title must be an object with explicit title.lines.')
    lines = title.get('lines')
    if not isinstance(lines,list) or not 1 <= len(lines) <= 2:
        raise ValueError('title.lines must contain one or two explicit {plain, highlight} objects.')
    size = title.get('size',122 if len(lines)==1 else 80)
    tracking = title.get('tracking',9 if len(lines)==1 else 4)
    limits = (80,122) if len(lines)==1 else (68,84)
    if not isinstance(size,int) or not limits[0] <= size <= limits[1]:
        raise ValueError(f'{len(lines)}-line title.size must be an integer from {limits[0]} to {limits[1]}.')
    if not isinstance(tracking,(int,float)) or not 0 <= tracking <= 12:
        raise ValueError('title.tracking must be between 0 and 12px.')
    for line in lines:
        if not isinstance(line,dict):
            raise ValueError('Each title line needs a plain and/or highlight string.')
        for key in ['plain','highlight']:
            if line.get(key): required_text(line[key], f'title.{key}')
        if not line.get('plain') and not line.get('highlight'):
            raise ValueError('A title line cannot be empty.')
    return lines,size,tracking


def render(config_path, output):
    config_path,output = Path(config_path).resolve(),Path(output).resolve()
    if output==SKILL or SKILL in output.parents:
        raise ValueError('Write outputs to the current case directory, outside the installed skill and its examples.')
    c=json.loads(config_path.read_text(encoding='utf-8'))
    lines,size,tracking=typography(c)
    topics=c.get('topics')
    if not isinstance(topics,list) or len(topics)!=3:
        raise ValueError('topics must contain exactly three short learning points.')
    for i,t in enumerate(topics): required_text(t,f'topics[{i}]')
    for key in ['channel','series','tools','subtitle']: required_text(c.get(key),key)
    base,provenance=prepare_background(c,config_path.parent)
    design=Cover(c,config_path.parent)
    design.text(c['channel'],[64,42,780,78],31,2,IVORY,'bold')
    design.rect([64,86,184,89],ACCENT)
    design.rect([190,86,208,89],IVORY)
    for x in [215,226]:
        points=[(x,82),(x+4,82),(x-1,90),(x-5,90)]
        design.draw.polygon(points,fill=ACCENT)
        design.svg.append(f'<polygon points="{" ".join(f"{px},{py}" for px,py in points)}" fill="{ACCENT}"/>')
    design.text(c['series'],[940,42,1016,78],38,0,ACCENT,'mono','right')
    title_boxes = [(100,238,1016)] if len(lines)==1 else [(100,192,1016),(202,294,780)]
    for line,(y1,y2,right) in zip(lines,title_boxes):
        x=64
        if line.get('plain'):
            x += design.text(line['plain'],[x,y1,right,y2],size,tracking,IVORY)
        if line.get('highlight'):
            if line.get('plain'): x += 16
            _,bounds,_,_=design.measure(line['highlight'],size,tracking,'title')
            width=bounds[2]-bounds[0]+48
            if x+width>right:
                raise ValueError(f'Title line with highlight exceeds x={right}px. Use an explicit second line or a smaller allowed title.size.')
            design.rect([x,y1,x+width,y2],ACCENT)
            design.text(line['highlight'],[x,y1,x+width,y2],size,tracking,INK,align='center')
    tool_y=(254,324) if len(lines)==1 else (310,380)
    subtitle_y=(338,374) if len(lines)==1 else (394,430)
    _,bounds,_,_=design.measure(c['tools'],49,0,'bold')
    tool_width=bounds[2]-bounds[0]+48
    if tool_width>716: raise ValueError('tools exceeds its 716px carrier; use a shorter tool name.')
    design.rect([64,tool_y[0],64+tool_width,tool_y[1]],ACCENT)
    design.text(c['tools'],[64,tool_y[0],64+tool_width,tool_y[1]],49,0,INK,'bold','center')
    design.text(c['subtitle'],[64,subtitle_y[0],780,subtitle_y[1]],35,1,IVORY,'regular')
    texture=Image.open(ASSETS/'footer_halftone.png').convert('RGBA')
    if texture.size!=(952,96): raise ValueError('The approved footer texture must be 952×96.')
    design.layer.alpha_composite(texture,(64,1294))
    design.svg.append(f'<image x="64" y="1294" width="952" height="96" href="{image_uri(texture)}"/>')
    cw=952/3
    for i,t in enumerate(topics):
        design.text(t,[64+i*cw,1294,64+(i+1)*cw,1390],46,2,INK,'bold','center')
    for i in [1,2]:
        x=64+i*cw
        design.draw.line((x,1323,x,1361),fill=INK,width=2)
        design.svg.append(f'<line x1="{x}" x2="{x}" y1="1323" y2="1361" stroke="{INK}" stroke-width="2"/>')
    protected={'main_artwork':(320,480,920,1030),'small_tv':(800,240,1050,470)}
    for name,box in protected.items():
        if design.layer.getchannel('A').crop(box).getbbox():
            raise ValueError(f'Typography overlaps the protected {name} region.')
    final=Image.alpha_composite(base,design.layer).convert('RGB')
    output.mkdir(parents=True,exist_ok=True)
    final.save(output/'cover.png',optimize=True)
    final.resize((360,480),Image.Resampling.LANCZOS).save(output/'thumbnail.png',optimize=True)
    design.layer.save(output/'text_layer.png',optimize=True)
    base.convert('RGB').save(output/'background_composite.png',optimize=True)
    if c['mode'] == 'artwork':
        quad = provenance['screen']['quad']
        detail_box = [max(0, math.floor(min(p[0] for p in quad))-20), max(0, math.floor(min(p[1] for p in quad))-20),
                      min(SIZE[0], math.ceil(max(p[0] for p in quad))+20), min(SIZE[1], math.ceil(max(p[1] for p in quad))+20)]
        base.crop(detail_box).convert('RGB').save(output/'screen_detail.png',optimize=True)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1440" viewBox="0 0 1080 1440">',
         f'<title>{html.escape(c["channel"])} cover</title>',f'<image width="1080" height="1440" href="{image_uri(base)}"/>',*design.svg,'</svg>']
    (output/'editable.svg').write_text('\n'.join(svg),encoding='utf-8')
    report={'size':list(SIZE),'provenance':provenance,'positions':design.positions,
            'font_files':{k:p.name for k,p in design.paths.items()},'fonts_redistributed':False,
            'glyphs_scaled':False,'protected_typography_regions_clear':True,'title_lines':len(lines),
            'settings':c,'settings_path_note':'Relative paths in settings resolve from the original input config directory.'}
    (output/'render_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'status':'ready','mode':c['mode'],'cover':str(output/'cover.png'),'representation':provenance['representation']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    try:
        print(json.dumps(render(args.config,args.output),ensure_ascii=False))
    except (ValueError,KeyError,OSError) as error:
        parser.exit(2,f'Cover render failed: {error}\n')
