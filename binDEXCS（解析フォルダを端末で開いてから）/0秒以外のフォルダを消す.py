#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 0秒以外のフォルダを消す.py
# by Yukiharu Iwamoto
# 2026/6/15 2:33:10 PM

import os
import signal
import subprocess
import shutil
import glob
from utilities import misc
from utilities import rmObjects

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    subprocess.run(['foamListTimes', '-rm', '-noZero'])
    rmObjects.removeProcessorDirs()
    for d in ('dynamicCode', 'logs'):
        if os.path.isdir(d):
            shutil.rmtree(d)
    for d in glob.iglob(f'*.analyzed{os.sep}'):
        shutil.rmtree(d)
    for i in ('PyFoam*', '*.logfile', '*.logfile.restart*', '*.log', 'log.*', '*_history.txt'):
        for f in glob.iglob(i):
            os.remove(f)
    rmObjects.removeLogPlotPngs()

    rmObjects.removeInessentials()
