"""뿌뿌 인스타툰 글자 얹기 도구 모음: box(말풍선/내레이션), outlined(테두리 글자), load, save. 1080x1350 기준."""
from PIL import Image, ImageDraw, ImageFont
import glob, os

import pathlib
HERE = pathlib.Path(__file__).resolve().parent
FB = str(HERE / 'fonts' / 'GmarketSansTTFBold.ttf')
FM = str(HERE / 'fonts' / 'GmarketSansTTFMedium.ttf')
INK = (58, 46, 40)
PINK = (254, 214, 206)
W, H = 1080, 1350


def font(p, s):
    return ImageFont.truetype(p, s)


def text_size(d, txt, f):
    b = d.textbbox((0, 0), txt, font=f)
    return b[2] - b[0], b[3] - b[1]


def box(d, x, y, lines, f, pad=(30, 22), radius=36, fill='white', stroke=INK, sw=5,
        align='left', tail=None, gap=12, colors=None):
    """lines: list of str. returns bbox"""
    ws = [text_size(d, t, f)[0] for t in lines]
    lh = text_size(d, '가', f)[1]
    w = max(ws) + pad[0] * 2
    h = lh * len(lines) + gap * (len(lines) - 1) + pad[1] * 2
    if tail:  # tail: (tx, ty) point the tail aims at
        tx, ty = tail
        cx = x + w / 2
        base = [(cx - 26, y + h - 4), (cx + 26, y + h - 4)] if ty > y + h else [(cx - 26, y + 4), (cx + 26, y + 4)]
        d.polygon(base + [(tx, ty)], fill=fill, outline=stroke)
        d.line(base[0:1] + [(tx, ty)] + base[1:2], fill=stroke, width=sw, joint='curve')
    d.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=stroke, width=sw)
    if tail:
        # cover the inner line where tail meets box
        d.line(base, fill=fill, width=sw + 2)
    cy = y + pad[1]
    for i, t in enumerate(lines):
        tw = ws[i]
        tx0 = x + pad[0] if align == 'left' else x + (w - tw) / 2
        d.text((tx0, cy - 4), t, font=f, fill=(colors[i] if colors else INK))
        cy += lh + gap
    return (x, y, x + w, y + h)


def outlined(d, xy, t, f, fill=INK, stroke='white', sw=8, anchor='la'):
    d.text(xy, t, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke, anchor=anchor)


def load(path):
    return Image.open(path).convert('RGB').resize((W, H), Image.LANCZOS)


def save(img, out_dir, name):
    os.makedirs(out_dir, exist_ok=True)
    img.convert('RGB').save(f'{out_dir}/{name}.jpg', quality=92)


