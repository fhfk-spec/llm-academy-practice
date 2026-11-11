"""뿌뿌 캐릭터 시트 렌더링 (무료) — python3 character_sheet.py → out/character_sheet/뿌뿌_캐릭터시트.png"""
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ST = HERE / 'stickers'
VF = HERE / 'vendor' / 'fonts'
OUT = HERE / 'out' / 'character_sheet'
OUT.mkdir(parents=True, exist_ok=True)

def img(name):
    return (ST / f'{name}.png').as_uri()

FACES = [('face_hehe', '헤헤'), ('face_sparkle_eyes', '반짝'), ('face_fighting', '화이팅'), ('face_smug', '뿌듯·으쓱'),
         ('face_hmm', '고민'), ('face_suspicious', '의심'), ('face_pokerface', '무덤덤'), ('face_annoyed', '짜증'),
         ('face_shock', '충격'), ('face_cry_big', '오열'), ('face_soul_out', '영혼 탈출'), ('face_sleepy', '졸림')]
POSES = [('laptop_typing', '노트북 작업'), ('notebook_study', '공부'), ('run_late', '지각 달리기'), ('jump_joy', '점프 기쁨'),
         ('desk_faceplant', '책상 뻗음'), ('phone_bed_lying', '누워서 폰'), ('hold_sign', '팻말'), ('thumbs_up', '최고')]
COLORS = [('#2E2A28', '머리·선', '올림머리, 외곽선'), ('#FFF4EA', '피부', '얼굴·손'), ('#F6B3AE', '볼터치', '양볼 동그라미'),
          ('#F6E5D0', '상의', '연베이지'), ('#A5D0EF', '바지', '하늘색 (확정)'),
          ('#D9765F', '스토리 포인트', '서사 회차'), ('#3F86C9', '정보 포인트', 'AI 나눔 회차')]

faces = ''.join(f'<div class="cell"><img src="{img(n)}"><span>{l}</span></div>' for n, l in FACES)
poses = ''.join(f'<div class="cell pose"><img src="{img(n)}"><span>{l}</span></div>' for n, l in POSES)
chips = ''.join(f'<div class="chip"><i style="background:{h}"></i><b>{n}</b><em>{d}<br>{h}</em></div>' for h, n, d in COLORS)

HTML = f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="{(VF / 'jua/index.css').as_uri()}">
<style>
@font-face{{font-family:Pretendard;font-weight:500;src:url('{(VF / 'pretendard/Pretendard-Medium.woff2').as_uri()}')}}
@font-face{{font-family:Pretendard;font-weight:700;src:url('{(VF / 'pretendard/Pretendard-Bold.woff2').as_uri()}')}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1920px;height:1240px;background:#fff;font-family:Pretendard;color:#2E2A28;padding:44px 52px;display:grid;
 grid-template-columns:520px 1fr;gap:40px}}
h1,h2,.name{{font-family:Jua;font-weight:400}}
.left{{background:#FFF4EF;border-radius:36px;padding:34px 30px;display:flex;flex-direction:column;align-items:center;position:relative}}
.tag{{font-family:Jua;background:#D9765F;color:#fff;border-radius:99px;padding:6px 20px;font-size:24px}}
.name{{font-size:92px;line-height:1;margin:14px 0 4px}}
.en{{font-size:22px;color:#B98A7C;letter-spacing:2px}}
.hero{{height:640px;margin:18px 0 6px;object-fit:contain}}
.ratio{{font-size:20px;color:#8a7a74;text-align:center;line-height:1.5}}
.quote{{margin-top:auto;font-family:Jua;font-size:34px;background:#fff;border:3px solid #2E2A28;border-radius:28px;padding:14px 26px;position:relative}}
.quote:before{{content:'';position:absolute;top:-18px;left:50%;border:10px solid transparent;border-bottom:16px solid #2E2A28;transform:translateX(-50%)}}
.right{{display:grid;grid-template-rows:auto auto auto 1fr;gap:22px}}
.top{{display:grid;grid-template-columns:1.25fr 1fr;gap:24px}}
.box{{border:2.5px solid #F3C3B4;border-radius:26px;padding:20px 26px}}
h2{{font-size:32px;margin-bottom:12px;display:flex;align-items:center;gap:10px}}
h2:before{{content:'';width:12px;height:30px;border-radius:6px;background:#D9765F}}
dl{{display:grid;grid-template-columns:120px 1fr;row-gap:9px;font-size:21px;line-height:1.4}}
dt{{color:#D9765F;font-weight:700}} dd{{font-weight:500}}
.kw{{display:flex;flex-wrap:wrap;gap:8px;margin-top:4px}}
.kw span{{background:#FFE4DA;border-radius:99px;padding:3px 14px;font-size:19px;font-weight:700}}
ul{{list-style:none;font-size:20px;line-height:1.55;font-weight:500}} li:before{{content:'✔ ';color:#3F86C9;font-weight:700}}
.chips{{display:grid;grid-template-columns:repeat(7,1fr);gap:12px}}
.chip{{text-align:center}} .chip i{{display:block;height:64px;border-radius:18px;border:2px solid #0001;margin-bottom:6px}}
.chip b{{font-size:19px;display:block}} .chip em{{font-style:normal;font-size:15px;color:#8a7a74;line-height:1.3}}
.grid{{display:grid;gap:10px}} .faces{{grid-template-columns:repeat(12,1fr)}} .poses{{grid-template-columns:repeat(8,1fr)}}
.cell{{background:#FAFAF8;border-radius:18px;display:flex;flex-direction:column;align-items:center;padding:8px 4px 6px}}
.cell img{{width:100%;height:96px;object-fit:contain}} .pose img{{height:150px}}
.cell span{{font-size:17px;font-weight:700;margin-top:4px;white-space:nowrap}}
.foot{{position:absolute;bottom:14px;right:60px;font-size:17px;color:#bbb}}
</style></head><body>
<div class="left">
 <div class="tag">취준 재도전 · AI 공부 중</div>
 <div class="name">뿌뿌</div><div class="en">PPUPPU</div>
 <img class="hero" src="{img('wave_smile')}">
 <div class="ratio">머리 5 : 몸 3 · 검은 올림머리 1개 · 앞머리 없음<br>작은 점 눈 · 양볼 분홍 동그라미 · 작은 귀</div>
 <div class="quote">"일단 대충이라도 하자."</div>
</div>
<div class="right">
 <div class="top">
  <div class="box"><h2>기본 설정</h2><dl>
   <dt>상태</dt><dd>취업 재도전 중, AI 부트캠프 수강생</dd>
   <dt>핵심 문장</dt><dd>늦었다고 생각해도, 그래도 해보는 사람.</dd>
   <dt>가치관</dt><dd>두려움이 없어야 움직이는 게 아니라,<br>두려워도 내가 할 일을 한다.</dd>
   <dt>성격</dt><dd><div class="kw"><span>현실적</span><span>신중함</span><span>책임감</span><span>관찰</span><span>끈기</span><span>조용한 성장</span></div></dd>
   <dt>갭 포인트</dt><dd>겉은 무덤덤·까칠, 속은 생각 많고 여림.<br>기쁘면 못 숨기고 와르르 무너짐.</dd>
   <dt>성장 루프</dt><dd>걱정 → 준비 → 시도 → 실패 → 복기 → 다시 시도</dd>
  </dl></div>
  <div class="box"><h2>그릴 때 체크</h2><ul>
   <li>올림머리는 정수리 위 동그란 1개</li><li>앞머리·속눈썹 그리지 않기</li><li>얼굴은 동그랗고 살짝 납작하게</li>
   <li>볼터치는 항상 양쪽 동그라미</li><li>상의 연베이지 / 바지 하늘색</li><li>색연필 질감 + 굵은 검정 외곽선</li>
   <li>그림 안에 글자 넣지 않기</li></ul></div>
 </div>
 <div><h2>컬러 팔레트</h2><div class="chips">{chips}</div></div>
 <div><h2>표정</h2><div class="grid faces">{faces}</div></div>
 <div><h2>포즈</h2><div class="grid poses">{poses}</div></div>
</div>
<div class="foot">@ppuppu_toon · character sheet v1</div>
</body></html>"""

p = OUT / 'sheet.html'
p.write_text(HTML, encoding='utf-8')
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={'width': 1920, 'height': 1240}, device_scale_factor=2)
    pg.goto(p.as_uri()); pg.wait_for_timeout(800)
    pg.screenshot(path=str(OUT / '뿌뿌_캐릭터시트.png'), full_page=True)
    b.close()
print(OUT / '뿌뿌_캐릭터시트.png')
