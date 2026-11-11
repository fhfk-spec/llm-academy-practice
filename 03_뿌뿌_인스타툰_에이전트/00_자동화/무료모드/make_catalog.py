"""스티커 목록 이미지 만들기: python3 make_catalog.py → 스티커_목록.jpg"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE = Path(__file__).resolve().parent
idx = json.loads((HERE / 'stickers' / 'stickers.json').read_text(encoding='utf-8'))
fb = ImageFont.truetype(str(HERE / 'fonts' / 'GmarketSansTTFBold.ttf'), 20)
fm = ImageFont.truetype(str(HERE / 'fonts' / 'GmarketSansTTFMedium.ttf'), 17)
C, S = 5, 300
ids = list(idx); R = (len(ids) + C - 1) // C
W = Image.new('RGB', (C * S, R * (S + 60)), (255, 245, 234)); d = ImageDraw.Draw(W)
for i, k in enumerate(ids):
    im = Image.open(HERE / 'stickers' / f'{k}.png'); im.thumbnail((S - 20, S - 20))
    x = (i % C) * S; y = (i // C) * (S + 60)
    W.paste(im, (x + (S - im.width) // 2, y + (S - im.height) // 2), im)
    d.text((x + 10, y + S + 2), k, font=fb, fill=(58, 46, 40))
    d.text((x + 10, y + S + 28), idx[k]['desc'][:18], font=fm, fill=(120, 100, 90))
W.save(HERE / '스티커_목록.jpg', quality=88)
print('스티커', len(ids), '개')
