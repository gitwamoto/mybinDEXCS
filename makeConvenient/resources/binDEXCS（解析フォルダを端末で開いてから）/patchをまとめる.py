#!/usr/bin/env python
# -*- coding: utf-8 -*-
# patchをまとめる.py
# by Yukiharu Iwamoto
# 2026/5/13 9:31:24 AM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行．system/createPatchDictにpatchをまとめる指示を書き込んでいることが前提

import sys
import signal
import subprocess
import os
from utilities import misc
from utilities import rmObjects
from utilities import dictParse
binDEXCS_path = os.path.expanduser('~/Desktop/binDEXCS（解析フォルダを端末で開いてから）') # dakuten.py -j -f <path> で濁点を結合しておく
sys.path.append(binDEXCS_path)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)
    if not misc.texteditwx_works_well():
        exit(1)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = False
        createPatchDict_is_written = True	# <- 書き込めていないと非インタラクティブにできるわけがない
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-N': # Non-interactive
                pass
            i += 1

    createPatchDict_path = os.path.join('system', 'createPatchDict')
    if interactive:
        createPatchDict_is_written = True if input(f'ファイル{createPatchDict_path}に'
            'patchをまとめる指示を書き込んでいますか？ (y/n) > ').strip().lower() == 'y' else False

    if not createPatchDict_is_written:
        if os.path.isfile(createPatchDict_path):
            os.rename(createPatchDict_path, f'{createPatchDict_path}_bak')
        with open(createPatchDict_path, 'w') as f:
            f.write('FoamFile\n'
                '{\n'
                '\tversion\t2.0;\n'
                '\tformat\tascii;\n'
                '\tclass\tdictionary;\n'
                '\tlocation\t"system";\n'
                '\tobject\tcreatePatchDict;\n'
                '}\n'
                '\npointSync\tfalse;\n'
                '\n'
                'patches\n(\n'
                '// まとめた後のパッチ名(A)，パッチの種類(B)，まとめたいパッチの名前(C)を書き換える．\n'
                '// まとめた後のパッチが複数になる場合，\n'
                '// {\n'
                '//     ...\n'
                '// }\n'
                '// の部分をコピーして使えば良い．\n'
                '\t{\n'
                '\t\tname\tassembledPatch1 /* <- (A) まとめた後のパッチ名 */;\n'
                '\t\tpatchInfo\n'
                '\t\t{\n'
                '\t\t\ttype\twall /* <- (B) まとめた後のパッチの種類 */;\n'
                '\t\t}\n'
                '\t\tconstructFrom\tpatches;\n'
                '\t\tpatches\t(')
            f.write(' '.join([i['element']['key'] for i in dictParse.DictParser(file_name =
                os.path.join('constant', 'polyMesh', 'boundary')).find_all_elements(
                    [{'type': 'list'}, {'type': 'block'}])]))
            f.write(') /* <- (C) まとめたいパッチの名前だけを残す */;\n'
                '\t}\n'
                ');\n')
        print(f'\n\033[3;4;5mファイル{createPatchDict_path}をtexteditwx.pyで開いています．')
        print('- 指示を読んで，必要に応じて書き換えて下さい．')
        print('- 書き換えたらtexteditwx.pyを終了して下さい．\033[m\n')
        subprocess.call(f'{os.path.join(binDEXCS_path, "texteditwx.py")} {createPatchDict_path}', shell = True)

    command = 'createPatch -overwrite'
    if subprocess.call(command, shell = True) != 0:
        print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
        sys.exit(1)

    rmObjects.removeInessentials()
