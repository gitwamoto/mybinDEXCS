#!/usr/bin/env python
# -*- coding: utf-8 -*-
# cartesianMeshを実行.py
# by Yukiharu Iwamoto
# 2026/4/30 3:30:46 PM

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

# DictParser2で書き直し済み

import os
import sys
import signal
import subprocess
import shutil
from utilities import misc
from utilities import rmObjects
from utilities import dictParse

two_dimensional = False
meshDict_path = os.path.join('system', 'meshDict')
meshDict_3D_path = meshDict_path + '_3D'

def handler(signum, frame):
    if two_dimensional and os.path.isfile(meshDict_3D_path):
        os.rename(meshDict_3D_path, meshDict_path) # can overwrite
    rmObjects.removeInessentials()
    sys.exit(1)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler) # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = exec_paraFoam = False
        front_name = 'front'
        back_name = 'back'
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

    if not os.path.isfile(meshDict_path):
        print(f'エラー: ファイル{meshDict_path}がありません．')
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
                domains = max(int(input('計算領域を何個に分割して並列計算しますか？ '
                    f'({threads}個まで, 1だと普通の計算) > ').strip()), 1)
                break
            except ValueError:
                pass
        two_dimensional = True if input('\ncartesian2DMeshで2次元メッシュを作りますか？\n'
            '*** 2次元メッシュでは，empty境界がx-y平面に平行でないといけません． (y/n) > '
            ).strip().lower() == 'y' else False
        if two_dimensional:
            front_name = input('(zが大きい)前側patchの名前を決めて下さい． (Enterのみ: front) > ').strip() or 'front'
            back_name = input('(zが小さい)後側patchの名前を決めて下さい． (Enterのみ: back) > ').strip() or 'back'
    domains = min(domains, threads)

    meshDict = dictParse.DictParser2(file_name = meshDict_path)

    # renameBoundary
    # {
    #   newPatchNames
    #   {
    #     PATCH_NAME
    #     {
    #       newName PATCH_NAME;
    #       type empty;
    #     }
    #     ...
    patch_types = {}
    empty_list = []
    for p in meshDict.find_all_elements([{'type': 'block', 'key': 'renameBoundary'},
        {'type': 'block', 'key': 'newPatchNames'}, {'type': 'block'}]):
        n = dictParse.find_element([{'type': 'dictionary', 'key': 'newName'}, {'except type': 'ignorable'}],
            parent = p['element'])['element']['value']
        t = dictParse.find_element([{'type': 'dictionary', 'key': 'newType'}, {'except type': 'ignorable'}],
            parent = p['element'])['element']['value']
        patch_types[n] = t
        if t == 'empty':
            empty_list.append(n)

    if two_dimensional:
        # surfaceFile "constant/triSurface/FMS_NAME.fms"; // (mandatory)
        surfaceFile = meshDict.find_element(
            [{'type': 'dictionary', 'key': 'surfaceFile'}, {'type': 'string'}])['element']
        stl_file_name_wo_ext = os.path.splitext(surfaceFile['value'].strip('"'))[0] # .fmsを取り除く
        stl_2D_file_name = f'{stl_file_name_wo_ext}_2D.stl' # 2次元の場合はfmsファイルでなくても十分であることが多い
        should_write = True
        with open(stl_2D_file_name, 'w') as f:
            for line in open(f'{stl_file_name_wo_ext}.stl', 'r'):
                if 'endsolid' in line and line.split()[-1] in empty_list:
                    should_write = True
                elif 'solid' in line and line.split()[-1] in empty_list:
                    should_write = False
                elif should_write:
                    f.write(line)
        surfaceFile['value'] = f'"{stl_2D_file_name}"'
        os.rename(meshDict_path, meshDict_3D_path) # can overwrite
        with open(meshDict_path, 'w') as f:
            f.write(dictParse.normalize(string = meshDict.file_string(pretty_print = True))[0])

    cfMesh = 'cartesian2DMesh' if two_dimensional else 'cartesianMesh'
    if domains != 1:
        rmObjects.removeProcessorDirs()
        decomposeParDict_path = os.path.join('system', 'decomposeParDict')
        decomposeParDict_bak_path = decomposeParDict_path + '_bak'
        if os.path.isfile(decomposeParDict_path):
            os.rename(decomposeParDict_path, decomposeParDict_bak_path)
        with open(decomposeParDict_path, 'w') as f:
            f.write('FoamFile\n'
                '{\n'
                '\tversion\t2.0;\n'
                '\tformat\tascii;\n'
                '\tclass\tdictionary;\n'
                '\tlocation\t"system";\n'
                '\tobject\tdecomposeParDict;\n'
                '}\n'
                f'numberOfSubdomains\t{domains};\n'
                'method\tscotch;\n') # 複雑な形状や境界条件がある場合に最適．デフォルトで推奨されることが多い．
        command = 'preparePar -noFunctionObjects'
        r = subprocess.call(command, shell = True)
        if r == 0:
            command = f'mpirun -np {domains} {cfMesh} -parallel -noFunctionObjects | tee {cfMesh}.log'
            r = subprocess.call(command, shell = True)
        if r == 0:
            command = 'reconstructParMesh -constant -mergeTol 1.0e-06 -noFunctionObjects'
            r = subprocess.call(command, shell = True)
        rmObjects.removeProcessorDirs()
        if os.path.isfile(decomposeParDict_bak_path):
            os.rename(decomposeParDict_bak_path, decomposeParDict_path)
        if r != 0:
            print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
            sys.exit(1)
    else:
        command = f'{cfMesh} -noFunctionObjects | tee {cfMesh}.log'
        if subprocess.call(command, shell = True) != 0:
            print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
            sys.exit(1)

    boundary_path = os.path.join('constant', 'polyMesh', 'boundary')
    boundary = dictParse.DictParser2(file_name = boundary_path)
    if two_dimensional:
        os.rename(meshDict_path, meshDict_path + '_2D') # can overwrite
        os.rename(meshDict_3D_path, meshDict_path) # can overwrite
        boundary.find_element(
            [{'type': 'list'}, {'type': 'block', 'key': 'topEmptyFaces'}])['element']['key'] = front_name
        boundary.find_element(
            [{'type': 'list'}, {'type': 'block', 'key': 'bottomEmptyFaces'}])['element']['key'] = back_name
        with open(boundary_path, 'w') as f:
            f.write(dictParse.normalize(string = boundary.file_string(pretty_print = True))[0])
    else: # not two_dimensional
        for p in boundary.find_all_elements([{'type': 'list',}, {'type': 'block'}]):
            i = dictParse.find_element([{'type': 'dictionary', 'key': 'type'}, {'except type': 'ignorable'}],
                parent = p['element'])
            t = patch_types[p['element']['key']]
            if i['element']['value'] != t:
                i['element']['value'] = t
                i = dictParse.find_element([{'type': 'dictionary', 'key': 'inGroups'}, {'type': 'list'},
                    {'except type': 'ignorable|list_start'}], parent = p['element'])
                if i['element'] is not None:
                    i['element']['value'] = t
        string = dictParse.normalize(string = boundary.file_string(pretty_print = True))[0]
        if boundary.string != string:
#            os.rename(boundary_path, boundary_path + '_bak')
            with open(boundary_path, 'w') as f:
                f.write(string)

    misc.convertMillimeterIntoMeter()
    misc.removePatchesHavingNoFaces() # フェイスを1つも含まないパッチを取り除く
    if two_dimensional:
        command = 'flattenMesh'
        if subprocess.call(command, shell = True) != 0:
            print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
            sys.exit(1)
    misc.execCheckMesh()
    sets = os.path.join('constant', 'polyMesh', 'sets')
    if os.path.isdir(sets):
        shutil.rmtree(sets)

    if interactive:
        exec_paraFoam = True if input('\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam, ambient = 0.0, diffuse = 1.0)

    rmObjects.removeInessentials()
