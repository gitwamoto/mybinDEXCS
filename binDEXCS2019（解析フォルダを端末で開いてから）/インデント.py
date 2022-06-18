#!/usr/bin/env python
# -*- coding: utf-8 -*-
# インデント.py
# by Yukiharu Iwamoto
# 2021/6/30 11:37:44 AM

# ---- オプションはない ----

import signal
import subprocess
import os
import glob
from utilities import misc
from utilities import dictFormat
from utilities import appendEntries
from utilities.dictParse import DictParser
from utilities import rmObjects

def indent(dir_name):
    if not os.path.isdir(dir_name):
        return
    for f in glob.iglob(os.path.join(dir_name, '*')):
        if os.path.isfile(f):
            print('{}を処理中...'.format(f))
            with open(f, 'r') as fp:
                s_old = fp.read()
            s = dictFormat.moveLineToBottom(DictParser(string = s_old)).toString()
            if s != s_old:
                with open(f, 'w') as fp:
                    fp.write(s)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    indent('0')
    indent('constant')
    indent('system')
    for d in glob.iglob(os.path.join('0', '*' + os.sep)):
        indent(d)
    for d in glob.iglob(os.path.join('constant', '*' + os.sep)):
        if os.path.isdir(os.path.join(d, 'polyMesh')):
            indent(d)
    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
        if os.path.isfile(os.path.join(d, 'fvSolution')):
            indent(d)

    appendEntries.intoFvSolution()
    appendEntries.intoFvSchemes()
    appendEntries.intoControlDict()

    rmObjects.removeInessentials()
