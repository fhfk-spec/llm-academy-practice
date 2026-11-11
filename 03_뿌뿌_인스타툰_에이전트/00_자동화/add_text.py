from PIL import Image, ImageDraw, ImageFont
import glob, os

SRC = sorted(glob.glob('/mnt/user-data/uploads/Downloads/ppuppu_ep1_*.png'))
OUT = '/home/claude/ep1/out'
os.makedirs(OUT, exist_ok=True)
FB = '/home/claude/ep1/fontzip/GmarketSansTTFBold.ttf'
FM = '/home/claude/ep1/fontzip/GmarketSansTTFMedium.ttf'
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


def load(i):
    return Image.open(SRC[i]).convert('RGB').resize((W, H), Image.LANCZOS)


def save(img, name):
    img.save(f'{OUT}/{name}.png')
    img.convert('RGB').save(f'{OUT}/{name}.jpg', quality=92)


# ---------- 00 표지 ----------
im = load(0); d = ImageDraw.Draw(im)
f = font(FB, 30)
pw, ph = text_size(d, 'EP.01', f)
d.rounded_rectangle((70, 66, 70 + pw + 44, 66 + ph + 26), radius=40, fill=INK)
d.text((92, 76), 'EP.01', font=f, fill=(253, 243, 233))
d.text((70 + pw + 64, 74), '뿌뿌의 취준 재도전기', font=font(FM, 32), fill=INK)
f2 = font(FB, 56)
d.text((70, 160), '6개월째 면접 탈락 중인', font=f2, fill=INK)
d.text((70, 236), '취준생에게 걸려 온', font=f2, fill=INK)
f3 = font(FB, 128)
tw, th = text_size(d, '전화 한 통', f3)
d.rounded_rectangle((60, 420, 60 + tw + 30, 470), radius=26, fill=PINK)
d.text((72, 322), '전화 한 통', font=f3, fill=INK)
fs = font(FM, 34)
outlined(d, (W - 60, 84), '넘겨서 보기 →', fs, sw=6, anchor='ra')
save(im, '00_표지')

# ---------- 01 ----------
im = load(1); d = ImageDraw.Draw(im)
box(d, 60, 56, ['면접 탈락, 6개월째.'], font(FB, 48), radius=14)
fm = font(FB, 40)
for k, (t, xy) in enumerate([('안타깝게도…', (60, 180)), ('아쉽게도…', (120, 245)), ('귀하의 역량은 충분하나…', (60, 310))]):
    outlined(d, xy, t, fm, fill=(98, 86, 78), sw=7)
save(im, '01_탈락메일')

# ---------- 02 ----------
im = load(2); d = ImageDraw.Draw(im)
box(d, 260, 50, ['…통장 잔고는', '기다려주지 않았다.'], font(FB, 46), radius=14)
save(im, '02_이불')

# ---------- 03 ----------
im = load(3); d = ImageDraw.Draw(im)
box(d, 60, 50, ['그래서 일단, 단기 행사팀장.'], font(FB, 46), radius=14)
box(d, 560, 220, ['이 박스는', 'B존으로요!'], font(FB, 48), tail=(760, 470))
save(im, '03_행사팀장')

# ---------- 04 ----------
im = load(4); d = ImageDraw.Draw(im)
box(d, 50, 60, ['네, 뿌뿌입니다…'], font(FB, 46), tail=(330, 330))
box(d, 470, 200, ['…네?', '추가 합격이요?'], font(FB, 52), tail=(650, 430))
save(im, '04_전화')

# ---------- 05 ----------
im = load(5); d = ImageDraw.Draw(im)
box(d, 40, 70, ['…방금', '뭐였지?'], font(FB, 46), tail=(240, 330))
box(d, 590, 50, ['[메일] 추가 합격을', '축하드립니다', '…진짜네?!'], font(FB, 40), tail=(800, 380),
    colors=[(130, 118, 110), (130, 118, 110), INK])
save(im, '05_재확인')

# ---------- 06 ----------
im = load(6); d = ImageDraw.Draw(im)
box(d, 60, 50, ['실장님… 제가 지원했던 곳에', '추가 합격이 돼서요.', '내일부터는 못 나올 것 같습니다…!'], font(FB, 44), tail=(560, 430))
save(im, '06_실장님통화')

# ---------- 07 ----------
im = load(7); d = ImageDraw.Draw(im)
outlined(d, (W // 2, 70), '이제 잘될 일만 남았다!!!', font(FB, 72), sw=10, anchor='ma')
outlined(d, (W // 2, 180), '하늘이시여 감사합니다—!!', font(FB, 58), fill=(196, 84, 70), sw=10, anchor='ma')
save(im, '07_만세')

# ---------- 08 ----------
im = load(8); d = ImageDraw.Draw(im)
box(d, 20, 640, ['물류 들어오면', '여기부터', '확인하시고요…'], font(FB, 40), tail=(380, 930))
box(d, 660, 430, ['(속마음) 꺄아아', '나 내일부터 부트캠프생!!'], font(FB, 32), fill=PINK, radius=24)
save(im, '08_인수인계')
print('done')
