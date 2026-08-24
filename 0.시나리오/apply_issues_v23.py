# -*- coding: utf-8 -*-
"""GitHub 이슈 #30~#33 반영 + 전투 대사 첫 줄 화자명 자리 확보 — v2.3

  python apply_issues_v23.py            # 미리보기
  python apply_issues_v23.py --write    # 반영

핵심 — 전투 대사 첫 줄에 '이름「' 자리가 없었다
--------------------------------------------------
시나리오 줄바꿈기(srwj_wrap)는 첫 줄에 화자명 자리 7칸을 예약한다.
그런데 전투 대사 줄바꿈(rewrap_ko)에는 그 예약이 없어, 화면에서 첫 줄 앞에
'이름「' 이 붙는 순간 대사창을 넘고 **그 줄이 통째로 빈 줄이 된다.**
화자명까지 함께 사라지므로 제보에는 '이름 미출력'으로 보였다(#25 #29 #31).

  실측 예 (#31 스크린샷, blk305 에이지 회피)
     번역   피하긴 했지만 움직임이 / 좋다…, 다음에도 / 잘된다는 보장은 없군
     화면   (빈 줄)              / 좋다…, 다음에도 / 잘된다는 보장은 없군
     첫 줄 12칸 + '에이지「' 4칸 = 16칸 → 대사창 초과

그래서 첫 줄 예산을 14 → 10 칸으로 낮춰 이름 4자(+「)까지 들어가게 한다.
합체기 블록(193)은 바이트 길이 보존 대상이라 건드리지 않는다.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
XLSX = os.path.join(HERE, 'srwj_matched_all_0625.xlsx')
BATTLE = os.path.join(ROOT, '2. 전투대사패치', 'battle_dialogue.json')

WRITE = '--write' in sys.argv
log = []

VAR = {'①': 3, '②': 3, '③': 3, '④': 7, '⑤': 6, '⑥': 6}
MARK = re.compile(r'\[[0-9a-f]{2}\]')
MAX_W, MAX_L = 14, 3
FIRST_W = 10                 # 14 − ('이름' 4자 + '「' 1자)
LEN_PRESERVE = {193}         # 합체기 — 길이 보존이라 제외


def norm(s):
    s = MARK.sub('', s or '')
    s = s.replace('…', '・・・').replace('...', '・・・').replace('‥', '・・')
    return re.sub(r'[.．]{2,}', lambda m: '・' * len(m.group()), s)


def W(s):
    return sum(VAR.get(c, 1) for c in norm(s))


def rewrap(text, first_budget=FIRST_W):
    """첫 줄만 예산이 좁은 그리디 줄바꿈. 3줄을 넘으면 None."""
    words = [t for t in text.replace('\n', ' ').replace('　', ' ').split(' ') if t]
    lines, cur = [], ''
    for wd in words:
        budget = first_budget if not lines else MAX_W
        cand = wd if not cur else cur + ' ' + wd
        if W(cand) <= budget:
            cur = cand
            continue
        if cur:
            lines.append(cur)
            cur = ''
        if W(wd) > (first_budget if not lines else MAX_W):
            return None
        cur = wd
    if cur:
        lines.append(cur)
    return lines if 0 < len(lines) <= MAX_L else None


# ══════════════════════════════════════════════════════════════════
# 1. 시나리오 (xlsx J열)
# ══════════════════════════════════════════════════════════════════
XLSX_FIX = [
    # (행, 옛문구, 새문구, 이슈, 근거)
    (670, '그체 조종과', '기체 조종과', '#30', '원문 機体のコントロール'),
    (1520, '가 보면 보실 수 있습니다.', '가 보면 알 수 있습니다.', '#31', '원문 行けば見れますよ'),
    (1465, '것도,', '것도', '#31', '줄맞춤 — 쉼표 하나로 끝 세 줄이 5/9칸으로 갈라짐'),
    (2504, '당신 지원군이라면서?\n그럼 당신은 어쩔 건데?',
     '당신 지원군이라면서요?\n그럼 당신은 어쩔 겁니까?', '#33', '아키토→아카츠키 존대'),
    (2506, '난 좋아서 싸우는 게 아니야!\n전쟁이라고 무조건 싸워야 한다는 게 싫을 뿐이야.',
     '전 좋아서 싸우는 게 아닙니다!\n전쟁이라고 무조건 싸워야 한다는 게 싫을 뿐입니다.',
     '#33', '아키토→아카츠키 존대'),
    (2508, '난...', '전...', '#33', '아키토→아카츠키 존대'),
]


def patch_xlsx():
    from openpyxl import load_workbook
    wb = load_workbook(XLSX)
    ws = wb[wb.sheetnames[0]]
    n = 0
    for row, old, new, iss, why in XLSX_FIX:
        c = ws.cell(row=row, column=10)
        v = str(c.value or '')
        if old in v:
            nv = v.replace(old, new)
            log.append(('시나리오', 'R%d' % row, v, nv, '%s (%s)' % (iss, why)))
            if WRITE:
                c.value = nv
            n += 1
        else:
            log.append(('시나리오', 'R%d' % row, '(못 찾음: %s)' % old, '-', iss))
    if WRITE:
        wb.save(XLSX)
    return n


# ══════════════════════════════════════════════════════════════════
# 2. 전투 대사
# ══════════════════════════════════════════════════════════════════
BATTLE_FIX = [
    (4603, '게에에키강!\n플레어어어!!', '#32', '무장명 게키강과 통일 (원문 ゲェェェキガン)'),
    (917, '그렇게\n두지 않아!!', '#31', '원문 やらせないよっ — 목적어 없이 끊겨 있었음'),
    (7558, '그렇게\n두지 않아!!', '#31', '원문 やらせない'),
]

# 첫 줄 10칸에 자동으로 못 들어가 손으로 다시 나눈 것
MANUAL = {
    3107: '옴잭 무기인가…\n제오라이머에도\n뒤지지 않는다!',
    3542: '제오라이머…!\n같이 죽는 한이\n있어도 쓰러뜨린다…!',
    3635: '그래, 키하라\n마사키… 이 힘이야말로\n나의…!',
    4380: '넌 오르판을\n떠났어…! 부모를\n배신하고 가족을 버리고!!',
    6446: '라담이 인간을\n멸하는 것도… 살기\n위해 짐승을 죽이는 것도',
    6468: '과연 사선을\n넘어온 만큼은 있군…\n스승이지만 반했다…!',
    7437: '피했지만\n움직임이 좋군…\n다음에도 통할지는 모른다',
    9633: '아직이다! 승부는\n지금부터! 우리는\n결코 지지 않는다!',
    9747: '으으으으… 내가\n패하다니… 미케네의\n야망도 여기까지인가',
    11647: '뭐라, 이 몸을\n무섭게 하다니… 저주의\n종자에서 나온 놈들!',
}


def patch_battle():
    d = json.load(open(BATTLE, encoding='utf-8'))
    ent = d['entries']
    n = 0
    for idx, new, iss, why in BATTLE_FIX:
        old = ent[idx].get('ko') or ''
        if old != new:
            log.append(('전투', 'i%d blk%s' % (idx, ent[idx]['blk']), old, new, '%s (%s)' % (iss, why)))
            if WRITE:
                ent[idx]['ko'] = new
            n += 1
    for idx, new in MANUAL.items():
        old = ent[idx].get('ko') or ''
        if old != new:
            log.append(('전투-첫줄(수동)', 'i%d blk%s' % (idx, ent[idx]['blk']), old, new,
                        '#31 화자명 자리 — 자동 재줄바꿈 불가라 문장을 줄임'))
            if WRITE:
                ent[idx]['ko'] = new
            n += 1
    auto = fail = 0
    for i, e in enumerate(ent):
        ko = e.get('ko') or ''
        if not ko.strip() or e['blk'] in LEN_PRESERVE or i in MANUAL:
            continue
        if W(ko.split('\n')[0]) <= FIRST_W:
            continue
        r = rewrap(ko)
        if r is None:
            fail += 1
            log.append(('전투-첫줄(실패)', 'i%d blk%s' % (i, e['blk']), ko, '(그대로 둠)', '#31'))
            continue
        new = '\n'.join(r)
        if new != ko:
            log.append(('전투-첫줄(자동)', 'i%d blk%s' % (i, e['blk']), ko, new, '#31 화자명 자리 확보'))
            if WRITE:
                e['ko'] = new
            auto += 1
    if WRITE:
        json.dump(d, open(BATTLE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('   첫 줄 재줄바꿈: 자동 %d건 / 수동 %d건 / 실패 %d건' % (auto, len(MANUAL), fail))
    return n + auto


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print('모드:', '반영(--write)' if WRITE else '미리보기')
    a = patch_xlsx()
    b = patch_battle()
    by = {}
    for kind, where, before, after, iss in log:
        by.setdefault(kind, []).append((where, before, after, iss))
    for kind in ('시나리오', '전투', '전투-첫줄(수동)', '전투-첫줄(실패)', '전투-첫줄(자동)'):
        rows = by.get(kind, [])
        if not rows:
            continue
        print('\n' + '=' * 78)
        print('%s — %d건' % (kind, len(rows)))
        print('=' * 78)
        for where, before, after, iss in rows[:25]:
            print('  [%s] %s' % (iss, where))
            print('     - %s' % before.replace('\n', ' ⏎ '))
            print('     + %s' % after.replace('\n', ' ⏎ '))
        if len(rows) > 25:
            print('  ... 외 %d건' % (len(rows) - 25))
    print('\n합계: 시나리오 %d / 전투 %d' % (a, b))
