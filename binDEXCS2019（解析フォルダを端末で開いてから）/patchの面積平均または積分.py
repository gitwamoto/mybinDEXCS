#!/usr/bin/env python
# -*- coding: utf-8 -*-
# patchの面積平均または積分.py
# by Yukiharu Iwamoto
# 2023/5/8 12:07:54 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -a 'patch1 patch2 ...' 'field1 field2 ...': patch1 patch2 ...に対してパラメータfield1 field2 ...の面積平均を行う
#                                             patch1 patch2 ...とfield1 field2 ...はスペース区切りで書いたものを'と'でくくる
# -b time_begin: patchの面積平均または積分を開始する時間をtime_beginにする．指定しない場合は最も小さい値を持つ時間になる
#                time_beginにlを指定すると，最も大きい値を持つ時間になる
# -e time_end: patchの面積平均または積分を終了する時間をtime_endにする．指定しない場合は最も大きい値を持つ時間になる
# -0: 0秒のデータを含める
# -i 'patch1 patch2 ...' 'field1 field2 ...': patch1 patch2 ...に対してパラメータfield1 field2 ...の面積積分を行う
#                                             patch1 patch2 ...とfield1 field2 ...はスペース区切りで書いたものを'と'でくくる
# -j: patchの面積平均または積分を実行せず，postProcessingフォルダ内にある過去の結果を消去するだけ

import sys
import signal
import os
import glob
import shutil
import re
from utilities import misc
from utilities import listFile
from utilities import folderTime
from utilities import rmObjects

def handler(signal, frame):
    rmObjects.removeInessentials()
    sys.exit(1)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler) # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)

    just_delete_previous_files = False
    average = integrate = [[], None]
    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = False
        time_begin, time_end, noZero = '-inf', 'inf', True
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-a':
                average = [sys.argv[i + 1].split(), ','.join(sys.argv[i + 2].split())]
                i += 2
            elif sys.argv[i] == '-b':
                i += 1
                time_begin = sys.argv[i]
            elif sys.argv[i] == '-e':
                i += 1
                time_end = sys.argv[i]
            elif sys.argv[i] == '-0':
                noZero = False
            elif sys.argv[i] == '-i':
                integrate = [sys.argv[i + 1].split(), ','.join(sys.argv[i + 2].split())]
                i += 2
            elif sys.argv[i] == '-j':
                just_delete_previous_files = True
            i += 1

    if os.path.isdir('postProcessing'):
        for d in glob.iglob(os.path.join('postProcessing', 'patch*' + os.sep)):
            p = os.path.basename(os.path.dirname(d))
            if p.startswith('patchAverage(') or p.startswith('patchIntegrate('):
                shutil.rmtree(d)
    if just_delete_previous_files:
        sys.exit(0) # 正常終了

    if interactive:
        patches = ' '.join(listFile.patchList())
        fields = ' '.join(listFile.volFieldList(folderTime.latestTime()))
        ans = True if (raw_input if sys.version_info.major <= 2 else input)(
            '面積平均を行いますか？ (y/n) > ').strip().lower() == 'y' else False
        if ans:
            average = [(raw_input if sys.version_info.major <= 2 else input)(
                'どのパッチに対して面積平均しますか？ ' + patches + ' の中からスペース区切りで指定して下さい． > ').split()]
            average.append(','.join((raw_input if sys.version_info.major <= 2 else input)(
                'どのパラメータを面積平均しますか？ ' + fields + ' の中からスペース区切りで指定して下さい． > ').split()))
        ans = True if (raw_input if sys.version_info.major <= 2 else input)(
            '面積積分を行いますか？ (y/n) > ').strip().lower() == 'y' else False
        if ans:
            integrate = [(raw_input if sys.version_info.major <= 2 else input)(
                'どのパッチに対して面積積分しますか？ ' + patches + ' の中からスペース区切りで指定して下さい． > ').split()]
            integrate.append(','.join(
                (raw_input if sys.version_info.major <= 2 else input)(
                'どのパラメータを面積積分しますか？ ' + fields + ' の中からスペース区切りで指定して下さい． > ').split()))
        time_begin, time_end, noZero = misc.setTimeBeginEnd('面積平均または面積積分')

    # http://penguinitis.g1.xrea.com/study/OpenFOAM/proc_results.html
    for i in average[0]:
        misc.execPostProcess(time_begin, time_end, noZero, func = 'patchAverage(name=' + i + ',' + average[1] + ')')
    for i in integrate[0]:
        misc.execPostProcess(time_begin, time_end, noZero, func = 'patchIntegrate(name=' + i + ',' + integrate[1] + ')')

    print('\n結果はpostProcessingフォルダに保存されています．')

    rmObjects.removeInessentials()
