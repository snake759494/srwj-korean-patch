# -*- coding: utf-8 -*-
"""전투 대사 줄바꿈 재배치 — 대사창 폭을 넘는 줄 고치기

왜 필요한가
------------
전투 대사는 시나리오와 달리 자동 줄바꿈이 없고 번역문의 '\\n' 을 그대로 쓴다.
그런데 삽입할 때 '…' 이 '・・・'(3칸)로 펼쳐지므로, 번역할 때 1칸으로 보고 맞춘
줄이 실제로는 2칸 더 넓어진다. 대사창을 넘긴 줄은 화면에서 **통째로 빈 줄**이 된다.
  (제보 #22 마사토 "옴잭의 / [빈 줄] / 안 뒤진다!" — 가운데 줄이 16칸이었다)

이 도구는 폭을 넘는 항목만 골라 같은 글로 다시 줄을 나눈다.
글자는 하나도 바꾸지 않고 줄바꿈 위치만 옮긴다.

사용법:
  python rewrap_ko.py            # 미리보기
  python rewrap_ko.py --go       # battle_dialogue.json 에 반영
"""
import sys, os, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_W = 14        # 한 줄 최대 칸 (・・・ 로 펼쳐진 뒤 기준)
MAX_L = 3         # 4줄 이상은 화자가 도몬으로 고정되는 버그
VAR_LEN = {'①': 3, '②': 3, '③': 3, '④': 7, '⑤': 6, '⑥': 6}
MARK = re.compile(r'\[[0-9a-f]{2}\]')      # 제어 마커 — 화면에 안 그려짐


def norm(s):
    """삽입기와 같은 변환(폭 계산용)."""
    s = MARK.sub('', s)
    s = s.replace('…', '・・・').replace('...', '・・・').replace('‥', '・・')
    return re.sub(r'[.．]{2,}', lambda m: '・' * len(m.group()), s)


def width(s):
    return sum(VAR_LEN.get(c, 1) for c in norm(s))


def tokens(text):
    """공백으로 자르되 [xx] 마커는 뒤 단어에 붙여 둔다."""
    flat = text.replace('\n', ' ').replace('　', ' ')
    return [t for t in flat.split(' ') if t]


def rewrap(text):
    """같은 글을 MAX_W 칸 이내 MAX_L 줄로 다시 나눈다. 실패하면 None."""
    words = tokens(text)
    lines, cur = [], ''
    for wd in words:
        cand = wd if not cur else cur + ' ' + wd
        if width(cand) <= MAX_W:
            cur = cand
            continue
        if cur:
            lines.append(cur)
        if width(wd) > MAX_W:
            return None            # 한 단어가 한 줄보다 김 → 사람이 손봐야 함
        cur = wd
    if cur:
        lines.append(cur)
    if len(lines) > MAX_L:
        return None
    return '\n'.join(lines)


def main():
    go = '--go' in sys.argv
    p = os.path.join(HERE, 'battle_dialogue.json')
    d = json.load(open(p, encoding='utf-8'))
    B = d['entries']

    fixed, manual = [], []
    for i, e in enumerate(B):
        ko = e.get('ko') or ''
        if not ko.strip():
            continue
        if all(width(l) <= MAX_W for l in ko.split('\n')) and \
                len(ko.split('\n')) <= MAX_L:
            continue
        new = rewrap(ko)
        if new is None:
            manual.append((i, e))
        else:
            fixed.append((i, e, ko, new))
            if go:
                e['ko'] = new

    print(f'폭/줄수를 넘는 항목 {len(fixed) + len(manual)}건')
    print(f'  줄바꿈 재배치로 해결 : {len(fixed)}건')
    print(f'  사람이 손봐야 함     : {len(manual)}건')
    for i, e, old, new in fixed[:15]:
        print(f"\n  #{i} blk{e['blk']}")
        print(f"     전 {old!r}")
        print(f"     후 {new!r}")
    for i, e in manual:
        ko = e['ko']
        print(f"\n  [손수정] #{i} blk{e['blk']}")
        print(f"     JP {e.get('jp')!r}")
        print(f"     KO {ko!r}  (줄별 폭 {[width(l) for l in ko.split(chr(10))]})")

    if go:
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'\n반영 완료 ({len(fixed)}건)')
    else:
        print('\n(미리보기 — --go 로 반영)')


if __name__ == '__main__':
    main()
