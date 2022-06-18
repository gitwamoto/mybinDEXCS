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

def remove_include_sentence(dir_name, include_file_name, ignore_path):
    if not os.path.isdir(dir_name):
        return
    if ignore_path:
        include_file_name = re.sub(r'^(\.\.' + os.sep + ')+', '', include_file_name)
    for f in glob.iglob(os.path.join(dir_name, '*')):
        if os.path.isfile(f):
            os.chmod(f, 0o0666)
            if os.path.basename(f) != 'cellToRegion':
                with open(f, 'r') as fp:
                    s_old = fp.read()
                print('{}を処理中...'.format(f))
                dp = DictParser(f)
                i = 0
                while i < len(dp.contents):
                    x = dp.contents[i]
                    if DictParserList.isType(x, DictParserList.INCLUDE) and (ignore_path and
                        re.sub(r'^(\.\.' + os.sep + ')+', '', x.value().strip('"')) == include_file_name or
                        not ignore_path and x.value().strip('"') == include_file_name):
                        del dp.contents[i]
                        if i < len(dp.contents) and (type(dp.contents[i]) is str):
                            dp.contents[i] = dp.contents[i].lstrip()
                    i += 1
                dp = dictFormat.moveLineToBottom(dp)
                s = re.sub(r'\n\n\n+', '\n\n', dp.toString())
                if s != s_old:
                    with open(f, 'w') as fp:
                        fp.write(s)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        include_file = (raw_input if sys.version_info.major <= 2 else input)(
            '取り除きたいincludeファイルの名前を教えて下さい． > ').strip()
        ignore_path = True if (raw_input if sys.version_info.major <= 2 else input)(
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
