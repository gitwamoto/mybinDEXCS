#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setFuncsInCD.py
# by Yukiharu Iwamoto
# 2022/6/9 1:56:04 PM

import os
import sys
import subprocess
import re
# {
# DEXCS2021だと，以下がないとfrom dictParse import DictParserでエラーが出る
if os.path.dirname(__file__) not in ([i.encode('UTF-8') if type(i) is unicode else i
    for i in sys.path] if sys.version_info.major <= 2 else sys.path):
    sys.path.append(os.path.dirname(__file__))
# }
from dictParse import DictParser
from dictParse import DictParserList

def setAllEnabled(enabled = True, path = os.curdir):
    controlDict = os.path.join(path, 'system', 'controlDict')
    dp = DictParser(controlDict)
    s_old = dp.toString()
    v = ['yes' if enabled else 'no']
    x = dp.getValueForKey(['functions'])
    if x is not None:
        for n, y in enumerate(x):
            if DictParserList.isType(y, DictParserList.BLOCK):
                i = dp.getIndexOfItem([y.key(), 'enabled'], y)
                vy = y.value()
                if (i is not None and DictParserList.isType(vy[i[1]], DictParserList.DICT)):
                    vy[i[1]].setValue(v)
                else:
                    z = DictParserList(DictParserList.DICT, ['enabled', '', v, '/* yesで実行 */'])
                    if len(vy) == 0:
                        vy.extend(['\n', z, '\n'])
                    if len(vy) > 0 and type(vy[-1]) is str:
                        vy[-1:] = ['\n', z, '\n' + vy[-1].lstrip()]
                    else:
                        vy.extend(['\n\n', z,' \n'])
            elif not enabled and DictParserList.isType(y, DictParserList.DICT) and y.key() == '#includeFunc':
                y.setKey('// ' + y.key())
            elif enabled and type(y) is str and y.find('#includeFunc'):
                x[n] = re.sub(r'//\s*(#includeFunc\s+)', r'\t\1', y)
    s = dp.toString()
    if s != s_old:
        with open(controlDict, 'w') as f:
            f.write(s)

def setEnabledForType(type_ = '', enabled = True, path = os.curdir):
    controlDict = os.path.join(path, 'system', 'controlDict')
    dp = DictParser(controlDict)
    s_old = dp.toString()
    v = ['yes' if enabled else 'no']
    x = dp.getValueForKey(['functions'])
    if x is not None:
        for n, y in enumerate(x):
            if DictParserList.isType(y, DictParserList.BLOCK):
                i = dp.getIndexOfItem([y.key(), 'type'], y)
                vy = y.value()
                if (i is None or
                   not DictParserList.isType(vy[i[1]], DictParserList.DICT) or
                   vy[i[1]].value()[0] != type_):
                   continue
                i = dp.getIndexOfItem([y.key(), 'enabled'], y)
                if (i is not None
                    and DictParserList.isType(vy[i[1]], DictParserList.DICT)):
                    vy[i[1]].setValue(v)
                else:
                    z = DictParserList(DictParserList.DICT, ['enabled', '', v,
                        '/* yesで実行 */'])
                    if len(vy) == 0:
                        vy.extend(['\n', z, '\n'])
                    if len(vy) > 0 and type(vy[-1]) is str:
                        vy[-1:] = ['\n', z, '\n' + vy[-1].lstrip()]
                    else:
                        vy.extend(['\n\n', z,' \n'])
            elif (not enabled and DictParserList.isType(y, DictParserList.DICT) and y.key() == '#includeFunc'
                and y.value()[0].startswith(type_ + '(')):
                y.setKey('// ' + y.key())
            elif enabled and type(y) is str and y.find('#includeFunc'):
                x[n] = re.sub(r'//\s*(#includeFunc\s+(?:/\*.+\*/\s*)?' + type_ + r'\()', r'\t\1', y)
    s = dp.toString()
    if s != s_old:
        with open(controlDict, 'w') as f:
            f.write(s)

if __name__ == '__main__':
    path = os.curdir if len(sys.argv) == 1 else sys.argv[1]
#    setAllEnabled(False, path)
    setEnabledForType('patchAverage', True, path)
