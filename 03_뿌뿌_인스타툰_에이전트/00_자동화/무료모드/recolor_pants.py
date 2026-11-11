"""뿌뿌 바지 색 바꾸기: 회청색 → 하늘색 (스티커 전체 일괄)

사용: python3 recolor_pants.py stickers_in/ stickers_out/ [--hue 205 --sat 3.0 --val 1.12]
- 바지 회청색(색상 190~240°, 채도 0.05~0.4, 밝기 0.45~0.92)만 골라 색상·채도·밝기를 옮긴다.
- 상의(연베이지)는 얼굴 피부색과 거의 같은 색이라 자동으로 분리할 수 없어 그대로 둔다.
"""
import sys, argparse
from pathlib import Path
import numpy as np
from PIL import Image
from matplotlib.colors import rgb_to_hsv, hsv_to_rgb


def recolor(img, hue=205, sat=3.0, val=1.12):
    a = np.array(img.convert('RGBA')).astype(float) / 255
    rgb, al = a[..., :3], a[..., 3]
    hsv = rgb_to_hsv(rgb)
    h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    m = (al > 0) & (h > 190) & (h < 240) & (s > 0.05) & (s < 0.4) & (v > 0.45) & (v < 0.92)
    hsv[..., 0] = np.where(m, hue / 360, hsv[..., 0])
    hsv[..., 1] = np.where(m, np.clip(s * sat, 0, 0.62), s)
    hsv[..., 2] = np.where(m, np.clip(v * val, 0, 0.98), v)
    out = np.dstack([hsv_to_rgb(hsv), al])
    return Image.fromarray((out * 255).round().astype('uint8'), 'RGBA'), int(m.sum())


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--hue', type=float, default=205); ap.add_argument('--sat', type=float, default=3.0)
    ap.add_argument('--val', type=float, default=1.12)
    a = ap.parse_args()
    out = Path(a.dst); out.mkdir(parents=True, exist_ok=True)
    for f in sorted(Path(a.src).glob('*.png')):
        im, n = recolor(Image.open(f), a.hue, a.sat, a.val)
        im.save(out / f.name)
        print(f.name, n)
