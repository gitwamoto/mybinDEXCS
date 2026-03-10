#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 0秒以外を除いてコピーを作る.py
# by Yukiharu Iwamoto
# 2021/6/30 12:05:11 PM

import signal
import subprocess
import os
import re
import shutil
from utilities import misc
from utilities import rmObjects

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    i = 1
    while True:
        cname = os.getcwd() + '_{}'.format(i)
        if not os.path.exists(cname):
            os.mkdir(cname)
            break
        else:
            i += 1
    pat = re.compile(r'(dynamicCode|postProcessing|logs|processor[0-9]+|0_potentialflow|log\..+|' +
        r'PyFoam.+|.+\.(analyzed|fcstd1|logfile(\.restart[0-9]+)?|log|fms|stl|png|foam|OpenFOAM|blockMesh|FCStd1))$')
    files = ['0']
    for i in os.listdir(os.curdir):
        try:
            float(i)
        except ValueError:
            if not pat.match(i):
                files.append(i)
    for i in files:
        src = os.path.join(os.curdir, i)
        dst = os.path.join(cname, i)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst)
    print('{}にコピーを作りました．'.format(cname))

    rmObjects.removeInessentials()
