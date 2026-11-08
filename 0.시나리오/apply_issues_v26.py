# -*- coding: utf-8 -*-
"""이슈 #5~#12 반영 — v2.6

  python apply_issues_v26.py            # 미리보기
  python apply_issues_v26.py --write    # 반영

#5  즐겨찾기 특전 설명 2·3행이 화면에서 사라짐
    일본어는 가나가 좁아 한 줄에 23~24자가 들어가지만, 한글은 같은 칸수여도
    글자 폭이 커서 창을 넘는다. 넘긴 줄은 통째로 안 그려진다.
    실제로 1행(15칸)만 보이고 2행(23칸)·3행(24칸)이 사라졌다. 15칸으로 줄였다.
#6  유우 '저게!' → '이 자식!' (원문 貴様っ！, 바로 뒤 히메가 '난 이 자식이 아니라'로 받는다)
#7  '겟키 강가' 등 표기 혼재 → '게키강가' 로 통일 / 토우야 대사 다듬기
#8  미나토 말투, 가이의 감탄사 'KIA!' → '캬아!' (원문 かーっ)
#9  엘리자베스 '같은 정도로는' → '같은 정도로'
#10 '아런 발표도' → '아무런 발표도' / '칼리지' → '대학'
#11 키라 전투 대사 번역투 — 원문이 僕 를 쓰는 부드러운 말투인데 '-다!' 로 굳어 있었다
#12 '카슈 씨' → '캇슈 씨' (다른 21곳은 이미 캇슈)
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
XLSX = os.path.join(HERE, 'srwj_matched_all_0625.xlsx')
BATTLE = os.path.join(ROOT, '2. 전투대사패치', 'battle_dialogue.json')
TRANS = os.path.join(ROOT, '3. SJIS추출', 'translations.json')
WRITE = '--write' in sys.argv
log = []

# ── 시나리오: (행, 옛문구, 새문구, 이슈, 근거) ──────────────────
SC_FIX = [
    (405, '저게!', '이 자식!', '#6', '원문 貴様っ！ — 바로 뒤 히메가 "난 이 자식이 아니라"로 받는다'),
    (1046, '저게!', '이 자식!', '#6', '같은 장면 다른 루트판'),
    (1459, '난 저 두 사람처럼은 모르겠어.', '난 저 두 사람처럼은 잘 모르겠어.', '#7',
     '원문 あの２人みたいにはわからない — 뜻은 두고 어색함만 덜었다'),
    (2129, '나데시코, 튤립 내부로 진입한다.\n진짜 들어가도 되는 거지?',
     '나데시코, 튤립 내부로 진입할게요.\n진짜 들어가도 되는 거죠?', '#8',
     '원문 入るわよ / いいのね — 미나토의 말투'),
    (2146, 'KIA! 불타오르는구나!!', '캬아! 불타오르는구나!!', '#8', '원문 かーっ — 감탄사다'),
    (2373, '적어도 에이지와 같은 정도로는', '적어도 에이지와 같은 정도로', '#9', '조사 중복'),
    (2841, '아직 아런 발표도', '아직 아무런 발표도', '#10', '오타'),
    (3056, '같은 칼리지에 다니는 애야', '같은 대학에 다니는 애야', '#10', '원문 カレッジ'),
    (4404, '카슈 씨', '캇슈 씨', '#12', '원문 カッシュ — 다른 21곳은 캇슈'),
]

# ── 표기 통일: 게키강가 (#7) ───────────────────────────────
GEKI = [('겟키 강가', '게키강가'), ('겟키강가', '게키강가'), ('게키 강가', '게키강가'),
        ('게키・간가', '게키강가'), ('게키간가', '게키강가'), ('겟키', '게키')]

# ── 전투 대사: 키라 블록(212) 말투 (#11) ─────────────────────
KIRA_BLK = 212
KIRA_RULES = [
    (r'거다(?=[!…·\.\n]|$)', '거야'), (r'있다(?=[!…·\.\n]|$)', '있어'),
    (r'없다(?=[!…·\.\n]|$)', '없어'), (r'아니다(?=[!…·\.\n]|$)', '아니야'),
    (r'않다(?=[!…·\.\n]|$)', '않아'), (r'아직이다', '아직이야'),
    (r'겠다(?=[!…·\.\n]|$)', '겠어'), (r'뿐이다(?=[!…·\.\n]|$)', '뿐이야'),
]

# ── 시스템 텍스트: 즐겨찾기 특전 설명 (#5) ────────────────────
TR_FIX = [
    ('0x0008EE20', '#|이후 전 유닛 최대개조 ２０', '#5',
     '23칸 → 15칸. 1행(15칸)은 보이므로 같은 길이로 맞췄다'),
    ('0x0008EDEC', '#|자금・경험치는 １．５배', '#5', '24칸 → 12칸'),
]


def patch_xlsx():
    from openpyxl import load_workbook
    wb = load_workbook(XLSX)
    ws = wb[wb.sheetnames[0]]
    n = 0
    for row, old, new, iss, why in SC_FIX:
        c = ws.cell(row=row, column=10)
        v = str(c.value or '')
        if old in v:
            nv = v.replace(old, new)
            log.append((iss, 'R%d' % row, v, nv, why))
            if WRITE:
                c.value = nv
            n += 1
        else:
            log.append((iss, 'R%d' % row, '(못 찾음) %s' % old, '-', why))
    # 게키강가 표기 통일
    g = 0
    for r in range(2, ws.max_row + 1):
        c = ws.cell(row=r, column=10)
        v = c.value
        if not v:
            continue
        s = nv = str(v)
        for a, b in GEKI:
            if a in nv:
                nv = nv.replace(a, b)
        if nv != s:
            if g < 6:
                log.append(('#7', 'R%d' % r, s, nv, '게키강가 표기 통일'))
            if WRITE:
                c.value = nv
            g += 1
            n += 1
    log.append(('#7', '합계', '게키강가 표기 통일', '%d개 턴' % g, ''))
    if WRITE:
        wb.save(XLSX)
    return n


def patch_battle():
    d = json.load(open(BATTLE, encoding='utf-8'))
    ent = d['entries']
    n = k = 0
    for i, e in enumerate(ent):
        ko = e.get('ko') or ''
        if not ko:
            continue
        nv = ko
        if e['blk'] == KIRA_BLK:
            for p, rep in KIRA_RULES:
                nv = re.sub(p, rep, nv)
        for a, b in GEKI:
            if a in nv:
                nv = nv.replace(a, b)
        if nv != ko:
            if e['blk'] == KIRA_BLK:
                k += 1
                if k <= 5:
                    log.append(('#11', 'i%d' % i, ko, nv, '키라 말투 (원문 僕 의 부드러운 어조)'))
            else:
                log.append(('#7', 'i%d blk%s' % (i, e['blk']), ko, nv, '게키강가 표기 통일'))
            if WRITE:
                e['ko'] = nv
            n += 1
    log.append(('#11', '합계', '키라 블록 말투', '%d개 항목' % k, ''))
    if WRITE:
        json.dump(d, open(BATTLE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return n


def patch_trans():
    d = json.load(open(TRANS, encoding='utf-8'))
    ent = d['entries']
    n = 0
    for off, new, iss, why in TR_FIX:
        for e in ent:
            if e['off'] == off:
                log.append((iss, off, e['ko'], new, why))
                if WRITE:
                    e['ko'] = new
                n += 1
                break
    # 시스템 텍스트에도 게키 표기가 있으면 통일
    for e in ent:
        ko = e.get('ko') or ''
        nv = ko
        for a, b in GEKI:
            if a in nv:
                nv = nv.replace(a, b)
        if nv != ko:
            log.append(('#7', e['off'], ko, nv, '게키강가 표기 통일'))
            if WRITE:
                e['ko'] = nv
            n += 1
    if WRITE:
        json.dump(d, open(TRANS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return n


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print('모드:', '반영(--write)' if WRITE else '미리보기')
    a = patch_xlsx()
    b = patch_battle()
    c = patch_trans()
    for iss, where, before, after, why in log:
        print('\n[%s] %s %s' % (iss, where, ('— ' + why) if why else ''))
        print('   - %s' % str(before).replace('\n', ' ⏎ ')[:150])
        print('   + %s' % str(after).replace('\n', ' ⏎ ')[:150])
    print('\n합계: 시나리오 %d / 전투 %d / 시스템 %d' % (a, b, c))
