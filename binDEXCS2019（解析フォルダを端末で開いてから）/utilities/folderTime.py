#!/usr/bin/env python
# -*- coding: utf-8 -*-
# folderTime.py
# by Yukiharu Iwamoto
# 2025/8/5 2:44:02 PM

import os
import glob

def firstTime(path = os.curdir):
    t = timesFolders(path)
    return None if len(t) == 0 else t[0]

def latestTime(path = os.curdir):
    t = timesFolders(path)
    return None if len(t) == 0 else t[-1]

def timesFolders(path = os.curdir):
    t = []
    for d in glob.iglob(os.path.join(path, '*' + os.sep)):
        d = os.path.basename(os.path.dirname(d))
        try:
            t.append([d, float(d)])
        except:
            pass
    return [i[0] for i in sorted(t, key = lambda x: x[1])] 

if __name__ == '__main__':
    print('firstTime = ' + firstTime())
    print('latestTime = ' + latestTime())
