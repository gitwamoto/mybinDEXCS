#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 流量を求める.py
# by Yukiharu Iwamoto
# 2023/5/8 12:08:57 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -b time_begin: 流量計算を開始する時間をtime_beginにする．指定しない場合は最も小さい値を持つ時間になる
#                time_beginにlを指定すると，最も大きい値を持つ時間になる
# -e time_end: 流量計算を終了する時間をtime_endにする．指定しない場合は最も大きい値を持つ時間になる
# -0: 0秒のデータを含める
# -j: 流量計算を実行せず，postProcessingフォルダ内にある過去の結果を消去するだけ
# -p 'patch1,patch2,...': patch1,patch2,...に対して流量を求める
#                         patch1,patch2,...はコンマ区切りで書いたものを'と'でくくる

import sys
import signal
import os
import glob
import shutil
import re
from utilities import misc
from utilities import listFile
from utilities import rmObjects

def handler(signal, frame):
    rmObjects.removeInessentials()
    sys.exit(1)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler) # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)

    just_delete_previous_files = False
    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = False
        patch_list = []
        time_begin, time_end, noZero = '-inf', 'inf', True
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-b':
                i += 1
                time_begin = sys.argv[i]
            elif sys.argv[i] == '-e':
                i += 1
                time_end = sys.argv[i]
            elif sys.argv[i] == '-0':
                noZero = False
            elif sys.argv[i] == '-p':
                i += 1
                patch_list = [j.strip() for j in sys.argv[i].split(',')]
            elif sys.argv[i] == '-j':
                just_delete_previous_files = True
            i += 1

    if os.path.isdir('postProcessing'):
        for d in glob.iglob(os.path.join('postProcessing', 'flowRatePatch(*' + os.sep)):
            shutil.rmtree(d)
    if just_delete_previous_files:
        sys.exit(0) # 正常終了

    if interactive:
        patch_list = (raw_input if sys.version_info.major <= 2 else input)(
            'どのパッチに対して流量を計算しますか？ ' + ' '.join(listFile.patchList()) +
            ' の中からスペース区切りで指定して下さい． > ').split()
        time_begin, time_end, noZero = misc.setTimeBeginEnd('流量計算')

    for i in patch_list:
        # http://penguinitis.g1.xrea.com/study/OpenFOAM/proc_results.html
        misc.execPostProcess(time_begin, time_end, noZero, func = 'flowRatePatch(name=' + i + ')')

    print('\n結果はpostProcessingフォルダに保存されています．')

    rmObjects.removeInessentials()
