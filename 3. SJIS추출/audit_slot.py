# -*- coding: utf-8 -*-
"""시스템 텍스트 슬롯 초과(=재배치 유발) 전수 검사

왜 보는가
--------
번역이 원문 슬롯(+뒤따르는 0 패딩)에 안 들어가면 build_patch 가 그 문자열을
자유공간으로 **재배치**하고, ROM을 훑어 찾은 포인터를 새 주소로 고쳐 쓴다.

검증 결과(2026-08): 재배치 대상 255건 전부에 대해 ROM 전역 참조 수와
find_pointers 결과가 일치했다 — 즉 **놓친 포인터는 없고 재배치는 정상 동작한다.**
따라서 슬롯 초과 자체는 대사 짤림의 원인이 아니다.
(짤림의 실제 원인은 줄 폭이었다. 0.시나리오/audit_linewidth.py 참고)

이 도구는 재배치가 몇 건 일어나는지, 어떤 문자열이 자유공간으로 옮겨지는지
파악하는 용도다. 재배치가 적을수록 ROM 구조 변경이 작아 안전하다.

사용법:
  python audit_slot.py [--csv 결과.csv]
"""
import sys, os, json, csv, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import srwj_codec as codec        # 한글 → 한자 폰트코드 인코더 (build_patch 와 동일)
ROM = os.path.join(HERE, '..', '0.시나리오', 'Super Robot Taisen J (Japan).gba')


def main():
    csv_path = sys.argv[sys.argv.index('--csv') + 1] if '--csv' in sys.argv else None
    ents = json.load(open(os.path.join(HERE, 'translations.json'),
                          encoding='utf-8'))['entries']
    ents = sorted(ents, key=lambda x: int(x['off'], 16))
    rom = open(ROM, 'rb').read()

    rows = []
    hist = collections.Counter()
    for i, e in enumerate(ents):
        off, L, ko = int(e['off'], 16), e['len'], (e.get('ko') or '')
        if not ko.strip():
            continue
        nxt = int(ents[i + 1]['off'], 16) if i + 1 < len(ents) else off + L + 4
        p = off + L
        while p < nxt and rom[p] == 0x00:
            p += 1
        avail = p - off
        enc, bad = codec.encode(ko)
        if bad:
            continue                  # 인코딩 불가 문자는 별도 검사 대상
        # build_patch 조건: len(enc) < avail 이어야 제자리
        need = len(enc) - (avail - 1)      # 몇 바이트 줄여야 제자리에 들어가는지
        hist[max(0, need)] += 1
        if need > 0:
            rows.append(dict(off=e['off'], slot=avail, enc=len(enc),
                             over_bytes=need, over_chars=(need + 1) // 2,
                             jp=e['jp'].replace('#|', '⏎'),
                             ko=ko.replace('#|', '⏎')))

    print('=' * 70)
    print(f'슬롯 초과 검사  ({len(ents):,}항목)')
    print('=' * 70)
    print('  줄여야 할 바이트 수 분포 (0 = 제자리, 안전):')
    for k in sorted(hist):
        tag = '  ← 재배치 발생' if k > 0 else '  (안전)'
        print(f'      {k:3}B  {hist[k]:5,}건{tag}')
    print(f'\n  재배치 유발 항목 : {len(rows)}건')
    print('  → 포인터는 모두 갱신되므로 표시 자체는 정상. 구조 변경 규모의 지표다.')

    rows.sort(key=lambda r: -r['over_bytes'])
    print(f'\n  많이 넘치는 순 상위 {min(30, len(rows))}건')
    for r in rows[:30]:
        print(f"    {r['off']}  슬롯{r['slot']}B  번역{r['enc']}B  "
              f"{r['over_chars']}글자 줄이면 됨")
        print(f"        JP {r['jp']}")
        print(f"        KO {r['ko']}")

    if csv_path and rows:
        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as fp:
            w = csv.DictWriter(fp, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
        print(f'\n  상세: {csv_path}')


if __name__ == '__main__':
    main()
