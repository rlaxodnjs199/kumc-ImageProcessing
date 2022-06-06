from typing import Tuple
from PIL import Image, ImageChops


def is_in_color_range(px: Tuple[int, int, int], minimal_color:int) -> bool:
    return px[0] >= minimal_color and px[1] >= minimal_color and px[2] >= minimal_color


def is_line_color_range(im: Image, y: int, minimal_color: int) -> bool:
    width, _ = im.size

    for x in range(0, width-1):
        px = im.getpixel((x, y))
        if not is_in_color_range(px, minimal_color):
            return False
    return True

def get_crop_box_by_px_color(
    im: Image, 
    px: Tuple[int, int], 
    scale: float, 
    offset: int) -> Tuple[int, int, int, int]:

    bg = Image.new(im.mode, im.size, px)
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, scale, offset)

    return diff.getbbox()

def crop_by_background(
    im: Image, 
    minimal_light_background_color_value: int, padding: int, offset: int) -> Tuple[int, int, int, int]:
    width, height = im.size
    original_box = (0, 0, width, height)

    # crop by top left pixel color
    px = im.getpixel((0,height-1))
    if is_in_color_range(px, minimal_light_background_color_value):
        bbox1 = get_crop_box_by_px_color(im, px, 2.0, offset)
    else: 
        bbox1 = original_box

    # crop by bottom right pixel color
    px = im.getpixel((width-1,height-1))
    if is_in_color_range(px, minimal_light_background_color_value):
        bbox2 = get_crop_box_by_px_color(im, px, 2.0, offset)
    else:
        bbox2 = original_box

    crop = (
        max(bbox1[0], bbox2[0]) - padding,
        max(bbox1[1], bbox2[1]) - padding,
        min(bbox1[2], bbox2[2]) + padding,
        min(bbox1[3], bbox2[3]) + padding
    )

    return crop

if __name__ == '__main__':
    path = 'Data/DN34020_IN0_EX0_postIR_whole1D_HAA700in_VesselTV0_max0.08min0.05_v0f_bottom_noLegendsAxis.png'
    img_path_without_extension, img_extension = path.rsplit('.', 1)
    img = Image.open(path)
    crop_bbox = crop_by_background(img, 200, 10, -50)
    img = img.crop(crop_bbox)
    img.save(img_path_without_extension + '_new.' + img_extension)