# -*- coding: utf-8 -*-
"""참조 팔레트표(ref_palettes.json) 생성기

img_replace.py 의 '색매핑' 경로는 원본(일본어) PNG의 16색 팔레트와
투명(인덱스0) 비율을 기준으로 한글 PNG의 색을 인덱스로 되돌린다.
원본 PNG는 게임 그래픽이라 저장소에 넣지 않으므로, 삽입에 실제로 필요한
정보(16색 RGB 표 + 투명 비율)만 뽑아 JSON으로 남긴다.

사용법(관리자용, 원본 PNG가 있을 때 한 번만):
  python make_ref_palettes.py <폴더명 ...>
    예) python make_ref_palettes.py 전투메시지 인터페이스
"""
import sys, os, re, json
from PIL import Image

KIT = os.path.dirname(os.path.abspath(__file__))


def build(folder):
    jp = os.path.join(KIT, folder, '일본어')
    out = {}
    for f in sorted(os.listdir(jp)):
        m = re.match(r'img_(\d+)_p\d+\.png$', f)
        if not m:
            continue
        im = Image.open(os.path.join(jp, f))
        pal = im.getpalette() or []
        if len(pal) < 48:
            raise SystemExit(f'{f}: 16색 팔레트가 아님')
        raw = im.tobytes()
        out[m.group(1).lstrip('0')] = {
            'pal': [[pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]] for i in range(16)],
            'zfrac': round(sum(1 for v in raw if v == 0) / len(raw), 6),
        }
    path = os.path.join(KIT, folder, 'ref_palettes.json')
    with open(path, 'w', encoding='utf-8') as fp:
        json.dump(out, fp, ensure_ascii=False, indent=1, sort_keys=True)
    print(f'{folder}: {len(out)}개 → {path}')


if __name__ == '__main__':
    for d in (sys.argv[1:] or ['전투메시지', '인터페이스']):
        build(d)
