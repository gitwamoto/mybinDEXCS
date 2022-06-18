#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 0秒フォルダにpatchを追加する.py
# by Yukiharu Iwamoto
# 2021/7/2 7:38:56 PM

# ---- オプションはない ----

import os
import signal
import glob
import re
from utilities import misc
from utilities.dictParse import DictParser, DictParserList
from utilities import rmObjects

def mykey(x):
    m = re.match('(.*?)([0-9]*)$', x[0])
    return m.group(1), -1 if m.group(2) == '' else int(m.group(2))

def append_patches(src, dst):
    dp = DictParser(os.path.join(src, 'polyMesh', 'boundary'))
    for x in dp.contents:
        if DictParserList.isType(x, DictParserList.LISTP):
            x = x.value()
            break
    patches = []
    for y in x:
        if DictParserList.isType(y, DictParserList.BLOCK):
            for z in y.value():
                 if DictParserList.isType(z, DictParserList.DICT) and z.key() == 'type':
                    patches.append([y.key(), z.value()[0]])
                    break
    patches.sort(key = mykey)
    a = ['\n\n\n']
    for i in patches:
        a.extend([DictParserList(DictParserList.BLOCK, [i[0], '\n', ['\n',
            DictParserList(DictParserList.DICT, ['type', '',
            [(i[1] if i[1] in ('empty', 'symmetryPlane', 'symmetry', 'wedge') else 'zeroGradient')], '']),
            '\n']]), '\n'])
    patches = set([i[0] for i in patches])
    for f in glob.iglob(os.path.join(dst, '*')):
        if os.path.isfile(f):
            os.chmod(f, 0o0666)
            if os.path.basename(f) != 'cellToRegion':
                print('{}を処理中...'.format(f))
                dp = DictParser(f)
                x = dp.getDPLForKey(['boundaryField'])
                if x is not None and DictParserList.isType(x, DictParserList.BLOCK):
                    patches_bf = set()
                    for y in x.value():
                        if DictParserList.isType(y, DictParserList.BLOCK):
                            patches_bf.add(y.key())
                    if patches != patches_bf:
                        x.setValue([dp.toString(x.value(), indent = '//\t')])
                        x.value().extend(a)
                        dp.writeFile(f)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    regions = []
    for d in glob.iglob(os.path.join('constant', '*' + os.sep)):
        if os.path.isdir(d + 'polyMesh'):
            regions.append(os.path.basename(d[:-len(os.sep)]))
    if len(regions) == 0:
        append_patches(src = 'constant', dst = '0')
    else:
        for i in regions:
            d = os.path.join('0', i)
            if os.path.isdir(d):
                append_patches(src = os.path.join('constant', i), dst = d)

    rmObjects.removeInessentials()
