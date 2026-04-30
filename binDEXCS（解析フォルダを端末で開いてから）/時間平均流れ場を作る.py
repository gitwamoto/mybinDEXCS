#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 時間平均流れ場を作る.py
# by Yukiharu Iwamoto
# 2026/4/30 4:02:22 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行．system/controlDictのfunctionsにfieldAverageに関する指示を書き込んでいることが前提
# -b time_begin: 平均を開始する時間をtime_beginにする．指定しない場合は最も小さい値を持つ時間になる
#                time_beginにlを指定すると，最も大きい値を持つ時間になる
# -e time_end: 平均を終了する時間をtime_endにする．指定しない場合は最も大きい値を持つ時間になる
# -0: 0秒のデータを含める
# -d: 最も大きい値を持つ時間以外の平均を消去する．多くの場合必要
# -j: 平均を実行せず，postProcessingフォルダ内にある過去の結果を消去するだけ
# -p -> paraFoamを実行する

# DictParser2で書き直し済み

import sys
import signal
import subprocess
import os
import glob
import shutil
from utilities import misc
from utilities import dictFormat
from utilities import rmObjects
from utilities import dictParse
path_binDEXCS = os.path.expanduser('~/Desktop/binDEXCS（解析フォルダを端末で開いてから）') # dakuten.py -j -f <path> で濁点を結合しておく
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

    string = (
        '\n'
        '\t// 時間平均流れ場を作る．\n'
        '\tFA // <- (A) 時間フォルダ内に作られるファイルの名前につく文字列，他と重複してはいけない！\n'
        '\t{\n'
        '\t\ttype\tfieldAverage;\n'
        '\t\tlibs\t("libfieldFunctionObjects.so");\n'
        '\t\tenabled\tyes; // yesで実行\n'
        '\t\twriteControl\twriteTime;\n'
        '\t\tfields // 時間平均を計算したいパラメータ\n'
        '\t\t(\n'
    )
    for field in misc.volFieldList(misc.latestTime()):
        string += (
            f'\t\t\t{field}\n'
            '\t\t\t{\n'
            '\t\t\t\tmean\ton; // 平均，onで計算\n'
            '\t\t\t\tprime2Mean\ton; // '
            f'{"変動^2の平均" if field != "U" else
            "変動速度相関の平均（レイノルズ応力に-1をかけたもの），uu, uv, uw, vv, vw, wwの順で出力"}，onで計算'
            '\t\t\t\t\n'
            '\t\t\t\tbase\ttime;\n'
            '\t\t\t}\n'
        )
    string += (
        '\t\t);\n'
        '\t}\n'
    )

    block_end = dictParse.find_element([{'type': 'block_end'}], parent = functions, reverse = True)
    block_end['parent'][block_end['index']:block_end['index']] = dictParse.DictParser2(string = string).elements
    dictParse.set_blank_line(functions, number_of_blank_lines = 1)

    string = dictParse.normalize(string = controlDict.file_string(pretty_print = True))[0]
    os.rename(controlDict_path, controlDict_path + '_bak')
    with open(controlDict_path, 'w') as f:
        f.write(string)

    print(f'\n\033[3;4;5mファイル{controlDict_path}のfunctionsにfieldAverageに関するテンプレートを追加して，'
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

    controlDict_path = os.path.join('system', 'controlDict')
    if not os.path.isfile(controlDict_path):
        print(f'エラー: ファイル{controlDict_path}がありません．')
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

    misc.setEnabledInControlDictFunctions(enabled = False)
    misc.setEnabledInControlDictFunctions(enabled = True, type_name = 'fieldAverage')
    if interactive:
        fieldAverage_is_written = True if input(f'ファイル{controlDict_path}の内容を確認して下さい．'
            'functionsにfieldAverageに関する指示が書き込まれていますか？ (y/n) > ').strip().lower() == 'y' else False
    controlDict = (DictParser2(file_name = controlDict_path) if fieldAverage_is_written
        else append_functions_in_controlDict(controlDict_path))

    types = controlDict.find_all_elements([{'type': 'block', 'key': 'functions'}, {'type': 'block'},
        {'type': 'dictionary', 'key': 'type'}])
    properties_list = [f'{i["parent"]["key"]}Properties' for i in types
        if dictParse.find_element([{'type': 'word'}], parent = i['element'])['element'] == 'fieldAverage']
    if len(properties_list) == 0:
        print(f'エラー: ファイル{controlDict_path}でfieldAverageに関する指示がありません．')
        sys.exit(1)

    if interactive:
        time_begin, time_end, noZero = misc.setTimeBeginEnd('平均')
    # https://develop.openfoam.com/Development/openfoam/-/tree/maintenance-v1906/src/functionObjects/field/fieldAverage
    command_string = f'Exec: {misc.execPostProcess(time_begin, time_end, noZero)}\n'

    if not os.path.isdir('postProcessing'):
        os.mkdir('postProcessing')
    with open(fieldAverage_related_files_txt, 'w') as f:
        for properties in properties_list:
            f.write(properties + '\n')

    time_begin = float(time_begin)
    time_end = float(time_end)
    for properties in properties_list:
        print('\n結果は各時間のフォルダに書き出され，'
            f'さらに各時間のフォルダの{os.path.join("uniform", properties)}に情報（何秒間の平均かなど）が記録されます．')

        time_dirs = []
        for d in glob.iglob('*' + os.sep):
            try:
                d = os.path.dirname(d)
                t = float(d)
                if t >= time_begin and t <= time_end:
                    time_dirs.append(d)
                    p = os.path.join(d, 'uniform', properties)
                    if not os.path.isfile(p):
                        with open(p, 'w') as f:
                            f.write(command_string)
            except:
                pass
        time_dirs.sort()
        longest = time_dirs[-1]
        time_dirs = time_dirs[:-1]
        if interactive:
            delete_except_for_newest_folder = True if input(f'{longest}以外のフォルダにある平均データを消しますか？'
                ' (y/n, 多くの場合yのはず) > ').strip().lower() == 'y' else False
        if delete_except_for_newest_folder:
            for d in time_dirs:
                try:
                    for f in glob.iglob(os.path.join(d, '*Mean')):
                        os.remove(f)
                    for f in glob.iglob(os.path.join(d, 'uniform', properties)):
                        os.remove(f)
                except:
                    pass

    if interactive:
        exec_paraFoam = True if input('\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam)

    rmObjects.removeInessentials()
