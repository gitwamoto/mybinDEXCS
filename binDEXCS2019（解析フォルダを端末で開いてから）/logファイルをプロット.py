#!/usr/bin/env python
# -*- coding: utf-8 -*-
# logファイルをプロット.py
# by Yukiharu Iwamoto
# 2021/7/21 1:01:09 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行，名前がFoam.logfileで終わるファイルが解析フォルダの中に1つしかないことが前提
# -l log_file_name -> logファイルの名前を指定して実行する

import signal
import os
import glob
import sys
import shutil
import matplotlib.pyplot as plt
import math
import subprocess
import re
from utilities import misc
from utilities import rmObjects

def appropriate_tick(xmin, xmax, n):
    tmp = abs(xmax - xmin)/(n + 0.01)
    tick = 10.0**math.floor(math.log10(tmp))
    tmp /= tick # 1 <= tmp < 10
    for i in (1.0, 2.0, 2.5, 5.0):
        if tmp < i:
            return i*tick
    return 10.0*tick

mycompreg = re.compile('([^0-9]*)([0-9]+)$')
def mycomp(x, y):
    try:
        x = mycompreg.match(x)
        y = mycompreg.match(y)
        if x.group(1) > y.group(1):
            return 1
        elif x.group(1) < y.group(1):
            return -1
        else:
            return int(x.group(2)) - int(y.group(2))
    except:
        return 0

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    log_file = None
    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = False
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-N': # Non-interactive
                pass
            elif sys.argv[i] == '-l':
                i += 1
                log_file = sys.argv[i]
            i += 1

    if log_file is None:
        log_file = glob.glob('*Foam.logfile')
        if len(log_file) == 0:
            print('logファイルがありません．')
            sys.exit(1)
        elif len(log_file) == 1:
            log_file = log_file[0]
        elif interactive:
            log_file = (raw_input if sys.version_info.major <= 2 else input)(
                ' '.join(log_file) + ' という複数のlogファイルがあります．どれを使いますか？ > ').strip()
        else:
            print(', '.join(log_file) + 'という複数のlogファイルがあるので．どれを使うか分かりません．')
            sys.exit(1)

    if os.path.isdir('logs'):
        shutil.rmtree('logs')
    command = 'foamLog {}'.format(log_file)
    if subprocess.call(command, shell = True) != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)
    print('\nlogsフォルダに残差 (residual) が書き出されます．')
    print('それぞれのファイル名についている最後の数字 (_0など) はサブイタレーションの回数を表します．0が最初のサブイタレーションです．')
    print('1つのサブイタレーションにおいて初期残差を記したファイルには数字 (_0など) が，' +
        '最終残差を記したファイルにはFinalResと数字 (FinalRes_0など) がファイル名についています．')

    rmObjects.removeLogPlotPngs()

    vars = [os.path.basename(i) for i in glob.iglob(os.path.join('logs', '*FinalRes_*'))]
    vars.sort(cmp = mycomp)
    i = 1
    while i < len(vars):
        if vars[i - 1][:vars[i - 1].find('FinalRes_')] == vars[i][:vars[i].find('FinalRes_')]:
            del vars[i - 1]
        else:
            i += 1
    if len(vars) == 0:
        print('残差をプロットすべき変数がありません．')
    else:
        x_min = float('inf')
        x_max = -x_min
        for v in vars:
            v = v.replace('FinalRes_', '_')
            x = []
            y = []
            for line in open(os.path.join('logs', v), 'r'):
                line = line.split()
                try:
                    fx = float(line[0])
                    fy = float(line[1])
                    x_max = max(x_max, fx)
                    x_min = min(x_min, fx)
                    x.append(fx)
                    y.append(fy)
                except:
                    pass
            if len(x) > 0:
                plt.plot(x, y, label = v)
        plt.xlabel('time [s]', fontsize = 16)
        plt.ylabel('initial residuals', fontsize = 16)
        tick = appropriate_tick(x_min, x_max, 5)
        x_max = tick*math.ceil(x_max/tick - 0.01)
        x_min = tick*math.floor(x_min/tick + 0.01)
        plt.xlim(x_min, x_max)
        plt.xticks([x_min + i*tick for i in range(int((x_max - x_min)/tick + 1.1))])
        plt.yscale('log')
        plt.tick_params(which = 'both', direction = 'in', labelsize = 14)
        plt.tick_params(length = 10, which = 'major')
        plt.tick_params(length = 5, which = 'minor')
        plt.legend(loc = 'best', prop = {'size': 16}, framealpha = 0.2)
        png_name = 'residualsInitial.png'
        plt.savefig(png_name)
        plt.clf()
        subprocess.call('xdg-open {}'.format(png_name), shell = True)
        print('最初のサブイタレーションにおける残差のグラフを{}に保存しました．'.format(png_name))

        x_min = float('inf')
        x_max = -x_min
        for v in vars:
            x = []
            y = []
            for line in open(os.path.join('logs', v), 'r'):
                line = line.split()
                try:
                    fx = float(line[0])
                    fy = float(line[1])
                    x_max = max(x_max, fx)
                    x_min = min(x_min, fx)
                    x.append(fx)
                    y.append(fy)
                except:
                    pass
            if len(x) > 0:
                plt.plot(x, y, label = v.replace('FinalRes_', '_'))
        plt.xlabel('time [s]', fontsize = 16)
        plt.ylabel('final residuals', fontsize = 16)
        tick = appropriate_tick(x_min, x_max, 5)
        x_max = tick*math.ceil(x_max/tick - 0.01)
        x_min = tick*math.floor(x_min/tick + 0.01)
        plt.xlim(x_min, x_max)
        plt.xticks([x_min + i*tick for i in range(int((x_max - x_min)/tick + 1.1))])
        plt.yscale('log')
        plt.tick_params(which = 'both', direction = 'in', labelsize = 14)
        plt.tick_params(length = 10, which = 'major')
        plt.tick_params(length = 5, which = 'minor')
        plt.legend(loc = 'best', prop = {'size': 16}, framealpha = 0.2)
        png_name = 'residualsFinal.png'
        plt.savefig(png_name)
        plt.clf()
        subprocess.call('xdg-open {}'.format(png_name), shell = True)
        print('最終残差のグラフを{}に保存しました．'.format(png_name))

    vars = [os.path.basename(i) for i in glob.iglob(os.path.join('logs', 'cont*_0'))]
    if len(vars) == 0:
        print('プロットすべき連続の式の誤差がありません．')
    else:
        x_min = float('inf')
        x_max = -x_min
        for v in vars:
            x = []
            y = []
            for line in open(os.path.join('logs', v), 'r'):
                line = line.split()
                try:
                    fx = float(line[0])
                    fy = abs(float(line[1]))
                    x_max = max(x_max, fx)
                    x_min = min(x_min, fx)
                    x.append(fx)
                    y.append(fy)
                except:
                    pass
            if len(x) > 0:
                label = v[4:].lower()
                if label.startswith('cumulative') or label.startswith('local'):
                    label = 'abs. of ' + label
                plt.plot(x, y, label = label)
        plt.xlabel('time [s]', fontsize = 16)
        plt.ylabel('continuity errors', fontsize = 16)
        tick = appropriate_tick(x_min, x_max, 5)
        x_max = tick*math.ceil(x_max/tick - 0.01)
        x_min = tick*math.floor(x_min/tick + 0.01)
        plt.xlim(x_min, x_max)
        plt.xticks([x_min + i*tick for i in range(int((x_max - x_min)/tick + 1.1))])
        plt.yscale('log')
        plt.tick_params(which = 'both', direction = 'in', labelsize = 14)
        plt.tick_params(length = 10, which = 'major')
        plt.tick_params(length = 5, which = 'minor')
        plt.legend(loc = 'best', prop = {'size': 16}, framealpha = 0.2)
        png_name = 'continuityErrors.png'
        plt.savefig(png_name)
        plt.clf()
        subprocess.call('xdg-open {}'.format(png_name), shell = True)
        print('連続の式の誤差のグラフを{}に保存しました．'.format(png_name))

    rmObjects.removeInessentials()
