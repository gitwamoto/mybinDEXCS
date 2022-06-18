#!/usr/bin/env python
# -*- coding: utf-8 -*-
# folderTime.py
# by Yukiharu Iwamoto
# 2021/3/13 10:14:57 PM

import os
import glob

def firstTime(path = os.curdir):
    s = 'inf'
    t = float(s)
    for d in glob.iglob(os.path.join(path, '*' + os.sep)):
        d = os.path.basename(os.path.dirname(d))
        try:
            fd = float(d)
            if t > fd:
                t, s = fd, d
        except:
            pass
    return None if s == 'inf' else s

def latestTime(path = os.curdir):
    s = '-inf'
    t = float(s)
    for d in glob.iglob(os.path.join(path, '*' + os.sep)):
        d = os.path.basename(os.path.dirname(d))
        try:
            fd = float(d)
            if t < fd:
                t, s = fd, d
        except:
            pass
    return None if s == '-inf' else s

if __name__ == '__main__':
    print('firstTime = ' + firstTime())
    print('latestTime = ' + latestTime())
