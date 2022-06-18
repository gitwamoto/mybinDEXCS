#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 乱流量を求める.py
# by Yukiharu Iwamoto
# 2021/7/21 2:51:44 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -b time_begin: Qと渦度の計算を開始する時間をtime_beginにする．指定しない場合は最も小さい値を持つ時間になる
# -e time_end: Qと渦度の計算を終了する時間をtime_endにする．指定しない場合は最も大きい値を持つ時間になる
# -f func: funcにk, epsilon, omega, Rのいずれかを指定して，求めたい乱流量を指定する
# -p -> paraFoamを実行する

import sys
import signal
import os
import glob
import shutil
from utilities import misc
from utilities import rmObjects

def handler(signal, frame):
    rmObjects.removeInessentials()
    sys.exit(1)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler) # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = exec_paraFoam = False
        time_begin = '-inf'
        time_end = 'inf'
        func = None
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-b':
                i += 1
                time_begin = sys.argv[i]
            elif sys.argv[i] == '-e':
                i += 1
                time_end = sys.argv[i]
            elif sys.argv[i] == '-f':
                i += 1
                func = sys.argv[i]
            elif sys.argv[i] == '-p':
                exec_paraFoam = True
            i += 1
        if func is None:
            print('エラー: 求めたい乱流量が指定されていません．')
            sys.exit(1)

    print('k, epsilonなどの乱流量からomegaなどの他の乱流量を求めます．')
    if interactive:
        print('(1) k')
        print('(2) epsilon')
        print('(3) omega')
        print('(4) R')
        func = (raw_input if sys.version_info.major <= 2 else input)(
            '何を求めますか？番号または名前で入力して下さい > ').strip()
        try:
            func = int(func)
            if func == 1:
                func = 'k'
            elif func == 2:
                func = 'epsilon'
            elif func == 3:
                func = 'omega'
            else:
                func = 'R'
        except:
            pass

    if interactive:
        time_begin, time_end = misc.setTimeBeginEnd(func + 'の計算')
    # https://www.openfoam.com/documentation/guides/latest/doc/guide-fos-field-turbulenceFields.html
    # Example by using the postProcess utility: <solver> -postProcess -func turbulenceFields
    misc.execPostProcess(time_begin, time_end, func = 'turbulenceFields(' + func + ')')
    print('\n結果は各時間のフォルダに書き出されます．')
    print('乱流量を変えて計算を継続したい場合，constant/turbulencePropertiesや最新時間における' +
        func +'の境界条件を適切なものに変更しなければなりません．')

    for f in glob.iglob(os.path.join('*', 'turbulenceProperties:' + func)):
        try:
            d = os.path.dirname(f)
            float(d)
            os.rename(f, os.path.join(d, func)) # can overwrite
        except:
            pass

    if interactive:
        exec_paraFoam = True if (raw_input if sys.version_info.major <= 2 else input)(
            '\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam)

    rmObjects.removeInessentials()
