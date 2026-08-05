# -*- coding: utf-8 -*-
"""시스템 텍스트(메뉴·승패조건·유닛정보) 표시폭 초과 전수 검사

이 구간은 대사창과 달리 **항목마다 표시 영역이 따로** 정해져 있다.
그래서 전역 최대치가 아니라 **그 항목의 일본어 원문 폭**을 상한으로 본다.
원문보다 넓으면 잘리거나(뒤가 사라짐) 통째로 안 그려진다.
  실제 사례: 이슈 #17 '소스케…격추' 조건문 — 원문 19칸인데 번역 22칸 → 미표시

폭 계산은 게임 렌더 기준(전각/반각 모두 1칸)이며,
줄바꿈 제어(#|)가 있으면 줄별로 나눠 각각 비교한다.

사용법:
  python audit_uiwidth.py [--csv 결과.csv] [--margin N]
     --margin N : 원문보다 N칸까지는 허용 (기본 0)
"""
import sys, os, json, csv, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
KOREA_TXT = os.path.join(HERE, '..', '0.시나리오', 'korea2350.txt')

# 화면에 글자로 그려지지 않는 제어 시퀀스 — 폭 계산에서 뺀다
CTRL = re.compile(r'#\||%[-0-9]*[sd]|&[A-Za-z]')


def cells(s):
    """실제로 그려지는 칸 수."""
    return len(CTRL.sub('', s))


def lines_of(s):
    return s.split('#|')


def main():
    csv_path = sys.argv[sys.argv.index('--csv') + 1] if '--csv' in sys.argv else None
    margin = int(sys.argv[sys.argv.index('--margin') + 1]) if '--margin' in sys.argv else 0

    d = json.load(open(os.path.join(HERE, 'translations.json'), encoding='utf-8'))
    ent = d['entries']
    ko_ok = set(open(KOREA_TXT, encoding='utf-8').read().replace('\n', '').replace('\r', ''))

    over, badchar, linediff = [], [], []
    diff_hist = collections.Counter()

    for i, e in enumerate(ent):
        jp, ko = e.get('jp') or '', e.get('ko') or ''
        if not ko.strip():
            continue
        jl, kl = lines_of(jp), lines_of(ko)
        if len(jl) != len(kl):
            linediff.append(dict(i=i, off=e['off'], jp_lines=len(jl),
                                 ko_lines=len(kl), jp=jp, ko=ko))
        for k in range(max(len(jl), len(kl))):
            jw = cells(jl[k]) if k < len(jl) else 0
            kw = cells(kl[k]) if k < len(kl) else 0
            diff_hist[kw - jw] += 1
            if kw > jw + margin:
                over.append(dict(i=i, off=e['off'], line=k + 1,
                                 jp_w=jw, ko_w=kw, over=kw - jw,
                                 jp=jp.replace('#|', '⏎'), ko=ko.replace('#|', '⏎')))
        bad = [c for c in ko if 0xAC00 <= ord(c) <= 0xD7A3 and c not in ko_ok]
        bad += [c for c in ko if 0x3130 <= ord(c) <= 0x318F]
        if bad:
            badchar.append(dict(i=i, off=e['off'], chars=''.join(sorted(set(bad))),
                                jp=jp, ko=ko))

    print('=' * 70)
    print(f'시스템 텍스트 표시폭 검사  ({len(ent):,}항목)')
    print('=' * 70)
    print('  번역폭 − 원문폭 분포:')
    tot = sum(diff_hist.values())
    for dd in sorted(diff_hist):
        mark = '  ← 초과' if dd > margin else ''
        print(f'      {dd:+4}칸 {diff_hist[dd]:6,} ({diff_hist[dd]*100/tot:5.2f}%){mark}')
    print(f'\n  폭 초과       : {len(over)}건')
    print(f'  줄 수 불일치  : {len(linediff)}건')
    print(f'  못 쓰는 문자  : {len(badchar)}건')

    over.sort(key=lambda r: -r['over'])
    if over:
        print(f'\n  [폭 초과] 큰 순서 상위 {min(40, len(over))}건')
        for r in over[:40]:
            print(f"    +{r['over']}칸 ({r['jp_w']}→{r['ko_w']})  {r['off']}")
            print(f"        JP {r['jp']}")
            print(f"        KO {r['ko']}")
    if linediff:
        print(f'\n  [줄 수 불일치] {min(10, len(linediff))}건')
        for r in linediff[:10]:
            print(f"    {r['off']}  {r['jp_lines']}줄→{r['ko_lines']}줄")
            print(f"        JP {r['jp']}"); print(f"        KO {r['ko']}")
    if badchar:
        print(f'\n  [못 쓰는 문자] {len(badchar)}건')
        for r in badchar[:20]:
            print(f"    {r['off']} '{r['chars']}'  {r['ko']}")

    if csv_path:
        for tag, rows in (('over', over), ('linediff', linediff), ('badchar', badchar)):
            if not rows:
                continue
            p = csv_path.replace('.csv', f'_{tag}.csv')
            with open(p, 'w', encoding='utf-8-sig', newline='') as fp:
                w = csv.DictWriter(fp, fieldnames=list(rows[0]))
                w.writeheader(); w.writerows(rows)
            print(f'  상세: {p}')


if __name__ == '__main__':
    main()
