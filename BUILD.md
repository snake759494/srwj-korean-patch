# 직접 빌드하기 — 처음부터 끝까지

이 문서 하나로 **아무것도 없는 PC에서** 원본 일본판 ROM만 준비하면 한글 패치 ROM과
배포용 `.xdelta` 를 스스로 만들 수 있습니다. 저장소를 clone 하면 필요한 도구·번역
데이터·폰트·한글 이미지가 **전부 들어 있습니다.**

> 게임 ROM과 원본(일본어) 그래픽만 저작권상 넣지 않았습니다.
> 원본 그래픽은 빌드에 필요 없습니다 — 삽입에 실제로 쓰이는 값(16색 팔레트·투명 비율)만
> `ref_palettes.json` 으로 동봉했고, 이것만으로 결과 ROM이 **바이트 단위까지 동일**하게 나옵니다.

---

## 0. 준비물

| 항목 | 설명 |
|---|---|
| **원본 일본판 ROM** | `Super Robot Taisen J (Japan).gba` · 16,777,216 바이트<br>MD5 `ef32f93816b6dbcf788f08faf1e71450` · 게임코드 `B6JJ`<br>**합법적으로 소유한 것만 사용하세요. 저장소에 없습니다.** |
| **Python** | 3.8 이상 (Windows/macOS/Linux) |
| **파이썬 패키지** | `pip install openpyxl pillow` |
| **xdelta** | 배포 패치를 만들 때만 필요 ([공식 배포처](https://github.com/jmacd/xdelta/releases)) |

```bash
git clone https://github.com/snake759494/srwj-korean-patch.git
cd srwj-korean-patch
pip install openpyxl pillow
```

원본 ROM을 **저장소 최상위**와 **`0.시나리오/`** 두 곳에 같은 이름으로 두세요.

```
srwj-korean-patch/
├─ Super Robot Taisen J (Japan).gba      ← 여기 (xdelta 생성용)
└─ 0.시나리오/
   └─ Super Robot Taisen J (Japan).gba   ← 그리고 여기 (빌드 입력)
```

---

## 1. 빌드 — 5단계를 순서대로

**반드시 0 → 1 → 2 → 3 → 4 순서**입니다. 각 단계의 출력 ROM이 다음 단계의 입력이 됩니다.
Windows 에서는 각 폴더의 `!bulid.bat` 를 눌러도 되고, 아래 명령을 그대로 써도 됩니다.

> 한글 출력이 깨지면 먼저 `set PYTHONIOENCODING=utf-8` (cmd) 또는
> `$env:PYTHONIOENCODING='utf-8'` (PowerShell) 을 실행하세요.

### 0단계 — 시나리오 대사 (약 1~2분)

```bash
cd "0.시나리오"
python patch_all.py --xlsx srwj_matched_all_0625.xlsx --expand-dict --rom "Super Robot Taisen J (Japan).gba" --out srwj_korean_all_s.gba
```

전 70챕터 대사를 삽입하고 **ROM을 16MB → 32MB로 자동 확장**합니다.
끝에 `번역 챕터 69개 중 파싱 정상 69, 실패 0` 이 나오면 성공입니다.

```bash
cp srwj_korean_all_s.gba "../1. 폰트변경/"
```

### 1단계 — 한글 폰트 이식 (약 30초)

```bash
cd "../1. 폰트변경"
python fill_hangul_galmuri.py srwj_korean_all_s.gba srwj_korean_all_sf0.gba --font Galmuri11.ttf --size 12 --ox 1 --oy -1
python patch_glyph.py srwj_korean_all_sf0.gba srwj_korean_all_sf.gba
cp srwj_korean_all_sf.gba "../2. 전투대사패치/"
```

한자 글리프 2350자 자리에 한글 `가`~`힣` 비트맵을 덮어씁니다.

### 2단계 — 전투 대사·합체기 (약 30초)

```bash
cd "../2. 전투대사패치"
python 패치하기.py srwj_korean_all_sf.gba srwj_korean_all_sfc.gba
cp srwj_korean_all_sfc.gba "../3. SJIS추출/input/out.gba"
```

### 3단계 — 메뉴·시스템 텍스트 (약 10초)

입력 파일 이름이 **반드시 `input/out.gba`** 여야 합니다.

```bash
cd "../3. SJIS추출"
python build_patch.py
cp "output/슈퍼로봇대전J_한글.gba" "../4. 이미지/"
```

### 4단계 — 그래픽 한글화 (약 1분, 최종)

```bash
cd "../4. 이미지"
python apply_all.py "슈퍼로봇대전J_한글.gba" srwj_korean_all.gba
```

시나리오 제목 PNG는 저장소에 없지만 `titles_ko.txt` + `neodgm.ttf` 로 이 단계에서
자동 렌더되므로(`… titles_ko.txt에서 렌더합니다` 메시지) 따로 준비할 것이 없습니다.

완성된 `srwj_korean_all.gba` (32MB)를 에뮬레이터에서 실행하면 됩니다.

### 제대로 빌드됐는지 확인

v2.3.1 기준으로, 위 절차를 그대로 따르면 결과 ROM이 **바이트 단위까지 동일**하게 나옵니다.

```bash
md5sum "4. 이미지/srwj_korean_all.gba"
```

| | 값 |
|---|---|
| 크기 | 33,554,432 바이트 (32MB) |
| MD5 | `f9828af24d850d80094aed33fc9a3d47` |

이 값은 빈 폴더에 `git clone` 만 하고 원본 ROM 하나를 넣어 0~4단계를 돌려 확인한 것입니다.
값이 다르면 단계를 건너뛰었거나 번역 파일을 수정한 경우입니다(수정했다면 다른 게 정상입니다).

### 배포용 xdelta 만들기 (선택)

```bash
cp "4. 이미지/srwj_korean_all.gba" .
xdelta -B 16777216 -e -9 -S none -vfs "Super Robot Taisen J (Japan).gba" srwj_korean_all.gba "Super.Robot.Taisen.J.Korean._v2.3.1.xdelta"
```

> **`-S none` 은 반드시 넣으세요.** 빼면 UniPatcher(안드로이드) 등에서
> `XDelta3 내부 오류`가 납니다. 패치가 ~18% 커지는 대신 어디서나 적용됩니다.

만든 패치는 이렇게 검증하세요 — 결과 MD5가 원본 ROM과 같아야 정상입니다.

```bash
xdelta -d -s "Super Robot Taisen J (Japan).gba" "Super.Robot.Taisen.J.Korean._v2.3.1.xdelta" test.gba
```

---

## 2. 번역만 고치고 싶다면

ROM을 직접 만질 필요 없이 **데이터 파일의 한국어만** 고친 뒤 해당 단계부터 다시 빌드하면 됩니다.

| 고칠 내용 | 파일 | 수정할 곳 | 다시 빌드 |
|---|---|---|---|
| 스토리 대사 | `0.시나리오/srwj_matched_all_0625.xlsx` | **J열**(한국어) | 0 → 4단계 전부 |
| 전투 대사·합체기 | `2. 전투대사패치/battle_dialogue.json` | `ko` 필드 | 2 → 4단계 |
| 메뉴·용어·승패조건 | `3. SJIS추출/translations.json` | `ko` 필드 | 3 → 4단계 |
| 시나리오 제목 | `4. 이미지/시나리오제목/titles_ko.txt` | 제목 문구 | 4단계 (`--render` 옵션) |
| 저작권 화면 | `4. 이미지/저작권화면/credits_ko.txt` | 문구 | 4단계 |

엑셀의 **K열(일본어 원문)과 I열(번역용 원문)은 매칭 키**이므로 절대 건드리지 마세요.

### 반드시 지켜야 할 규칙

1. **이름 변수 `①②③④⑤⑥` 는 개수를 그대로 유지**하세요. 게임이 실행 중 이름으로 바꿉니다.
   `①`·`③`=주인공 이름, `②`=성, `④`=풀네임, `⑤`=기체명.
   변수 뒤 조사는 **받침 없는 이름 기준**으로: `는/를/가/와/야/라면` (❌ `이/을/과/아`)
2. **일본어 문자(히라가나·가타카나·한자) 금지.** 남으면 미완성 번역입니다.
3. **한글은 완성형 2350자(KS X 1001)만.** `떄`·`뷁` 같은 글자는 폰트에 없어 안 나옵니다.
   낱자모(`ㄱ`, `ㅏ`)도 불가합니다.
4. **전투 대사는 3줄 이하.** 4줄 이상이면 화자가 도몬으로 고정되는 버그가 납니다.
5. `#|`, `%s`, `%-d`, `&G`, `「」`, `、`, `。` 등 **제어·기호는 그대로** 두세요.
6. **승패조건은 고정 폭**입니다. 바이트 길이를 원문과 정확히 맞춰야 하며
   (모자라면 전각공백 `　`으로 채움), 표시 폭도 원문 칸수를 넘으면 통째로 안 나옵니다.
7. 말줄임표(`…`, `...`) 뒤에 단어가 오면 **한 칸 띄우세요.** 게임에서 `・・・`(3칸)로
   펼쳐져 줄바꿈이 어긋납니다.

### 검사 도구

빌드 전에 규칙 위반을 미리 잡을 수 있습니다.

```bash
python "2. 전투대사패치/audit_battle_jp.py"      # 전투대사 일본어 잔존·미번역 감사
python "2. 전투대사패치/audit_battle_bytes.py"   # 전투 구간 바이트 단위 완전성
python "3. SJIS추출/verify.py"                   # 시스템 텍스트 검증
python "0.시나리오/audit_trailing_empty.py"      # 대사 끝 빈 줄(닫힘 괄호만) 검사
```

---

## 3. 저장소에 없는 것과 그 이유

| 항목 | 이유 | 대처 |
|---|---|---|
| 게임 ROM (`*.gba`) | 저작권 | 합법적으로 소유한 것을 직접 준비 |
| 원본(일본어) 그래픽 PNG | 게임 그래픽 | **불필요** — 삽입에 쓰는 팔레트·투명비율만 `ref_palettes.json` 으로 동봉 |

원본 PNG를 직접 뽑아 보고 싶다면(색 확인·재편집용) 각 폴더의 추출기를 쓰면 됩니다.
빌드에는 필요 없습니다.

```bash
cd "4. 이미지/전투메시지"
PYTHONPATH=../공통 python bm_extract.py <32MB로_패치된.gba> 한국어 일본어
```

### 동봉한 폰트

| 폰트 | 쓰임 | 라이선스 |
|---|---|---|
| **Galmuri11** | 게임 본문 한글 2350자 | SIL Open Font License 1.1 |
| **Galmuri9** | 부팅 저작권 화면 | SIL Open Font License 1.1 |
| **NeoDunggeunmo(neodgm)** | 시나리오 제목 | SIL Open Font License 1.1 |

세 폰트 모두 OFL 1.1로 재배포가 허용되어 동봉했습니다. 원 저작자에게 감사드립니다.
(Galmuri — quiple / NeoDunggeunmo — 둥근모꼴 계열)

---

## 4. 문제 해결

| 증상 | 원인·해결 |
|---|---|
| `UnicodeEncodeError: 'cp949'` | `PYTHONIOENCODING=utf-8` 설정 |
| `[오류] input/out.gba 가 없습니다` | 3단계 입력은 파일명이 정확히 `input/out.gba` 여야 함 |
| 3단계에서 `크기가 32MB가 아닙니다` | 0·1·2단계를 건너뛰었는지 확인 (누적 적용이 원칙) |
| 폰트 파일을 못 찾음 | 1단계는 `1. 폰트변경/` 안에서 실행해야 함 |
| `코드 미배정 문자 N개` | 폰트 2350자 밖 글자를 번역에 썼음. 메시지의 글자를 고칠 것 |
| 이미지 단계에서 추출 실패 | 입력 ROM이 32MB인지, 앞 단계를 모두 거쳤는지 확인 |
| 패치가 UniPatcher에서 실패 | xdelta 생성 시 `-S none` 을 빠뜨림 |

---

## 5. 구조를 더 알고 싶다면

- [README.md](README.md) — 파이프라인 개요와 한글화 원리(한자 자리 바꿔치기)
- 각 단계 폴더의 `README` — 도구별 상세 설명
- `2. 전투대사패치/subpilot_map/` — 서브파일럿 분기 구조 분석 자료
