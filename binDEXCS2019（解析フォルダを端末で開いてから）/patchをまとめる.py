#!/usr/bin/env python
# -*- coding: utf-8 -*-
# patchをまとめる.py
# by Yukiharu Iwamoto
# 2021/7/2 8:49:45 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行．system/createPatchDictにpatchをまとめる指示を書き込んでいることが前提

import sys
import signal
import subprocess
import os
from utilities import misc
from utilities import listFile
from utilities import rmObjects
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
        createPatchDict_is_written = True	# <- 書き込めていないと非インタラクティブにできるわけがない
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-N': # Non-interactive
                pass
            i += 1

    createPatchDict = os.path.join('system', 'createPatchDict')
    if interactive:
        createPatchDict_is_written = True if (raw_input if sys.version_info.major <= 2 else input)(
            '{}ファイルにpatchをまとめる指示を書き込んでいますか？ (y/n) > '.format(createPatchDict)
            ).strip().lower() == 'y' else False

    if not createPatchDict_is_written:
        createPatchDict_bak = createPatchDict + '_bak'
        if os.path.isfile(createPatchDict):
            os.rename(createPatchDict, createPatchDict_bak)
        patches = ' '.join(listFile.patchList())
        with open(createPatchDict, 'w') as f:
            f.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tdictionary;\n')
            f.write('\tlocation\t"system";\n')
            f.write('\tobject\tcreatePatchDict;\n')
            f.write('}\n')
            f.write('\npointSync\tfalse;\n\n')
            f.write('patches\n(\n')
            f.write('// まとめた後のパッチ名(A)，パッチの種類(B)，まとめたいパッチの名前(C)を書き換える．\n')
            f.write('// まとめた後のパッチが複数になる場合，\n')
            f.write('// {\n')
            f.write('//     ...\n')
            f.write('// }\n')
            f.write('// の部分をコピーして使えば良い．\n')
            f.write('\t{\n')
            f.write('\t\tname\tassembledPatch1 /* <- (A) まとめた後のパッチ名 */;\n')
            f.write('\t\tpatchInfo\n')
            f.write('\t\t{\n')
            f.write('\t\t\ttype\twall /* <- (B) まとめた後のパッチの種類 */;\n')
            f.write('\t\t}\n')
            f.write('\t\tconstructFrom\tpatches;\n')
            f.write('\t\tpatches\t(' + patches + ') /* <- (C) まとめたいパッチの名前だけを残す */;\n')
            f.write('\t}\n')
            f.write(');\n')
        print('\n\033[3;4;5m{}ファイルをtexteditwx.pyで開いています．'.format(createPatchDict))
        print('- 指示を読んで，必要に応じて書き換えて下さい．')
        print('- 書き換えたらtexteditwx.pyを終了して下さい．\033[m\n')
        subprocess.call(os.path.join(path_binDEXCS, 'texteditwx.py') + ' {}'.format(createPatchDict), shell = True)

    command = 'createPatch -overwrite'
    if subprocess.call(command, shell = True) != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)

    rmObjects.removeInessentials()
