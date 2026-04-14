#!/usr/bin/env python
# -*- coding: utf-8 -*-
# paraFoamを実行.py
# by Yukiharu Iwamoto
# 2020/7/2 8:26:25 PM

# ---- オプションはない ----

import signal
from utilities import misc
from utilities import rmObjects

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)
    misc.execParaFoam()
    rmObjects.removeInessentials()
