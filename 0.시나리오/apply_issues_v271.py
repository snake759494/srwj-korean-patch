# -*- coding: utf-8 -*-
"""이슈 #30·#45 추가 반영 — v2.7.1

  python apply_issues_v271.py            # 미리보기
  python apply_issues_v271.py --write    # 반영

#30  23화 아크엔젤 루트, 캐서린이 격추되지 않았는데도 쟝갈 증원 시
     '캐서린은 후퇴했나 보군' 이 나왔다.
     v2.7 에서는 게임 쪽 이벤트 조건이라고 보고 닫았는데, 다시 파 보니
     **조건별 두 판본의 번역이 서로 맞바뀌어** 있었다.

       t280 원문 わかっておる。…            (캐서린이 그 자리에 있을 때)
       t281 원문 行き違いでカザリーンは撤退したか。… (캐서린이 이미 빠졌을 때)

     번역이 t280 에 '캐서린은 후퇴했나', t281 에 '알고 있네' 를 붙여 놓아
     캐서린이 살아 있는데도 후퇴했다는 대사가 떴다. 두 턴을 맞바꾼다.
     (전 35,268턴을 같은 기준으로 훑었고 뒤바뀐 쌍은 이 하나뿐이었다.)

#45  32화, 카티아가 토우야에게만 '그렇습니다' 로 답하고 있었다.
     같은 장면의 테니아 판본은 반말, 멜루아 판본은 존댓말로 원문대로인데
     카티아 판본만 어긋나 있었다.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(HERE, 'srwj_matched_all_0625.xlsx')
WRITE = '--write' in sys.argv
log = []

SWAP = [(12349, 12350, '#30',
         't280 은 캐서린이 그 자리에 있는 판본(원문 わかっておる), '
         't281 은 캐서린이 빠진 판본(원문 行き違いでカザリーンは撤退したか)')]

FIX = [(17781, '... 그렇습니다', '... 응', '#45',
        '원문 ・・・はい — 카티아는 토우야에게 반말을 쓴다 '
        '(같은 장면 테니아 판본은 반말, 멜루아 판본은 존댓말로 원문대로다)')]


def main():
    from openpyxl import load_workbook
    wb = load_workbook(XLSX)
    ws = wb[wb.sheetnames[0]]
    n = 0
    for a, b, iss, why in SWAP:
        ca, cb = ws.cell(row=a, column=10), ws.cell(row=b, column=10)
        va, vb = str(ca.value or ''), str(cb.value or '')
        log.append((iss, 'R%d ↔ R%d' % (a, b), va + '  ||  ' + vb, vb + '  ||  ' + va, why))
        if WRITE:
            ca.value, cb.value = vb, va
        n += 2
    for row, old, new, iss, why in FIX:
        c = ws.cell(row=row, column=10)
        v = str(c.value or '')
        if old in v:
            nv = v.replace(old, new)
            log.append((iss, 'R%d' % row, v, nv, why))
            if WRITE:
                c.value = nv
            n += 1
        else:
            log.append((iss, 'R%d' % row, '(못 찾음) ' + old, repr(v), why))
    if WRITE:
        wb.save(XLSX)
    return n


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print('모드:', '반영(--write)' if WRITE else '미리보기')
    n = main()
    for iss, where, before, after, why in log:
        print('\n[%s] %s — %s' % (iss, where, why))
        print('   - %s' % before.replace('\n', ' ⏎ ')[:200])
        print('   + %s' % after.replace('\n', ' ⏎ ')[:200])
    print('\n총 %d개 턴' % n)
