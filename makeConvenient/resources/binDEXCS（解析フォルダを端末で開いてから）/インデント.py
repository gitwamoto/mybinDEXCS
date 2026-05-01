#!/usr/bin/env python
# -*- coding: utf-8 -*-
# インデント.py
# by Yukiharu Iwamoto
# 2026/5/1 2:18:53 PM

# ---- オプションはない ----

# DictParser2で書き直し済み

import signal
import os
import glob
from utilities import misc
from utilities import appendEntries
from utilities import rmObjects
from utilities import dictParse

def indent(dir_name):
    for i in glob.iglob(os.path.join(dir_name, '*')):
        if os.path.isfile(i):
            print(f'{i}を処理中...')
            parser = dictParse.DictParser2(file_name = i)
            string = dictParse.normalize(string = parser.file_string(pretty_print = True))[0]
            if parser.string != string:
#               os.rename(i, f'{i}_bak')
                with open(i, 'w') as f:
                    f.write(string)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    indent('0')
    indent('constant')
    indent('system')
    for i in glob.iglob(os.path.join('0', '*' + os.sep)):
        indent(i)
    for i in glob.iglob(os.path.join('constant', '*' + os.sep)):
        if os.path.isdir(os.path.join(i, 'polyMesh')):
            indent(i)
    for i in glob.iglob(os.path.join('system', '*' + os.sep)):
        if os.path.isfile(os.path.join(i, 'fvSolution')):
            indent(i)

    appendEntries.intoFvSolution()
    appendEntries.intoFvSchemes()
    appendEntries.intoControlDict()

    rmObjects.removeInessentials()
