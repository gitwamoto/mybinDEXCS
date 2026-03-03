#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 0秒フォルダにpatchを追加する.py
# by Yukiharu Iwamoto
# 2026/3/3 4:25:14 PM

# ---- オプションはない ----

# DictParser2で書き直し済み

import os
import signal
import glob
import re
from utilities import misc
from utilities import rmObjects
from utilities import dictParse

def append_patches(src, dst):
    src = os.path.join(src, 'polyMesh', 'boundary')
    os.chmod(src, 0o0666) # 誰でも（所有者・グループ・その他全員）読み書きができるが、実行権限（x）はない

    boundary = dictParse.DictParser2(file_name = src)

    patches = boundary.find_all_elements([{'type': 'list'}, {'type': 'block'}])
    patches.sort(key = lambda p: p['element']['key'])

    linebreak = dictParse.DictParser2(string = '\n').elements[0]
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
        i = dictParse.find_element([{'type': 'block_end'}], parent = boundaryField, reverse = True)['index']
        boundaryField_end = dictParse.find_element([{'type': 'linebreak'}], parent = boundaryField, start = i - 1,
            reverse = True, index_not_found = i)['index']

        for p in patches:
            i = dictParse.find_element([{'type': 'block', 'key': p['element']['key']}], parent = boundaryField)
            if i['element'] is None:
                v = dictParse.find_element([{'type': 'dictionary', 'key': 'type'},
                    {'except type': 'whitespace|line_comment|block_comment|linebreak'}],
                    parent = p['element'])['element']['value']
                if v not in ('empty', 'symmetryPlane', 'symmetry', 'wedge'):
                    v = 'zeroGradient'
                b = dictParse.DictParser2(string = '\n' +
                    p['element']['key'] + '\n' +
                    '{\n' +
                    'type\t' + v + ';\n' +
                    '}\n').elements
                boundaryField['value'][boundaryField_end:boundaryField_end] = b
                boundaryField_end += len(b)
            else:
                # popで1つ引き抜くので，差し込む場所はboundaryField_end - 1にする．
                i['parent'][boundaryField_end - 1:boundaryField_end - 1] = [linebreak, i['parent'].pop(i['index'])]
                boundaryField_end += 1 # linebreakのぶん増える
        dictParse.set_blank_line(boundaryField, number_of_blank_lines = 1)

        string = dictParse.normalize(string = parameter.file_string(pretty_print = True))[0]
        if parameter.string != string:
#            os.rename(f, f + '_back')
            with open(f, 'w') as f:
                f.write(string)

if __name__ == '__main__':
#    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
#    misc.showDirForPresentAnalysis(__file__)

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

#    rmObjects.removeInessentials()
