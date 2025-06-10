#!/usr/bin/env python
# -*- coding: utf-8 -*-
# cartesianMeshを実行.py
# by Yukiharu Iwamoto
# 2025/6/10 11:25:32 AM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行
# -2 cartesian2DMeshで2次元メッシュを作る．emptyのpatchはx-y平面に平行でなければならない
# -b back_name -> 【-2オプションがある時のみ有効】(zが大きい)後側patchの名前をback_nameにする．
#                 このオプションがない場合，backという名前になる．
# -f front_name -> 【-2オプションがある時のみ有効】(zが大きい)前側patchの名前をfront_nameにする．
#                  このオプションがない場合，frontという名前になる．
# -p -> paraFoamを実行する
# -r domains -> 計算領域をdomains個に分割して並列計算を行う，1だと普通の計算

import os
import sys
import signal
import subprocess
import shutil
from utilities import misc
from utilities.dictParse import DictParser, DictParserList
from utilities import rmObjects

two_dimensional = False
meshDict = os.path.join('system', 'meshDict')
meshDict_3D = meshDict + '_3D'

def handler(signal, frame):
    if two_dimensional and os.path.isfile(meshDict_3D):
        os.rename(meshDict_3D, meshDict) # can overwrite
    rmObjects.removeInessentials()
    sys.exit(1)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler) # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = exec_paraFoam = False
        front_name, back_name = 'front', 'back'
        domains = 1
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-N': # Non-interactive
                pass
            elif sys.argv[i] == '-2':
                two_dimensional = True
            elif sys.argv[i] == '-b':
                i += 1
                back_name = sys.argv[i]
            elif sys.argv[i] == '-f':
                i += 1
                front_name = sys.argv[i]
            elif sys.argv[i] == '-p':
                exec_paraFoam = True
            elif sys.argv[i] == '-r':
                i += 1
                domains = max(int(sys.argv[i]), 1)
            i += 1

    if not os.path.isfile(meshDict):
        print('エラー: {}ファイルがありません．'.format(meshDict))
        sys.exit(1)
    if os.path.isdir('dynamicCode'):
        shutil.rmtree('dynamicCode')
    rmObjects.removeProcessorDirs()
    for f in ('cartesianMesh.log', 'cartesianMesh.logfile', 'cartesian2DMesh.log', 'cartesian2DMesh.logfile'):
        if os.path.isfile(f):
            os.remove(f)

    threads = misc.cpu_count()
    if interactive:
        while True:
            try:
                domains = max(int((raw_input if sys.version_info.major <= 2 else input)(
                    '計算領域を何個に分割して並列計算しますか？ ({}個まで, 1だと普通の計算) > '.format(threads)).strip()), 1)
                break
            except ValueError:
                pass
        two_dimensional = True if (raw_input if sys.version_info.major <= 2 else input)(
            '\ncartesian2DMeshで2次元メッシュを作りますか？\n' +
            '*** 2次元メッシュでは，empty境界はx-y平面に平行でなければならなりません． (y/n) > '
            ).strip().lower() == 'y' else False
    domains = min(domains, threads)

    if two_dimensional:
        dp_meshDict = DictParser(meshDict)
        empty_list = []
        for x in dp_meshDict.getValueForKey(['renameBoundary', 'newPatchNames']):
            if DictParserList.isType(x, DictParserList.BLOCK):
                bname = tname = None
                for y in x.value():
                    if DictParserList.isType(y, DictParserList.DICT):
                        if y.key() == 'newName':
                            bname = y.value()[0]
                        elif y.key() == 'type':
                            tname = y.value()[0]
                        if bname is not None and tname is not None and tname == 'empty':
                            empty_list.append(bname)
                            break
        x = dp_meshDict.getItemAtIndex(dp_meshDict.getIndexOfItem(['surfaceFile'])[:-1])
        stl_file_name_wo_ext = os.path.splitext(x.value()[0].strip('"'))[0]
        stl_2D_file_name = stl_file_name_wo_ext + '_2D.stl'
        should_write = True
        with open(stl_2D_file_name, 'w') as f2d:
            with open(stl_file_name_wo_ext + '.stl', 'r') as f:
                for line in f:
                    if 'endsolid' in line and line.split()[-1] in empty_list:
                        should_write = True
                    elif 'solid' in line and line.split()[-1] in empty_list:
                        should_write = False
                    elif should_write:
                        f2d.write(line)
        x.setValue(['"' + os.path.basename(stl_2D_file_name) + '"'])
        os.rename(meshDict, meshDict_3D) # can overwrite
        dp_meshDict.writeFile(meshDict)

    cfMesh = 'cartesian2DMesh' if two_dimensional else 'cartesianMesh'
    if domains != 1:
        rmObjects.removeProcessorDirs()
        decomposeParDict = os.path.join('system', 'decomposeParDict')
        decomposeParDict_bak = decomposeParDict + '_bak'
        if os.path.isfile(decomposeParDict):
            os.rename(decomposeParDict, decomposeParDict_bak)
        with open(decomposeParDict, 'w') as f:
            f.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tdictionary;\n')
            f.write('\tlocation\t"system";\n')
            f.write('\tobject\tdecomposeParDict;\n')
            f.write('}\n')
            f.write('numberOfSubdomains\t{};\n'.format(domains))
            f.write('method\tscotch;\n')
            f.write('scotchCoeffs\n')
            f.write('{\n\tprocessorWeights\t(1' + ' 1'*(domains - 1) + ');\n}\n')
            f.write('distributed\tno;\n')
            f.write('roots\t();\n')
        command = 'preparePar -noFunctionObjects'
        r = subprocess.call(command, shell = True)
        if r == 0:
            command = 'mpirun -np {} {} -parallel -noFunctionObjects | tee {}.log'.format(domains, cfMesh, cfMesh)
            r = subprocess.call(command, shell = True)
        if r == 0:
            command = 'reconstructParMesh -constant -mergeTol 1.0e-06 -noFunctionObjects'
            r = subprocess.call(command, shell = True)
        rmObjects.removeProcessorDirs()
        if os.path.isfile(decomposeParDict_bak):
            os.rename(decomposeParDict_bak, decomposeParDict)
        if r != 0:
            print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
            sys.exit(1)
    else:
        command = '{} -noFunctionObjects | tee {}.log'.format(cfMesh, cfMesh)
        if subprocess.call(command, shell = True) != 0:
            print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
            sys.exit(1)

    boundary = os.path.join('constant', 'polyMesh', 'boundary')
    if two_dimensional:
        os.rename(meshDict, meshDict + '_2D') # can overwrite
        os.rename(meshDict_3D, meshDict) # can overwrite
        if interactive:
            front_name = (raw_input if sys.version_info.major <= 2 else input)(
                '(zが大きい)前側patchの名前を決めて下さい． (Enterのみ: front) > ').strip()
            if front_name == '':
                front_name = 'front'
            back_name = (raw_input if sys.version_info.major <= 2 else input)(
                '(zが小さい)後側patchの名前を決めて下さい． (Enterのみ: back) > ').strip()
            if back_name == '':
                back_name = 'back'
        dp_boundary = DictParser(boundary)
        for a in dp_boundary.contents:
            if DictParserList.isType(a, DictParserList.LISTP):
                a = a.value()
                break
        for b in a:
            if DictParserList.isType(b, DictParserList.BLOCK):
                if b.key() == 'topEmptyFaces':
                    b.setKey(front_name)
                elif b.key() == 'bottomEmptyFaces':
                    b.setKey(back_name)
        dp_boundary.writeFile(boundary)
    else: # not two_dimensional
        dp_boundary = DictParser(boundary)
        s_old = dp_boundary.toString()
        for a in dp_boundary.contents:
            if DictParserList.isType(a, DictParserList.LISTP):
                a = a.value()
                break
        for x in DictParser(meshDict).getValueForKey(['renameBoundary', 'newPatchNames']):
            if DictParserList.isType(x, DictParserList.BLOCK):
                bname = tname = None
                for y in x.value():
                    if DictParserList.isType(y, DictParserList.DICT):
                        if y.key() == 'newName':
                            bname = y.value()[0]
                        elif y.key() == 'type':
                            tname = y.value()[0]
                        if bname is not None and tname is not None:
                            for b in a:
                                if DictParserList.isType(b, DictParserList.BLOCK) and b.key() == bname:
                                    for c in b.value():
                                        if DictParserList.isType(c, DictParserList.DICT):
                                            if c.key() == 'type':
                                                c.setValue([tname])
                                            elif (c.key() == 'inGroups' and
                                                DictParserList.isType(c.value()[0], DictParserList.LISTP)):
                                                c.value()[0].setValue([tname])
                            break
        s = dp_boundary.toString()
        if s != s_old:
            with open(boundary, 'w') as f:
                f.write(s)

    misc.convertLengthUnitInMillimeterToMeter()
    misc.removePatchesHavingNoFaces() # フェイスを1つも含まないパッチを取り除く
    if two_dimensional:
        command = 'flattenMesh'
        if subprocess.call(command, shell = True) != 0:
            print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
            sys.exit(1)
    misc.execCheckMesh()
    sets = os.path.join('constant', 'polyMesh', 'sets')
    if os.path.isdir(sets):
        shutil.rmtree(sets)

    if interactive:
        exec_paraFoam = True if (raw_input if sys.version_info.major <= 2 else input)(
            '\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam, ambient = 0.0, diffuse = 0.1)

    rmObjects.removeInessentials()
