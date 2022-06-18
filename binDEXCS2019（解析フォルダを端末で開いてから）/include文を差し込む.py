#!/usr/bin/env python
# -*- coding: utf-8 -*-
# include文を差し込む.py
# by Yukiharu Iwamoto
# 2021/7/21 12:59:52 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -f include_file -> 差し込みたいincludeファイルの名前をinclude_fileにする

import signal
import os
import sys
import glob
import re
from utilities import misc
from utilities.dictParse import DictParser, DictParserList
from utilities import dictFormat
from utilities import appendEntries
from utilities import rmObjects

def append_include_sentence(dir_name, include_file_name):
    if not os.path.isdir(dir_name):
        return
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
                    if DictParserList.isType(x, DictParserList.INCLUDE) and x.value().strip('"') == include_file_name:
                        del dp.contents[i]
                        if i < len(dp.contents) and (type(dp.contents[i]) is str):
                            dp.contents[i] = dp.contents[i].lstrip()
                    i += 1
                i = dp.searchString(r'// (\* )+//')
                if i is not None and len(i) == 1 and type(dp.contents[i[0]]) is str:
                    dp.contents[i[0]] = dp.contents[i[0]].rstrip() + '\n\n'
                    dp.contents[i[0] + 1:i[0] + 1] = [
                        DictParserList(DictParserList.INCLUDE, ['', '"' + include_file_name + '"']), '\n\n']
                else:
                    i = dp.getIndexOfItem(['FoamFile'])
                    if (i is not None and len(i) == 2 and
                        DictParserList.isType(dp.contents[i[0]], DictParserList.BLOCK)):
                        dp.contents[i[0] + 1:i[0] + 1] = ['\n\n',
                            DictParserList(DictParserList.INCLUDE, ['', '"' + include_file_name + '"']), '\n\n']
                    else:
                        dp.contents[0:0] = [
                            DictParserList(DictParserList.INCLUDE, ['', '"' + include_file_name + '"']), '\n\n']
                dp = dictFormat.moveLineToBottom(dp)
                s = re.sub(r'\n\n\n+', '\n\n', dp.toString())
                if s != s_old:
                    with open(f, 'w') as fp:
                        fp.write(s)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    print('\n!!! 他のファイルと同様に，includeファイルの中でも行の終わりには ； が必要です． !!!\n')

    if len(sys.argv) == 1:
        include_file = (raw_input if sys.version_info.major <= 2 else input)(
            '差し込みたいincludeファイルの名前を教えて下さい． > ').strip()
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

    include_file = os.path.join(os.pardir, include_file)
    append_include_sentence(dir_name = '0', include_file_name = include_file)
    append_include_sentence(dir_name = 'constant', include_file_name = include_file)
    append_include_sentence(dir_name = 'system', include_file_name = include_file)

    include_file = os.path.join(os.pardir, include_file)
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
