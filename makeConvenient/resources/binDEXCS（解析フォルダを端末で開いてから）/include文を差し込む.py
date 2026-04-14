#!/usr/bin/env python
# -*- coding: utf-8 -*-
# include文を差し込む.py
# by Yukiharu Iwamoto
# 2026/3/18 7:03:20 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -f include_file -> 差し込みたいincludeファイルの名前をinclude_fileにする

# DictParser2で書き直し済み

import signal
import os
import sys
import glob
import re
from utilities import misc
from utilities import appendEntries
from utilities import rmObjects
from utilities import dictParse

def append_include_sentence(dir_name, include_file_name):
    if not os.path.isdir(dir_name):
        return
    include_file_name = os.path.relpath(include_file_name, dir_name)
    for f in glob.iglob(os.path.join(dir_name, '*')):
        if not os.path.isfile(f):
            continue
        os.chmod(f, 0o0666)
        if os.path.basename(f) == 'cellToRegion':
            continue
        print('{}を処理中...'.format(f))
        parser = dictParse.DictParser2(file_name = f)
        inserted = False
        for i in reversed(parser.find_all_elements([{'type': 'directive', 'key': '#include'}])):
            n = dictParse.find_element([{'type': 'string'}], parent = i['element'])['element']['value'].strip('"')
            if n == include_file_name:
                inserted = True
                break
        if inserted:
            continue
        i = parser.find_element([{'type': 'block_comment'}])
        if i['element'] is not None and '-*- C++ -*-' in i['element']['value']:
            i = i['index'] + 1
        else:
            i = 0
        i = parser.find_element([{'type': 'block', 'key': 'FoamFile'}], start = i, index_not_found = i - 1)['index'] + 1
        head_index = parser.find_element([{'except type': 'whitespace|linebreak|separator'}], start = i)['index']
        parser.elements[head_index:head_index] = dictParse.DictParser2(string = 
            f'#include "{include_file_name}"\n' +
            '\n').elements
        string = dictParse.normalize(string = parser.file_string(pretty_print = True))[0]
#        os.rename(f, f + '_bak')
        with open(f, 'w') as fp:
            fp.write(string)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    print('\n!!! 他のファイルと同様に，includeファイルの中でも行の終わりには ； が必要です． !!!\n')

    if len(sys.argv) == 1:
        include_file = input('差し込みたいincludeファイルの名前を教えて下さい． > ').strip()
    else:
        include_file = None
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-f':
                i += 1
                include_file = sys.argv[i]
            i += 1
    if include_file is None:
        print('エラー: includeファイルが指定されていません．')
        sys.exit(1)

    if not os.path.isfile(include_file):
        with open(include_file, 'w') as f:
            pass

    append_include_sentence(dir_name = '0', include_file_name = include_file)
    append_include_sentence(dir_name = 'constant', include_file_name = include_file)
    append_include_sentence(dir_name = 'system', include_file_name = include_file)

    for d in glob.iglob(os.path.join('0', '*' + os.sep)):
        append_include_sentence(dir_name = d, include_file_name = include_file)
    for d in glob.iglob(os.path.join('constant', '*' + os.sep)):
        if os.path.isdir(os.path.join(d, 'polyMesh')):
            append_include_sentence(dir_name = d, include_file_name = include_file)
    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
        if os.path.isfile(os.path.join(d, 'fvSolution')):
            append_include_sentence(dir_name = d, include_file_name = include_file)

    appendEntries.intoFvSolution()

    rmObjects.removeInessentials()
    misc.correctLocation()
