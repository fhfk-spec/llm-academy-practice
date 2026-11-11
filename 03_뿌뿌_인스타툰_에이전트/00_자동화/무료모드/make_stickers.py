"""뿌뿌 스티커 라이브러리 만들기 (무료, 로컬 실행)

그림(장면·표정 시트·프로필)에서 뿌뿌만 배경 없이 잘라 stickers/*.png 로 저장하고
stickers/stickers.json 에 이름·감정 태그를 기록한다.

사용: python3 make_stickers.py sticker_sources.json stickers/
  sticker_sources.json = [{"id": "cheer", "src": "경로", "crop": [x0,y0,x1,y1] (선택),
                           "tags": ["기쁨","만세"], "desc": "두 팔 번쩍 만세"}]
배경 제거: rembg (isnet-anime 모델, 무료·오프라인). 처음 한 번 모델(176MB)을 받는다.
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None


def clean_alpha(img, keep_ratio=0.03):
    """희미한 그림자·잔티 제거: 약한 알파는 0으로, 작은 덩어리는 버린다."""
    a = np.array(img.getchannel('A'))
    a[a < 60] = 0
    if cv2 is not None:
        # 윤곽선 안쪽이 반투명하게 빠지는 문제: 바깥과 이어지지 않은 구멍은 모두 채운다
        m = (a > 40).astype(np.uint8) * 255
        h, w = m.shape
        pad = np.zeros((h + 2, w + 2), np.uint8); pad[1:-1, 1:-1] = m
        ff = pad.copy(); fmask = np.zeros((h + 4, w + 4), np.uint8)
        cv2.floodFill(ff, fmask, (0, 0), 128)
        inside = (ff[1:-1, 1:-1] != 128)
        a = np.where(inside, 255, 0).astype(np.uint8)
        n, lab, stats, _ = cv2.connectedComponentsWithStats((a > 0).astype(np.uint8), 8)
        if n > 1:
            big = stats[1:, cv2.CC_STAT_AREA].max()
            for i in range(1, n):
                if stats[i, cv2.CC_STAT_AREA] < big * keep_ratio:
                    a[lab == i] = 0
    img.putalpha(Image.fromarray(a).filter(ImageFilter.GaussianBlur(0.6)))
    bb = img.getbbox()
    return img.crop(bb) if bb else img


def main(spec_path, out_dir):
    from rembg import remove, new_session
    spec = json.loads(Path(spec_path).read_text(encoding='utf-8'))
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    index_path = out / 'stickers.json'
    index = json.loads(index_path.read_text(encoding='utf-8')) if index_path.exists() else {}
    sess = new_session('isnet-anime')
    for s in spec:
        im = Image.open(s['src']).convert('RGB')
        if s.get('crop'):
            im = im.crop(tuple(s['crop']))
        if s.get('upscale'):
            im = im.resize((im.width * s['upscale'], im.height * s['upscale']), Image.LANCZOS)
        if s.get('already_transparent'):
            cut = Image.open(s['src']).convert('RGBA')
        else:
            # 색은 원본 그대로, 알파(모양)만 rembg 마스크에서 가져온다
            mask = remove(im, session=sess, only_mask=True).convert('L')
            cut = im.convert('RGBA'); cut.putalpha(mask)
        if s.get('erase'):  # 잘라낸 뒤 남은 배경 조각 지우기: 사각형 [x0,y0,x1,y1] 또는 다각형 [[x,y],...] (크롭 기준)
            from PIL import ImageDraw
            a = cut.getchannel('A'); d = ImageDraw.Draw(a)
            for e in s['erase']:
                if isinstance(e[0], list):
                    d.polygon([tuple(pt) for pt in e], fill=0)
                else:
                    d.rectangle(e, fill=0)
            cut.putalpha(a)
        cut = clean_alpha(cut.convert('RGBA'), s.get('keep_ratio', 0.03))
        cut.save(out / f"{s['id']}.png")
        index[s['id']] = {'tags': s.get('tags', []), 'desc': s.get('desc', ''), 'size': cut.size,
                          'kind': s.get('kind', 'full')}
        print('ok', s['id'], cut.size)
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
