#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setFieldsを実行.py
# by Yukiharu Iwamoto
# 2026/5/12 9:53:57 AM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行．system/setFieldsDictに設定値に関する指示を書き込んでいることが前提

import sys
import signal
import subprocess
import os
import shutil
from utilities import misc
from utilities import rmObjects
from utilities import dictParse
binDEXCS_path = os.path.expanduser('~/Desktop/binDEXCS（解析フォルダを端末で開いてから）') # dakuten.py -j -f <path> で濁点を結合しておく
sys.path.append(binDEXCS_path)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)
    if misc.texteditwx_works_well() == False:
        exit(1)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = False
        setFieldsDict_is_written = True	# <- 書き込めていないと非インタラクティブにできるわけがない
        set_for_orig = False
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-N': # Non-interactive
                pass
            if sys.argv[i] == '-o':
                set_for_orig = True
            i += 1

    setFieldsDict_path = os.path.join('system', 'setFieldsDict')
    if interactive:
        setFieldsDict_is_written = ((True if input(f'ファイル{setFieldsDict_path}の内容を確認して下さい．'
            '設定値に関する指示が書き込まれていますか？ (y/n) > ').strip().lower() == 'y' else False)
            if os.path.isfile(setFieldsDict_path) else False)

    if not setFieldsDict_is_written:
        if os.path.isfile(setFieldsDict_path):
            os.rename(setFieldsDict_path, f'{setFieldsDict_path}_bak')
        with open(setFieldsDict_path, 'w') as f:
            f.write('FoamFile\n'
                '{\n'
                '\tversion\t2.0;\n'
                '\tformat\tascii;\n'
                '\tclass\tdictionary;\n'
                '\tlocation\t"system";\n'
                '\tobject\tsetFieldsDict;\n'
                '}\n'
                '\n'
                'defaultFieldValues // まず，領域全体で値を設定する．\n'
                '(\n'
                '\tvolScalarFieldValue alpha.water 0 // スカラーの場合 -> 変数の名前 値\n'
                '\tvolVectorFieldValue U (0 0 0) // ベクトルの場合 -> 変数の名前 (x成分 y成分 z成分)\n'
                ');\n'
                '\n'
                'regions\n'
                '(\n'
                '\tboxToCell // boxで決められた直方体の範囲の値を設定する．\n'
                '\t{\n'
                '\t\tbox\t(-1 -1 -1) (2 2 2); // (x_min y_min z_min) (x_max y_max z_max)\n'
                '\t\tfieldValues\n'
                '\t\t(\n'
                '\t\t\tvolScalarFieldValue alpha.water 1 // スカラーの場合 -> 変数の名前 値\n'
                '\t\t\tvolVectorFieldValue U (1 1 1) // ベクトルの場合 -> 変数の名前 (x成分 y成分 z成分)\n'
                '\t\t);\n'
                '\t}\n'
                ');\n')
        print(f'\n\033[3;4;5mファイル{setFieldsDict_path}にテンプレートを追加して，texteditwx.pyで開いています．')
        print('説明コメントを読んで，自分が行いたいことに合わせてテンプレートを書き換えて下さい．')
        print('書き換えたらtexteditwx.pyを終了して下さい．\033[m\n')
        subprocess.call(f'{os.path.join(binDEXCS_path, "texteditwx.py")} setFieldsDict_path', shell = True)

    setFieldsDict = dictParse.DictParser(file_name = setFieldsDict_path)

    fieldValues = (
        setFieldsDict.find_all_elements(
            [{'type': 'dictionary', 'key': 'defaultFieldValues'}, {'type': 'list'},
            {'except type': 'ignorable|list_start|list_end'}]) +
        setFieldsDict.find_all_elements(
            [{'type': 'dictionary', 'key': 'regions'}, {'type': 'list'}, {'type': 'block'},
            {'type': 'dictionary', 'value': 'fieldValues'}, {'type': 'list'},
            {'except type': 'ignorable|list_start|list_end'}]))
    fields_set = sorted({fieldValues[i]['element']['value'] for i in range(1, len(fieldValues), 3)}) # list

    for i in fields_set:
        i = os.path.join('0', i)
        i_orig = f'{i}.orig'
        if os.path.isfile(i_orig):
            shutil.copy(i_orig, i)
        else:
            shutil.copy(i, i_orig)

    command = 'setFields -noFunctionObjects'
    if subprocess.call(command, shell = True) != 0:
        print(f'{command}で失敗しました．よく分かる人に相談して下さい．')
        sys.exit(1)

    print('setFieldsで書き換えられる前のファイルは，末尾に.origをつけた名前でバックアップされています．')

    rmObjects.removeInessentials()
