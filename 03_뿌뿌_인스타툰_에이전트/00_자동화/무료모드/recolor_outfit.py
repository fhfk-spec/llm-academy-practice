"""뿌뿌 옷 색 바꾸기 (상의·바지) — 시드 지점에서 검정 윤곽선 안쪽만 칠한다

사용 (코드): recolor_outfit(img, top_seeds, pants_seeds, top_hex, pants_hex)
- top_seeds/pants_seeds: 상의/바지 안쪽 좌표 [(x,y), ...]
- 원래 명암(색연필 질감)을 유지한 채 색만 바꾼다.
"""
import numpy as np
from PIL import Image
import cv2


def _region(rgba, seeds):
    a = np.array(rgba)
    lum = a[..., :3].mean(-1)
    wall = ((lum < 120) | (a[..., 3] < 128)).astype(np.uint8)
    wall = cv2.dilate(wall, np.ones((3, 3), np.uint8))
    free = (1 - wall).astype(np.uint8)
    n, lab = cv2.connectedComponents(free, connectivity=4)
    m = np.zeros(lab.shape, bool)
    for x, y in seeds:
        if lab[y, x]:
            m |= lab == lab[y, x]
    m = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & (a[..., 3] > 0) & (lum >= 120)
    return m


def _paint(arr, m, hexcol):
    t = np.array([int(hexcol[i:i + 2], 16) for i in (1, 3, 5)], float)
    rgb = arr[..., :3].astype(float)
    lum = rgb.mean(-1)
    ref = np.percentile(lum[m], 90) if m.any() else 255
    shade = np.clip(lum / ref, 0.55, 1.08)[..., None]
    new = np.clip(t * shade, 0, 255)
    arr[..., :3] = np.where(m[..., None], new, rgb).astype(np.uint8)


def recolor_outfit(img, top_seeds, pants_seeds, top_hex, pants_hex):
    rgba = img.convert('RGBA')
    arr = np.array(rgba).copy()
    mt = _region(rgba, top_seeds)
    mp = _region(rgba, pants_seeds)
    _paint(arr, mt, top_hex)
    _paint(arr, mp, pants_hex)
    return Image.fromarray(arr, 'RGBA')
