rem -S none : 2차 압축 끔 (UniPatcher 등 구버전/축소 xdelta3 호환. -S djw 는 "XDelta3 내부 오류" 유발)
xdelta.exe -B 16777216 -e -9 -S none -vfs "Super Robot Taisen J (Japan).gba" "srwj_korean_all.gba" "Super.Robot.Taisen.J.Korean._v1.9.xdelta"

pause
