#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 半角に出来る文字は全て半角に.py
# by Yukiharu Iwamoto
# 2026/2/20 9:23:55 PM

import sys
import signal
import os
import glob
from utilities import misc
from utilities import dictParse
from utilities import appendEntries
from utilities import rmObjects

include_files = set()

def normalize(dir_name):
    if not os.path.isdir(dir_name):
        return
    for i in glob.iglob(os.path.join(dir_name, '*')):
        if os.path.isfile(i):
            print('%sを処理中...' % i)
            dictParse.normalize(file_name = i, overwrite_file = True)
            dp = dictParse.DictParser2(string = s)
            for e in dp.find_all_elements([{'type': 'directive', 'key': '#include'}]):
                # os.path.normpath -> パスの余計な部分を整理して、きれいな形に整える
                include_files.add(os.path.normpath(os.path.join(dir_name, e['element']['value'][1:-1])))

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    normalize('0')
    normalize('constant')
    normalize('system')
    for d in glob.iglob(os.path.join('0', '*' + os.sep)):
        normalize(d)
    for d in glob.iglob(os.path.join('constant', '*' + os.sep)):
        if os.path.isdir(os.path.join(d, 'polyMesh')):
            normalize(d)
    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
        if os.path.isfile(os.path.join(d, 'fvSolution')):
            normalize(d)

    for i in include_files:
        print('%sを処理中...' % i)
        dictParse.normalize(file_name = i, overwrite_file = True)

    appendEntries.intoFvSolution()
    appendEntries.intoFvSchemes()
    appendEntries.intoControlDict()

    rmObjects.removeInessentials()
