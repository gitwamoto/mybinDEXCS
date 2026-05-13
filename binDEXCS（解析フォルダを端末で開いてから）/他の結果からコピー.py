#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 他の結果からコピー.py
# by Yukiharu Iwamoto
# 2026/5/13 9:18:37 AM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -s source_path -> コピー元となる解析フォルダのパスをsource_pathにする．解析フォルダからの相対パスでも良い
# -p -> paraFoamを実行する

import signal
import subprocess
import os
import sys
from utilities import misc
from utilities import rmObjects
from utilities import dictParse

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = False
        exec_paraFoam = False
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

    controlDict_path = os.path.join('system', 'controlDict')
    if not os.path.isfile(controlDict_path):
        print(f'エラー: ファイル{controlDict_path}がありません．')
        sys.exit(1)

    controlDict = dictParse.DictParser(file_name = controlDict_path)
    startFrom = controlDict.find_element(
        [{'type': 'dictionary', 'key': 'startFrom'}, {'except type': 'ignorable'}])['element']
    if startFrom is None:
        print(f'エラー: ファイル{controlDict_path}にstartFromの指定がありません．')
        sys.exit(1)
    startFrom = startFrom['value']
    if startFrom == 'latestTime':
        start_from = misc.latestTime()
        if start_from is None:
            print('エラー: 結果フォルダがありません．')
            sys.exit(1)
        start_from = f'latestTime = {start_from}'
    elif startFrom == 'firstTime':
        start_from = misc.firstTime()
        if start_from is None:
            print('エラー: 結果フォルダがありません．')
            sys.exit(1)
        start_from = f'firstTime = {start_from}'
    elif startFrom == 'startTime':
        start_from = controlDict.find_element(
            [{'type': 'dictionary', 'key': 'startTime'}, {'except type': 'ignorable'}])['element']
        if start_from is None:
            print(f'エラー: ファイル{controlDict_path}にstartTimeの指定がありません．')
            sys.exit(1)
        start_from = f"startTime = {start_from['value']}"
    else:
        print(f'エラー: ファイル{controlDict_path}のstartFromの指定が正しくありません．')
        sys.exit(1)

    print(f'現在の解析フォルダにあるファイル{controlDict_path}に書いてあるstartFrom = '
        f'{start_from}の結果を他の解析フォルダのlatestTimeの結果で書き換えます．')
    print('メッシュが違っても良いですが，境界の形や境界条件は同じでないといけません．')

    if interactive:
        source_path = input('コピー元となる解析フォルダのパスを入力して下さい． > ').strip()

    command = 'mapFields -consistent -sourceTime latestTime ' + source_path
    if subprocess.call(command, shell = True) != 0:
        print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
        sys.exit(1)

    if interactive:
        exec_paraFoam = True if input('\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam)

    rmObjects.removeInessentials()
