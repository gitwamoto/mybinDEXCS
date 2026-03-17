#!/usr/bin/env python
# -*- coding: utf-8 -*-
# folderTime.py
# by Yukiharu Iwamoto
# 2026/3/17 11:56:53 PM

import os

def firstTime(path = os.curdir):
    t = timesFolders(path)
    return None if len(t) == 0 else t[0]

def latestTime(path = os.curdir):
    t = timesFolders(path)
    return None if len(t) == 0 else t[-1]

def timesFolders(path = os.curdir):
    times = []
    for i in os.listdir(path):
        if os.path.isdir(os.path.join(path, i)):
            try:
                times.append([i, float(i)])
            except:
                pass
    return [i[0] for i in sorted(times, key = lambda x: x[1])]

if __name__ == '__main__':
    print('firstTime = ' + firstTime())
    print('latestTime = ' + latestTime())
