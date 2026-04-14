#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 0秒以外のフォルダを消す.py
# by Yukiharu Iwamoto
# 2021/4/27 2:17:11 PM

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

    subprocess.call('foamListTimes -rm -noZero', shell = True)
    rmObjects.removeProcessorDirs()
    for d in ('dynamicCode', 'logs'):
        if os.path.isdir(d):
            shutil.rmtree(d)
    for d in glob.iglob('*.analyzed/'):
        shutil.rmtree(d)
    for i in ('PyFoam*', '*.logfile', '*.logfile.restart*', '*.log', 'log.*'):
        for f in glob.iglob(i):
            os.remove(f)
    rmObjects.removeLogPlotPngs()
    rmObjects.removePyFoamPlots()

    rmObjects.removeInessentials()
