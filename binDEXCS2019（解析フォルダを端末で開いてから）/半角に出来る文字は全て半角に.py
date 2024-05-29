#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 半角に出来る文字は全て半角に.py
# by Yukiharu Iwamoto
# 2024/5/29 12:03:02 PM

import sys
import signal
import os
import glob
import zenhan
from utilities import misc
from utilities.dictParse import DictParser, DictParserList
from utilities import appendEntries
from utilities import rmObjects

include_files = set()

def hankaku(dir_name):
    if not os.path.isdir(dir_name):
        return
    for f in glob.iglob(os.path.join(dir_name, '*')):
        if os.path.isfile(f):
            print('%sを処理中...' % f)
            with open(f, 'r') as fp:
                s_old = fp.read()
            s = (zenhan.z2h(s_old.decode('UTF-8'), mode = 3).encode('UTF-8') if sys.version_info.major <= 2
                else zenhan.z2h(s_old, mode = 3)) # ALL = 7, ASCII = 1, DIGIT = 2, KANA = 4
            if s != s_old:
                with open(f, 'w') as fp:
                    fp.write(s)
            dp = DictParser(string = s)
            for x in dp.contents:
                if DictParserList.isType(x, DictParserList.INCLUDE):
                    include_files.add(os.path.normpath(os.path.join(dir_name, x.value()[1:-1])))

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    hankaku('0')
    hankaku('constant')
    hankaku('system')
    for d in glob.iglob(os.path.join('0', '*' + os.sep)):
        hankaku(d)
    for d in glob.iglob(os.path.join('constant', '*' + os.sep)):
        if os.path.isdir(os.path.join(d, 'polyMesh')):
            hankaku(d)
    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
        if os.path.isfile(os.path.join(d, 'fvSolution')):
            hankaku(d)

    for f in include_files:
        print('%sを処理中...' % f)
        with open(f, 'r') as fp:
            s_old = fp.read()
        s = (zenhan.z2h(s_old.decode('UTF-8'), mode = 3).encode('UTF-8') if sys.version_info.major <= 2
            else zenhan.z2h(s_old, mode = 3)) # ALL = 7, ASCII = 1, DIGIT = 2, KANA = 4
        if s != s_old:
            with open(f, 'w') as fp:
                fp.write(s)

    appendEntries.intoFvSolution()
    appendEntries.intoFvSchemes()
    appendEntries.intoControlDict()

    rmObjects.removeInessentials()
