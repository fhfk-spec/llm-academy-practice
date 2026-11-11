"""뿌뿌 무료 카드 렌더러 — 회차 JSON 한 개로 업로드 직전 패키지까지

사용: python3 render_cards.py episode.json 출력폴더
결과: 출력폴더/업로드용/01_표지.jpg ...  캡션_복사용.txt  업로드_체크리스트.txt
      출력폴더/미리보기.jpg (전체 한눈에)

비용 0원: 그림은 stickers/ 의 뿌뿌 스티커를 조합하고, 소품은 Twemoji(무료 오픈 라이선스 CC-BY 4.0) SVG,
글자는 HTML/CSS 로 배치한 뒤 Playwright(Chromium)로 1080x1350 jpg 로 찍는다.

카드 종류(type)
- cover : 표지 (series, ep, title, title_hl, subtitle, sticker, props)
- toon  : 툰 컷 (narration, sticker, pos, size, bubbles[], props[], bg, fx)
- info  : AI 정보 카드 (label, title, points[], box, sticker, say)
- compare: 비교 카드 (title, left{head,items}, right{head,items}, verdict, sticker)
- next  : 다음 화 예고 (text, sticker)
- intro : 뿌뿌 소개 카드 (계정 소개글 3줄 + 팔로우 유도)
"""
import json, sys, re, html, shutil, tarfile, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 1080, 1350
STK = HERE / 'stickers'
FONTS = HERE / 'fonts'
EMOJI_DIR = HERE / 'vendor' / 'twemoji'
EMOJI_TGZ = HERE / 'vendor' / 'twemoji-svg-15.0.0.tgz'

BG = {
    'cream': ('#FFF5EA', '#FCE9D8'),
    'pink': ('#FFECE8', '#FBD6CF'),
    'night': ('#E3E8F5', '#C9D3EC'),
    'mint': ('#EAF6EF', '#D3ECDD'),
    'yellow': ('#FFF7DA', '#FBEAB0'),
    'gray': ('#F1EFEC', '#E2DED8'),
    'coral': ('#FFEDE6', '#FFD5C7'),
    'sky': ('#EAF2FC', '#D2E3F7'),
}
INK = '#3A2E28'
PINK = '#FED6CE'
HL = '#FFB7AA'

INTRO_LINES = ['면접 6연패 취준생 → AI 부트캠프생 🎒', '일단 대충이라도 하자, 성장 기록 중', '내가 배운 AI, 쉽게 나눠드려요 🤖']
HANDLE = '@ppuppu_toon'


# ---------- emoji ----------
def ensure_emoji():
    if (EMOJI_DIR / 'package').exists():
        return EMOJI_DIR / 'package'
    if EMOJI_TGZ.exists():
        EMOJI_DIR.mkdir(parents=True, exist_ok=True)
        with tarfile.open(EMOJI_TGZ) as t:
            t.extractall(EMOJI_DIR, filter='data')
        return EMOJI_DIR / 'package'
    return None


EMOJI_RE = re.compile('([\U0001F000-\U0001FAFF☀-➿⬀-⯿←-⇿⌀-⏿✀-➿]'
                      '[️‍\U0001F3FB-\U0001F3FF\U0001F000-\U0001FAFF☀-➿]*)')


def emoji_file(ch):
    base = ensure_emoji()
    if not base:
        return None
    cps = [f'{ord(c):x}' for c in ch]
    for cand in ('-'.join(cps), '-'.join(c for c in cps if c != 'fe0f')):
        f = base / f'{cand}.svg'
        if f.exists():
            return f
    return None


def emojify(text, size='1em'):
    """텍스트 속 이모지를 Twemoji 이미지로 바꾼다(서버에 컬러 이모지 폰트가 없어도 예쁘게)."""
    out = []
    for part in EMOJI_RE.split(text):
        if part and EMOJI_RE.fullmatch(part):
            f = emoji_file(part)
            out.append(f'<img class="emo" src="{f.as_uri()}" style="height:{size}">' if f else html.escape(part))
        else:
            out.append(html.escape(part).replace('\n', '<br>'))
    return ''.join(out)


def rich(text, size='1em'):
    """**강조** → 형광펜, 이모지 → 이미지"""
    parts = re.split(r'(\*\*.+?\*\*)', text, flags=re.S)
    return ''.join(f'<span class="hl">{emojify(p[2:-2], size)}</span>' if p.startswith('**') else emojify(p, size)
                   for p in parts)


# ---------- pieces ----------
def sticker_img(sid, style):
    f = STK / f'{sid}.png'
    if not f.exists():
        raise SystemExit(f'스티커 없음: {sid}  (stickers/stickers.json 목록 확인)')
    return f'<img class="stk" data-id="{sid}" src="{f.as_uri()}" style="{style}">'


def props_html(props):
    out = []
    for p in props or []:
        f = emoji_file(p['emoji'])
        if not f:
            continue
        rot = p.get('rot', 0)
        out.append(f'<img class="prop" src="{f.as_uri()}" style="left:{p["x"]}px;top:{p["y"]}px;'
                   f'width:{p.get("size", 110)}px;transform:rotate({rot}deg);opacity:{p.get("op", 1)}">')
    return ''.join(out)


SLOTS = {  # 말풍선 기본 자리 (left, top) / right 기준이면 음수 대신 'r'
    'tl': 'left:60px;top:250px', 'tr': 'right:60px;top:250px',
    'ml': 'left:50px;top:520px', 'mr': 'right:50px;top:520px',
    'top': 'left:50%;top:230px;transform:translateX(-50%)',
    'bl': 'left:60px;bottom:120px', 'br': 'right:60px;bottom:120px',
}


def bubble_html(b):
    kind = b.get('kind', 'say')  # say / think / shout / inner
    pos = SLOTS.get(b.get('pos', 'tr'), '')
    if 'x' in b:
        pos = f'left:{b["x"]}px;top:{b["y"]}px'
    if b.get('_style'):
        pos = b['_style']
    fs = b.get('size', 50 if kind != 'shout' else 92)
    tail = 'none' if b.get('tail') is False or kind in ('shout', 'alert') else kind
    to = f' data-tx="{b["to"][0]}" data-ty="{b["to"][1]}"' if b.get('to') else ''
    return (f'<div class="bub {kind}" data-tail="{tail}"{to} style="{pos};font-size:{fs}px;'
            f'max-width:{b.get("w", 560)}px">{rich(b["text"])}</div>')


def fx_html(fx):
    if fx == 'rays':
        return '<div class="fx rays"></div>'
    if fx == 'lines':
        return '<div class="fx lines"></div>'
    if fx == 'gloom':
        return '<div class="fx gloom"></div>'
    return ''


def place_sticker(c, default_size=760):
    size = c.get('size', default_size)
    pos = c.get('pos', 'center')
    bottom = c.get('bottom', 40)
    if pos == 'left':
        st = f'left:{c.get("dx", 30)}px;bottom:{bottom}px;height:{size}px'
    elif pos == 'right':
        st = f'right:{c.get("dx", 30)}px;bottom:{bottom}px;height:{size}px'
    else:
        st = f'left:50%;bottom:{bottom}px;height:{size}px;transform:translateX(-50%)'
    if c.get('flip'):
        st += ';scale:-1 1' if pos == 'center' else ';transform:scaleX(-1)'
    return sticker_img(c['sticker'], st) + '<div class="shadow" data-for="stk"></div>'



# ---------- 감정 배경 (mood) ----------
# urgent: 큰일·다급 → 회색 집중선 / shock: 충격 → 검정 / gloomy: 우중충 → 먹구름 회색+빗줄기
# happy: 화기애애·행복 → tone yellow|pink|sky|mix 파스텔 + 몽글몽글 방울
MOOD_TONES = {'yellow': ('#FFF6C9', '#FFE9A8'), 'pink': ('#FFE6EE', '#FFD3DF'), 'sky': ('#E3F3FF', '#CBE7FB'),
              'mix': ('#FFF3C4', '#FFDCE6', '#D6EEFF')}
DARK_MOODS = ('shock', 'gloomy')


def mood_html(m, tone='mix'):
    if not m:
        return ''
    if m == 'happy':
        cs = MOOD_TONES.get(tone, MOOD_TONES['mix'])
        grad = f"linear-gradient(165deg,{','.join(cs)})"
        dots = ('radial-gradient(circle at 12% 18%,rgba(255,255,255,.75) 0 46px,transparent 47px),'
                'radial-gradient(circle at 86% 12%,rgba(255,255,255,.6) 0 30px,transparent 31px),'
                'radial-gradient(circle at 80% 62%,rgba(255,255,255,.55) 0 64px,transparent 65px),'
                'radial-gradient(circle at 20% 78%,rgba(255,255,255,.6) 0 38px,transparent 39px),'
                'radial-gradient(circle at 52% 92%,rgba(255,255,255,.5) 0 24px,transparent 25px),'
                'radial-gradient(circle at 40% 40%,rgba(255,255,255,.35) 0 90px,transparent 91px)')
        return f'<div class="mood" style="background:{dots},{grad}"></div>'
    return f'<div class="mood mood-{m}"></div>'


MOOD_CSS = """
.mood{position:absolute;inset:0;z-index:0;pointer-events:none}
.mood-urgent{background:radial-gradient(ellipse 34% 30% at 50% 46%,#fff 0 55%,rgba(255,255,255,0) 100%),
 repeating-conic-gradient(from 0deg at 50% 46%,#4E4F55 0deg .9deg,#C3C4C9 .9deg 4.2deg,#77787F 4.2deg 4.9deg,#D2D3D7 4.9deg 8.6deg)}
.mood-shock{background:repeating-linear-gradient(100deg,rgba(255,255,255,.035) 0 2px,transparent 2px 15px),
 radial-gradient(ellipse 70% 60% at 50% 42%,#38383E 0%,#161618 72%,#0B0B0C 100%)}
.mood-gloomy{background:repeating-linear-gradient(76deg,rgba(255,255,255,.13) 0 2px,transparent 2px 34px),
 repeating-linear-gradient(0deg,rgba(0,0,0,.05) 0 3px,transparent 3px 9px),linear-gradient(180deg,#59606B 0%,#454B55 60%,#383D45 100%)}
.card.dark .ftext{color:#fff;text-shadow:0 0 1px #000,3px 3px 0 rgba(0,0,0,.45)}
.cont{position:absolute;right:52px;bottom:40px;z-index:9;font-size:34px;font-family:Jua,GB;color:#3A2E28;background:#fff;
 border:3px solid #3A2E28;border-radius:30px;padding:6px 24px}
"""

# ---------- cards ----------
def card_cover(c, ep):
    ep = {**ep, **{k: c[k] for k in ('title', 'title_hl', 'subtitle', 'series', 'ep', 'ep_label') if k in c}}
    t = html.escape(ep['title'])
    hl = ep.get('title_hl')
    if hl and hl in ep['title']:
        t = t.replace(html.escape(hl), f'<span class="hl">{html.escape(hl)}</span>')
    t = t.replace('\\n', '<br>')
    return f'''
    <div class="chead">
      <div class="pill0">{html.escape(ep.get("ep_label") or f'EP.{int(ep["ep"]):02d}')}</div>
      <div class="series">{html.escape(ep.get("series", "뿌뿌의 취준 재도전기"))}</div>
      <div class="ctitle">{t}</div>
      <div class="csub">{rich(ep.get("subtitle", ""))}</div>
    </div>
    <div class="swipe">넘겨서 보기 →</div>
    {fx_html(c.get("fx", ""))}
    {props_html(c.get("props"))}
    {place_sticker(c, c.get("size", 640))}
    {''.join(bubble_html(b) for b in c.get("bubbles", []))}
    '''


def card_toon(c, ep):
    nar = f'<div class="nar">{rich(c["narration"])}</div>' if c.get('narration') else ''
    return f'''{fx_html(c.get("fx", ""))}{nar}{props_html(c.get("props"))}{place_sticker(c)}
    {''.join(bubble_html(b) for b in c.get("bubbles", []))}'''


def card_info(c, ep):
    pts = ''.join(f'<li><span class="num">{i + 1}</span><span>{rich(p)}</span></li>'
                  for i, p in enumerate(c.get('points', [])))
    box = f'<div class="box">{rich(c["box"])}</div>' if c.get('box') else ''
    stk = sticker_img(c['sticker'], f'right:30px;bottom:30px;height:{c.get("size", 360)}px') if c.get('sticker') else ''
    say = (f'<div class="bub say" data-tail="say" style="right:{c.get("say_right", 330)}px;bottom:{c.get("say_bottom", 250)}px;'
           f'font-size:40px;max-width:430px">{rich(c["say"])}</div>') if c.get('say') else ''
    return f'''
    <div class="label">{rich(c.get("label", "🤖 AI 나눔"))}</div>
    <div class="ititle">{rich(c["title"])}</div>
    <ul class="pts">{pts}</ul>{box}{props_html(c.get("props"))}{stk}{say}'''


def card_compare(c, ep):
    def col(d, cls):
        items = ''.join(f'<li>{rich(x)}</li>' for x in d.get('items', []))
        return f'<div class="col {cls}"><div class="colh">{rich(d["head"])}</div><ul>{items}</ul></div>'
    stk = sticker_img(c['sticker'], f'left:50%;bottom:20px;height:{c.get("size", 330)}px;transform:translateX(-50%)') if c.get('sticker') else ''
    verdict = f'<div class="verdict">{rich(c["verdict"])}</div>' if c.get('verdict') else ''
    return f'''<div class="label">{rich(c.get("label", "🤖 AI 나눔"))}</div>
    <div class="ititle">{rich(c["title"])}</div>
    <div class="cols">{col(c["left"], "l")}{col(c["right"], "r")}</div>{verdict}{stk}'''


def card_next(c, ep):
    return f'''<div class="pill big">다음 화 예고</div>
    <div class="nexttxt">{rich(c["text"])}</div>
    {props_html(c.get("props"))}{place_sticker(c, c.get("size", 640))}
    {''.join(bubble_html(b) for b in c.get("bubbles", []))}'''


def card_intro(c, ep):
    lines = ''.join(f'<div class="iline">{rich(x)}</div>' for x in c.get('lines', INTRO_LINES))
    return f'''<div class="pill">캐릭터 소개</div>
    <div class="iname">뿌뿌</div>
    <div class="ilines">{lines}</div>
    {sticker_img(c.get("sticker", "wave_smile"), f"left:50%;bottom:150px;height:{c.get('size', 560)}px;transform:translateX(-50%)")}
    <div class="shadow" data-for="stk"></div>
    <div class="cta">뿌뿌의 성장기, 팔로우하고 같이 봐요 ♥</div>
    <div class="handle">{HANDLE}</div>'''


PANEL_BOX = (34, 34, 1012, 1282)  # 안쪽 영역 x, y, w, h
GAP = 22


def panel_rects(layout, n):
    x0, y0, W0, H0 = PANEL_BOX
    if layout == '1+2':
        h = (H0 - GAP) // 2; w = (W0 - GAP) // 2
        return [(x0, y0, W0, h), (x0, y0 + h + GAP, w, h), (x0 + w + GAP, y0 + h + GAP, w, h)]
    if layout == '2+1':
        h = (H0 - GAP) // 2; w = (W0 - GAP) // 2
        return [(x0, y0, w, h), (x0 + w + GAP, y0, w, h), (x0, y0 + h + GAP, W0, h)]
    if layout == '2h':
        w = (W0 - GAP) // 2
        return [(x0, y0, w, H0), (x0 + w + GAP, y0, w, H0)]
    n = n or 2
    h = (H0 - GAP * (n - 1)) // n
    return [(x0, y0 + i * (h + GAP), W0, h) for i in range(n)]


def panel_slot(pos, w, h, top0):
    return {'tl': f'left:22px;top:{top0}px', 'tr': f'right:22px;top:{top0}px',
            'ml': f'left:22px;top:{int(h * .42)}px', 'mr': f'right:22px;top:{int(h * .42)}px',
            'top': f'left:50%;top:{top0}px;transform:translateX(-50%)'}.get(pos, f'right:22px;top:{top0}px')


def card_panels(c, ep):
    ps = c['panels']
    layout = c.get('layout', {2: '2v', 3: '3v'}.get(len(ps), '2v'))
    rects = panel_rects(layout if layout in ('1+2', '2+1', '2h') else 'v', len(ps))
    out = []
    for p, (x, y, w, h) in zip(ps, rects):
        inner = mood_html(p.get('mood'), p.get('tone', 'mix')) + fx_html(p.get('fx', ''))
        top0 = 22
        if p.get('narration'):
            inner += f'<div class="pnar">{rich(p["narration"])}</div>'; top0 = 96
        if p.get('title'):
            inner += f'<div class="ptitle" style="top:{top0 + 6}px">{rich(p["title"])}</div>'
        if p.get('caption'):
            inner += f'<div class="pcap">{rich(p["caption"])}</div>'
        inner += props_html(p.get('props'))
        if p.get('sticker'):
            size = p.get('size', int(h * (0.78 if w > 700 else 0.62)))
            pp = dict(p, size=size, bottom=p.get('bottom', -8 if p.get('crop_bottom') else 10))
            inner += place_sticker(pp)
        for b in p.get('bubbles', []):
            b = dict(b)
            b.setdefault('size', 40 if h > 500 else 36)
            b.setdefault('w', int(w * 0.58))
            if 'x' not in b:
                b['_style'] = panel_slot(b.get('pos', 'tl'), w, h, top0)
            inner += bubble_html(b)
        bg = p.get('bg_color', '#fff')
        out.append(f'<div class="panel" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{bg}">{inner}</div>')
    return ''.join(out)



def card_flow(c, ep):
    """테두리 없는 자유 배치 페이지: 장면 그림·스티커·글자를 지그재그로 띄운다"""
    out = []
    for it in c.get('items', []):
        if 'closeup' in it:  # 클로즈업: 얼굴 스티커를 크게, 화면 밖으로 잘리게
            it = {'x': 40, 'y': 380, 'w': 1000, 'z': 2, **it, 'img': it['closeup']}
        st = f"left:{it.get('x', 0)}px;top:{it.get('y', 0)}px;transform:rotate({it.get('rot', 0)}deg);z-index:{it.get('z', 3)}"
        if 'blob' in it:
            out.append(f'<div class="blob" style="{st};width:{it["w"]}px;height:{it["h"]}px;background:{it["blob"]}"></div>')
        elif 'img' in it:
            src = it['img']
            f = (HERE / src[6:]) if src.startswith('scene:') else (STK / f'{src}.png')
            if not f.exists():
                raise SystemExit(f'그림 없음: {src}')
            shape = it.get('shape', 'soft' if src.startswith('scene:') else 'none')
            cls = 'stk' if not src.startswith('scene:') else 'stk scene'
            out.append(f'<img class="{cls} shape-{shape}" src="{f.as_uri()}" style="{st};width:{it["w"]}px;position:absolute">')
        elif 'text' in it:
            out.append(f'<div class="ftext" style="{st};font-size:{it.get("size", 46)}px;max-width:{it.get("mw", 900)}px;'
                       f'text-align:{it.get("align", "left")};{"width:%dpx;" % it.get("mw", 900) if it.get("align") == "center" else ""}">{rich(it["text"])}</div>')
        elif 'label' in it:
            out.append(f'<div class="flabel" style="{st}">{rich(it["label"])}</div>')
    out.append(props_html(c.get('props')))
    for b in c.get('bubbles', []):
        out.append(bubble_html(b))
    return ''.join(out)


RENDER = {'flow': card_flow, 'panels': card_panels, 'cover': card_cover, 'toon': card_toon, 'info': card_info, 'compare': card_compare,
          'next': card_next, 'intro': card_intro}


CSS = """
@font-face{font-family:GB;src:url('%(fb)s')}
@font-face{font-family:GM;src:url('%(fm)s')}
*{box-sizing:border-box;margin:0;padding:0}
body{width:%(w)dpx;height:%(h)dpx;overflow:hidden;font-family:GM;color:%(ink)s}
.card{position:relative;width:%(w)dpx;height:%(h)dpx;overflow:hidden}
.paper{position:absolute;inset:0;background-image:radial-gradient(rgba(120,90,60,.06) 1.2px,transparent 1.4px);background-size:14px 14px}
.frame{position:absolute;inset:22px;border:4px solid rgba(58,46,40,.85);border-radius:34px;pointer-events:none}
.emo{vertical-align:-0.14em;display:inline-block}
.hl{background:linear-gradient(transparent 52%%,%(hl)s 52%%,%(hl)s 92%%,transparent 92%%);padding:0 .08em}
.stk{position:absolute;z-index:3}
.shadow{position:absolute;z-index:2;height:34px;border-radius:50%%;background:rgba(80,60,40,.13)}
.prop{position:absolute;z-index:4}
.nar{position:absolute;left:60px;right:60px;top:66px;z-index:6;background:#fff;border:4px solid %(ink)s;border-radius:16px;
     padding:24px 30px;font-family:GB;font-size:44px;line-height:1.38;text-align:center;box-shadow:6px 6px 0 rgba(58,46,40,.18)}
.bub{position:absolute;z-index:7;background:#fff;border:4px solid %(ink)s;border-radius:44px;padding:24px 36px;
     font-family:GB;line-height:1.32;text-align:center;white-space:pre-wrap;word-break:keep-all}
.bub.think{border-style:dashed;border-radius:60px}
.bub.inner{background:%(pink)s}
.bub.alert{border-radius:20px;border-color:#D9534F;border-width:5px;font-family:GM;color:#5a2a26;box-shadow:8px 8px 0 rgba(217,83,79,.18)}
.bub.shout{background:none;border:none;padding:0;color:#fff;font-family:GB;letter-spacing:-1px;
     -webkit-text-stroke:14px %(ink)s;paint-order:stroke fill;line-height:1.1}
svg.tails{position:absolute;inset:0;z-index:6;pointer-events:none}
.pill{position:absolute;left:70px;top:70px;z-index:6;background:%(ink)s;color:#fff;font-family:GB;font-size:34px;
      padding:12px 26px;border-radius:40px}
.pill.big{font-size:40px}
.chead{position:absolute;left:66px;right:60px;top:66px;z-index:6;display:flex;flex-direction:column;align-items:flex-start;gap:18px}
.pill0{background:%(ink)s;color:#fff;font-family:GB;font-size:34px;padding:12px 26px;border-radius:40px}
.series{font-family:GB;font-size:40px;color:#8A6F60}
.ctitle{font-family:GB;font-size:96px;line-height:1.16;letter-spacing:-2px;word-break:keep-all}
.csub{font-size:42px;line-height:1.4;color:#6B574C;word-break:keep-all}
.swipe{position:absolute;right:64px;top:84px;z-index:6;font-family:GB;font-size:30px;color:#8A6F60}
.label{position:absolute;left:70px;top:72px;z-index:6;background:#fff;border:4px solid %(ink)s;border-radius:40px;
       font-family:GB;font-size:34px;padding:10px 26px}
.ititle{position:absolute;left:70px;right:70px;top:160px;z-index:6;font-family:GB;font-size:70px;line-height:1.22;letter-spacing:-1.5px;word-break:keep-all}
.pts{position:absolute;left:70px;right:70px;top:420px;z-index:6;list-style:none;display:flex;flex-direction:column;gap:26px}
.pts li{display:flex;gap:22px;align-items:flex-start;font-size:42px;line-height:1.38;word-break:keep-all;
        background:rgba(255,255,255,.88);border:3px solid rgba(58,46,40,.25);border-radius:22px;padding:20px 26px}
.num{flex:none;width:58px;height:58px;border-radius:50%%;background:%(ink)s;color:#fff;font-family:GB;font-size:34px;
     display:flex;align-items:center;justify-content:center;margin-top:-2px}
.box{position:absolute;left:70px;right:420px;bottom:90px;z-index:6;background:#2F2A27;color:#FDF3E7;border-radius:22px;
     padding:26px 30px;font-size:36px;line-height:1.45;word-break:keep-all}
.cols{position:absolute;left:60px;right:60px;top:390px;z-index:6;display:flex;gap:24px}
.col{flex:1;background:#fff;border:4px solid %(ink)s;border-radius:26px;padding:24px 26px}
.col.r{background:%(pink)s}
.colh{font-family:GB;font-size:46px;text-align:center;margin-bottom:16px}
.col ul{list-style:none;display:flex;flex-direction:column;gap:14px}
.col li{font-size:39px;line-height:1.35;word-break:keep-all}
.col li:before{content:'· '}
.verdict{position:absolute;left:60px;right:60px;bottom:410px;z-index:6;text-align:center;font-family:GB;font-size:46px;word-break:keep-all}
.nexttxt{position:absolute;left:70px;right:70px;top:170px;z-index:6;font-family:GB;font-size:74px;line-height:1.24;letter-spacing:-1.5px;word-break:keep-all}
.iname{position:absolute;left:0;right:0;top:150px;text-align:center;font-family:GB;font-size:110px;z-index:6}
.ilines{position:absolute;left:60px;right:60px;top:300px;z-index:6;display:flex;flex-direction:column;gap:14px;align-items:center}
.iline{background:#fff;border:3px solid %(ink)s;border-radius:40px;padding:12px 30px;font-family:GB;font-size:38px}
.cta{position:absolute;left:0;right:0;bottom:78px;text-align:center;font-family:GB;font-size:40px;z-index:6}
.handle{position:absolute;left:0;right:0;bottom:40px;text-align:center;font-size:28px;color:#8A6F60;z-index:6}
.panel{position:absolute;overflow:hidden;border:4px solid %(ink)s;border-radius:20px}
.panel .fx{inset:0;border-radius:0}
.pnar{position:absolute;left:50%%;top:16px;transform:translateX(-50%%);z-index:6;background:#fff;border:3px solid %(ink)s;border-radius:12px;
      padding:10px 22px;font-family:GB;font-size:32px;line-height:1.3;text-align:center;white-space:nowrap;max-width:94%%}
.ptitle{position:absolute;left:24px;right:24px;z-index:6;text-align:center;font-family:GB;font-size:52px;line-height:1.25;word-break:keep-all}
.scene{z-index:2}
.shape-soft{-webkit-mask-image:radial-gradient(ellipse 50%% 50%% at 50%% 50%%,#000 70%%,transparent 100%%);mask-image:radial-gradient(ellipse 50%% 50%% at 50%% 50%%,#000 70%%,transparent 100%%)}
.shape-round{border-radius:46px}
.shape-blob{border-radius:48%% 52%% 45%% 55%% / 55%% 45%% 55%% 45%%}
.blob{position:absolute;border-radius:50%% 46%% 54%% 48%% / 48%% 55%% 45%% 52%%;opacity:.9;z-index:1}
.ftext{position:absolute;z-index:6;font-family:GB;line-height:1.3;word-break:keep-all;color:%(ink)s}
.flabel{position:absolute;z-index:6;background:%(ink)s;color:#fff;font-family:GB;font-size:30px;padding:8px 22px;border-radius:30px}
.pcap{position:absolute;left:30px;right:30px;top:50%%;transform:translateY(-50%%);z-index:6;text-align:center;font-family:GB;font-size:62px;line-height:1.25;word-break:keep-all}
.fx{position:absolute;inset:26px;border-radius:30px;overflow:hidden;z-index:1}
.fx.rays{background:repeating-conic-gradient(from 0deg at 50%% 62%%,rgba(255,226,140,.55) 0 6deg,transparent 6deg 15deg)}
.fx.lines{background:repeating-conic-gradient(from 0deg at 50%% 55%%,rgba(58,46,40,.10) 0 1.6deg,transparent 1.6deg 7deg);
          -webkit-mask:radial-gradient(circle at 50%% 55%%,transparent 34%%,#000 60%%)}
.fx.gloom{background:linear-gradient(rgba(70,80,120,.18),rgba(70,80,120,.02))}
"""

JS = """
() => {
  // 스티커 그림자 위치
  document.querySelectorAll('.shadow').forEach(s => {
    const st = s.previousElementSibling && s.previousElementSibling.classList.contains('stk') ? s.previousElementSibling
             : document.querySelector('.stk');
    if (!st) { s.remove(); return; }
    const r = st.getBoundingClientRect(); const pr = (s.offsetParent || document.body).getBoundingClientRect();
    s.style.left = (r.left - pr.left + r.width*0.18) + 'px'; s.style.width = (r.width*0.64) + 'px';
    s.style.top = (r.bottom - pr.top - 22) + 'px';
  });
  // 말풍선 꼬리: 가장 가까운 스티커의 머리(위쪽 30%) 쪽으로
  const NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS, 'svg'); svg.setAttribute('class','tails');
  svg.setAttribute('width', 1080); svg.setAttribute('height', 1350);
  const stks = [...document.querySelectorAll('.stk')];
  document.querySelectorAll('.bub').forEach(b => {
    const kind = b.dataset.tail;
    const pnl = b.closest('.panel'); const cand = pnl ? [...pnl.querySelectorAll('.stk')] : stks;
    if (kind === 'none' || (!cand.length && !b.dataset.tx)) return;
    if (!cand.length) cand.push(b);
    const r = b.getBoundingClientRect(); const cx = r.left + r.width/2, cy = r.top + r.height/2;
    let best = null, bd = 1e9;
    cand.forEach(s => { const q = s.getBoundingClientRect();
      const hx = q.left + q.width/2, hy = q.top + q.height*0.28;
      const d = Math.hypot(hx-cx, hy-cy); if (d < bd) { bd = d; best = [hx, hy, q]; } });
    let [tx, ty, q] = best;
    if (b.dataset.tx) { tx = +b.dataset.tx; ty = +b.dataset.ty; q = {width: 120}; }
    // 머리 가장자리 바깥까지만
    const ang = Math.atan2(ty-cy, tx-cx);
    // 풍선 테두리에서 출발점
    const ex = cx + Math.cos(ang) * r.width/2 * 0.92, ey = cy + Math.sin(ang) * r.height/2 * 0.92;
    const len = Math.min(110, Math.max(50, Math.hypot(tx-ex, ty-ey) - q.width*0.33));
    const px = ex + Math.cos(ang)*len, py = ey + Math.sin(ang)*len;
    const nx = -Math.sin(ang), ny = Math.cos(ang), w = 22;
    if (kind === 'think') {
      [0.45, 0.8, 1.05].forEach((t,i) => { const c = document.createElementNS(NS,'circle');
        c.setAttribute('cx', ex + Math.cos(ang)*len*t); c.setAttribute('cy', ey + Math.sin(ang)*len*t);
        c.setAttribute('r', [16,11,7][i]); c.setAttribute('fill','#fff'); c.setAttribute('stroke','#3A2E28');
        c.setAttribute('stroke-width','4'); svg.appendChild(c); });
      return;
    }
    const fill = getComputedStyle(b).backgroundColor;
    const p = document.createElementNS(NS,'path');
    p.setAttribute('d', `M${ex+nx*w},${ey+ny*w} L${px},${py} L${ex-nx*w},${ey-ny*w}`);
    p.setAttribute('fill', fill); p.setAttribute('stroke','#3A2E28'); p.setAttribute('stroke-width','4');
    p.setAttribute('stroke-linejoin','round'); svg.appendChild(p);
    // 풍선 테두리와 꼬리 이음새를 덮는 패치
    const m = document.createElementNS(NS,'path');
    m.setAttribute('d', `M${ex+nx*(w-5)},${ey+ny*(w-5)} L${ex+Math.cos(ang)*5},${ey+Math.sin(ang)*5} L${ex-nx*(w-5)},${ey-ny*(w-5)} Z`);
    m.setAttribute('fill', fill); m.setAttribute('stroke', fill); m.setAttribute('stroke-width','6');
    svg.appendChild(m);
  });
  document.querySelector('.card').appendChild(svg);
  // 말풍선을 꼬리 위로
  document.querySelectorAll('.bub').forEach(b => b.style.zIndex = 8);
  // 화면 밖으로 나간 요소 검사
  const bad = [];
  document.querySelectorAll('.bub,.nar,.pnar,.chead,.pts,.box,.cols,.ititle,.nexttxt,.verdict').forEach(e => {
    const r = e.getBoundingClientRect(); const P = e.closest('.panel'); const pr = P ? P.getBoundingClientRect() : {left:20,top:20,right:1060,bottom:1330};
    if (r.left < pr.left - 1 || r.top < pr.top - 1 || r.right > pr.right + 1 || r.bottom > pr.bottom + 1) bad.push(e.className + ':' + e.innerText.slice(0,12));
  });
  return bad;
}
"""


VF = HERE / 'vendor' / 'fonts'
FONTSETS = {  # 이름: (font-family, CSS 파일 또는 None, 굵기)
    'gmarket': ('GB', None, 'normal'),
    'jua': ('Jua', 'jua/index.css', 'normal'),
    'dohyeon': ('Do Hyeon', 'do-hyeon/index.css', 'normal'),
    'gaegu': ('Gaegu', 'gaegu/700.css', '700'),
    'gowun': ('Gowun Dodum', 'gowun-dodum/index.css', 'normal'),
    'pretendard': ('Pretendard', 'pretendard', '700'),
}
THEMES = {  # 흰 배경 + 포인트 컬러
    'story': dict(point='#FFE4DA', accent='#D9765F', hl='#FFCFC0', frame='#F3C3B4', nar='#FFF4EF'),
    'info': dict(point='#DDEEFC', accent='#3F86C9', hl='#C4E0FA', frame='#A7D0F2', nar='#F0F7FE'),
}
TITLE_SEL = '.ftext,.flabel,.ptitle,.pcap,.ctitle,.ititle,.nexttxt,.iname,.bub.shout,.pill0,.pill,.series,.colh,.verdict,.num'
BODY_SEL = 'body,.bub,.nar,.csub,.pts li,.box,.col li,.label,.cta,.iline,.handle,.swipe'


def ensure_font(src):
    # vendor/fonts/<이름>/ 이 없으면 vendor/fonts_tgz/ 의 npm 패키지(.tgz)에서 풀어 쓴다
    d = src.split('/')[0]
    if (VF / d).exists():
        return
    tgz = HERE / 'vendor' / 'fonts_tgz'
    import glob
    for f in glob.glob(str(tgz / f'*{d}*.tgz')):
        tmp = VF / ('_' + d); tmp.mkdir(parents=True, exist_ok=True)
        with tarfile.open(f) as t:
            t.extractall(tmp, filter='data')
        (tmp / 'package').rename(VF / d); tmp.rmdir()
        return


def font_css(role, key):
    fam, src, wt = FONTSETS.get(key, FONTSETS['gmarket'])
    if src and src != 'pretendard':
        ensure_font(src)
    if fam == 'GB':
        return '', ''
    links = ''
    if src == 'pretendard':
        for w, f in [(500, 'Medium'), (700, 'Bold'), (800, 'ExtraBold')]:
            links += f"<style>@font-face{{font-family:Pretendard;font-weight:{w};src:url('{(VF / 'pretendard' / f'Pretendard-{f}.woff2').as_uri()}')}}</style>"
    elif src:
        links = f'<link rel="stylesheet" href="{(VF / src).as_uri()}">'
    sel = TITLE_SEL if role == 'title' else BODY_SEL
    css = f"{sel}{{font-family:'{fam}',GB;font-weight:{wt}}}"
    return links, css


def page_html(c, ep):
    c = {**ep.get('style', {}), **c}
    bg1, bg2 = BG.get(c.get('bg', 'cream'), BG['cream'])
    css = CSS % {'fb': (FONTS / 'GmarketSansTTFBold.ttf').as_uri(), 'fm': (FONTS / 'GmarketSansTTFMedium.ttf').as_uri(),
                 'w': W, 'h': H, 'ink': INK, 'pink': PINK, 'hl': HL}
    body = RENDER[c['type']](c, ep)
    if c.get('hl'):
        css += (".hl{background:linear-gradient(transparent 52%%,%s 52%%,%s 92%%,transparent 92%%)}" % (c['hl'], c['hl'])).replace('%%', '%')
    if c.get('layout', c.get('cover_layout')) == 'center' and c['type'] == 'cover':
        css += (".chead{left:60px;right:60px;align-items:center;text-align:center}.ctitle{text-align:center}"
                ".csub{text-align:center}.swipe{display:none}")
    if c.get('accent'):
        css += ".pill0{background:%s}.series{color:%s}" % (c['accent'], c['accent'])
    th = THEMES.get(c.get('theme', ''))
    if th:
        bg1 = bg2 = '#FFFFFF'
        css += (f".paper{{display:none}}.frame{{border-color:{th['frame']}}}.pill0,.pill{{background:{th['accent']}}}"
                f".series{{color:{th['accent']}}}.nar{{background:{th['nar']};border-color:{th['accent']};box-shadow:6px 6px 0 {th['point']}}}"
                f".label{{background:{th['point']};border-color:{th['accent']}}}.num{{background:{th['accent']}}}"
                f".col.r{{background:{th['point']}}}.pts li{{background:{th['nar']};border-color:{th['frame']}}}"
                f".pnar{{background:{th['nar']};border-color:{th['accent']}}}.flabel{{background:{th['accent']}}}"
                f".shadow{{background:{th['point']}}}.bub.shout{{color:{th['accent']};-webkit-text-stroke:12px #fff;filter:drop-shadow(0 0 0 {INK}) drop-shadow(3px 3px 0 {INK})}}"
                f".hl{{background:linear-gradient(transparent 52%,{th['hl']} 52%,{th['hl']} 92%,transparent 92%)}}")
    links = ''
    for role in ('body', 'title'):
        if c.get('fonts', {}).get(role):
            l, fc = font_css(role, c['fonts'][role]); links += l; css += fc
    frame = '<div class="frame"></div>' if c.get('frame', c['type'] not in ('panels', 'flow')) else ''
    css += MOOD_CSS
    mood = mood_html(c.get('mood'), c.get('tone', 'mix')) if c['type'] != 'cover' else ''
    dark = ' dark' if c.get('mood') in DARK_MOODS else ''
    if c.get('_last') and ep.get('format') == 'series':
        body += f'<div class="cont">{c.get("cont_text", "(계속)")}</div>'
    body = mood + body
    return (f'<!doctype html><html><head><meta charset="utf-8">{links}<style>{css}</style></head><body>'
            f'<div class="card{dark}" style="background:linear-gradient(170deg,{bg1},{bg2})"><div class="paper"></div>'
            f'{body}{frame}</div></body></html>')


def safe_name(s):
    return re.sub(r'[\\/:*?"<>|\s]+', '', s)[:16] or 'card'


def main(ep_path, out_dir):
    ep = json.loads(Path(ep_path).read_text(encoding='utf-8'))
    out = Path(out_dir).resolve(); up = out / '업로드용'
    if up.exists():
        shutil.rmtree(up)
    up.mkdir(parents=True)
    tmp = out / '_html'; tmp.mkdir(exist_ok=True)
    from playwright.sync_api import sync_playwright
    files, warns = [], []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=1)
        for i, c in enumerate(ep['cards'], 1):
            name = f'{i:02d}_{safe_name(c.get("name", c["type"]))}'
            hp = tmp / f'{name}.html'
            c = dict(c, _last=(i == len(ep['cards'])))
            hp.write_text(page_html(c, ep), encoding='utf-8')
            pg.goto(hp.as_uri()); pg.wait_for_load_state('networkidle')
            pg.evaluate('document.fonts.ready')
            bad = pg.evaluate(JS)
            if bad:
                warns.append(f'{name}: 화면 밖으로 나감 → {bad}')
            png = tmp / f'{name}.png'
            pg.screenshot(path=str(png), type='png')
            from PIL import Image
            jpg = up / f'{name}.jpg'
            Image.open(png).convert('RGB').save(jpg, quality=93)
            files.append(jpg)
        b.close()
    # 캡션: 제목 한 줄 + 해시태그
    cap = ep.get('caption_title', ep['title'].replace('\\n', ' '))
    tags = ' '.join(t if t.startswith('#') else '#' + t for t in ep.get('hashtags', []))
    (up / '캡션_복사용.txt').write_text(f'{cap}\n\n{tags}\n', encoding='utf-8')
    (up / '업로드_체크리스트.txt').write_text(
        f'EP.{int(ep["ep"]):02d} 업로드 체크리스트\n'
        f'[ ] 사진 {len(files)}장 순서대로 선택 (01 → {len(files):02d})\n'
        '[ ] 자르기 4:5 (원본 비율)\n[ ] 필터: 원본\n[ ] 캡션_복사용.txt 붙여넣기\n'
        '[ ] 최종 손보기(글자·순서) 후 공유\n', encoding='utf-8')
    # 미리보기
    from PIL import Image
    th = [Image.open(f).resize((270, 338)) for f in files]
    cols = 4; rows = (len(th) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * 280 + 10, rows * 348 + 10), 'white')
    for i, t in enumerate(th):
        sheet.paste(t, (10 + (i % cols) * 280, 10 + (i // cols) * 348))
    sheet.save(out / '미리보기.jpg', quality=88)
    shutil.rmtree(tmp)
    print(f'완성 {len(files)}장 → {up}')
    for w in warns:
        print('⚠', w)
    return warns


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
