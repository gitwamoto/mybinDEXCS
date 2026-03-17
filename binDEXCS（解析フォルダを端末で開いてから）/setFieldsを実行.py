#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setFieldsを実行.py
# by Yukiharu Iwamoto
# 2026/3/17 11:08:33 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行．system/setFieldsDictに設定値に関する指示を書き込んでいることが前提

# DictParser2で書き直し済み

import sys
import signal
import subprocess
import os
import shutil
from utilities import misc
from utilities import rmObjects
from utilities import dictParse
path_binDEXCS = os.path.expanduser('~/Desktop/binDEXCS2019（解析フォルダを端末で開いてから）') # dakuten.py -j -f <path> で濁点を結合しておく
sys.path.append(path_binDEXCS)

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
        setFieldsDict_is_written = (True if (raw_input if sys.version_info.major <= 2 else input)(
            setFieldsDict_path + 'ファイルの内容を確認して下さい．設定値に関する指示が書き込まれていますか？ (y/n) > '
            ).strip().lower() == 'y' else False) if os.path.isfile(setFieldsDict_path) else False

    if not setFieldsDict_is_written:
        if os.path.isfile(setFieldsDict_path):
            os.rename(setFieldsDict_path, setFieldsDict_path + '_bak')
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
        print('\n\033[3;4;5m' + setFieldsDict_path + 'ファイルにテンプレートを追加して，texteditwx.pyで開いています．')
        print('説明コメントを読んで，自分が行いたいことに合わせてテンプレートを書き換えて下さい．')
        print('書き換えたらtexteditwx.pyを終了して下さい．\033[m\n')
        subprocess.call(os.path.join(path_binDEXCS, 'texteditwx.py') + ' ' + setFieldsDict_path, shell = True)

    setFieldsDict = dictParse.DictParser2(file_name = setFieldsDict_path)

    fields_set = set()
    fieldValues = (
        setFieldsDict.find_all_elements(
            [{'type': 'dictionary', 'key': 'defaultFieldValues'}, {'type': 'list'},
            {'except type': 'ignorable|list_start|list_end'}]) +
        setFieldsDict.find_all_elements(
            [{'type': 'dictionary', 'key': 'regions'}, {'type': 'list'}, {'type': 'block'},
            {'type': 'dictionary', 'value': 'fieldValues'}, {'type': 'list'},
            {'except type': 'ignorable|list_start|list_end'}]))
    i = 0
    while i < len(fieldValues):
        if (fieldValues[i]['element']['type'] == 'word' and
            fieldValues[i]['element']['value'] in ('volScalarFieldValue', 'volVectorFieldValue')):
            fields_set.add(fieldValues[i + 1]['element']['value'])
            i += 3
        else:
            i += 1
    fields_set = sorted(list(fields_set))

    for i in fields_set:
        i = os.path.join('0', i)
        if os.path.isfile( i + '.orig'):
            shutil.copy(i + '.orig', i)
        else:
            shutil.copy(i, i + '.orig')

    command = 'setFields -noFunctionObjects'
    if subprocess.call(command, shell = True) != 0:
        print(f'{command}で失敗しました．よく分かる人に相談して下さい．')
        sys.exit(1)

    print('setFieldsで書き換えられる前のファイルは，末尾に.origをつけた名前でバックアップされています．')

    rmObjects.removeInessentials()
