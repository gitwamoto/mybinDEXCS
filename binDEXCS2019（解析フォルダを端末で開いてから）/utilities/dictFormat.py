#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dictFormat.py
# by Yukiharu Iwamoto
# 2022/11/25 5:39:21 PM

import sys
# {
# DEXCS2021だと，以下がないとfrom dictParse import DictParserでエラーが出る
import os
if os.path.dirname(__file__) not in ([i.encode('UTF-8') if type(i) is unicode else i
    for i in sys.path] if sys.version_info.major <= 2 else sys.path):
    sys.path.append(os.path.dirname(__file__))
# }
from dictParse import DictParser
from dictParse import DictParserList

def moveLineToBottom(dp):
    if type(dp) is str:
        file_name = dp
        dp = DictParser(dp)
    else:
        file_name = None
    i = dp.searchString('// \\*+ //')
    if i is not None and len(i) == 1:
        i = i[0]
        s = '\n\n' + dp.contents[i].strip() + '\n'
        if i != len(dp.contents) - 1:
            dp.contents[i] = '\n\n'
            if len(dp.contents) > 0 and type(dp.contents[-1]) is str:
                dp.contents[-1] = dp.contents[-1].rstrip() + s
            else:
                dp.contents.append(s)
        else:
            dp.contents[i] = s
    if file_name is not None:
        dp.writeFile(file_name)
    return dp

def insertEntryIntoBlockBottom(entry, block): # ブロック内のいちばん下の行に挿入
    if isinstance(entry, tuple):
        entry = list(entry)
    else:
        entry = [entry]
    if len(block) == 0:
        block.extend(entry)
    elif type(block[-1]) is str:
        if block[-1].endswith('\n'):
            block.extend(entry)
        else:
            block.extend(['\n'] + entry)
    else:
        block.extend(['\n'] + entry)

def insertEntryIntoBlockTop(entry, block): # ブロック内のいちばん上の行に挿入
    if isinstance(entry, tuple):
        entry = list(entry)
    else:
        entry = [entry]
    if len(block) == 0:
        block[:0] = entry
    elif type(block[0]) is str:
        if block[0].startswith('\n'):
            block[0:1] = ['\n'] + entry + [block[0][1:]]
        else:
            block[:0] = ['\n'] + entry
    else:
        block[:0] = ['\n'] + entry

def insertEntryIntoTopLayerBottom(entry, contents): # 最上層のいちばん下の行に挿入
    if isinstance(entry, tuple):
        entry = list(entry)
    else:
        entry = [entry]
    if len(contents) == 0:
        contents.extend(entry)
    elif type(contents[-1]) is str:
        bottom = contents[-1].rstrip()
        if len(contents) == 1 and bottom == '':
            contents[:] = entry
        else:
            contents[-1:] = [bottom + '\n'] + entry
    else:
        contents.extend(['\n'] + entry)

if __name__ == '__main__':
    moveLineToBottom(sys.argv[1])
