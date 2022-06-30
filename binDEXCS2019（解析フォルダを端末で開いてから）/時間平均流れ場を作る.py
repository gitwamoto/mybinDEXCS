#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 時間平均流れ場を作る.py
# by Yukiharu Iwamoto
# 2022/6/30 8:37:41 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行．system/controlDictのfunctionsにfieldAverageに関する指示を書き込んでいることが前提
# -b time_begin: 平均を開始する時間をtime_beginにする．指定しない場合は最も小さい値を持つ時間になる
# -e time_end: 平均を終了する時間をtime_endにする．指定しない場合は最も大きい値を持つ時間になる
# -0: 0秒のデータを含める
# -d: 最も大きい値を持つ時間以外の平均を消去する．多くの場合必要
# -j: 平均を実行せず，postProcessingフォルダ内にある過去の結果を消去するだけ
# -p -> paraFoamを実行する

import sys
import signal
import subprocess
import os
import glob
import shutil
from utilities import misc
from utilities import setFuncsInCD
from utilities import listFile
from utilities import dictFormat
from utilities.dictParse import DictParser, DictParserList
from utilities import folderTime
from utilities import rmObjects
path_binDEXCS = os.path.expanduser('~/Desktop/binDEXCS2019（解析フォルダを端末で開いてから）') # dakuten.py -j -f <path> で濁点を結合しておく
sys.path.append(path_binDEXCS)

def handler(signal, frame):
    setFuncsInCD.setAllEnabled(False)
    rmObjects.removeInessentials()
    sys.exit(1)

def append_functions_in_controlDict(controlDict):
    a = ''
    for f in listFile.volFieldList(folderTime.latestTime()):
        a += (
            f + '\n' +
            '{\n' +
            'mean\ton /* 平均，onで計算 */;\n' +
            'prime2Mean\ton /* ' + (
            '変動^2の平均，onで計算' if f != 'U' else
            '変動速度相関の平均（レイノルズ応力に-1をかけたもの），' +
                'uu, uv, uw, vv, vw, wwの順で出力，onで計算') +
            ' */;\n' +
            'base\ttime;\n' +
            '}\n'
        )
    a = (
        '// 時間平均流れ場を作る．\n' +
        'FA // <- (A) 時間フォルダ内に作られるファイルの名前につく文字列，' +
            '他と重複してはいけない！\n' +
        '{\n' +
        'type\tfieldAverage;\n' +
        'libs\t("libfieldFunctionObjects.so");\n' +
        'enabled\tyes /* yesで実行 */;\n' +
        'writeControl\twriteTime;\n' +
        'fields\t// 時間平均を計算したいパラメータ\n' +
        '(\n' + a + ');\n' +
        '}\n'
    )
    dp_controlDict = DictParser(controlDict)
    x = dp_controlDict.getValueForKey(['functions'])
    if x is not None:
        dictFormat.insertEntryIntoBlockBottom(entry = DictParser(string = a).contents, block = x)
    else:
        dictFormat.insertEntryIntoTopLayerBottom(
            entry = DictParser(string = '\nfunctions\n{\n' + a + '}\n').contents,
            contents = dp_controlDict.contents)
    shutil.copy(controlDict, controlDict + '_bak')
    dp_controlDict = dictFormat.moveLineToBottom(dp_controlDict)
    dp_controlDict.writeFile(controlDict)
    print('\n\033[3;4;5m%sファイルをtexteditwx.pyで開いています．' % controlDict)
    print('- functionsの中にあるfieldAverageに関する指示を読んで，必要に応じて書き換えて下さい．')
    print('- 書き換えたらtexteditwx.pyを終了して下さい．\033[m\n')
    subprocess.call(os.path.join(path_binDEXCS, 'texteditwx.py') + ' %s' % controlDict, shell = True)
    return dp_controlDict

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler) # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)
    if misc.texteditwx_works_well() == False:
        exit(1)

    just_delete_previous_files = False
    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = delete_except_for_newest_folder = exec_paraFoam = False
        fieldAverage_is_written = True	# <- 書き込めていないと非インタラクティブにできるわけがない
        time_begin, time_end, noZero = '-inf', 'inf', True
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-N': # Non-interactive
                pass
            elif sys.argv[i] == '-b':
                i += 1
                time_begin = sys.argv[i]
            elif sys.argv[i] == '-e':
                i += 1
                time_end = sys.argv[i]
            elif sys.argv[i] == '-0':
                noZero = False
            elif sys.argv[i] == '-d':
                delete_except_for_newest_folder = True
            elif sys.argv[i] == '-j':
                just_delete_previous_files = True
            elif sys.argv[i] == '-p':
                exec_paraFoam = True
            i += 1

    controlDict = os.path.join('system', 'controlDict')
    if not os.path.isfile(controlDict):
        print('エラー: %sファイルがありません．' % controlDict)
        sys.exit(1)

    fieldAverage_related_files_txt = os.path.join('postProcessing', '_fieldAverage_related_files.txt')
    if os.path.isdir('postProcessing') and os.path.isfile(fieldAverage_related_files_txt):
        with open(fieldAverage_related_files_txt, 'r') as f:
            properties = f.readline().rstrip()
        for d in glob.iglob('*' + os.sep):
            try:
                float(os.path.dirname(d))
                for f in glob.iglob(os.path.join(d, '*Mean')):
                    os.remove(f)
                for f in glob.iglob(os.path.join(d, 'uniform', properties)):
                    os.remove(f)
            except:
                pass
    if just_delete_previous_files:
        sys.exit(0) # 正常終了

    setFuncsInCD.setAllEnabled(False)
    setFuncsInCD.setEnabledForType('fieldAverage', True)
    if interactive:
        fieldAverage_is_written = True if (raw_input if sys.version_info.major <= 2 else input)(
            '%sファイルのfunctionsにfieldAverageに関する指示を書き込んでいますか？ (y/n) > ' % controlDict
            ).strip().lower() == 'y' else False
    dp_controlDict = DictParser(controlDict) if fieldAverage_is_written else append_functions_in_controlDict(controlDict)

    properties_list = []
    if dp_controlDict.getValueForKey(['functions']) is not None:
        for x in dp_controlDict.getValueForKey(['functions']):
            if DictParserList.isType(x, DictParserList.BLOCK):
                for y in x.value():
                    if (DictParserList.isType(y, DictParserList.DICT) and
                        y.key() == 'type' and 'fieldAverage' in y.value()):
                        properties_list.append(x.key() + 'Properties')
                        break
    if len(properties_list) == 0:
        print('%sファイルでfieldAverageに関する指示がありません．' % controlDict)
        sys.exit(1)

    if interactive:
        time_begin, time_end, noZero = misc.setTimeBeginEnd('平均')
    # https://develop.openfoam.com/Development/openfoam/-/tree/maintenance-v1906/src/functionObjects/field/fieldAverage
    command = 'Exec: ' + misc.execPostProcess(time_begin, time_end, noZero) + '\n'

    if not os.path.isdir('postProcessing'):
        os.mkdir('postProcessing')
    with open(fieldAverage_related_files_txt, 'w') as f:
        for properties in properties_list:
            f.write(properties + '\n')

    time_begin = float(time_begin)
    time_end = float(time_end)
    for properties in properties_list:
        print('\n結果は各時間のフォルダに書き出され，' +
            'さらに各時間のフォルダの%s' % os.path.join('uniform', properties) +
            'に情報（何秒間の平均かなど）が記録されます．')

        x = []
        for d in glob.iglob('*' + os.sep):
            try:
                d = os.path.dirname(d)
                t = float(d)
                if t >= time_begin and t <= time_end:
                    x.append(d)
                    p = os.path.join(d, 'uniform', properties)
                    if not os.path.isfile(p):
                        with open(p, 'w') as f:
                            f.write(command)
            except:
                pass
        x.sort()
        longest = x[-1]
        x = x[:-1]
        if interactive:
            delete_except_for_newest_folder = True if (raw_input if sys.version_info.major <= 2 else input)(
                '{}以外のフォルダにある平均データを消しますか？ '.format(longest) + '(y/n, 多くの場合yのはず) > '
                ).strip().lower() == 'y' else False
        if delete_except_for_newest_folder:
            for d in x:
                try:
                    for f in glob.iglob(os.path.join(d, '*Mean')):
                        os.remove(f)
                    for f in glob.iglob(os.path.join(d, 'uniform', properties)):
                        os.remove(f)
                except:
                    pass

    if interactive:
        exec_paraFoam = True if (raw_input if sys.version_info.major <= 2 else input)(
            '\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam)

    rmObjects.removeInessentials()
