# 슈퍼로봇대전 J 한글화 프로젝트 (TRANS‑SRWJ)

<p align="center">
  <img src="docs/title_ko.png" alt="슈퍼로봇대전 J 한글 패치 타이틀 화면" width="480">
</p>

GBA 『슈퍼로봇대전 J』(Super Robot Taisen J, 2005)의 **게임 전반을 한국어화**하는 PC용 파이썬 툴킷과 번역 데이터 모음입니다.
한글 폰트 이식부터 타이틀·이미지, 시나리오 대사, 전투 대사, 메뉴/시스템 텍스트까지 게임 내 텍스트·그래픽을 단계별로 한국어로 교체합니다.

대사 출처 : 추꾸 https://www.chuggu.net/ani/96242633

최종 결과물은 **원본 ROM을 포함하지 않는 `xdelta` 차분 패치**로 배포됩니다.

> ⚠️ **법적 고지 — ROM 미포함**
> 이 저장소에는 게임 ROM이 **포함되어 있지 않으며, 절대 커밋하지 마세요.**
> 원본 일본판 ROM과 패치된 ROM은 저작권 보호 대상입니다. 배포물은 ROM 데이터를 담지 않는
> `xdelta` **차분 패치**뿐입니다. 본인이 **합법적으로 소유한** 일본판 ROM에 직접 적용해 사용하세요.
> `.gitignore` 가 `*.gba`·세이브·이미지 등을 자동 제외합니다. (단, `*.xdelta` 차분 패치는 ROM을 포함하지 않으므로 추적합니다.)

---

## 빠른 시작 — 패치 적용 (플레이어용)

1. **합법적으로 소유한** 일본판 원본 ROM `Super Robot Taisen J (Japan).gba` (16MB) 를 준비합니다.
2. [**Releases**](https://github.com/snake7594/GBA-SRW-J/releases/latest) 에서 최신 `.xdelta` 패치를 내려받습니다.
3. [xdelta](https://github.com/jmacd/xdelta) 로 적용합니다(또는 xdelta UI 도구 사용):

   ```bash
   xdelta -d -s "Super Robot Taisen J (Japan).gba" "Super.Robot.Taisen.J.Korean._v1.8.xdelta" "srwj_korean.gba"
   ```

4. 생성된 `srwj_korean.gba` (한글 적용, 자동 확장으로 32MB) 를 mGBA·VBA 등 에뮬레이터나 플래시카트에서 실행합니다.

> 배포용 `.xdelta` 패치는 저장소 트리가 아니라 **[Releases](https://github.com/snake7594/GBA-SRW-J/releases)** 에 올라갑니다.

---

## 버그·오타 제보

플레이 중 발견한 오류나 오·번역은 **[여기서 제보](https://github.com/snake7594/GBA-SRW-J/issues/new/choose)** 해 주세요. 양식이 준비돼 있습니다.

- 🐞 **버그·오류 제보** — 멈춤·크래시·화면 깨짐 등. 패치 **버전 · 에뮬레이터/기기 · 발생 위치(몇 화) · 증상**을 적어 주시면 빠르게 확인·수정합니다.
- ✏️ **오타·오역 제보** — 대사·메뉴의 잘못되거나 어색한 표현.
- 💬 **질문·잡담** — 제보가 아닌 사용법 문의·의견은 [Discussions](https://github.com/snake7594/GBA-SRW-J/discussions) 에 남겨 주세요.

> 제보 시 스크린샷·세이브 파일(`.sav`)은 큰 도움이 됩니다. **단, 원본/패치 ROM 파일(`*.gba`)은 저작권상 첨부하지 마세요.**

---

## 저장소 구성

| 폴더 / 파일 | 내용 |
|---|---|
| [`1. 폰트변경/`](1.%20폰트변경/) | 한자 글리프 자리에 한글 2350자(KS X 1001)를 비트맵으로 채우는 **폰트 이식** 도구 |
| [`4. 이미지/`](4.%20이미지/) | 타이틀 로고·에피소드 제목·전투 메시지·저작권 화면·UI 아이콘 등 **그래픽 한글화** 도구 |
| [`0. 시나리오/`](0.%20시나리오/) | 전 70챕터 **시나리오 대사** 삽입 도구 + 번역 매칭 엑셀(`srwj_matched_all_*.xlsx`) |
| [`2. 전투대사패치/`](2.%20전투대사패치/) | **전투(배틀) 대사·합체기** 삽입 도구 + `battle_dialogue*.json` |
| [`3. SJIS추출/`](3.%20SJIS추출/) | **메뉴·정신커맨드·아이템 등 시스템 텍스트** 추출·번역(`translations.json`)·빌드 |
| 루트 `!xdelta_e_SRWJ.bat` | 최종 통합 ROM에서 **배포용 차분 패치(xdelta)** 를 만드는 스크립트 (패치 자체는 [Releases](https://github.com/snake7594/GBA-SRW-J/releases)) |

각 폴더에는 자체 `README` 가 들어 있습니다.

---

## 한글화 파이프라인

각 단계는 앞 단계 결과 ROM을 입력으로 받아 누적 적용합니다.

```
원본 일본판 ROM  Super Robot Taisen J (Japan).gba  (16MB)
   │
   ▼  0. 시나리오   patch_all.py    대사 삽입(xlsx) · ROM 16→32MB 확장   → srwj_korean_all_s.gba
   ▼  1. 폰트변경   fill_hangul_galmuri.py + patch_glyph.py  한글 2350자  → srwj_korean_all_sf.gba
   ▼  2. 전투대사   패치하기.py     전투 대사·합체기                      → srwj_korean_all_sfc.gba
   ▼  3. SJIS추출   build_patch.py  메뉴/용어/조건 등 시스템 텍스트        → 슈퍼로봇대전J_한글.gba
   ▼  4. 이미지     apply_all.py    타이틀/제목/전투메시지/저작권/UI       → srwj_korean_all.gba (최종 32MB)
   │
   └──[ xdelta ]──►  배포용 .xdelta 차분 패치 (Releases)
```

> **빌드는 반드시 폴더 번호 0 → 1 → 2 → 3 → 4 순서**로 진행하며, 각 폴더의 `!bulid.bat` 가 그 단계의 명령입니다.
> 한 단계의 출력 ROM을 다음 폴더로 복사한 뒤 그 폴더의 `!bulid.bat` 를 실행합니다. (3단계는 입력을 `3. SJIS추출/input/out.gba` 로 넣습니다.)

> **핵심 원리 — 한글 = 한자 자리 바꿔치기**
> 폰트 단계(1)에서 일본 한자 글리프(2350자) 자리에 한글(`가`~`힣`)을 덮어씁니다. 텍스트(대사·메뉴)에
> 한글을 적을 때는 같은 격자에 있던 한자의 Shift‑JIS 코드를 적습니다 (한글 → EUC‑KR → 같은 바이트를
> EUC‑JP로 해석 = 한자 → 그 한자의 cp932 코드). 글리프 덮어쓰기와 텍스트 기록은 ROM의 서로 다른
> 영역이라 순서와 무관합니다. 한글 대사는 원문보다 길어 원래 자리에 안 들어가면 빈 공간에 새로 기록하고
> 포인터를 갱신하며, 모자라면 ROM을 32MB까지 자동 확장합니다.

---

## 단계별 상세

### 0. 시나리오 — 스토리 대사  *(1단계)*
일본판 원본 ROM에 전 70챕터 대사를 번역 매칭 엑셀에서 읽어 삽입합니다. 모자라면 ROM을 32MB까지 자동 확장합니다.
- `patch_all.py` — 메인 패처. 예: `python patch_all.py --xlsx srwj_matched_all_0625.xlsx --expand-dict --rom "Super Robot Taisen J (Japan).gba" --out srwj_korean_all_s.gba`
  - 옵션: `--reserve N`(화자「 예약 폭, 기본 7) · `--keep-jp`(미번역 턴은 일본어 유지) · `--placeholder-text "..."` · `--addr 0x...`
- `srwj_codec.py`(인코딩) · `srwj_wrap.py`(줄바꿈: 한 줄 14자, 첫 줄 7자) · `srwj_decode.py` · `srwj_parser.py` · `srwj_inject_lib.py` · `merge_xlsx.py`
- 데이터: **`srwj_matched_all_*.xlsx`** (번역 단일 원본 — `J열`(한국어)만 수정), `korea2350.txt`/`japan2350.txt`(폰트 매핑), `seg1_victim_rank.json`

### 1. 폰트변경 — 한글 폰트 이식  *(2단계)*
한자 폰트 슬롯(SJIS `0x889F`~)에 한글 2350자를 16×11 비트맵으로 렌더링해 채웁니다. 반각 가타카나는
폭 압축(max‑pool)으로 처리합니다.
- `fill_hangul_galmuri.py` — 2350자 일괄 채우기. 예: `python fill_hangul_galmuri.py srwj_korean_all_s.gba srwj_korean_all_sf0.gba --font Galmuri11.ttf --size 12 --ox 1 --oy -1`
- `patch_glyph.py` — 개별 글리프 교체, 반각 자동 압축, `--preview` ASCII 미리보기. 예: `python patch_glyph.py srwj_korean_all_sf0.gba srwj_korean_all_sf.gba`
- 폰트는 **Galmuri11** 을 사용합니다. (폰트 파일은 라이선스상 저장소에 미포함 — 별도 준비)

### 2. 전투대사패치 — 전투/합체기 대사  *(3단계)*
JSON 기반으로 전투 대사를 삽입합니다. **도몬 버그(합체기에서 화자가 도몬으로 고정·대사 깨짐)는 한 대사가
4줄 이상일 때 발생**하므로, 모든 전투 대사를 **≤3줄**로 유지합니다(`rewrap_battle.py` 14칸 규칙).
- `패치하기.py` — 메인 런처: `python 패치하기.py srwj_korean_all_sf.gba srwj_korean_all_sfc.gba`
- `build_battle_json.py`(추출) · `srwj_battle_kr_insert.py`(삽입 엔진) · `rewrap_battle.py`(줄바꿈) · `verify_battle.py`(검증) · `srwj_battle_codec.py`(코덱)
- 데이터: `battle_dialogue.json`(패치 사용) / `battle_dialogue_unique.json`(`ko`만 수정), `battle_dialogue_glossary.json`(용어 일관성 적용본 — 참고)
- 입력 ROM은 시나리오·폰트가 적용된 **32MB** 여야 합니다.

### 3. SJIS추출 — 메뉴/용어/조건/시스템 텍스트  *(4단계)*
메뉴·정신커맨드·아이템 설명·승리/패배 조건 등 SJIS 문자열을 추출·번역해 패치합니다. 슬롯에 맞으면 제자리, 넘치면
빈 공간으로 재배치하고 포인터를 갱신합니다. **입력은 `input/out.gba`** (앞 단계 출력)로 넣습니다.
- `build_patch.py` — `translations.json` → 패치 ROM(`output/슈퍼로봇대전J_한글.gba`) + `build_report.json`
- `srwj_codec.py`(코덱) · `verify.py`(검증: 미완성 카나/장음 잔존 탐지) · `remove_ko_spaces.py`(공백 정리)
- 데이터: **`translations.json`** (용어사전 겸 시스템 텍스트, 3267항목 — `ko`만 수정). 조건 문자열은 고정 폭이라 슬롯을 정확히 채워야 합니다.

### 4. 이미지 — 그래픽 한글화  *(5단계, 최종)*
ECD(LZSS) 압축 아카이브(약 15,000개 에셋)를 풀고 한글 이미지를 다시 넣어 **최종 ROM `srwj_korean_all.gba`** 를 만듭니다.
- `apply_all.py` — 타이틀 로고 + 에피소드 제목 68개 + 전투 메시지 70종 + 저작권 화면 + UI 아이콘 일괄 적용. 예: `python apply_all.py 슈퍼로봇대전J_한글.gba srwj_korean_all.gba`
- `make_titles.py` / `scn_title_insert.py` / `scn_title_extract.py` — 에피소드 제목 PNG 렌더·삽입·추출(SCR 타일맵 재생성·타일 중복 제거)
- `img_replace.py` · `bm_extract.py` · `credits_make.py` — 일반 이미지 교체 / 팔레트 보정 추출 / 저작권 화면 생성
- 데이터: `titles_ko.txt`(제목표), `credits_ko.txt`(저작권 문구), `pal_override.json`(팔레트 보정), `시나리오제목/neodgm.ttf`·`저작권화면/Galmuri9.ttf`(렌더 폰트)

### 루트 / 빌드 — 배포 패치 생성
- `!xdelta_e_SRWJ.bat` — 통합 한글 ROM에서 `xdelta` 차분 패치를 생성:
  `xdelta -B 16777216 -e -9 -S none -vfs "Super Robot Taisen J (Japan).gba" "srwj_korean_all.gba" "..._YYYYMMDD.xdelta"`
  - **`-S none`(2차 압축 끔)을 반드시 사용**하세요. `-S djw`(기본 2차 압축)는 [UniPatcher](https://github.com/btimofeev/UniPatcher) 등 구버전·축소 빌드 xdelta3에서 `XDelta3 내부 오류`(unknown secondary compressor ID)를 일으킵니다. 패치가 ~18% 커지지만 PC·모바일 모두에서 적용됩니다.
- 생성된 `.xdelta` 패치는 저장소 트리가 아닌 **[Releases](https://github.com/snake7594/GBA-SRW-J/releases)** 로 배포합니다(원본 ROM 미포함 차분).

---

## 요구 환경
- **Python 3.8+** (Windows / macOS / Linux)
- `openpyxl` — 시나리오 단계의 번역 엑셀(.xlsx) 읽기
- `Pillow` — 폰트·이미지 렌더링 단계
- `xdelta` — 배포 패치 생성/적용 (Windows `xdelta.exe` 동봉 안 함, 각자 준비)

```bash
pip install openpyxl pillow
```

---

## 번역 수정 방법 (번역가용)
직접 ROM을 만지지 않고 **데이터 파일의 한국어만** 고치면 됩니다.
- 시나리오: `srwj_matched_all_*.xlsx` 의 **J열(한국어)** 만 수정 (K열=일본어 원문은 참고용)
- 전투: `battle_dialogue*.json` 의 `ko` 필드만 수정
- 메뉴/용어: `translations.json` 의 `ko` 필드만 수정
- 공통: 카타카나/히라가나·장음 `ー` 가 남아 있으면 미완성. `#| %s %-d &G 「」、。・` 등 제어·기호는 그대로 둘 것. 수정 후 해당 단계 빌드 스크립트를 다시 실행하세요.

---

## 저작권 / 라이선스
- 본 저장소는 **팬 번역(2차적 저작물) 도구·데이터**입니다. 원작 『슈퍼로봇대전 J』 및 등장 작품의 모든 권리는 각 권리자(반프레스토/반다이남코 등)에 있습니다.
- 게임 ROM·그래픽·폰트 원본은 포함하지 않습니다. 배포물은 ROM을 포함하지 않는 `xdelta` 차분 패치뿐입니다.
- 본인이 합법적으로 소유한 ROM에 한해 개인적 용도로 사용하세요.
- 대사의 모든 번역 출처는 아래와 같습니다. https://github.com/sinjunyoung
