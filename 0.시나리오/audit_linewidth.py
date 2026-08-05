# -*- coding: utf-8 -*-
"""대사 짤림 전수 검사 — 대사창 폭 초과 / 못 쓰는 문자

짤림의 두 원인을 패치 ROM에서 직접 확인한다.

  (1) 폭 초과   — 한 줄이 대사창 칸수를 넘으면 그 줄이 잘리거나 통째로 안 나온다.
                  상한은 추정하지 않고 **원본 일본어의 실측 최대폭**을 쓴다.
                  화면상 첫 줄에는 '화자명「' 이 앞에 붙으므로 그만큼 좁다.
  (2) 못 쓰는 문자 — 폰트에 없는 글자(KS X 1001 2350자 밖·낱자모)는 빈칸으로 나온다.

변수 ①②③④⑤⑥ 는 실행 중 이름으로 치환되므로 '가장 긴 치환값' 기준으로 환산한다.

사용법:
  python audit_linewidth.py <원본.gba> <한글패치.gba> [--csv 결과.csv]
"""
import sys, os, csv, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import srwj_decode as D
import srwj_parser as P

# ── 변수 치환 실측 길이 (남주/여주/기체 분기 중 최대) ────────────────
#  ①③ 이름 토우야·칼비나(3)  ② 성 시운(2)·크란쥬(3)
#  ④ 풀네임 '칼비나 크란쥬'(7)  ⑤ 기체 벨제루트(4)·그랑티드(4)·B・브리간디(6)
VAR_LEN = {'①': 3, '②': 3, '③': 3, '④': 7, '⑤': 6, '⑥': 6}

# ── 폰트가 가진 글자(2350자)는 korea2350.txt 가 정본 ────────────────
KOREA_TXT = os.path.join(HERE, 'korea2350.txt')


def rendered_width(s: str) -> int:
    return sum(VAR_LEN.get(c, 1) for c in s)


def jp_lines(rom):
    """원본: 사전 그대로 디코딩."""
    dic = D.Dictionary(rom)
    for m in D.find_all_dialogue_blocks(rom):
        info = P.parse_dialogue_block(rom, m['rom_addr'], m['block_size'], dic)
        for d in info['dialogues']:
            for ti, t in enumerate(d['turns']):
                yield m['archive_idx'], d['idx'], ti, t['cid'], t['decoded'].split('\n')


def kr_lines(rom, kanji2ko):
    """패치본: 사전 디코딩 결과의 한자를 한글로 되돌린다(patch_all.verify 와 동일)."""
    dic = D.Dictionary(rom)
    idx = D.load_archive_index(rom)
    for m in D.find_all_dialogue_blocks(
            open(os.path.join(HERE, 'Super Robot Taisen J (Japan).gba'), 'rb').read()):
        ai = m['archive_idx']
        addr = D.IDX_BASE + idx[ai]
        ptrs = P.read_dialogue_pointers(rom, addr)
        info = P.parse_dialogue_block(rom, addr, ptrs[-1], dic)
        for d in info['dialogues']:
            for ti, t in enumerate(d['turns']):
                out = []
                for line in t['lines']:
                    s = ''
                    for code, w in D.tokenize(line):
                        s += ''.join(kanji2ko.get(c, c) for c in dic.decode(code))
                    out.append(s)
                yield ai, d['idx'], ti, t['cid'], out


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    jp_path, kr_path = sys.argv[1], sys.argv[2]
    csv_path = sys.argv[sys.argv.index('--csv') + 1] if '--csv' in sys.argv else None

    # ── 1) 원본에서 대사창 실측 상한 구하기 ──────────────────────
    jp = D.load_rom(jp_path)
    first = collections.Counter()
    rest = collections.Counter()
    for ai, di, ti, cid, lines in jp_lines(jp):
        for i, ln in enumerate(lines):
            w = rendered_width(ln)
            if w > 30:          # arc191 의 깨진 더미 데이터 제외
                continue
            (first if i == 0 else rest)[w] += 1
    JP_FIRST_MAX, JP_REST_MAX = max(first), max(rest)
    print('=' * 68)
    print('1) 원본 일본어 실측 — 대사창 상한의 근거')
    print('=' * 68)
    print(f'   첫 줄      최대 {JP_FIRST_MAX}칸   (화면에는 앞에 화자명「 이 더 붙음)')
    print(f'   둘째 줄~   최대 {JP_REST_MAX}칸')
    print(f'   → 판정 기준: 첫 줄 {JP_FIRST_MAX}칸 / 나머지 {JP_REST_MAX}칸 초과 시 짤림 후보')

    # ── 2) 폰트 보유 글자 집합 ────────────────────────────────
    ko_ok = set(open(KOREA_TXT, encoding='utf-8').read().replace('\n', '').replace('\r', ''))

    # ── 3) 패치 ROM 전수 검사 ─────────────────────────────────
    import srwj_codec as C
    codec = C.HangulCodec(jp, KOREA_TXT, os.path.join(HERE, 'japan2350.txt'), [])
    kanji2ko = {v: k for k, v in codec.ko2kanji.items()}

    kr = D.load_rom(kr_path)
    over, badchar = [], []
    kfirst, krest = collections.Counter(), collections.Counter()
    nline = 0
    for ai, di, ti, cid, lines in kr_lines(kr, kanji2ko):
        for i, ln in enumerate(lines):
            nline += 1
            w = rendered_width(ln)
            (kfirst if i == 0 else krest)[w] += 1
            lim = JP_FIRST_MAX if i == 0 else JP_REST_MAX
            if w > lim:
                over.append(dict(archive=ai, dlg=di, turn=ti, cid=cid,
                                 line=i + 1, of=len(lines), width=w,
                                 limit=lim, text=ln))
            bad = [c for c in ln
                   if 0xAC00 <= ord(c) <= 0xD7A3 and c not in ko_ok]
            bad += [c for c in ln if 0x3130 <= ord(c) <= 0x318F]   # 낱자모
            if bad:
                badchar.append(dict(archive=ai, dlg=di, turn=ti, cid=cid,
                                    line=i + 1, of=len(lines),
                                    chars=''.join(sorted(set(bad))), text=ln))

    print()
    print('=' * 68)
    print(f'2) 한글 패치 전수 검사  (총 {nline:,}줄)')
    print('=' * 68)
    print(f'   폭 초과      : {len(over)}건')
    print(f'   못 쓰는 문자 : {len(badchar)}건')
    print(f'   관측 최대폭  : 첫 줄 {max(kfirst)}칸 / 나머지 {max(krest)}칸')

    for name, rows in (('폭 초과', over), ('못 쓰는 문자', badchar)):
        if not rows:
            continue
        print(f'\n   [{name}] archive 별:',
              ', '.join(f'{a}:{c}' for a, c in
                        collections.Counter(r['archive'] for r in rows).most_common(20)))
        for r in rows[:30]:
            extra = f"{r['width']}>{r['limit']}" if 'width' in r else f"'{r['chars']}'"
            print(f"     arc{r['archive']:3} d{r['dlg']:3} t{r['turn']:3} "
                  f"L{r['line']}/{r['of']}  {extra}  {r['text']}")

    if csv_path:
        for tag, rows in (('over', over), ('badchar', badchar)):
            if not rows:
                continue
            p = csv_path.replace('.csv', f'_{tag}.csv')
            with open(p, 'w', encoding='utf-8-sig', newline='') as fp:
                w = csv.DictWriter(fp, fieldnames=list(rows[0]))
                w.writeheader(); w.writerows(rows)
            print(f'   상세: {p}')


if __name__ == '__main__':
    main()
