#!/usr/bin/env python
# -*- coding: utf-8 -*-
# showDir.py
# by Yukiharu Iwamoto
# 2019/12/19 5:21:47 PM

import os
import subprocess

def showDirForPresentAnalysis(file = __file__, path = os.getcwd()):
    # https://qiita.com/PruneMazui/items/8a023347772620025ad6
    print('\033[7;1m----- 現在の解析フォルダは %s です． -----\033[m' % path)
    # https://joppot.info/2013/12/17/235 , http://tldp.org/HOWTO/Xterm-Title-3.html
    print('\033]2;%s - %s\007' % (path, os.path.basename(file)))

if __name__ == '__main__':
    showDirForPresentAnalysis()
