#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 他の結果からコピー.py
# by Yukiharu Iwamoto
# 2021/7/21 2:51:20 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -s source_path -> コピー元となる解析フォルダのパスをsource_pathにする．解析フォルダからの相対パスでも良い
# -p -> paraFoamを実行する

import signal
import subprocess
import os
import sys
import shutil
from utilities import misc
from utilities.dictParse import DictParser, DictParserList
from utilities import folderTime
from utilities import rmObjects

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = exec_paraFoam = False
        source_path = None
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-s':
                i += 1
                source_path = sys.argv[i]
            elif sys.argv[i] == '-p':
                exec_paraFoam = True
            i += 1
        if source_path is None:
            print('エラー: -sオプションを使ってコピー元となる解析フォルダのパスを入力して下さい．')
            sys.exit(1)

    controlDict = os.path.join('system', 'controlDict')
    if not os.path.isfile(controlDict):
        print('エラー: %sファイルがありません．' % controlDict)
        sys.exit(1)

    dp_controlDict = DictParser(controlDict)
    startFrom = dp_controlDict.getValueForKey(['startFrom'])
    if startFrom is None:
        print('エラー: %sファイルにstartFromの指定がありません．' % controlDict)
        sys.exit(1)
    startFrom = startFrom[0]
    if startFrom == 'latestTime':
        start_from = folderTime.latestTime()
        if start_from is None:
            print('エラー: 結果フォルダがありません．')
            sys.exit(1)
        start_from = 'latestTime = ' + start_from
    elif startFrom == 'firstTime':
        start_from = folderTime.firstTime()
        if start_from is None:
            print('エラー: 結果フォルダがありません．')
            sys.exit(1)
        start_from = 'firstTime = ' + start_from
    elif startFrom == 'startTime':
        start_from = dp_controlDict.getValueForKey(['startTime'])
        if start_from is None:
            print('エラー: %sファイルにstartTimeの指定がありません．' % controlDict)
            sys.exit(1)
        start_from = 'startTime = ' + str(start_from)
    else:
        print('エラー: %sファイルのstartFromの指定が正しくありません．' % controlDict)
        sys.exit(1)

    print('現在の解析フォルダにある' + controlDict + 'に書いてあるstartFrom = ' +
        start_from + 'の結果を他の解析フォルダのlatestTimeの結果で書き換えます．')
    print('メッシュが違っても良いですが，境界の形や境界条件は同じでないといけません．')

    if interactive:
        source_path = (raw_input if sys.version_info.major <= 2 else input)(
            'コピー元となる解析フォルダのパスを入力して下さい． > ').strip()

    command = 'mapFields -consistent -sourceTime latestTime ' + source_path
    if subprocess.call(command, shell = True) != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)

    if interactive:
        exec_paraFoam = True if (raw_input if sys.version_info.major <= 2 else input)(
            '\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam)

    rmObjects.removeInessentials()
