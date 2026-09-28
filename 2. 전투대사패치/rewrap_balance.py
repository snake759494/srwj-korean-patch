# -*- coding: utf-8 -*-
"""전투 대사 균형 줄바꿈 — 끊는 자리를 다시 고른다

왜 필요한가
------------
전투 대사는 자동 줄바꿈이 없고 번역문의 '\\n' 을 그대로 쓴다. 그래서
"나도 할 수 / 있어!" 처럼 구가 두 줄로 갈리거나 한 글자만 남기고 끊기는 곳이 많다
(제보 #1 의 '줄맞춤 필요' 다수).

무엇을 하나
------------
글자는 하나도 바꾸지 않고, 같은 폭 예산 안에서 끊는 자리만 다시 고른다.
  · 첫 줄 예산 8칸 — 화면에서 첫 줄 앞에 '이름「' 이 붙기 때문이다.
    대사창은 15칸이고 화자명은 최대 6~7자이므로 8칸이 안전한 상한이다.
    (v2.3 의 10칸은 이름이 6자 이상이면 창을 넘길 수 있었다)
  · 나머지 줄 14칸, 최대 3줄 (4줄이면 화자가 도몬으로 고정되는 버그)
  · 한 글자만 남기고 끊으면 벌점, 문장부호 뒤에서 끊으면 가점
합체기 블록(193)은 바이트 길이 보존 대상이라 건드리지 않는다.

사용법:
  python rewrap_balance.py           # 미리보기
  python rewrap_balance.py --go      # battle_dialogue.json 에 반영
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, 'battle_dialogue.json')

FIRST_W_BUDGET = 8      # 첫 줄: 이름「 자리를 뺀 나머지
MAX_W = 14              # 둘째 줄부터
MAX_L = 3
LEN_PRESERVE = {193}

VAR_LEN = {'①': 3, '②': 3, '③': 3, '④': 7, '⑤': 6, '⑥': 6}
MARK = re.compile(r'\[[0-9a-f]{2}\]')
END_SENT = ('。', '.', '!', '?', '！', '？', '…', '・')
END_COMMA = (',', '、')
FIRST_WEIGHT, ORPHAN, SENT_BONUS, COMMA_BONUS = 2, 60, 40, 15


def norm(s):
    s = MARK.sub('', s or '')
    s = s.replace('…', '・・・').replace('...', '・・・').replace('‥', '・・')
    return re.sub(r'[.．]{2,}', lambda m: '・' * len(m.group()), s)


def width(s):
    return sum(VAR_LEN.get(c, 1) for c in norm(s))


def tokens(text):
    return [t for t in text.replace('\n', ' ').replace('　', ' ').split(' ') if t]


def plan(toks, budgets):
    """토큰을 budgets 줄 수에 맞춰 나눈다. 못 맞추면 None."""
    n, m = len(budgets), len(toks)
    w = [width(t) for t in toks]
    pre = [0]
    for x in w:
        pre.append(pre[-1] + x)
    INF = float('inf')
    dp = [[INF] * (n + 1) for _ in range(m + 1)]
    back = [[None] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = 0
    for li in range(n):
        for i in range(m):
            if dp[i][li] == INF:
                continue
            for j in range(i + 1, m + 1):
                wd = pre[j] - pre[i] + (j - i - 1)
                if wd > budgets[li]:
                    break
                slack = budgets[li] - wd
                c = slack * slack * (FIRST_WEIGHT if li == 0 else 1)
                if li < n - 1:
                    if w[j - 1] <= 1:
                        c += ORPHAN
                    if toks[j - 1].endswith(END_SENT):
                        c -= SENT_BONUS
                    elif toks[j - 1].endswith(END_COMMA):
                        c -= COMMA_BONUS
                if dp[i][li] + c < dp[j][li + 1]:
                    dp[j][li + 1] = dp[i][li] + c
                    back[j][li + 1] = i
    if dp[m][n] == INF:
        return None
    out, j, li = [], m, n
    while li > 0:
        i = back[j][li]
        out.append(' '.join(toks[i:j]))
        j, li = i, li - 1
    return out[::-1]


def rewrap(text):
    """가장 적은 줄 수로, 그 안에서 가장 균형 있게."""
    toks = tokens(text)
    if not toks:
        return None
    for n in range(1, MAX_L + 1):
        budgets = [FIRST_W_BUDGET] + [MAX_W] * (n - 1)
        r = plan(toks, budgets)
        if r:
            return r
    return None


def main():
    go = '--go' in sys.argv
    d = json.load(open(PATH, encoding='utf-8'))
    ent = d['entries']
    chg = keep = fail = 0
    samples = []
    for e in ent:
        ko = e.get('ko') or ''
        if not ko.strip() or e['blk'] in LEN_PRESERVE:
            continue
        r = rewrap(ko)
        if r is None:
            fail += 1
            continue
        new = '\n'.join(r)
        if new == ko:
            keep += 1
            continue
        chg += 1
        if len(samples) < 25:
            samples.append((e['blk'], ko, new))
        if go:
            e['ko'] = new
    print('바뀜 %d / 그대로 %d / 못 맞춤 %d' % (chg, keep, fail))
    for blk, a, b in samples:
        print('  blk%-4s %-34s → %s' % (blk, a.replace('\n', ' ⏎ '), b.replace('\n', ' ⏎ ')))
    if go:
        json.dump(d, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('반영 완료')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
