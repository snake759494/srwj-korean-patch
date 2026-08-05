# -*- coding: utf-8 -*-
"""전투 대사 짤림 전수 검사 — 대사창 폭 초과 / 줄 수 초과 / 못 쓰는 문자

판정 기준은 추정하지 않고 **같은 블록의 일본어 원문 실측 최대치**를 쓴다.
(전투 대사창은 시나리오 대사창과 크기가 다르므로 따로 잰다.)

  · 폭 초과      : 한 줄이 원문 최대폭을 넘으면 그 줄이 잘리거나 안 나온다
  · 줄 수 초과   : 4줄 이상이면 화자가 도몬으로 고정되는 알려진 버그
  · 못 쓰는 문자 : 폰트 2350자(KS X 1001) 밖 글자·낱자모 → 빈칸

사용법:
  python audit_battle_width.py [--csv 결과.csv]
"""
import sys, os, json, csv, collections

HERE = os.path.dirname(os.path.abspath(__file__))
KOREA_TXT = os.path.join(HERE, '..', '0.시나리오', 'korea2350.txt')

VAR_LEN = {'①': 3, '②': 3, '③': 3, '④': 7, '⑤': 6, '⑥': 6}
MAX_LINES = 3          # 4줄 이상 = 도몬 버그


def width(s):
    return sum(VAR_LEN.get(c, 1) for c in s)


def main():
    csv_path = sys.argv[sys.argv.index('--csv') + 1] if '--csv' in sys.argv else None
    d = json.load(open(os.path.join(HERE, 'battle_dialogue.json'), encoding='utf-8'))
    ent = d['entries']
    ko_ok = set(open(KOREA_TXT, encoding='utf-8').read().replace('\n', '').replace('\r', ''))

    # ── 1) 원문 실측 상한 ────────────────────────────────────
    jw = collections.Counter()
    jl = collections.Counter()
    for e in ent:
        lines = e['jp'].split('\n')
        jl[len(lines)] += 1
        for ln in lines:
            jw[width(ln)] += 1
    JP_MAX_W = max(jw)
    JP_MAX_L = max(jl)
    print('=' * 68)
    print('1) 전투 대사 원문(일본어) 실측')
    print('=' * 68)
    print('   줄 폭 분포:')
    tot = sum(jw.values()); acc = 0
    for w in sorted(jw):
        acc += jw[w]
        print(f'      {w:3}칸 {jw[w]:6,}   누적 {acc*100/tot:6.2f}%')
    print(f'   줄 수 분포: ' + ', '.join(f'{k}줄 {v:,}건' for k, v in sorted(jl.items())))
    print(f'\n   → 원문 최대 폭 {JP_MAX_W}칸 / 최대 {JP_MAX_L}줄')

    # ── 2) 번역 검사 ────────────────────────────────────────
    over, toolong, badchar = [], [], []
    kw = collections.Counter()
    for i, e in enumerate(ent):
        ko = e.get('ko') or ''
        if not ko.strip():
            continue
        lines = ko.split('\n')
        for j, ln in enumerate(lines):
            w = width(ln)
            kw[w] += 1
            if w > JP_MAX_W:
                over.append(dict(i=i, blk=e['blk'], off=e['off'], line=j + 1,
                                 of=len(lines), width=w, limit=JP_MAX_W,
                                 jp=e['jp'].replace('\n', '⏎'), ko=ko.replace('\n', '⏎')))
        if len(lines) > MAX_LINES:
            toolong.append(dict(i=i, blk=e['blk'], off=e['off'], lines=len(lines),
                                jp=e['jp'].replace('\n', '⏎'), ko=ko.replace('\n', '⏎')))
        bad = [c for c in ko if 0xAC00 <= ord(c) <= 0xD7A3 and c not in ko_ok]
        bad += [c for c in ko if 0x3130 <= ord(c) <= 0x318F]
        bad += [c for c in ko if 0x3040 <= ord(c) <= 0x30FF]      # 남은 가나
        if bad:
            badchar.append(dict(i=i, blk=e['blk'], off=e['off'],
                                chars=''.join(sorted(set(bad))),
                                jp=e['jp'].replace('\n', '⏎'), ko=ko.replace('\n', '⏎')))

    print()
    print('=' * 68)
    print(f'2) 번역 전수 검사 ({len(ent):,}항목)')
    print('=' * 68)
    print('   번역 줄 폭 분포:')
    tot = sum(kw.values()); acc = 0
    for w in sorted(kw):
        acc += kw[w]
        mark = '  ← 원문 최대 초과' if w > JP_MAX_W else ''
        print(f'      {w:3}칸 {kw[w]:6,}   누적 {acc*100/tot:6.2f}%{mark}')
    print(f'\n   폭 초과      : {len(over)}건')
    print(f'   줄 수 초과   : {len(toolong)}건 (4줄 이상)')
    print(f'   못 쓰는 문자 : {len(badchar)}건')

    for name, rows, key in (('폭 초과', over, 'width'),
                            ('줄 수 초과', toolong, 'lines'),
                            ('못 쓰는 문자', badchar, 'chars')):
        if not rows:
            continue
        print(f'\n   [{name}] 상위 {min(25, len(rows))}건')
        for r in rows[:25]:
            print(f"     #{r['i']:5} blk{r['blk']} {r[key]}")
            print(f"        JP {r['jp']}")
            print(f"        KO {r['ko']}")

    if csv_path:
        for tag, rows in (('over', over), ('toolong', toolong), ('badchar', badchar)):
            if not rows:
                continue
            p = csv_path.replace('.csv', f'_{tag}.csv')
            with open(p, 'w', encoding='utf-8-sig', newline='') as fp:
                w = csv.DictWriter(fp, fieldnames=list(rows[0]))
                w.writeheader(); w.writerows(rows)
            print(f'   상세: {p}')


if __name__ == '__main__':
    main()
