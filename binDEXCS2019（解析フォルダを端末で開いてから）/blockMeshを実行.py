#!/usr/bin/env python
# -*- coding: utf-8 -*-
# blockMeshを実行.py
# by Yukiharu Iwamoto
# 2026/3/10 9:25:39 AM

import os
import sys
import signal
import subprocess
import shutil
from utilities import misc
from utilities import rmObjects

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    if os.path.isdir('dynamicCode'):
        shutil.rmtree('dynamicCode')

    command = 'blockMesh'
    if subprocess.call(command, shell = True) != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)

    misc.removePatchesHavingNoFaces() # フェイスを1つも含まないパッチを取り除く
    misc.execCheckMesh()

    exec_paraFoam = True if input('\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam, ambient = 0.0, diffuse = 1.0)

    rmObjects.removeInessentials()
