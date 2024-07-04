#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 連続計算雛形.py
# by Yukiharu Iwamoto
# 2022/6/11 4:44:36 PM

import os
import signal
import sys
import shutil
import subprocess
import glob
path_binDEXCS = os.path.expanduser('~/Desktop/binDEXCS2019（解析フォルダを端末で開いてから）') # dakuten.py -j -f <path> で濁点を結合しておく
if path_binDEXCS not in sys.path:
    sys.path.append(path_binDEXCS)
from utilities.dictParse import DictParser, DictParserList
from utilities import dictFormat
from utilities import appendEntries
from utilities import ofpolymesh
from utilities import folderTime
from utilities import rmObjects
from utilities import showDir
from utilities import dakuten
from utilities import listFile
from utilities import setComment
from utilities import findMaxMin
from utilities import misc
from utilities import setFuncsInCD

regions = 32 # 分割領域

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了

    dir_name = os.path.abspath(os.path.dirname(__file__)) # このファイルがあるフォルダの名前

    # 上書きされているかもしれないファイルを元々のファイルで上書き
    for d in ('elbow_vane01_10', 'elbow_vane02_10', 'elbow_vane03_10', 'elbow_wovane'):
        os.chdir(os.path.join(dir_name, d))

        if os.path.exists('0'):
            shutil.rmtree('0')
        shutil.copytree(os.path.join(dir_name, 'elbow_format', '0'), '0')

        shutil.copyfile(os.path.join(dir_name, 'elbow_format', 'setting.txt'), 'setting.txt')

        fvSolution = os.path.join('system', 'fvSolution')
        shutil.copyfile(os.path.join(dir_name, 'elbow_format', fvSolution), fvSolution)

        controlDict = os.path.join('system', 'controlDict')
        shutil.copyfile(os.path.join(dir_name, 'elbow_format', controlDict), controlDict)

        turbulenceProperties = os.path.join('constant', 'turbulenceProperties')
        shutil.copyfile(os.path.join(dir_name, 'elbow_format', turbulenceProperties), turbulenceProperties)

    # ならし計算
    for d in ('elbow_vane01_10', 'elbow_vane02_10', 'elbow_vane03_10', 'elbow_wovane'):
        os.chdir(os.path.join(dir_name, d))

        if os.path.isdir('dynamicCode'): # どうせ作り直すので，dynamicCodeフォルダを削除
            shutil.rmtree('dynamicCode')

        # ----- 従来のならし計算を使う場合 -----
        with open('setting.txt', 'r') as f:
            lines = f.readlines()
        os.rename('setting.txt', 'setting_bak.txt')
        for i in xrange(len(lines)):
            lines[i] = setComment.uncomment(setComment.comment(lines[i], '// accurate'), '// idle')
            # 行の末尾に// accurateと書かれている行をコメントアウトし，末尾に// idleと書かれている行をアンコメントする
            # '// accurate', '// idle'の文字は，スペースの個数を含めて完全に一致する必要あり
        with open('setting.txt', 'w') as f:
            f.writelines(lines)

        fvSolution = os.path.join('system', 'fvSolution')
        with open(fvSolution, 'r') as f:
            lines = f.readlines()
        os.rename(fvSolution, fvSolution + '_bak')
        for i in xrange(len(lines)):
            lines[i] = setComment.uncomment(setComment.comment(lines[i], '// accurate'), '// idle')
            # 行の末尾に// accurateと書かれている行をコメントアウトし，末尾に// idleと書かれている行をアンコメントする
            # '// accurate', '// idle'の文字は，スペースの個数を含めて完全に一致する必要あり
        with open(fvSolution, 'w') as f:
            f.writelines(lines)

        subprocess.call(os.path.join(path_binDEXCS, '計算.py') + ' -r %d' % regions + ' -e -d', shell = True)
        # ' -e -d'などのオプションの意味は，計算.pyの上の方に書いてある．オプションなので半角スペースで区切らないといけない

#        # ----- ベイズ最適化を使ったならし計算を使う場合 -----
#        subprocess.call(os.path.join(path_binDEXCS, '計算.py') + ' -r %d' % regions + ' -e -d -i -1 -6', shell = True)

    # 正確な計算
    for d in ('elbow_vane01_10', 'elbow_vane02_10', 'elbow_vane03_10', 'elbow_wovane'):
        os.chdir(os.path.join(dir_name, d))

        # ----- 従来のならし計算を使う場合 -----
        with open('setting.txt', 'r') as f:
            lines = f.readlines()
        os.rename('setting.txt', 'setting_bak.txt')
        for i in xrange(len(lines)):
            lines[i] = setComment.comment(setComment.uncomment(lines[i], '// accurate'), '// idle')
            # 行の末尾に// accurateと書かれている行をアンコメントし，末尾に// idleと書かれている行をコメントアウトする
            # '// accurate', '// idle'の文字は，スペースの個数を含めて完全に一致する必要あり
        with open('setting.txt', 'w') as f:
            f.writelines(lines)

        fvSolution = os.path.join('system', 'fvSolution')
        with open(fvSolution, 'r') as f:
            lines = f.readlines()
        os.rename(fvSolution, fvSolution + '_bak')
        for i in xrange(len(lines)):
            lines[i] = setComment.comment(setComment.uncomment(lines[i], '// accurate'), '// idle')
            # 行の末尾に// accurateと書かれている行をアンコメントし，末尾に// idleと書かれている行をコメントアウトする
            # '// accurate', '// idle'の文字は，スペースの個数を含めて完全に一致する必要あり
        with open(fvSolution, 'w') as f:
            f.writelines(lines)

        subprocess.call(os.path.join(path_binDEXCS, '計算.py') + ' -r %d' % regions + ' -e', shell = True)
        # ' -e'のオプションの意味は，並列計算.pyの上の方に書いてある．オプションなので半角スペースで区切らないといけない

#        # ----- ベイズ最適化を使ったならし計算を使う場合 -----
#        subprocess.call(os.path.join(path_binDEXCS, '計算.py') + ' -r %d' % regions + ' -e', shell = True)
#        # ' -e'のオプションの意味は，並列計算.pyの上の方に書いてある．オプションなので半角スペースで区切らないといけない