#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Qと渦度を求める.py
# by Yukiharu Iwamoto
# 2022/6/30 8:33:26 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行
# -b time_begin: Qと渦度の計算を開始する時間をtime_beginにする．指定しない場合は最も小さい値を持つ時間になる
# -e time_end: Qと渦度の計算を終了する時間をtime_endにする．指定しない場合は最も大きい値を持つ時間になる
# -0: 0秒のデータを含める
# -j: Qと渦度の計算を実行せず，過去に計算したQと渦度の結果を消去するだけ
# -p -> paraFoamを実行する

import sys
import signal
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

    for d in glob.iglob('*' + os.sep):
        try:
            float(os.path.dirname(d))
            for t in ('Q', 'vorticity'):
                f = os.path.join(d, 'Q')
                if os.path.isfile(f):
                    os.remove(f)
        except:
            pass
    if just_delete_previous_files:
        sys.exit(0) # 正常終了

    print('速度勾配テンソルの第2不変量Q（正だと回転が強く，負だとせん断が強い）と渦度vorticityを求めます．')
    print('*** ParaViewで見たいだけならば，ParaViewのフィルタGradient of Unstructured DataSetを使う事もできます．' +
        'Gradientsの成分は0が∂ u/∂ x，1が∂ u/∂ y，2が∂ u/∂ z，3が∂ v/∂ x，4が∂ v/∂ y，...の順です．')
    if interactive:
        time_begin, time_end, noZero = misc.setTimeBeginEnd('Qと渦度の計算')
    # https://www.openfoam.com/documentation/guides/latest/doc/guide-fos-field-Q.html
    # Example by using the postProcess utility: postProcess -func Q
    misc.execPostProcess(time_begin, time_end, noZero, func = 'Q', solver = False)
    # https://www.openfoam.com/documentation/guides/latest/doc/guide-fos-field-vorticity.html
    # Example by using the postProcess utility: postProcess -func vorticity
    misc.execPostProcess(time_begin, time_end, noZero, func = 'vorticity', solver = False)
    print('\n結果は各時間のフォルダに書き出されます．')

    if interactive:
        exec_paraFoam = True if (raw_input if sys.version_info.major <= 2 else input)(
            '\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam)

    rmObjects.removeInessentials()
