# -*- coding: utf-8 -*-
"""판본 쌍 번역 뒤바뀜 전수 감사.

왜 보는가
--------
같은 장면이라도 **조건에 따라 다른 판본**이 쓰이는 대사가 있다.
  · 어떤 인물이 아직 살아 있나 / 이미 빠졌나
  · 서브파일럿이 누구인가 (카티아 / 테니아 / 멜루아)
  · 특정 기체·부대를 얻었나
이런 판본은 보통 **연속한 턴에 같은 화자ID**로 나란히 들어 있다.
번역할 때 두 판본의 순서를 혼동하면, 조건에 맞지 않는 대사가 화면에 뜬다.

  실제 사례: 이슈 #30 — 캐서린이 격추되지 않았는데도 쟝갈이
            「캐서린은 후퇴했나 보군」 이라고 말했다. 원문 t280 은
            `わかっておる`(알고 있네), t281 이 `行き違いでカザリーンは撤退したか`
            인데 번역이 서로 맞바뀌어 있었다.

어떻게 찾나
----------
연속한 두 턴(같은 블록·같은 화자ID)에 대해,
  원문 A 에만 있는 고유명사가 **번역 B 에만** 들어 있으면 뒤바뀜으로 본다.
고유명사는 NAME_KO 표(일본어 ↔ 한국어 표기)로 대조한다.

사용법:
  python audit_variant_swap.py [--xlsx 파일]
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_XLSX = os.path.join(HERE, 'srwj_matched_all_0625.xlsx')

NAME_KO = {
    'カザリーン': '캐서린', 'ジャンギャル': '쟝갈', 'ハイネル': '하이넬',
    'ナデシコ': '나데시코', 'アークエンジェル': '아크엔젤', 'ボルテス': '볼테스',
    'コン・バトラー': '컴・배틀러', 'エステバリス': '에스테바리스', 'ユリカ': '유리카',
    'アキト': '아키토', 'カティア': '카티아', 'テニア': '테니아', 'メルア': '멜루아',
    'クルツ': '쿠르츠', 'マオ': '마오', 'ソウスケ': '소스케', 'ガウルン': '가우룽',
    'キラ': '키라', 'アスラン': '아스란', 'ムウ': '무우', 'ナタル': '나탈',
    'バルトフェルド': '발트펠트', 'ドモン': '도몬', 'レイン': '레인',
    'サイ・サイシー': '사이사이시', 'ジョルジュ': '죠르주', 'アルゴ': '아르고',
    'エイジ': '에이지', 'ミリィ': '밀리', 'ブレード': '블레이드', 'ユウ': '유우',
    'ヒメ': '히메', 'カナン': '카난', 'ネリー': '네리', 'ジョナサン': '조나단',
    'マサト': '마사토', 'ミク': '미쿠', '甲児': '코우지', 'さやか': '사야카',
    '鉄也': '테츠야', '豹馬': '효마', 'ボンタくん': '본타군',
}


def load(xlsx):
    import openpyxl
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = []
    for r, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
        rows.append((r, str(row[0]), str(row[1]), str(row[4]),
                     str(row[9] or ''), str(row[10] or '')))
    wb.close()
    return rows


def find_swapped(rows):
    out, seen = [], set()
    for i in range(len(rows) - 1):
        r1, b1, t1, c1, k1, j1 = rows[i]
        r2, b2, t2, c2, k2, j2 = rows[i + 1]
        if b1 != b2 or c1 != c2:
            continue
        if not (j1 and j2 and k1 and k2) or k1 == k2 or j1 == j2:
            continue
        for jp_name, ko_name in NAME_KO.items():
            in_j1, in_j2 = jp_name in j1, jp_name in j2
            in_k1, in_k2 = ko_name in k1, ko_name in k2
            swapped = (in_j1 and not in_j2 and in_k2 and not in_k1) or \
                      (in_j2 and not in_j1 and in_k1 and not in_k2)
            if swapped and (r1, r2) not in seen:
                seen.add((r1, r2))
                out.append((r1, r2, b1, c1, jp_name, ko_name))
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    xlsx = sys.argv[sys.argv.index('--xlsx') + 1] if '--xlsx' in sys.argv else DEFAULT_XLSX
    rows = load(xlsx)
    hits = find_swapped(rows)
    d = {r: (b, t, c, k, j) for r, b, t, c, k, j in rows}
    print('=' * 68)
    print('판본 쌍 번역 뒤바뀜 감사 — 총 %d턴 검사' % len(rows))
    print('=' * 68)
    print('   의심 쌍: %d' % len(hits))
    for r1, r2, blk, cid, jn, kn in hits:
        print('\n── R%d ↔ R%d  blk%s cid=%s  (단서 %s/%s)' % (r1, r2, blk, cid, jn, kn))
        for r in (r1, r2):
            b, t, c, k, j = d[r]
            print('   R%-6s t%-5s KO %s' % (r, t, k.replace('\n', ' / ')[:92]))
            print('                 JP %s' % j.replace('\n', ' / ')[:92])
    if not hits:
        print('   → 뒤바뀐 판본 쌍 없음')
    return 0 if not hits else 1


if __name__ == '__main__':
    sys.exit(main())
