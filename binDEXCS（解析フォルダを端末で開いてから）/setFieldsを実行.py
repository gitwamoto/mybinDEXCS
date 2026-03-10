#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setFieldsを実行.py
# by Yukiharu Iwamoto
# 2023/11/10 4:28:45 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行．system/setFieldsDictに設定値に関する指示を書き込んでいることが前提
# -o -> 0秒のフォルダに.origで終わるファイルがある場合，それに対してsetFieldsを行う

import sys
import signal
import subprocess
import os
import shutil
from utilities import misc
from utilities.dictParse import DictParser, DictParserList
from utilities import rmObjects
path_binDEXCS = os.path.expanduser('~/Desktop/binDEXCS2019（解析フォルダを端末で開いてから）') # dakuten.py -j -f <path> で濁点を結合しておく
sys.path.append(path_binDEXCS)

def find_fields(dpl):
    fields = []
    for x in dpl:
        if isinstance(x, (tuple, list)):
            if DictParserList.isType(x, DictParserList.LISTP):
                i = 0
                y = x[2]
                while i < len(y):
                    if type(y[i]) is str and y[i] in ('volScalarFieldValue', 'volVectorFieldValue'):
                        i += 2
                        if i < len(y) and type(y[i]) is str:
                            fields.append(y[i])
                    elif isinstance(y[i], (tuple, list)):
                        fields.extend(find_fields(y[i]))
                    i += 1
            else:
                fields.extend(find_fields(x))
    return list(set(fields))

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

    setFieldsDict = os.path.join('system', 'setFieldsDict')
    if interactive:
        setFieldsDict_is_written = (True if (raw_input if sys.version_info.major <= 2 else input)(
            setFieldsDict + 'ファイルの内容を確認して下さい．設定値に関する指示が書き込まれていますか？ (y/n) > '
            ).strip().lower() == 'y' else False) if os.path.isfile(setFieldsDict) else False

    if not setFieldsDict_is_written:
        if os.path.isfile(setFieldsDict):
            os.rename(setFieldsDict, setFieldsDict + '_bak')
        with open(setFieldsDict, 'w') as f:
            f.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tdictionary;\n')
            f.write('\tlocation\t"system";\n')
            f.write('\tobject\tsetFieldsDict;\n')
            f.write('}\n')
            f.write('\n// まず，領域全体で値を設定する．\n')
            f.write('defaultFieldValues\n(\n')
            f.write('\tvolScalarFieldValue /* 変数の名前 = */ alpha.water /* 値 = */ 0\n')
            f.write(');\n')
            f.write('\nregions\n(\n')
            f.write('\t// boxで決められた直方体の範囲の値を設定する．\n')
            f.write('\tboxToCell\n\t{\n')
            f.write('\t\tbox\t/* (x_min y_min z_min) = */ (-1 -1 -1) /* (x_max y_max z_max) = */ (2 2 2);\n')
            f.write('\t\tfieldValues\n\t\t(\n')
            f.write('\t\t\tvolScalarFieldValue /* 変数の名前 = */ alpha.water /* 値 = */ 1\n')
            f.write('\t\t);\n')
            f.write('\t}\n')
            f.write(');\n')
        print('\n\033[3;4;5m' + setFieldsDict + 'ファイルにテンプレートを追加して，texteditwx.pyで開いています．')
        print('説明コメントを読んで，自分が行いたいことに合わせてテンプレートを書き換えて下さい．')
        print('書き換えたらtexteditwx.pyを終了して下さい．\033[m\n')
        subprocess.call(os.path.join(path_binDEXCS, 'texteditwx.py') + ' {}'.format(setFieldsDict), shell = True)

    fields_to_be_set = find_fields(DictParser(setFieldsDict).contents)
    orig_fields = []
    for i in fields_to_be_set:
        field = os.path.join('0', i)
        if os.path.isfile(field + '.orig'):
            orig_fields.append(i + '.orig')
    if interactive and len(orig_fields) > 0:
        set_for_orig = True if (raw_input if sys.version_info.major <= 2 else input)(
            '0秒フォルダにある{}に対してsetFieldsを行いますか？ (y/n) > '.format(', '.join(orig_fields))
            ).strip().lower() == 'y' else False
    if set_for_orig:
        for i in orig_fields:
            field = os.path.join('0', i)
            shutil.copy(field, field[:-5])
    for i in fields_to_be_set:
        field = os.path.join('0', i)
        shutil.copy(field, field + '.orig')

    command = 'setFields -noFunctionObjects'
    if subprocess.call(command, shell = True) != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)

    print('setFieldsで書き換えられる前のファイルは，末尾に.origをつけた名前でバックアップされています．')

    rmObjects.removeInessentials()
