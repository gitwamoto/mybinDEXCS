#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 壁面せん断応力を求める.py
# by Yukiharu Iwamoto
# 2022/3/16 8:16:02 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行
# -b time_begin: 壁面せん断応力の計算を開始する時間をtime_beginにする．指定しない場合は最も小さい値を持つ時間になる
# -e time_end: 壁面せん断応力の計算の計算を終了する時間をtime_endにする．指定しない場合は最も大きい値を持つ時間になる
# -j: 壁面せん断応力の計算を実行せず，過去に計算した壁面せん断応力の結果を消去するだけ
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
        time_begin = '-inf'
        time_end = 'inf'
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
            f = os.path.join(d, 'wallShearStress')
            if os.path.isfile(f):
                os.remove(f)
            for r in regions:
                f = os.path.join(d, r, 'wallShearStress')
                if os.path.isfile(f):
                    os.remove(f)
        except:
            pass
    d = os.path.join('postProcessing', 'wallShearStress')
    if os.path.isdir(d):
        shutil.rmtree(d)
    if just_delete_previous_files:
        sys.exit(0) # 正常終了

    print('壁面せん断応力wallShearStressを求めます．ただし，非圧縮性流体の場合はwallShearStressは壁面せん断応力/密度に相当します．')
    if interactive:
        time_begin, time_end = misc.setTimeBeginEnd('壁面せん断応力の計算')
    # hhttps://www.openfoam.com/documentation/guides/latest/doc/guide-fos-field-wallShearStress.html
    # Example by using the postProcess utility: <solver> -postProcess -func wallShearStress
    if len(regions) == 0:
        misc.execPostProcess(time_begin, time_end, func = 'wallShearStress')
    else:
        for r in regions:
            misc.execPostProcess(time_begin, time_end, func = 'wallShearStress', region = r)

    print('\n結果は各時間のフォルダに書き出され，さらにpostProcessingフォルダにまとめが保存されます．')

    if interactive:
        exec_paraFoam = True if (raw_input if sys.version_info.major <= 2 else input)(
            '\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam)

    rmObjects.removeInessentials()
