#!/usr/bin/env python
# -*- coding: utf-8 -*-
# listFile.py
# by Yukiharu Iwamoto
# 2023/10/23 7:31:18 PM

import os
import sys
# {
# DEXCS2021だと，以下がないとfrom dictParse import DictParserでエラーが出る
if os.path.dirname(__file__) not in ([i.encode('UTF-8') if type(i) is unicode else i
    for i in sys.path] if sys.version_info.major <= 2 else sys.path):
    sys.path.append(os.path.dirname(__file__))
# }
from dictParse import DictParser
from dictParse import DictParserList

def patchList(path = os.curdir):
    boundary = os.path.join(path, 'constant', 'polyMesh', 'boundary')
    dp = DictParser(boundary)
    for a in dp.contents:
        if DictParserList.isType(a, DictParserList.LISTP):
            a = a.value()
            break
    patches = []
    for b in a:
        if DictParserList.isType(b, DictParserList.BLOCK):
            patches.append(b.key())
    return patches

def volFieldList(path = os.curdir):
    fields = []
    for i in os.listdir(path):
        tmp = os.path.join(path, i)
        if os.path.isfile(tmp) and os.sep + '.' not in tmp:
            vol_field = False
            for line in open(tmp, 'r'):
                if 'volScalarField' in line or 'volVectorField' in line:
                    vol_field = True
                    break
                elif 'surfaceScalarField' in line or 'surfaceVectorField' in line:
                    break
            if vol_field:
                fields.append(i)
    return fields

if __name__ == '__main__':
    path = os.curdir if len(sys.argv) == 1 else sys.argv[1]
    print(volFieldList(path))
    print(patchList(path))
