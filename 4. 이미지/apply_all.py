# -*- coding: utf-8 -*-
"""SRW J 그래픽 한글화 원클릭 적용

사용법:
  python apply_all.py <입력.gba> <출력.gba> [--render]

한 번 실행으로 다음을 모두 적용:
  1) 타이틀 화면(한글 로고 포함) — 자산 스냅샷(타이틀로고/logo_snapshot.bin) 이식
  2) 시나리오 제목 68화 — 동봉 PNG 삽입 (--render 시 titles_ko.txt에서 새로 렌더)
  3) 전투 메시지 70종 — 전투메시지/한국어 PNG 삽입
  4) 부팅 저작권 화면 — 저작권화면/credits_ko.txt에서 렌더·삽입
  5) 인터페이스 4종 — 인터페이스/한국어 PNG 삽입

입력 ROM: 텍스트 패치가 적용된 SRW J ROM (그래픽 패치 적용 전 권장).
같은 ROM에 두 번 실행해도 동작하지만 재배치 영역(0x1800000~)이 누적 사용됩니다.
"""
import sys, os, struct
import importlib.util

KIT = os.path.dirname(os.path.abspath(__file__))
# 공통 라이브러리만 경로에 추가(여러 폴더에 동명 모듈이 있어도 충돌 없게,
# 각 단계의 도구는 아래 _load로 해당 폴더에서 명시적으로 불러온다)
sys.path.insert(0, os.path.join(KIT, '공통'))
import scn_title_lib as L  # noqa: E402


def _load(folder, modname):
    """KIT/<folder>/<modname>.py 를 그 위치에서 명시적으로 로드(경로 의존 제거)."""
    path = os.path.join(KIT, folder, modname + '.py')
    spec = importlib.util.spec_from_file_location(f'{folder}_{modname}', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def step_logo(rom):
    path = os.path.join(KIT, '타이틀로고', 'logo_snapshot.bin')
    blob = open(path, 'rb').read()
    n = struct.unpack_from('<I', blob, 0)[0]
    p = 4
    for _ in range(n):
        i, off, ln = struct.unpack_from('<III', blob, p)
        p += 12
        rom[off:off + ln] = blob[p:p + ln]
        struct.pack_into('<I', rom, L.BASE + i * 4, off - L.BASE)
        p += ln
    print(f'[1/5] 타이틀 화면 자산 {n}개 이식 완료')


def step_titles(rom, render):
    import glob, re
    sti = _load('시나리오제목', 'scn_title_insert')
    png_to_cells, insert_ep = sti.png_to_cells, sti.insert_ep
    pngdir = os.path.join(KIT, '시나리오제목', '시나리오제목_한글')
    # PNG는 titles_ko.txt + neodgm.ttf 로 언제든 재생성되는 산출물이라 저장소에 넣지 않는다.
    # 없으면(=갓 clone 한 상태) 조용히 0화가 되지 않도록 여기서 자동 렌더한다.
    if not render and not glob.glob(os.path.join(pngdir, 'e*_img*.png')):
        print('    · 시나리오제목 PNG가 없어 titles_ko.txt에서 렌더합니다...')
        render = True
    if render:
        import subprocess
        subprocess.run([sys.executable, os.path.join(KIT, '시나리오제목', 'make_titles.py'),
                        os.path.join(KIT, '시나리오제목', 'titles_ko.txt'), pngdir,
                        '--font', os.path.join(KIT, '시나리오제목', 'neodgm.ttf')],
                       check=True, cwd=os.path.join(KIT, '시나리오제목'))
    cnt = 0
    for pth in sorted(glob.glob(os.path.join(pngdir, 'e*_img*.png'))):
        m = re.search(r'e(\d{2})_', os.path.basename(pth))
        if not m:
            continue
        cells = png_to_cells(pth)
        insert_ep(rom, int(m.group(1)), cells, grow=True)
        cnt += 1
    if cnt == 0:
        raise SystemExit(f'시나리오 제목 PNG를 하나도 찾지 못했습니다: {pngdir}')
    print(f'[2/5] 시나리오 제목 {cnt}화 삽입 완료')


def _jp_dir(folder):
    """원본(일본어) PNG 폴더. 없으면 None — img_replace 가 ref_palettes.json 을 쓴다.

    원본 PNG는 게임 그래픽이라 저장소에 넣지 않는다. 삽입에 실제로 필요한 값은
    16색 팔레트와 투명 비율뿐이라 그 표만 ref_palettes.json 으로 동봉한다.
    """
    jp = os.path.join(KIT, folder, '일본어')
    import glob as _g
    return jp if _g.glob(os.path.join(jp, '*.png')) else None


def step_battle(rom):
    img_replace = _load('전투메시지', 'img_replace')
    ko = os.path.join(KIT, '전투메시지', '한국어')
    # img_replace.apply 내부 print 억제 없이 그대로 사용
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        nrel = img_replace.apply(rom, ko, _jp_dir('전투메시지'))
    print(f'[3/5] 전투 메시지 70종 삽입 완료 (재배치 {nrel}건)')


def step_interface(rom):
    img_replace = _load('인터페이스', 'img_replace')
    ko = os.path.join(KIT, '인터페이스', '한국어')
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        nrel = img_replace.apply(rom, ko, _jp_dir('인터페이스'))
    print(f'[5/5] 인터페이스 4종 삽입 완료 (재배치 {nrel}건)')


def step_credits(rom):
    credits_make = _load('저작권화면', 'credits_make')
    table = os.path.join(KIT, '저작권화면', 'credits_ko.txt')
    font = os.path.join(KIT, '저작권화면', 'Galmuri9.ttf')
    S = credits_make.render_screen(credits_make.load_lines(table), font)
    n, cap, *_ = credits_make.insert(rom, S)
    print(f'[4/5] 저작권 화면 삽입 완료 (타일 {n}/{cap})')


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    rom_in, rom_out = sys.argv[1], sys.argv[2]
    render = '--render' in sys.argv
    rom = bytearray(open(rom_in, 'rb').read())
    if len(rom) != 0x2000000:
        print(f'경고: ROM 크기 {len(rom):#x} (예상 0x2000000)')
    step_logo(rom)
    step_titles(rom, render)
    step_battle(rom)
    step_credits(rom)
    step_interface(rom)
    open(rom_out, 'wb').write(rom)
    print('저장:', rom_out)


if __name__ == '__main__':
    main()
