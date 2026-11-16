"""굿즈용 뿌뿌 도안 모음판 + 투명 PNG 묶음"""
import json, zipfile
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
H = Path(__file__).resolve().parent; ST = H / 'stickers'; OUT = H / 'out' / 'goods'; VF = H / 'vendor' / 'fonts'
desc = json.load(open(ST / 'stickers.json'))
D = lambda k: (desc.get(k, {}).get('desc') if isinstance(desc.get(k), dict) else desc.get(k)) or k
GROUPS = [
 ('★ 굿즈 추천 대표 도안', ['wave_smile', 'bust_wave_hehe', 'face_hehe', 'face_fighting', 'pose_sulky_sit', 'cheer', 'jump_joy', 'thumbs_up', 'peek_side', 'hold_sign', 'face_sparkle_eyes', 'face_smug']),
 ('컬러 버전 (투표 후보)', ['wave_v1_yellow_navy', 'wave_v2_coral_sky', 'wave_v3_lavender_yellow']),
]
used = {k for _, ks in GROUPS for k in ks}
faces = [k for k in desc if k.startswith('face_') and k not in used]
rest = [k for k in desc if k not in used and k not in faces and k != 'ep2_cover']
GROUPS += [('표정', faces), ('일상 포즈·상황', rest)]
CN = {'wave_v1_yellow_navy': '1번 옐로&네이비', 'wave_v2_coral_sky': '2번 코랄&스카이블루', 'wave_v3_lavender_yellow': '3번 라벤더&옐로'}
def cm(k):
    w, h = Image.open(ST / f'{k}.png').size
    return w, h, round(max(w, h) / 300 * 2.54, 1)
sec = ''
n = 0
for title, ks in GROUPS:
    cells = ''
    for k in ks:
        n += 1
        w, h, c = cm(k)
        badge = '<i class="ok">인쇄 OK</i>' if c >= 6 else '<i class="sm">작은 굿즈용</i>'
        cells += (f'<div class="c"><div class="no">{n:02d}</div><img src="{(ST / (k + ".png")).as_uri()}">'
                  f'<b>{CN.get(k, D(k))}</b><em>{k}.png · {w}×{h}px · 최대 약 {c}cm</em>{badge}</div>')
    sec += f'<h2>{title} <small>{len(ks)}종</small></h2><div class="g">{cells}</div>'
html = f'''<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="{(VF / 'jua/index.css').as_uri()}">
<style>@font-face{{font-family:P;font-weight:700;src:url('{(VF / 'pretendard/Pretendard-Bold.woff2').as_uri()}')}}
@font-face{{font-family:P;font-weight:500;src:url('{(VF / 'pretendard/Pretendard-Medium.woff2').as_uri()}')}}
*{{margin:0;box-sizing:border-box}}body{{width:1600px;background:#fff;font-family:P;color:#2E2A28;padding:50px 56px}}
h1{{font-family:Jua;font-weight:400;font-size:64px}}.sub{{font-size:22px;color:#8a7a74;margin:6px 0 10px;font-weight:500}}
h2{{font-family:Jua;font-weight:400;font-size:36px;margin:34px 0 14px;display:flex;align-items:center;gap:12px}}
h2:before{{content:'';width:12px;height:32px;border-radius:6px;background:#D9765F}}small{{font-size:22px;color:#aaa}}
.g{{display:grid;grid-template-columns:repeat(6,1fr);gap:14px}}
.c{{position:relative;border-radius:22px;padding:12px 10px 12px;text-align:center;
background:repeating-conic-gradient(#F4F4F4 0 25%,#fff 0 50%) 0 0/22px 22px;border:2px solid #EEE}}
.c img{{width:100%;height:190px;object-fit:contain}}.c b{{display:block;font-size:17px;margin-top:6px;line-height:1.3;min-height:44px}}
.c em{{display:block;font-style:normal;font-size:12.5px;color:#999;margin:3px 0 6px;font-weight:500}}
.c i{{font-style:normal;font-size:13px;border-radius:99px;padding:2px 10px;font-weight:700}}
.ok{{background:#DDEEFC;color:#3F86C9}}.sm{{background:#FFE4DA;color:#D9765F}}
.no{{position:absolute;left:12px;top:10px;font-family:Jua;font-size:20px;color:#D9765F}}
</style><h1>뿌뿌 굿즈 도안 모음</h1>
<div class="sub">모두 배경이 투명한 PNG입니다(체크무늬 = 투명). 「최대 약 ○cm」는 300dpi 인쇄 기준이에요. {n}종 · @ppuppu_toon</div>{sec}'''
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'board.html').write_text(html, encoding='utf-8')
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1600, 'height': 1000}, device_scale_factor=1.5)
    pg.goto((OUT / 'board.html').as_uri()); pg.wait_for_timeout(800)
    pg.screenshot(path=str(OUT / '뿌뿌_굿즈도안_모음.png'), full_page=True); b.close()
with zipfile.ZipFile(OUT / '뿌뿌_굿즈도안_투명PNG.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    i = 0
    for _, ks in GROUPS:
        for k in ks:
            i += 1; z.write(ST / f'{k}.png', f'{i:02d}_{CN.get(k, k)}.png')
print(n)
