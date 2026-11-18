# -*- coding: utf-8 -*-
"""이슈 #51·#52 반영 — v2.7.2

  python apply_issues_v272.py            # 미리보기
  python apply_issues_v272.py --write    # 반영

#51 35화 인터미션·맵
      마오   '개소름' — 원문 趣味の悪い話 에 없는 인터넷 말투
      로안   '말씀하시면' — 원문 もうその辺で 에 경어가 없다
      카티아 '알겠어요!' — 토우야에게는 반말
#52 블루어스(밀리 탑승) 전투 대사
      원문은 전부 アキさん 인데 번역에서 '씨' 가 빠졌다.
      같은 블록 안에서 '제대로 노려주세요'·'물러나 주세요' 처럼 존댓말은
      쓰면서 호칭만 반말이라 어긋나 보였다.

덧붙여, 같은 '원문에 さん 이 있는데 번역에서 빠짐' 유형을 전투 대사 전체에서
훑어 함께 맞췄다. 한 블록 안에서도 표기가 갈려 있었다.
   blk193  i170 '사야카 씨' ↔ i137·153·156·196·212 '사야카'
   blk287  i6197 '노알 씨'  ↔ i258·6122 '노알'
(시나리오 쪽 さん 은 '테츠야 형'·'미나토 언니'처럼 한국어 호칭으로 이미
 옮겨져 있거나, 코우지↔사야카처럼 또래 사이라 그대로 두었다.)
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
XLSX = os.path.join(HERE, 'srwj_matched_all_0625.xlsx')
BATTLE = os.path.join(ROOT, '2. 전투대사패치', 'battle_dialogue.json')
WRITE = '--write' in sys.argv
log = []

SC_FIX = [
 (20122, '정말 개소름이네', '정말 악취미네', '#51',
  '원문 ったく、趣味の悪い話ね — 소름이 아니라 "취향이 고약하다"는 뜻이고, 원문에 비속어도 없다'),
 (20202, '아서, 그 이상 말씀하시면...', '아서, 그쯤 해 둬...', '#51',
  '원문 アーサー、もうその辺で・・・ — 경어가 없고, 뜻도 "그만하라"에 가깝다'),
 (20433, '알겠어요!', '알았어!', '#51', '원문 はい！ — 카티아는 토우야에게 반말을 쓴다'),
 (20439, '알겠어요!', '알았어!', '#51', '원문 はい！ — 여주인공 판본'),
]

# 원문 '이름さん' 인데 번역에 '씨' 가 없는 전투 대사 — 이름별로 일괄
HONOR = [('アキさん', '아키', '#52', '밀리는 아키를 アキさん 으로 부른다'),
         ('さやかさん', '사야카', '#44', '같은 블록 i170 은 이미 "사야카 씨" 다'),
         ('ノアルさん', '노알', '#52', '같은 계열 i6197 은 이미 "노알 씨" 다')]
OK_TAIL = ('씨', '님', '군', '양', '쨩', '짱', '상')


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
            log.append((iss, 'R%d' % row, '(못 찾음) ' + old, repr(v), why))
    if WRITE:
        wb.save(XLSX)
    return n


def add_honorific(ko, name):
    """이름 뒤에 호칭이 없는 자리에만 ' 씨' 를 넣는다."""
    out, i = [], 0
    for m in re.finditer(re.escape(name), ko):
        tail = ko[m.end():m.end() + 4].lstrip(' \u3000\n')
        if tail[:1] in OK_TAIL:
            continue
        # 더 긴 이름의 일부면(예: 아키 ⊂ 아키토) 건너뛴다
        if ko[m.end():m.end() + 1] not in ('', ' ', '\u3000', '\n', ',', '，', '!', '！',
                                           '?', '？', '.', '。', '…', '・', '는', '도', '를', '을'):
            continue
        out.append(m.end())
    for p in reversed(out):
        ko = ko[:p] + ' 씨' + ko[p:]
    return ko, len(out)


def patch_battle():
    d = json.load(open(BATTLE, encoding='utf-8'))
    ent = d['entries']
    n = 0
    for jp_name, ko_name, iss, why in HONOR:
        c = 0
        for i, e in enumerate(ent):
            ko, jp = e.get('ko') or '', e.get('jp') or ''
            if jp_name not in jp or ko_name not in ko:
                continue
            nv, cnt = add_honorific(ko, ko_name)
            if cnt and nv != ko:
                if c < 3:
                    log.append((iss, 'i%d blk%s' % (i, e['blk']), ko, nv, why))
                if WRITE:
                    e['ko'] = nv
                c += 1
                n += 1
        log.append((iss, '합계', '%s → %s 씨' % (ko_name, ko_name), '%d건' % c, ''))
    if WRITE:
        json.dump(d, open(BATTLE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return n


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print('모드:', '반영(--write)' if WRITE else '미리보기')
    a = patch_xlsx(); b = patch_battle()
    for iss, where, before, after, why in log:
        print('\n[%s] %s %s' % (iss, where, ('— ' + why) if why else ''))
        print('   - %s' % str(before).replace('\n', ' ⏎ ')[:150])
        print('   + %s' % str(after).replace('\n', ' ⏎ ')[:150])
    print('\n합계: 시나리오 %d / 전투 %d' % (a, b))
