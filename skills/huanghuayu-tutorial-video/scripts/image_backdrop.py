"""Keep a sharp fitted image over a soft backdrop made from the same image."""
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


def fit_with_backdrop(source, size):
    source = source.convert('RGB')
    foreground = ImageOps.contain(source, size, Image.Resampling.LANCZOS)
    if foreground.size == size:
        return foreground
    background = ImageOps.fit(source, size, Image.Resampling.LANCZOS)
    background = background.filter(ImageFilter.GaussianBlur(min(size) * .085))
    # Align the palette with the fitted foreground, extending its end colors into padding.
    fw, fh = foreground.size
    column = source.resize((1, fh), Image.Resampling.BOX)
    color_wash = Image.new('RGB', (1, size[1]))
    offset_y = (size[1]-fh)//2
    if offset_y:
        color_wash.paste(column.getpixel((0, 0)), (0, 0, 1, offset_y))
    color_wash.paste(column, (0, offset_y))
    if offset_y+fh < size[1]:
        color_wash.paste(column.getpixel((0, fh-1)), (0, offset_y+fh, 1, size[1]))
    color_wash = color_wash.resize(size)
    color_wash = color_wash.filter(ImageFilter.GaussianBlur(min(size) * .05))
    background = Image.blend(background, color_wash, .92 if offset_y else .72)
    background = ImageEnhance.Color(background).enhance(.98)
    mask = Image.new('L', foreground.size, 0)
    feather = max(4, round(min(size) * .018))
    inset_x = feather if fw < size[0] else 0
    inset_y = feather if fh < size[1] else 0
    ImageDraw.Draw(mask).rectangle((inset_x, inset_y, fw-inset_x, fh-inset_y), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(feather*.7))
    background.paste(foreground, ((size[0]-fw)//2, (size[1]-fh)//2), mask)
    return background
