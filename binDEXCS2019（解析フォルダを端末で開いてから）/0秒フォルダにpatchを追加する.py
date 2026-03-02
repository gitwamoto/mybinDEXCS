#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 0秒フォルダにpatchを追加する.py
# by Yukiharu Iwamoto
# 2026/3/2 8:56:44 PM

# ---- オプションはない ----

# DictParser2で書き直し済み

import os
import signal
import glob
import re
from utilities import misc
from utilities.dictParse import DictParser, DictParserList
from utilities import rmObjects

from utilities import dictParse

#def mykey(x):
#    m = re.match('(.*?)([0-9]*)$', x[0])
#    return m.group(1), -1 if m.group(2) == '' else int(m.group(2))
#
#def append_patches(src, dst):
#    dp = DictParser(os.path.join(src, 'polyMesh', 'boundary'))
#    for x in dp.contents:
#        if DictParserList.isType(x, DictParserList.LISTP):
#            x = x.value()
#            break
#    patches = []
#    for y in x:
#        if DictParserList.isType(y, DictParserList.BLOCK):
#            for z in y.value():
#                 if DictParserList.isType(z, DictParserList.DICT) and z.key() == 'type':
#                    patches.append([y.key(), z.value()[0]])
#                    break
#    patches.sort(key = mykey)
#    a = ['\n\n\n']
#    for i in patches:
#        a.extend([DictParserList(DictParserList.BLOCK, [i[0], '\n', ['\n',
#            DictParserList(DictParserList.DICT, ['type', '',
#            [(i[1] if i[1] in ('empty', 'symmetryPlane', 'symmetry', 'wedge') else 'zeroGradient')], '']),
#            '\n']]), '\n'])
#    patches = set([i[0] for i in patches])
#    for f in glob.iglob(os.path.join(dst, '*')):
#        if os.path.isfile(f):
#            os.chmod(f, 0o0666)
#            if os.path.basename(f) != 'cellToRegion':
#                print('{}を処理中...'.format(f))
#                dp = DictParser(f)
#                x = dp.getDPLForKey(['boundaryField'])
#                if x is not None and DictParserList.isType(x, DictParserList.BLOCK):
#                    patches_bf = set()
#                    for y in x.value():
#                        if DictParserList.isType(y, DictParserList.BLOCK):
#                            patches_bf.add(y.key())
#                    if patches != patches_bf:
#                        x.setValue([dp.toString(x.value(), indent = '//\t')])
#                        x.value().extend(a)
#                        dp.writeFile(f)

def mykey(x):
    m = re.match('(.*?)([0-9]*)$', x[0])
    return m.group(1), -1 if m.group(2) == '' else int(m.group(2))

def append_patches(src, dst):
    src = os.path.join(src, 'polyMesh', 'boundary')
    os.chmod(src, 0o0666) # 誰でも（所有者・グループ・その他全員）読み書きができるが、実行権限（x）はない

    boundary = dictParse.DictParser2(file_name = src)

    patches = boundary.find_all_elements([{'type': 'list'}, {'type': 'block'}])
    patches.sort(key = lambda p: p['element']['key'])

    for f in glob.iglob(os.path.join(dst, '*')):
        if not os.path.isfile(f):
            continue

        os.chmod(f, 0o0666)
        if os.path.basename(f) == 'cellToRegion':
            continue

        print('{}を処理中...'.format(f))
        parameter = dictParse.DictParser2(file_name = f)
        boundaryField = parameter.find_element([{'type': 'block', 'key': 'boundaryField'}])['element']
        if boundaryField is None:
            boundaryField_and_linebreak = dictParse.DictParser2(string =
                'boundaryField\n'
                '{\n'
                '}\n'
                '\n').elements
            footer_index = parameter.find_separators(footer_index_not_found = len(parameter.elements))[1]['index']
            parameter.elements[footer_index:footer_index] = boundaryField_and_linebreak
            boundaryField = boundaryField_and_linebreak[0]
        i = dictParse.find_element([{'type': 'block_start'}], parent = boundaryField)['index'] + 1
        start = dictParse.find_element([{'type': 'linebreak'}], parent = boundaryField, start = i,
            index_not_found = i - 1)['index'] + 1

        linebreak = dictParse.DictParser2(string = '\n').elements[0]
        for p in reversed(patches):
            i = dictParse.find_element([{'type': 'block', 'key': p['element']['key']}], parent = boundaryField)
            if i['element'] is None:
                v = dictParse.find_element([{'type': 'dictionary', 'key': 'type'},
                    {'except type': 'whitespace|line_comment|block_comment|linebreak'}],
                    parent = p['element'])['element']['value']
                if v not in ('empty', 'symmetryPlane', 'symmetry', 'wedge'):
                    v = 'zeroGradient'
                boundaryField['value'][start:start] = dictParse.DictParser2(string = '\n' +
                    p['element']['key'] + '\n' +
                    '{\n' +
                    'type\t' + v + ';\n' +
                    '}\n').elements
            else:
                i['parent'][start:start] = [i['parent'].pop(i['index']), linebreak]
        dictParse.set_blank_line(boundaryField, number_of_blank_lines = 1)

        string = dictParse.normalize(string = parameter.file_string(pretty_print = True))[0]
        if parameter.string != string:
#            os.rename(f, f + '_back')
            with open(f, 'w') as f:
                f.write(string)

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
