#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ミリをメートルに.py
# by Yukiharu Iwamoto
# 2025/6/10 5:04:53 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行
# -p -> paraFoamを実行する

import signal
import subprocess
import os
import sys
from utilities import misc
from utilities import rmObjects

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = exec_paraFoam = False
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-N': # Non-interactive
                pass
            elif sys.argv[i] == '-p':
                exec_paraFoam = True
            i += 1

    boundary = os.path.join('constant', 'polyMesh', 'boundary')
    if not os.path.isfile(boundary):
        print('エラー: %sファイルがありません．' % boundary)
        sys.exit(1)
    if misc.isConvertedMillimeterIntoMeter():
        print('長さの単位はすでにメートルです．')
    else:
        misc.convertLengthUnitInMillimeterToMeter()

    if interactive:
        exec_paraFoam = True if (raw_input if sys.version_info.major <= 2 else input)(
            '\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam, ambient = 0.0, diffuse = 1.0)

    rmObjects.removeInessentials()
