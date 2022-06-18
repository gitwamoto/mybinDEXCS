#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 並列計算結果をまとめる.py
# by Yukiharu Iwamoto
# 2021/7/18 8:26:42 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行
# -p -> paraFoamを実行する

import os
import signal
import sys
import shutil
import re
import subprocess
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

    command = 'reconstructPar -newTimes -noFunctionObjects'
    if os.path.exists(os.path.join('constant', 'regionProperties')):
        command += ' -allRegions'
    subprocess.call(command, shell = True)
    rmObjects.removeProcessorDirs('noLatest')

    if interactive:
        exec_paraFoam = True if (raw_input if sys.version_info.major <= 2 else input)(
            '\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam)

    rmObjects.removeInessentials()
