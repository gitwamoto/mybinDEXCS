#!/usr/bin/env python
# -*- coding: utf-8 -*-
# yPlusを求める.py
# by Yukiharu Iwamoto
# 2022/6/30 8:33:51 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行
# -b time_begin: 壁座標の計算を開始する時間をtime_beginにする．指定しない場合は最も小さい値を持つ時間になる
# -e time_end: 壁座標の計算の計算を終了する時間をtime_endにする．指定しない場合は最も大きい値を持つ時間になる
# -0: 0秒のデータを含める
# -j: 壁座標の計算を実行せず，過去に計算した壁座標の結果を消去するだけ
# -p -> paraFoamを実行する

import sys
import signal
import subprocess
import os
import glob
import shutil
from utilities import misc
from utilities import rmObjects

def handler(signal, frame):
    rmObjects.removeInessentials()
    sys.exit(1)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler) # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)

    just_delete_previous_files = False
    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = exec_paraFoam = False
        time_begin, time_end, noZero = '-inf', 'inf', True
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-N': # Non-interactive
                pass
            elif sys.argv[i] == '-b':
                i += 1
                time_begin = sys.argv[i]
            elif sys.argv[i] == '-e':
                i += 1
                time_end = sys.argv[i]
            elif sys.argv[i] == '-0':
                noZero = False
            elif sys.argv[i] == '-j':
                just_delete_previous_files = True
            elif sys.argv[i] == '-p':
                exec_paraFoam = True
            i += 1

    regions = []
    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
        if os.path.isfile(os.path.join(d, 'fvSolution')):
            regions.append(os.path.basename(os.path.dirname(d)))
    for d in glob.iglob('*' + os.sep):
        try:
            float(os.path.dirname(d))
            f = os.path.join(d, 'yPlus')
            if os.path.isfile(f):
                os.remove(f)
            for r in regions:
                f = os.path.join(d, r, 'yPlus')
                if os.path.isfile(f):
                    os.remove(f)
        except:
            pass
    d = os.path.join('postProcessing', 'yPlus')
    if os.path.isdir(d):
        shutil.rmtree(d)
    if just_delete_previous_files:
        sys.exit(0) # 正常終了

    print('壁座標yPlus（y+ < 5で粘性底層，5 < y+ < 30で遷移層，30 < y+で乱流層に入る）を求めます．')
    if interactive:
        time_begin, time_end, noZero = misc.setTimeBeginEnd('壁座標の計算')
    # https://www.openfoam.com/documentation/guides/latest/doc/guide-fos-field-yPlus.html
    # Example by using the postProcess utility: <solver> -postProcess -func yPlus
    if len(regions) == 0:
        misc.execPostProcess(time_begin, time_end, noZero, func = 'yPlus')
    else:
        for r in regions:
            misc.execPostProcess(time_begin, time_end, noZero, func = 'yPlus', region = r)

    print('\n結果は各時間のフォルダに書き出され，さらにpostProcessingフォルダにまとめが保存されます．')

    if interactive:
        exec_paraFoam = True if (raw_input if sys.version_info.major <= 2 else input)(
            '\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam)

    rmObjects.removeInessentials()
