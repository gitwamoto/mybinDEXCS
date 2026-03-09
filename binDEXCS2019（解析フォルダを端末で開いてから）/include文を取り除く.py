#!/usr/bin/env python
# -*- coding: utf-8 -*-
# include文を取り除く.py
# by Yukiharu Iwamoto
# 2021/7/21 1:00:23 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -f include_file -> 取り除きたいincludeファイルの名前をinclude_fileにする
# -p -> パスが一致していなくても，ファイル名が同じならば取り除く

import signal
import os
import sys
import glob
import re
from utilities import misc
from utilities.dictParse import DictParser, DictParserList
from utilities import dictFormat
from utilities import rmObjects

from utilities import dictParse

def remove_include_sentence(dir_name, include_file_name, ignore_path):
    if not os.path.isdir(dir_name):
        return
    if ignore_path:
        include_file_name = re.sub(r'^(\.\.' + os.sep + ')+', '', include_file_name)
    for f in glob.iglob(os.path.join(dir_name, '*')):
        if not os.path.isfile(f):
            continue
            os.chmod(f, 0o0666)
        if os.path.basename(f) == 'cellToRegion':
            continue
        print('{}を処理中...'.format(f))
        parser = dictParse.DictParser2(file_name = f)
        for i in reversed(parser.find_all_elements([{'type': 'directive'}])):
            if i['element']['key'] != '#include':
                continue
            n = dictParse.find_element([{'type': 'string'}], parent = i['element'])['value'].strip('"')
            if ignore_path:
                n = re.sub(r'^(?:\.\./)+', '', n)
            if n == include_file_name:
                del i['parent'][i['index']:
                    dictParse.find_element([{'except type': 'whitespace|linebreak'}],
                        parent = i['parent'], start = start + 1, index_not_found = start + 1)['index']]
        string = dictParse.normalize(string = parameter.file_string(pretty_print = True))[0]
        if parameter.string != string:
#            os.rename(f, f + '_bak')
            with open(f, 'w') as fp:
                fp.write(string)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        include_file = input('取り除きたいincludeファイルの名前を教えて下さい． > ').strip()
        ignore_path = True if input(
            'パスが一致していなくても，ファイル名が同じならば取り除きますか？ (y/n) > '
            ).strip().lower() == 'y' else False
    else:
        include_file = None
        ignore_path = False
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-f':
                i += 1
                include_file = sys.argv[i]
            elif sys.argv[i] == '-p':
                ignore_path = True
            i += 1
    if include_file is None:
        print('エラー: includeファイルが指定されていません．')
        sys.exit(1)

    include_file = os.path.join(os.pardir, include_file)
    remove_include_sentence(dir_name = '0', include_file_name = include_file, ignore_path = ignore_path)
    remove_include_sentence(dir_name = 'constant', include_file_name = include_file, ignore_path = ignore_path)
    remove_include_sentence(dir_name = 'system', include_file_name = include_file, ignore_path = ignore_path)

    include_file = os.path.join(os.pardir, include_file)
    for d in glob.iglob(os.path.join('0', '*' + os.sep)):
        remove_include_sentence(dir_name = d, include_file_name = include_file, ignore_path = ignore_path)
    for d in glob.iglob(os.path.join('constant', '*' + os.sep)):
        if os.path.isdir(os.path.join(d, 'polyMesh')):
            remove_include_sentence(dir_name = d, include_file_name = include_file, ignore_path = ignore_path)
    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
        if os.path.isfile(os.path.join(d, 'fvSolution')):
            remove_include_sentence(dir_name = d, include_file_name = include_file, ignore_path = ignore_path)

    rmObjects.removeInessentials()
    misc.correctLocation()
