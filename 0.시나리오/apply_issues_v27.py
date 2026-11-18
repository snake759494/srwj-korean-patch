# -*- coding: utf-8 -*-
"""이슈 #13~#50 반영 — v2.7

  python apply_issues_v27.py            # 미리보기
  python apply_issues_v27.py --write    # 반영

제보 38건을 파고들어 보니 개별 오타 말고도 **원인이 하나인 묶음**이 넷 있었다.

 (A) 따옴표 방향  — 코덱이 ASCII " ' 를 무조건 '닫는' 전각 따옴표로 바꿔서
                    여는 자리에도 닫는 따옴표가 찍혔다.           → #19 #42 #47 #50
 (B) 인라인 코드  — 전투 대사의 [7d](이름)·[7e](기체명)·[7f](무기명)을
                    v2.4 균형 줄바꿈이 '폭 0'으로 보고 앞 줄에 붙여 버렸다.
                    실행 중 이름이 들어가면 줄이 넘쳐 통째로 안 그려진다. → #18
 (C) 조사 누락    — 기체명 변수 ⑤ 뒤에 조사가 빠진 턴이 많았다.    → #27 #31 #45 #48
 (D) 화자명 유실  — 원문이 본문에 'バルトフェルド「' 처럼 이름을 품고 있는데
                    번역에서 이름이 빠진 턴이 있었다.             → #15
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
XLSX = os.path.join(HERE, 'srwj_matched_all_0625.xlsx')
BATTLE = os.path.join(ROOT, '2. 전투대사패치', 'battle_dialogue.json')
TRANS = os.path.join(ROOT, '3. SJIS추출', 'translations.json')
WRITE = '--write' in sys.argv
log = []

def L(iss, where, before, after, why=''):
    log.append((iss, where, before, after, why))

# ══════════════════════════════════════════════════════════════════
#  A. 따옴표 방향 — 여는 자리에는 여는 따옴표
# ══════════════════════════════════════════════════════════════════
OS_, CS_, OD_, CD_ = '\u2018', '\u2019', '\u201c', '\u201d'

def fix_quotes(s):
    """한 턴 안에서 홑/겹 따옴표를 번갈아 여는/닫는 글자로 맞춘다."""
    out, open_s, open_d = [], False, False
    for c in s:
        if c in ("'", OS_, CS_):
            out.append(OS_ if not open_s else CS_); open_s = not open_s
        elif c in ('"', OD_, CD_):
            out.append(OD_ if not open_d else CD_); open_d = not open_d
        else:
            out.append(c)
    return ''.join(out)

# ══════════════════════════════════════════════════════════════════
#  D. 화자명이 빠진 턴 (#15)
# ══════════════════════════════════════════════════════════════════
SPEAKER_FIX = [
    (2499, '함장'), (4794, '발트펠트'), (4796, '발트펠트'), (4798, '발트펠트'),
    (4800, '발트펠트'), (4802, '발트펠트'), (4806, '발트펠트'), (4809, '발트펠트'),
    (4813, '발트펠트'), (4817, '발트펠트'),
]

# ══════════════════════════════════════════════════════════════════
#  C. 기체명·이름 변수 뒤 조사 (#27 #31 #45 #48)
# ══════════════════════════════════════════════════════════════════
#   (행, 변수, 넣을 조사) — 원문 조사를 보고 하나씩 확인했다
JOSA = [
    (6681,'⑤','에'), (7786,'⑤','는'), (7958,'⑤','를'), (8936,'⑤','를'),
    (10782,'⑤','는'), (10784,'⑤','를'), (11014,'⑤','를'), (11015,'⑤','를'),
    (11020,'⑤','를'), (11035,'⑤','를'), (12524,'⑤','를'), (12552,'⑤','가'),
    (13087,'⑤','의'), (13090,'⑤','는'), (13095,'⑤','를'), (15546,'⑤','가'),
    (15572,'⑤','가'), (16026,'⑤','를'), (16031,'⑤','를'), (16042,'⑤','를'),
    (16046,'⑤','를'), (17833,'⑤','를'), (18063,'⑤','를'), (18064,'⑤','를'),
    (18067,'⑤','가'), (18803,'⑤','가'), (18830,'⑤','를'), (21855,'⑤','를'),
    (21856,'⑤','가'), (22247,'⑤','를'), (22431,'⑤','가'), (22442,'⑤','가'),
    (23647,'⑤','가'), (23658,'⑤','를'), (23673,'⑤','가'), (23680,'⑤','가'),
    (27993,'⑤','가'), (28545,'⑤','를'), (28568,'⑤','를'), (31168,'⑤','가'),
    (31291,'⑤','가'), (31300,'⑤','가'), (31474,'⑤','가'), (31485,'⑤','를'),
    (10278,'③','를'), (18764,'②','가'),
]
# 17918 은 ⑤ 가 두 번 나오고 둘 다 조사가 없다 — 따로 처리
JOSA_ALL = [(17918, '⑤', '를')]

# ══════════════════════════════════════════════════════════════════
#  시나리오 개별 수정
# ══════════════════════════════════════════════════════════════════
SC_FIX = [
 (4525, '이런 줄은', '이럴 줄은', '#14', '원문 こんなだって知らなかったんだもん'),
 (5234, '그럴수도 있겠네요', '그럴 수도 있겠네', '#17', '카티아는 토우야에게 반말을 쓴다'),
 (5964, '너랑 이야기하고 있다는', '너랑 이야기하고 싶다는', '#20', '원문 あなたと話したいという人'),
 (8233, '골치 아파 뒤지겠는데', '골치 아파 죽겠는데', '#21', '원문 やっかいだってのに — 거친 말투가 원문에 없다'),
 (8233, '돌겠네 진짜', '미치겠네 진짜', '#21', '원문 たまらんなぁ'),
 (8596, '베이브', '베이비', '#21', '원문 ベイブ(babe) — 한국어 관용은 베이비'),
 (8965, '영상에 출현할 배우', '영상에 출연할 배우', '#22', '出演 — 출연'),
 (9810, '해 본 적도 없어요', '해 본 적도 없어', '#24', '미쿠는 이 장면에서 반말이다'),
 (9810, '어쩔 수 없어요...', '어쩔 수 없어...', '#24', ''),
 (9810, '그게 제 전부니까요', '그게 내 전부니까', '#24', '원문 それが、私のすべてだから'),
 (10945, '모르는 것투성이', '모르는 것 투성이', '#26', '띄어쓰기'),
 (10959, '그건 아마 그 때문이었을 거야', '아마 그것 때문이었을 거야', '#26', ''),
 (11561, '시킬 수는 없어요!', '시킬 수 없어!', '#27', '히메는 카난에게 반말을 쓴다'),
 (12141, '어째서 모르는 거예요?', '어째서 모르는 거야?', '#29', '카티아→토우야는 반말'),
 (12141, '잘 알고 있잖아요?', '잘 알고 있잖아?', '#29', ''),
 (12143, '③, 당신같은 사람이 아니에요.', '③는 당신 같은 사람이 아니에요.', '#29', '주격 조사 누락'),
 (12146, '전 납득할 수 없어요', '난 납득할 수 없어', '#29', '카티아→토우야는 반말'),
 (14365, '가능한 한 말해주도록 하겠다...', '가능한 한 말씀드리겠습니다...', '#34', '원문 お話をいたしましょう — 존대'),
 (14395, '쟝갈 장군께서 온 건가', '쟝갈 장군이 온 건가', '#34', '캐서린은 쟝갈을 높이지 않는다'),
 (14530, '여려분', '여러분', '#34', '오타'),
 (15163, '아스트레이랑', '어스트레이랑', '#35', 'アストレイ — 다른 표기와 통일'),
 (15522, '네, 다른 사람들은?', '저기, 다른 사람들은?', '#36', '원문 ええ。あの人たちは？'),
 (15992, '네, 다른 사람들은?', '저기, 다른 사람들은?', '#36', ''),
 (15696, '당신들도 서둘러 기체에 탑승해주세요.', '너희들도 서둘러 기체에 탑승해.', '#36', '네리는 유우 일행에게 반말'),
 (16185, '당신들도 서둘러 기체에 탑승해주세요.', '너희들도 서둘러 기체에 탑승해.', '#36', ''),
 (15712, '가즈아!', '가자아!', '#36', '원문 いけよやァ！！ — 유행어가 원문에 없다'),
 (16201, '가즈아!', '가자아!', '#36', ''),
 (15723, '무슨 소리를 하는 거예요!', '무슨 소리를 하는 거야!', '#36', '네리는 유우에게 반말'),
 (16214, '무슨 소리를 하는 거예요!', '무슨 소리를 하는 거야!', '#36', ''),
 (16760, '사아캬, 미안해', '미안해, 사야카', '#39', '오타(사아캬) + 어순'),
 (2442, '사아캬,', '사야카 씨,', '#39', '오타(사아캬) — 원문 さやかさん'),
 (16913, '조금 활약 좀 못 했다고', '조금 활약 못 했다고', '#39', "'조금'과 '좀'이 겹쳤다"),
 (17583, '응, 널 찾더라', '네, 당신을 찾았대요', '#43', '유리카는 에이지에게 존대를 쓴다'),
 (17744, '저도... 같이 데려가 줘요', '나도... 같이 데려가 줘', '#45', '미쿠는 마사토에게 반말'),
 (17746, '제발 저도 같이 데려가 주세요.', '제발 나도 같이 데려가 줘.', '#45', ''),
 (17746, '전...', '난...', '#45', ''),
 (19126, "특무분함대'의 제군들", "특무분함대'의 제군들", '#48', ''),
 (19143, '사이사이시랑', '사이사이시 형이랑', '#48', ''),
 (19453, '스폐셜 메뉴', '스페셜 메뉴', '#49', '오타'),
 (24746, '은색의 다리 스폐셜!', '은색의 다리 스페셜!', '#49', '오타'),
 (27146, '게키강가 스폐셜 판', '게키강가 스페셜 판', '#49', '오타'),
 (19968, '라사', '라져', '#49', '원문 ラーサ — 전투 대사에선 이미 라져'),
 (20000, '네, 네!', '으, 응!', '#49', '카티아→토우야는 반말'),
 (5859, '가진 자들이 있다.', '가진 자들이 있다.', '#19', ''),
]
# 한 턴 전체를 바꾸는 것 (줄바꿈까지 손대야 하는 경우)
SC_WHOLE = [
 (19126, '#48', '줄 끝에 조사만 남던 줄바꿈 정리'),
]

# ══════════════════════════════════════════════════════════════════
#  전투 대사
# ══════════════════════════════════════════════════════════════════
BT_FIX = [
 (353, '면!', '머리!', '#13', '원문 メンッ！ — 검도의 머리치기 구호'),
 (354, '면!!', '머리!!', '#13', ''),
 (355, '며어어어어언!\n!', '머리이이이잇!\n!', '#13', '원문 メェェェェェェン！！'),
 (11, '초전자\n타・츠・마・키이이이!!', '초전자\n회・오・리이이이!!', '#33', '竜巻 = 회오리. 무기명도 용권으로 번역돼 있다'),
 (143, '간다,\n테츠야!', '간다,\n테츠야 씨!', '#28', '원문 やるぜ、鉄也さん！'),
 (6917, '두지 않겠어!', '가만두지 않겠어!', '#23', '원문 やらせないわよ！'),
 (6921, '캔디다!', '캔디야!', '#23', '원문 キャンディーよ！ — 마오의 말투'),
 (6957, '굼뜨다!', '굼뜨네!', '#23', '원문 とろいっ！'),
 (6963, '당신으론\n이 화려한 움직임을\n따라올 수 없겠지!', '너로는\n이 화려한 움직임을\n따라올 수 없어!', '#23', '원문 あんたじゃ…ないわね！'),
 (303, '떨궈드리겠습니\n다 !', '떨어뜨려\n드리죠!', '#25', '원문 落とさせてもらいます！ — 줄 가운데서 낱말이 갈렸다'),
 (5381, '라져!!', '라져!!', '#49', ''),
]
# 문자열 치환(블록 지정) — 여러 항목에 걸친 표기 통일
BT_SUB = [
 ('데거', '대거', None, '#16', 'テッカマンダガー — Dagger'),
 ('조르주', '죠르주', None, '#37', 'ジョルジュ — 다른 표기와 통일'),
 ('가우루우우운', '가아루우우웅', None, '#38', '원문 ガウルゥゥゥーンッ'),
 ('쿡쿡쿡', '큭큭큭', None, '#41', '원문 クックックック — 한국어 의성어는 큭큭'),
 ('브레스트 바안', '브레스트 버언', None, '#44', '원문 ブレストバァァン (Breast Burn)'),
 ('아스트레이', '어스트레이', None, '#35', 'アストレイ'),
 ('목표의 진로를 예측해라!', '목표의 진로를 예측해 줘!', 363, '#16', '토우야는 서브파일럿에게 명령조를 쓰지 않는다'),
]

# ══════════════════════════════════════════════════════════════════
#  시스템 텍스트
# ══════════════════════════════════════════════════════════════════
TR_FIX = [
 ('0x0008C1CC', '전율！ ５인의 테카맨', '#46',
  '반각 느낌표(1바이트)가 2바이트 단위로 읽는 화면을 어긋나게 해 뒷글자가 깨졌다'),
 ('0x0008D080', '소스케·마오·코우지·테츠야·사야카격추', '#40',
  '원문 19칸에 맞추느라 번역에서 「격추」가 통째로 빠져 있었다'),
 ('0x00089B94', 'Ｍ１어스트레이・포메이션', '#35', 'アストレイ 표기 통일'),
 ('0x00089BB8', '어스트레이・포메이션', '#35', ''),
]


# ══════════════════════════════════════════════════════════════════
def patch_xlsx():
    from openpyxl import load_workbook
    wb = load_workbook(XLSX)
    ws = wb[wb.sheetnames[0]]
    n = 0

    # D. 화자명 복구
    for row, name in SPEAKER_FIX:
        c = ws.cell(row=row, column=10)
        v = str(c.value or '')
        if v.startswith(name + '「'):
            continue
        nv = name + '「' + v + ('」' if not v.rstrip().endswith('」') else '')
        L('#15', 'R%d' % row, v, nv, '원문이 %s「…」 로 이름을 품고 있다' % name)
        if WRITE: c.value = nv
        n += 1

    # C. 조사
    for row, var, josa in JOSA:
        c = ws.cell(row=row, column=10)
        v = str(c.value or '')
        for sep in (' ', '\u3000', '\n'):
            if var + sep in v:
                nv = v.replace(var + sep, var + josa + sep, 1)
                L('#27·#31·#45·#48', 'R%d' % row, v, nv, '%s 뒤 조사 %s' % (var, josa))
                if WRITE: c.value = nv
                n += 1
                break
    for row, var, josa in JOSA_ALL:
        c = ws.cell(row=row, column=10)
        v = str(c.value or '')
        nv = re.sub(re.escape(var) + r'(?=[ \u3000\n])', var + josa, v)
        if nv != v:
            L('#45', 'R%d' % row, v, nv, '%s 뒤 조사 %s (턴 안 전부)' % (var, josa))
            if WRITE: c.value = nv
            n += 1

    # 개별 수정
    for row, old, new, iss, why in SC_FIX:
        if old == new:
            continue
        c = ws.cell(row=row, column=10)
        v = str(c.value or '')
        if old in v:
            nv = v.replace(old, new)
            L(iss, 'R%d' % row, v, nv, why)
            if WRITE: c.value = nv
            n += 1
        else:
            L(iss, 'R%d' % row, '(못 찾음) ' + old, '-', why)

    # A. 따옴표 전수 정리
    q = 0
    for r in range(2, ws.max_row + 1):
        c = ws.cell(row=r, column=10)
        v = c.value
        if not v: continue
        s = str(v)
        if not any(x in s for x in ("'", '"', OS_, CS_, OD_, CD_)): continue
        nv = fix_quotes(s)
        if nv != s:
            if q < 5: L('#19·#42·#47·#50', 'R%d' % r, s, nv, '여는 자리에 닫는 따옴표')
            if WRITE: c.value = nv
            q += 1; n += 1
    L('#19·#42·#47·#50', '합계', '따옴표 방향 정리', '%d개 턴' % q, '')

    if WRITE: wb.save(XLSX)
    return n


# ══════════════════════════════════════════════════════════════════
#  B. 전투 인라인 코드 줄 복구 (#18)
# ══════════════════════════════════════════════════════════════════
MARK = re.compile(r'\[[0-9a-f]{2}\]')
TAIL = '！!?？、，,。.・ \u3000'

def code_alone(text):
    for ln in (text or '').split('\n'):
        if MARK.search(ln) and not MARK.sub('', ln).strip().strip(TAIL):
            return True
    return False

def split_code_line(ko):
    """인라인 코드가 든 줄에서 코드(+붙은 문장부호)를 별도 줄로 떼어 낸다."""
    out = []
    for ln in ko.split(chr(10)):
        m = MARK.search(ln)
        if not m or not MARK.sub('', ln).strip().strip(TAIL):
            out.append(ln); continue
        head = ln[:m.start()].rstrip(' 　')
        rest = ln[m.start():]
        # 코드 뒤에 붙은 문장부호까지가 '코드 줄'
        j = m.end() - m.start()
        while j < len(rest) and rest[j] in TAIL:
            j += 1
        code, tail = rest[:j].rstrip(' 　'), rest[j:].lstrip(' 　')
        if head: out.append(head)
        out.append(code)
        if tail: out.append(tail)
    return chr(10).join(out)


FIRST_BUDGET, LINE_BUDGET, MAX_LINES = 8, 14, 3
INF = float('inf')

def _w(s):
    return len(MARK.sub('', s))

def wrap_head(text, nlines):
    """코드가 아닌 본문을 nlines 줄로 채운다 (첫 줄 8칸, 나머지 14칸)."""
    toks = [t for t in text.replace(chr(10), ' ').replace(chr(0x3000), ' ').split(' ') if t]
    if not toks:
        return []
    for k in range(max(1, nlines), MAX_LINES + 1):
        budgets = [FIRST_BUDGET] + [LINE_BUDGET] * (k - 1)
        m, n = len(toks), k
        dp = [[INF] * (n + 1) for _ in range(m + 1)]
        bk = [[None] * (n + 1) for _ in range(m + 1)]
        dp[0][0] = 0
        pre = [0]
        for t in toks:
            pre.append(pre[-1] + _w(t))
        for i in range(m):
            for li in range(n):
                if dp[i][li] == INF:
                    continue
                for j in range(i + 1, m + 1):
                    wd = pre[j] - pre[i] + (j - i - 1)
                    if wd > budgets[li]:
                        break
                    slack = budgets[li] - wd
                    c = slack * slack * (2 if li == 0 else 1)
                    if dp[i][li] + c < dp[j][li + 1]:
                        dp[j][li + 1] = dp[i][li] + c
                        bk[j][li + 1] = i
        if dp[m][n] < INF:
            out, j, li = [], m, n
            while li > 0:
                i = bk[j][li]
                out.append(' '.join(toks[i:j]))
                j, li = i, li - 1
            return out[::-1]
    return None


def patch_battle():
    d = json.load(open(BATTLE, encoding='utf-8'))
    ent = d['entries']
    n = 0

    # B. 인라인 코드 줄 복구
    fixed = failed = 0
    for i, e in enumerate(ent):
        ko, jp = e.get('ko') or '', e.get('jp') or ''
        if not ko or not MARK.search(ko): continue
        if not code_alone(jp) or code_alone(ko): continue
        parts = split_code_line(ko).split(chr(10))
        code = [l for l in parts if MARK.search(l) and not MARK.sub('', l).strip().strip(TAIL)]
        head = ' '.join(l for l in parts if l not in code).strip()
        jpl = len([x for x in jp.split(chr(10)) if x.strip()])
        want = max(1, min(jpl, MAX_LINES) - len(code))
        hl = wrap_head(head, want) if head else []
        if head and hl is None:
            failed += 1
            continue
        # 원문에서 코드가 맨 앞이면 앞에, 아니면 뒤에 둔다
        jl = [x for x in jp.split(chr(10)) if x.strip()]
        lead = bool(jl) and bool(MARK.search(jl[0])) and                not MARK.sub('', jl[0]).strip().strip(TAIL)
        nv = chr(10).join((code + hl) if lead else (hl + code))
        if nv != ko:
            if fixed < 6:
                L('#18', 'i%d blk%s' % (i, e['blk']), ko, nv,
                  '[7d]이름·[7e]기체명·[7f]무기명은 실행 중 글자로 바뀐다 — 원문처럼 따로 둔다')
            if WRITE: e['ko'] = nv
            fixed += 1; n += 1
    if failed:
        L('#18', '미처리', '3줄 안에 못 담은 항목', '%d건' % failed, '')
    L('#18', '합계', '인라인 코드 줄 복구', '%d개 항목' % fixed, '')

    # 코드 줄 위치 보정 — 원문이 맨 앞에 둔 코드가 뒤로 가 있으면 되돌린다
    moved = 0
    for i, e in enumerate(ent):
        ko, jp = e.get('ko') or '', e.get('jp') or ''
        lines = ko.split(chr(10))
        if len(lines) < 2: continue
        jl = [x for x in jp.split(chr(10)) if x.strip()]
        if not jl: continue
        def alone(x):
            return bool(MARK.search(x)) and not MARK.sub('', x).strip().strip(TAIL)
        if alone(jl[0]) and alone(lines[-1]) and not alone(lines[0]):
            nv = chr(10).join([lines[-1]] + lines[:-1])
            if moved < 3: L('#18', 'i%d blk%s' % (i, e['blk']), ko, nv, '원문처럼 코드를 맨 앞에')
            if WRITE: e['ko'] = nv
            moved += 1; n += 1
    if moved: L('#18', '보정', '코드 줄 위치', '%d건' % moved, '')

    # 개별 수정
    for i, old, new, iss, why in BT_FIX:
        if old == new: continue
        e = ent[i]
        if (e.get('ko') or '') == old or old in (e.get('ko') or ''):
            nv = (e['ko']).replace(old, new)
            L(iss, 'i%d blk%s' % (i, e['blk']), e['ko'], nv, why)
            if WRITE: e['ko'] = nv
            n += 1
        else:
            L(iss, 'i%d' % i, '(못 찾음) ' + old, repr(e.get('ko')), why)

    # 표기 통일
    for old, new, blk, iss, why in BT_SUB:
        if old == new: continue
        c = 0
        for i, e in enumerate(ent):
            if blk is not None and e['blk'] != blk: continue
            ko = e.get('ko') or ''
            if old in ko:
                nv = ko.replace(old, new)
                if c < 2: L(iss, 'i%d blk%s' % (i, e['blk']), ko, nv, why)
                if WRITE: e['ko'] = nv
                c += 1; n += 1
        L(iss, '합계', '%s → %s' % (old, new), '%d건' % c, '')

    if WRITE:
        json.dump(d, open(BATTLE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return n


def patch_trans():
    d = json.load(open(TRANS, encoding='utf-8'))
    n = 0
    for off, new, iss, why in TR_FIX:
        for e in d['entries']:
            if e['off'] == off:
                if e['ko'] != new:
                    L(iss, off, e['ko'], new, why)
                    if WRITE: e['ko'] = new
                    n += 1
                break
        else:
            L(iss, off, '(없음)', new, why)
    if WRITE:
        json.dump(d, open(TRANS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return n


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print('모드:', '반영(--write)' if WRITE else '미리보기')
    a = patch_xlsx(); b = patch_battle(); c = patch_trans()
    for iss, where, before, after, why in log:
        print('\n[%s] %s %s' % (iss, where, ('— ' + why) if why else ''))
        print('   - %s' % str(before).replace('\n', ' ⏎ ')[:170])
        print('   + %s' % str(after).replace('\n', ' ⏎ ')[:170])
    print('\n합계: 시나리오 %d / 전투 %d / 시스템 %d' % (a, b, c))
