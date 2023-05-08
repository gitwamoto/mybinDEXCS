#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 結果を抽出.py
# by Yukiharu Iwamoto
# 2023/5/8 12:09:05 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行．system/controlDictのfunctionsにsetsまたはsurfacesに関する指示を書き込んでいることが前提
# -b time_begin: 抽出を開始する時間をtime_beginにする．指定しない場合は最も小さい値を持つ時間になる
#                time_beginにlを指定すると，最も大きい値を持つ時間になる
# -e time_end: 抽出を終了する時間をtime_endにする．指定しない場合は最も大きい値を持つ時間になる
# -0: 0秒のデータを含める
# -j: 抽出を実行せず，postProcessingフォルダ内にある過去の結果を消去するだけ

import sys
import signal
import subprocess
import os
import shutil
from utilities import misc
from utilities import setFuncsInCD
from utilities import listFile
from utilities import folderTime
from utilities import dictFormat
from utilities.dictParse import DictParser, DictParserList
from utilities import rmObjects
path_binDEXCS = os.path.expanduser('~/Desktop/binDEXCS2019（解析フォルダを端末で開いてから）') # dakuten.py -j -f <path> で濁点を結合しておく
sys.path.append(path_binDEXCS)

def handler(signal, frame):
    setFuncsInCD.setAllEnabled(False)
    rmObjects.removeInessentials()
    sys.exit(1)

def append_functions_in_controlDict(controlDict):
    fields = ' '.join(listFile.volFieldList(folderTime.latestTime()))
    patches = ' '.join(listFile.patchList())
    a = (
        'setSampling // postProcessingフォルダ内に作られるフォルダの名前\n' +
        '{\n' +
            'type\tsets /* 直線や点からデータを抽出 */;\n' +
            'libs\t("libsampling.so");\n' +
            'enabled\tyes /* yesで実行 */;\n' +
            'setFormat\traw;\n' +
            'interpolationScheme\tcellPoint;\n' +
            'fields\t(' + fields + ') /* 抽出したいパラメータ */;\n' +
            'sets\n' +
            '(\n' +
            '// 直線上に等間隔に配置された点からデータを抽出する．\n' +
            '// 少なくとも直線の始点(B)，終点(C)，直線上に配置する点の数(D)は修正する必要がある．\n' +
            '// 複数の条件に対して抽出したい場合，\n' +
            '// line\n' +
            '// {\n' +
            '//     ...\n' +
            '// }\n' +
            '// の部分をコピーして使えば良い．\n' +
            'line // <- (A) ファイル名につく文字列，他と重複してはいけない！\n' +
            '{\n' +
            'type\tuniform;\n' +
            'axis\txyz;\n' +
            'start\t(0.1 0.2 0.3) /* <- (B) 始点の(x y z)座標 */;\n' +
            'end\t(0.4 0.5 0.6) /* <- (C) 終点の(x y z)座標 */;\n' +
            'nPoints\t10 /* <- (D) 直線上に配置する点の数 */;\n' +
            '}\n\n' +
            '// 任意の点からデータをデータを抽出する．\n' +
            '// 少なくとも点の座標(B)は修正する必要がある．\n' +
            'points // <- (A) ファイル名につく文字列，他と重複してはいけない！\n' +
            '{\n' +
            'type\tcloud;\n' +
            'axis\txyz;\n' +
            'points\t((0.1 0.2 0.3) (0.4 0.5 0.6)) ' +
                '/* <- (B) 点の(x y z)座標，複数の点を書くこともできる． */;\n' +
            '}\n' +
            ');\n' +
        '}\n\n' +
        'surfaceSampling // postProcessingフォルダ内に作られるフォルダの名前\n' +
        '{\n' +
            'type\tsurfaces;\n' +
            'libs\t("libsampling.so");\n' +
            'enabled\tyes /* yesで実行 */;\n' +
            'surfaceFormat\traw;\n' +
            'interpolationScheme\tcellPoint;\n' +
            'fields\t(' + fields + ') /* 抽出したいパラメータ */;\n' +
            'surfaces\n' +
            '(\n' +
            '// patchからデータを抽出する．\n' +
            '// 少なくともpatches(B)は修正する必要がある．\n' +
            'patch // <- (A) ファイル名につく文字列，他と重複してはいけない！\n' +
            '{\n' +
            'type\tpatch;\n' +
            'patches\t(' + patches + ') /* <- (B) 複数のpatchを指定することもできる． */;\n' +
            'interpolate\tno /* noだとセル中心，yesだとメッシュの交点での値を出力 */;\n' +
            '}\n\n' +
            '// patchから一定距離だけ離れた面からデータを抽出する．\n' +
            '// 少なくともpatches(B)と距離(C)は修正する必要がある．\n' +
            '// 複数の条件に対して抽出したい場合，\n' +
            '// patchOffset\n' +
            '// {\n' +
            '//     ...\n' +
            '// }\n' +
            '// の部分をコピーして使えば良い．\n' +
            'patchOffset // <- (A) ファイル名につく文字列，他と重複してはいけない！\n' +
            '{\n' +
            'type\tpatchInternalField;\n' +
            'patches\t(' + patches + ') /* <- (B) 複数のpatchを指定することもできる． */;\n' +
            'interpolate\tno /* noだとセル中心，yesだとメッシュの交点での値を出力 */;\n' +
            'offsetMode\tnormal;\n' +
            'distance\t0.001 /* <- (C) patchからの距離 */;\n' +
            '}\n\n' +
            '// basePointを通ってnormalVectorに垂直な平面からデータを抽出する．\n' +
            '// 少なくともbasePoint(B)とnormalVector(C)は修正する必要がある．\n' +
            '// 複数の条件に対して抽出したい場合，\n' +
            '// cuttingPlane\n' +
            '// {\n' +
            '//     ...\n' +
            '// }\n' +
            '// の部分をコピーして使えば良い．\n' +
            'cuttingPlane // <- (A) ファイル名につく文字列，他と重複してはいけない！\n' +
            '{\n' +
            'type\tcuttingPlane;\n' +
            'planeType\tpointAndNormal;\n' +
            'pointAndNormalDict\n' +
            '{\n' +
            'basePoint\t(0.0 0.0 0.0) /* <- (B) 平面上の点の(x y z)座標 */;\n' +
            'normalVector\t(1.0 0.0 0.0) /* <- (C) 平面の法線ベクトル(x y z) */;\n' +
            '}\n' +
            'interpolate\tno;\n' +
            '}\n' +
            ');\n' +
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
    print('\n\033[3;4;5m{}ファイルをtexteditwx.pyで開いています．'.format(controlDict))
    print('- functionsの中にあるsetsまたはsurfacesに関する指示を読んで，必要に応じて書き換えて下さい．')
    print('- 書き換えたらtexteditwx.pyを終了して下さい．\033[m\n')
    subprocess.call(os.path.join(path_binDEXCS, 'texteditwx.py') + ' ' + controlDict, shell = True)
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
        interactive = False
        sampling_is_written = True	# <- 書き込めていないと非インタラクティブにできるわけがない
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
            elif sys.argv[i] == '-j':
                just_delete_previous_files = True
            i += 1

    controlDict = os.path.join('system', 'controlDict')
    if not os.path.isfile(controlDict):
        print('エラー: {}ファイルがありません．'.format(controlDict))
        sys.exit(1)

    sampling_related_folders_txt = os.path.join('postProcessing', '_sampling_related_folders.txt')
    if os.path.isdir('postProcessing') and os.path.isfile(sampling_related_folders_txt):
        for line in open(sampling_related_folders_txt, 'r'):
            tmp = os.path.join('postProcessing', line.rstrip())
            if os.path.isdir(tmp):
                shutil.rmtree(tmp)
        os.remove(sampling_related_folders_txt)
    if just_delete_previous_files:
        sys.exit(0) # 正常終了

    setFuncsInCD.setAllEnabled(False)
    setFuncsInCD.setEnabledForType('sets', True)
    setFuncsInCD.setEnabledForType('surfaces', True)
    if interactive:
        sampling_is_written = True if (raw_input if sys.version_info.major <= 2 else input)(
            '{}ファイルのfunctionsにsetsまたはsurfacesに関する指示を書き込んでいますか？ (y/n) > '.format(controlDict)
            ).strip().lower() == 'y' else False
    dp_controlDict = DictParser(controlDict) if sampling_is_written else append_functions_in_controlDict(controlDict)

    sets_dir_list = []
    surface_dir_list = []
    for x in dp_controlDict.getValueForKey(['functions']):
        if DictParserList.isType(x, DictParserList.BLOCK):
            for y in x.value():
                if DictParserList.isType(y, DictParserList.DICT) and y.key() == 'type':
                    if 'sets' in y.value():
                        sets_dir_list.append(x.key())
                        break
                    elif 'surfaces' in y.value():
                        surface_dir_list.append(x.key())
                        break
    if len(sets_dir_list) == 0 and len(surface_dir_list) == 0:
        print('{}ファイルでsetsまたはsurfacesに関する指示がありません．'.format(controlDict))
        sys.exit(1)

    if interactive:
        time_begin, time_end, noZero = misc.setTimeBeginEnd('抽出')
    # http://penguinitis.g1.xrea.com/study/OpenFOAM/sampling.html
    misc.execPostProcess(time_begin, time_end, noZero)

    with open(sampling_related_folders_txt, 'w') as f:
        for sets_dir in sets_dir_list:
            f.write(sets_dir + '\n')
        for surface_dir in surface_dir_list:
            f.write(surface_dir + '\n')

    print('\n結果はpostProcessingフォルダに保存されています．')

    rmObjects.removeInessentials()
