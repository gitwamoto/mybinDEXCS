#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 結果を抽出.py
# by Yukiharu Iwamoto
# 2026/4/20 8:02:42 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行．system/controlDictのfunctionsにsetsまたはsurfacesに関する指示を書き込んでいることが前提
# -b time_begin: 抽出を開始する時間をtime_beginにする．指定しない場合は最も小さい値を持つ時間になる
#                time_beginにlを指定すると，最も大きい値を持つ時間になる
# -e time_end: 抽出を終了する時間をtime_endにする．指定しない場合は最も大きい値を持つ時間になる
# -0: 0秒のデータを含める
# -j: 抽出を実行せず，postProcessingフォルダ内にある過去の結果を消去するだけ

# DictParser2で書き直し済み

import sys
import signal
import subprocess
import os
import shutil
from utilities import misc
from utilities import dictFormat
from utilities import rmObjects
from utilities import dictParse
path_binDEXCS = os.path.expanduser('~/Desktop/binDEXCS2019（解析フォルダを端末で開いてから）') # dakuten.py -j -f <path> で濁点を結合しておく
sys.path.append(path_binDEXCS)

def handler(signum, frame):
    misc.setEnabledInControlDictFunctions(enabled = False)
    rmObjects.removeInessentials()
    sys.exit(1)

def append_functions_in_controlDict(controlDict_path):
    controlDict = DictParser(controlDict_path)
    functions = controlDict.find_element([{'type': 'block', 'key': 'functions'}])['element']
    if functions is None:
        linebreak_and_functions = dictParse.DictParser2(string =
            '\n'
            '\n'
            'functions\n'
            '{\n'
            '}').elements
        tail_index = controlDict.find_element([{'except type': 'whitespace|linebreak|separator'}],
            reverse = True, index_not_found = len(controlDict.elements) - 1)['index'] + 1
        controlDict.elements[tail_index:tail_index] = linebreak_and_functions
        functions = linebreak_and_functions[-1]

    fields = ' '.join(misc.volFieldList(misc.latestTime()))
    patches = ' '.join([i['element']['key'] for i in dictParse.DictParser2(
        file_name = os.path.join('constant', 'polyMesh', 'boundary')).find_all_elements(
            [{'type': 'list'}, {'type': 'block'}])])

    block_end = dictParse.find_element([{'type': 'block_end'}], parent = functions, reverse = True)
    block_end['parent'][block_end['index']:block_end['index']] = dictParse.DictParser2(string =
        '\n'
        '\tsetSampling // postProcessingフォルダ内に作られるフォルダの名前\n'
        '\t{\n'
        '\t\ttype\tsets; // 直線や点からデータを抽出\n'
        '\t\tlibs\t("libsampling.so");\n'
        '\t\tenabled\tyes; // yesで実行\n'
        '\t\tsetFormat\traw;\n'
        '\t\tinterpolationScheme\tcellPoint;\n'
        f'\t\tfields\t({fields}); // 抽出したいパラメータ\n'
        '\t\tsets\n'
        '\t\t(\n'
        '\t\t\t// 直線上に等間隔に配置された点からデータを抽出する．\n'
        '\t\t\t// 直線がいちど計算領域外に飛び出すと，そこで抽出をやめてしまうので，計算領域外をまたぐ直線の場合は2直線に分ける．\n'
        '\t\t\t// 少なくとも直線の始点(B)，終点(C)，直線上に配置する点の数(D)は修正する必要がある．\n'
        '\t\t\t// 複数の条件に対して抽出したい場合，\n'
        '\t\t\t// line\n'
        '\t\t\t// {\n'
        '\t\t\t//     ...\n'
        '\t\t\t// }\n'
        '\t\t\t// の部分をコピーして使えば良い．\n'
        '\t\t\tline // <- (A) ファイル名につく文字列，他と重複してはいけない！\n'
        '\t\t\t{\n'
        '\t\t\t\ttype\tuniform;\n'
        '\t\t\t\taxis\txyz;\n'
        '\t\t\t\tstart\t(0.1 0.2 0.3); // <- (B) 始点の(x y z)座標\n'
        '\t\t\t\tend\t(0.4 0.5 0.6); // <- (C) 終点の(x y z)座標\n'
        '\t\t\t\tnPoints\t10; // <- (D) 直線上に配置する点の数\n'
        '\t\t\t}\n'
        '\n'
        '\t\t\t// 任意の点からデータをデータを抽出する．\n'
        '\t\t\t// 少なくとも点の座標(B)は修正する必要がある．\n'
        '\t\t\tpoints // <- (A) ファイル名につく文字列，他と重複してはいけない！\n'
        '\t\t\t{\n'
        '\t\t\t\ttype\tcloud;\n'
        '\t\t\t\taxis\txyz;\n'
        '\t\t\t\tpoints\t((0.1 0.2 0.3) (0.4 0.5 0.6)); // <- (B) 点の(x y z)座標，複数の点を書くこともできる．\n'
        '\t\t\t}\n'
        '\t\t);\n'
        '\t}\n'
        '\n'
        '\tsurfaceSampling // postProcessingフォルダ内に作られるフォルダの名前\n'
        '\t{\n'
        '\t\ttype\tsurfaces;\n'
        '\t\tlibs\t("libsampling.so");\n'
        '\t\tenabled\tyes /* yesで実行 */;\n'
        '\t\tsurfaceFormat\traw;\n'
        '\t\tinterpolationScheme\tcellPoint;\n'
        f'\t\tfields\t({fields}) /* 抽出したいパラメータ */;\n'
        '\t\tsurfaces\n'
        '\t\t(\n'
        '\t\t\t// patchからデータを抽出する．\n'
        '\t\t\t// 少なくともpatches(B)は修正する必要がある．\n'
        '\t\t\tpatch // <- (A) ファイル名につく文字列，他と重複してはいけない！\n'
        '\t\t\t{\n'
        '\t\t\t\ttype\tpatch;\n'
        f'\t\t\t\tpatches\t({patches}); // <- (B) 複数のpatchを指定することもできる．\n'
        '\t\t\t\tinterpolate\tno /* noだとセル中心，yesだとメッシュの交点での値を出力 */;\n'
        '\t\t\t}\n\n'
        '\t\t\t// patchから一定距離だけ離れた面からデータを抽出する．\n'
        '\t\t\t// 少なくともpatches(B)と距離(C)は修正する必要がある．\n'
        '\t\t\t// 複数の条件に対して抽出したい場合，\n'
        '\t\t\t// patchOffset\n'
        '\t\t\t// {\n'
        '\t\t\t//     ...\n'
        '\t\t\t// }\n'
        '\t\t\t// の部分をコピーして使えば良い．\n'
        '\t\t\tpatchOffset // <- (A) ファイル名につく文字列，他と重複してはいけない！\n'
        '\t\t\t{\n'
        '\t\t\t\ttype\tpatchInternalField;\n'
        f'\t\t\t\tpatches\t({patches}); // <- (B) 複数のpatchを指定することもできる．\n'
        '\t\t\t\tinterpolate\tno; // noだとセル中心，yesだとメッシュの交点での値を出力\n'
        '\t\t\t\toffsetMode\tnormal;\n'
        '\t\t\t\tdistance\t0.001; // <- (C) patchからの距離\n'
        '\t\t\t}\n\n'
        '\t\t\t// basePointを通ってnormalVectorに垂直な平面からデータを抽出する．\n'
        '\t\t\t// 少なくともbasePoint(B)とnormalVector(C)は修正する必要がある．\n'
        '\t\t\t// 複数の条件に対して抽出したい場合，\n'
        '\t\t\t// cuttingPlane\n'
        '\t\t\t// {\n'
        '\t\t\t//     ...\n'
        '\t\t\t// }\n'
        '\t\t\t// の部分をコピーして使えば良い．\n'
        '\t\t\tcuttingPlane // <- (A) ファイル名につく文字列，他と重複してはいけない！\n'
        '\t\t\t{\n'
        '\t\t\t\ttype\tcuttingPlane;\n'
        '\t\t\t\tplaneType\tpointAndNormal;\n'
        '\t\t\t\tpointAndNormalDict\n'
        '\t\t\t\t{\n'
        '\t\t\t\t\tbasePoint\t(0.0 0.0 0.0); // <- (B) 平面上の点の(x y z)座標\n'
        '\t\t\t\t\tnormalVector\t(1.0 0.0 0.0); // <- (C) 平面の法線ベクトル(x y z)\n'
        '\t\t\t\t}\n'
        '\t\t\t\tinterpolate\tno;\n'
        '\t\t\t}\n'
        '\t\t);\n'
        '\t}\n').elements
    dictParse.set_blank_line(functions, number_of_blank_lines = 1)

    string = dictParse.normalize(string = controlDict.file_string(pretty_print = True))[0]
    os.rename(controlDict_path, controlDict_path + '_bak')
    with open(controlDict_path, 'w') as f:
        f.write(string)

    print(f'\n\033[3;4;5mファイル {controlDict_path} のfunctionsにsetsまたはsurfacesに関するテンプレートを追加して，'
        'texteditwx.pyで開いています．')
    print('説明コメントを読んで，自分が行いたいことに合わせてテンプレートを書き換えて下さい．')
    print('書き換えたらtexteditwx.pyを終了して下さい．\033[m\n')
    subprocess.call(f'{os.path.join(path_binDEXCS, "texteditwx.py")} {controlDict_path}', shell = True)
    return controlDict

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

    controlDict_path = os.path.join('system', 'controlDict')
    if not os.path.isfile(controlDict_path):
        print(f'エラー: ファイル {controlDict_path} がありません．')
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

    misc.setEnabledInControlDictFunctions(enabled = False)
    misc.setEnabledInControlDictFunctions(enabled = True, type_name = 'sets')
    misc.setEnabledInControlDictFunctions(enabled = True, type_name = 'surfaces')
    if interactive:
        sampling_is_written = True if input(f'ファイル {controlDict_path} の内容を確認して下さい．'
            'functionsにsetsまたはsurfacesに関する指示が書き込まれていますか？ (y/n) > ').strip().lower() == 'y' else False
    controlDict = (DictParser2(controlDict_path) if sampling_is_written
        else append_functions_in_controlDict(controlDict_path))

    sets_dir_list = []
    surface_dir_list = []
    for x in controlDict.getValueForKey(['functions']):
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
        print(f'エラー: ファイル {controlDict_path} でsetsまたはsurfacesに関する指示がありません．')
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
