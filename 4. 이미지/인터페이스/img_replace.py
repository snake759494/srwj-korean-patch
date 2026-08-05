# -*- coding: utf-8 -*-
"""범용 IMG 자산 교체: img_NNNNN_pNNNN.png 형식 PNG 폴더 → ROM
(전투 메시지 등 SCR 없는 단순 행우선 스트립용)

사용법:
  python img_replace.py <rom_in.gba> <rom_out.gba> <한글PNG폴더> [원본PNG폴더]

- PNG 처리 우선순위:
  1) 한글 PNG가 16색 이하 P(인덱스) 모드 → 인덱스를 그대로 보존(권장; 색 변형 없음).
     투명은 PNG의 tRNS, 없으면 인덱스0을 투명으로 간주.
  2) 그 외(RGBA/24bit 등) → 원본(jp) PNG의 16색 팔레트 기준 최근접 색 매핑(폴백).
     이때 배경이 불투명(흰색 등)으로 굳은 파일은 테두리 플러드필(허용오차 48)로 자동 투명화.
- 파일명에서 자산 번호 인식: img_03242_p3237.png → IMG#3242
- 슬롯 초과 시 ROM 끝 여유 공간(0x1800000~)으로 재배치 + 인덱스 갱신.
- 기록 후 라운드트립 디코드 검증 자동.

[중요] 파일명의 _pXXXX는 추출 편의용일 뿐 실제 인게임 팔레트와 다를 수 있다.
색을 맞춰 보려면 bm_extract.py로 올바른 팔레트(pal_override.json)를 적용해 추출하라.
삽입은 인덱스만 보존되면 게임이 실제 팔레트로 정확히 렌더하므로 색 걱정이 없다.
"""
import sys, os, re, json, struct
from collections import deque, Counter
from PIL import Image
import scn_title_lib as L

_HERE = os.path.dirname(os.path.abspath(__file__))
_OVERRIDE = {}
_op = os.path.join(_HERE, 'pal_override.json')
if os.path.exists(_op):
    _OVERRIDE = {int(k): tuple(v) for k, v in json.load(open(_op, encoding='utf-8')).items() if k.isdigit()}


_REFPAL = {}
_rp = os.path.join(_HERE, 'ref_palettes.json')
if os.path.exists(_rp):
    _REFPAL = {int(k): v for k, v in json.load(open(_rp, encoding='utf-8')).items() if k.isdigit()}


def _ref_from_png_or_table(jp_dir, fname, ai):
    """(16색 팔레트, 투명비율) — 원본(일본어) PNG가 있으면 그것을, 없으면 ref_palettes.json.

    원본 PNG는 게임 그래픽이라 저장소에 없다. 삽입에 실제로 필요한 값은
    16색 RGB 표와 투명(인덱스0) 비율뿐이므로 표만 남겨 두고 그대로 쓴다.
    (make_ref_palettes.py 로 생성)
    """
    p = os.path.join(jp_dir, fname) if jp_dir else None
    if p and os.path.exists(p):
        im = Image.open(p)
        pal = im.getpalette() or []
        if len(pal) >= 48:
            raw = im.tobytes()
            return ([tuple(pal[i * 3:i * 3 + 3]) for i in range(16)],
                    sum(1 for v in raw if v == 0) / len(raw))
    e = _REFPAL.get(ai)
    if e:
        return ([tuple(c) for c in e['pal']], e['zfrac'])
    return (None, 0.0)


def _plt_bank_from_rom(rom, plt_i, bank):
    o = L.asset_off(rom, plt_i)
    if rom[o:o + 3] != b'PLT':
        return None
    base = bank * 16
    return [((struct.unpack_from('<H', rom, o + 8 + (base + k) * 2)[0] & 31) << 3,
             ((struct.unpack_from('<H', rom, o + 8 + (base + k) * 2)[0] >> 5) & 31) << 3,
             ((struct.unpack_from('<H', rom, o + 8 + (base + k) * 2)[0] >> 10) & 31) << 3) for k in range(16)]


def fix_bg(ko, jp_zero_frac):
    W, H = ko.size
    px = ko.load()
    n = W * H
    kz = sum(1 for y in range(H) for x in range(W) if px[x, y][3] < 128) / n
    if kz >= jp_zero_frac - 0.10:
        return  # 투명도 정상
    c = Counter()
    for x in range(W):
        c[px[x, 0][:3]] += 1; c[px[x, H - 1][:3]] += 1
    for y in range(H):
        c[px[0, y][:3]] += 1; c[px[W - 1, y][:3]] += 1
    bg = c.most_common(1)[0][0]
    def near(p):
        return abs(p[0] - bg[0]) <= 48 and abs(p[1] - bg[1]) <= 48 and abs(p[2] - bg[2]) <= 48
    seen = [[False] * W for _ in range(H)]
    q = deque()
    for x in range(W):
        for y in (0, H - 1):
            if px[x, y][3] >= 128 and near(px[x, y][:3]):
                seen[y][x] = True; q.append((x, y))
    for y in range(H):
        for x in (0, W - 1):
            if px[x, y][3] >= 128 and near(px[x, y][:3]) and not seen[y][x]:
                seen[y][x] = True; q.append((x, y))
    while q:
        x, y = q.popleft()
        px[x, y] = (0, 0, 0, 0)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and not seen[ny][nx] \
               and px[nx, ny][3] >= 128 and near(px[nx, ny][:3]):
                seen[ny][nx] = True; q.append((nx, ny))


def _alpha_index_from_indexed(im):
    """P 모드 이미지에서 (인덱스맵, 투명인덱스집합) 반환. 투명은 tRNS 또는 관례상 0."""
    idx = list(im.getdata())
    transp = set()
    tr = im.info.get('transparency')
    if isinstance(tr, int):
        transp.add(tr)
    elif isinstance(tr, (bytes, bytearray)):
        for i, a in enumerate(tr):
            if a < 128:
                transp.add(i)
    return idx, transp


def apply(rom, ko_dir, jp_dir, verbose=True):
    """한글 PNG 폴더 → ROM.
    우선순위 1) ko PNG가 16색 이하 P 모드 → 인덱스 직접 보존(권장; 색 변형 없음).
              2) 그 외 → 원본(jp) PNG의 16색 팔레트 기준 최근접 색 매핑(폴백)."""
    nrel = 0
    for f in sorted(os.listdir(ko_dir)):
        m = re.match(r'img_(\d+)', f)
        if not m or not f.endswith('.png'):
            continue
        ai = int(m.group(1))
        img, *_ = L.ecd_decode(bytes(rom), ai)
        assert img[:3] == b'IMG', f'{f}: IMG 자산 아님'
        tw, th = img[5], img[6]
        ko_raw = Image.open(os.path.join(ko_dir, f))
        if (ko_raw.width, ko_raw.height) != (tw * 8, th * 8):
            raise SystemExit(f'{f}: 크기 {ko_raw.size} != ROM {(tw*8, th*8)}')

        tiles = bytearray(tw * th * 32)
        mode_used = ''
        W = tw * 8

        # --- 경로 1a: P 모드 + 16색 → 인덱스 그대로 보존 ---
        #   단, PNG 팔레트가 '기준 팔레트와 같은 순서'일 때만 보존한다.
        #   기준 = (교정자산) 게임 PLT, (그 외) 일본어 원본 PNG 팔레트.
        #   편집기가 팔레트 순서를 바꿔 저장한 경우(밀림/재정렬) 보존하면 색이 깨지므로
        #   색 매핑 경로로 넘긴다. (이것이 예전 동작과 호환되는 안전한 처리)
        if ko_raw.mode == 'P':
            idx, transp = _alpha_index_from_indexed(ko_raw)
            within16 = (max(idx) if idx else 0) <= 15
            palette_ok = within16
            if within16:
                # 기준 팔레트 결정
                ref_pal = None
                if ai in _OVERRIDE:
                    ref_pal = _plt_bank_from_rom(rom, _OVERRIDE[ai][0], _OVERRIDE[ai][1])
                else:
                    ref_pal, _ = _ref_from_png_or_table(jp_dir, f, ai)
                pp = ko_raw.getpalette() or []
                png_cols = [tuple(pp[i * 3:i * 3 + 3]) for i in range(16)] if len(pp) >= 48 else []
                if not ref_pal or not png_cols:
                    palette_ok = False
                else:
                    # 사용된 불투명 인덱스의 색이 기준 팔레트와 같은 위치인지 확인
                    used_nonzero = set(idx) - transp
                    for k in used_nonzero:
                        if k >= 16 or png_cols[k] != ref_pal[k]:
                            palette_ok = False
                            break
            if palette_ok:
                for t in range(tw * th):
                    bx, by = (t % tw) * 8, (t // tw) * 8
                    p = [[0] * 8 for _ in range(8)]
                    for yy in range(8):
                        for xx in range(8):
                            v = idx[(by + yy) * W + (bx + xx)]
                            p[yy][xx] = 0 if v in transp else v
                    L.tile_put(tiles, t, p)
                mode_used = '인덱스보존'

        # --- 경로 1b: RGBA/24bit지만 실제 색이 16색 이하 → 교정 팔레트로 인덱스 환원 ---
        if not mode_used and ai in _OVERRIDE:
            ref = _plt_bank_from_rom(rom, _OVERRIDE[ai][0], _OVERRIDE[ai][1])
            ko = ko_raw.convert('RGBA')
            px = ko.load()
            colors = set()
            for yy in range(ko.height):
                for xx in range(ko.width):
                    r, g, b, a = px[xx, yy]
                    if a >= 128:
                        colors.add((r, g, b))
            # 불투명 색이 15가지 이하이고 모두 교정 팔레트(1~15)에 정확히 존재하면 인덱스 환원
            pal_rgb = {ref[k]: k for k in range(1, 16)}
            if ref and len(colors) <= 15 and all(c in pal_rgb for c in colors):
                # 가장자리에서 가장 많이 쓰인 색 = 배경. 편집기가 투명을 불투명색(빨강 등)으로
                # 칠해버린 경우를 대비해, 가장자리 최빈색이면 투명(0)으로 보낸다.
                W2, H2 = ko.width, ko.height
                edge = Counter()
                for xx in range(W2):
                    for yy in (0, H2 - 1):
                        r, g, b, a = px[xx, yy]
                        if a >= 128:
                            edge[(r, g, b)] += 1
                for yy in range(H2):
                    for xx in (0, W2 - 1):
                        r, g, b, a = px[xx, yy]
                        if a >= 128:
                            edge[(r, g, b)] += 1
                bg_col = edge.most_common(1)[0][0] if edge else None
                for t in range(tw * th):
                    bx, by = (t % tw) * 8, (t // tw) * 8
                    p = [[0] * 8 for _ in range(8)]
                    for yy in range(8):
                        for xx in range(8):
                            r, g, b, a = px[bx + xx, by + yy]
                            if a < 128 or (r, g, b) == bg_col:
                                p[yy][xx] = 0
                            else:
                                p[yy][xx] = pal_rgb[(r, g, b)]
                    L.tile_put(tiles, t, p)
                mode_used = '인덱스환원(교정팔레트)'

        # --- 경로 2: 색 최근접 매핑(폴백) ---
        if not mode_used:
            # 기준 팔레트 결정 우선순위:
            #  (a) pal_override.json에 교정 팔레트가 있으면 ROM에서 그 PLT/뱅크를 사용
            #  (b) 없으면 원본(jp) PNG 팔레트
            ref = None
            ov = _OVERRIDE.get(ai)
            if ov is not None:
                ref = _plt_bank_from_rom(rom, ov[0], ov[1])
            if ref is None:
                ref, jz = _ref_from_png_or_table(jp_dir, f, ai)
                if ref is None:
                    raise SystemExit(f'{f}: 기준 팔레트가 없어 매핑 불가 '
                                     f'(원본 PNG 또는 ref_palettes.json 필요)')
            else:
                jz = 0.0  # 교정 팔레트 사용 시 배경 휴리스틱 생략(투명은 알파로만 판단)
            ko = ko_raw.convert('RGBA')
            if jz:
                fix_bg(ko, jz)
            W2, H2 = ko.size
            px = ko.load()
            cache = {}

            # 교정 자산: ROM 팔레트의 idx0 '실제 색'을 알고 있으므로, 그 색과 일치하는
            #   픽셀은 idx0(투명)으로, 나머지는 1~15 최근접으로 매핑한다.
            #   (플러드필 같은 위험한 휴리스틱 없이, 색만으로 정확히 구분 → 글자 외곽선 보존)
            if ov is not None:
                idx0_col = ref[0]  # 게임 팔레트의 투명색(예: 144,72,144)
                # 추출기가 idx0을 마젠타(255,0,255)로 표시했을 수도 있으니 둘 다 투명 취급
                transparent_rgb = {idx0_col, (255, 0, 255)}
                choices = list(range(1, 16))
                for t in range(tw * th):
                    bx, by = (t % tw) * 8, (t // tw) * 8
                    p = [[0] * 8 for _ in range(8)]
                    for yy in range(8):
                        for xx in range(8):
                            r, g, b, a = px[bx + xx, by + yy]
                            if a < 128 or (r, g, b) in transparent_rgb:
                                p[yy][xx] = 0
                                continue
                            v = cache.get((r, g, b))
                            if v is None:
                                v = min(choices, key=lambda k: (ref[k][0]-r)**2 + (ref[k][1]-g)**2 + (ref[k][2]-b)**2)
                                cache[(r, g, b)] = v
                            p[yy][xx] = v
                    L.tile_put(tiles, t, p)
                mode_used = '색매핑(교정팔레트)'
            else:
                # 비교정 자산: 기존 동작 그대로(0~15 전체 최근접, 투명은 알파만)
                for t in range(tw * th):
                    bx, by = (t % tw) * 8, (t // tw) * 8
                    p = [[0] * 8 for _ in range(8)]
                    for yy in range(8):
                        for xx in range(8):
                            r, g, b, a = px[bx + xx, by + yy]
                            if a < 128:
                                continue
                            v = cache.get((r, g, b))
                            if v is None:
                                v = min(range(16), key=lambda k: (ref[k][0]-r)**2 + (ref[k][1]-g)**2 + (ref[k][2]-b)**2)
                                cache[(r, g, b)] = v
                            p[yy][xx] = v
                    L.tile_put(tiles, t, p)
                mode_used = '색매핑'

        total, rel = L.ecd_write(rom, ai, L.img_build(tw, th, tiles), 8)
        nrel += rel
        # 자체 점검: 새로 쓴 타일의 투명(idx0) 비율이 80%를 넘으면 매핑 오류 의심
        zero = sum(1 for b in tiles for v in (b & 0xF, b >> 4) if v == 0)
        zfrac = zero / (len(tiles) * 2)
        warn = '  ⚠ 투명비율 높음(매핑 의심)' if zfrac > 0.80 else ''
        if verbose:
            print(f'IMG#{ai}: {total}B {"재배치" if rel else "제자리"} [{mode_used}]{warn}')
    return nrel


def main():
    rom_in, rom_out, ko_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    jp_dir = sys.argv[4] if len(sys.argv) > 4 else None
    rom = bytearray(open(rom_in, 'rb').read())
    nrel = apply(rom, ko_dir, jp_dir)
    open(rom_out, 'wb').write(rom)
    print(f'저장: {rom_out} (재배치 {nrel}건)')
