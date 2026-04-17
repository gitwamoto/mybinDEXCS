#!/usr/bin/env python
# -*- coding: utf-8 -*-
# メッシュを細かく.py
# by Yukiharu Iwamoto
# 2026/4/15 9:08:09 PM

# ---- オプション ----
# -p -> paraFoamを実行する
# -s -> constant/polyMesh/boundaryに // converted millimeter into meter と書かれていない時にメッシュの長さを1/1000倍する
# -xr x_max x_min -> 細かくする範囲のx方向の最大，最小値をx_max, x_minにする
# -yr y_max y_min -> 細かくする範囲のy方向の最大，最小値をy_max, y_minにする
# -zr z_max z_min -> 細かくする範囲のz方向の最大，最小値をz_max, z_minにする
# -xf -> x方向に細かくする
# -yf -> y方向に細かくする
# -zf -> z方向に細かくする

import signal
import subprocess
import os
import sys
import re
import shutil
from utilities import misc
from utilities import rmObjects

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = exec_paraFoam = scaleMesh_0p001 = x_fine = y_fine = z_fine = False
        x_max = x_min = y_max = y_min = z_max = z_min = None
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-xr':
                try:
                    i += 1
                    x_max = float(sys.argv[i])
                    i += 1
                    x_min = float(sys.argv[i])
                except:
                    print('エラー: -xrで指定されたx_maxまたはx_minが数値ではありません．')
                    sys.exit(1)
            elif sys.argv[i] == '-yr':
                try:
                    i += 1
                    y_max = float(sys.argv[i])
                    i += 1
                    y_min = float(sys.argv[i])
                except:
                    print('エラー: -yrで指定されたy_maxまたはy_minがが数値ではありません．')
                    sys.exit(1)
            elif sys.argv[i] == '-zr':
                try:
                    i += 1
                    z_max = float(sys.argv[i])
                    i += 1
                    z_min = float(sys.argv[i])
                except:
                    print('エラー: -zrで指定されたz_maxまたはz_minがが数値ではありません．')
                    sys.exit(1)
            elif sys.argv[i] == '-xf':
                x_fine = True
            elif sys.argv[i] == '-yf':
                y_fine = True
            elif sys.argv[i] == '-zf':
                z_fine = True
            i += 1
        if x_max is None or x_min is None or y_max is None or y_min is None or z_max is None or z_min:
            print('エラー: 細かくする範囲が指定されていません．')
            sys.exit(1)

    boundary_path = os.path.join('constant', 'polyMesh', 'boundary')
    if not os.path.isfile(boundary_path):
        print(f'エラー: ファイル {boundary_path} がありません．')
        sys.exit(1)
    converted_millimeter_into_meter = misc.isConvertedMillimeterIntoMeter()

    box = misc.bounding_box_of_calculation_range(os.path.join('constant', 'polyMesh', 'points'))[1]
    if interactive:
        print('細かくする範囲を指定します．')
        while True:
            try:
                x_min, x_max = sorted([float(i) for i in
                    input('x方向の最大，最小値x_max x_minをスペース区切りで入力して下さい．'
                        f' ({box[0][0]} <= x_max, x_min <= {box[0][1]}) > ').replace(',', ' ').split()])
            except ValueError:
                pass
        while True:
            try:
                y_min, y_max = sorted([float(i) for i in
                    input('y方向の最大，最小値y_max y_minをスペース区切りで入力して下さい．'
                        f' ({box[1][0]} <= y_max, y_min <= {box[1][1]}) > ').replace(',', ' ').split()])
            except ValueError:
                pass
        while True:
            try:
                z_min, z_max = sorted([float(i) for i in
                    input('z方向の最大，最小値z_max z_minをスペース区切りで入力して下さい．'
                        f' ({box[2][0]} <= z_max, z_min <= {box[2][1]}) > ').replace(',', ' ').split()])
            except ValueError:
                pass

    topoSetDict_path = os.path.join('system', 'topoSetDict')
    topoSetDict_bak_path = topoSetDict_path + '_bak'
    if os.path.isfile(topoSetDict_path):
        os.rename(topoSetDict_path, topoSetDict_bak_path)
    with open(topoSetDict_path, 'w') as f:
        f.write('FoamFile\n'
            '{\n'
            '\tversion\t2.0;\n'
            '\tformat\tascii;\n'
            '\tclass\tdictionary;\n'
            '\tlocation\t"system";\n'
            '\tobject\ttopoSetDict;\n'
            '}\n'
            'actions\n'
            '(\n'
            '\t{\n'
            '\t\tname\tc0;\n'
            '\t\ttype\tcellSet;\n'
            '\t\taction\tnew;\n'
            '\t\tsource\tboxToCell;\n'
            '\t\tsourceInfo\n'
            '\t\t{\n'
            f'\t\t\tbox\t({x_min} {y_min} {z_min}) ({x_max} {y_max} {z_max});\n'
            '\t\t}\n'
            '\t}\n'
            ');\n')
    command = 'topoSet'
    r = subprocess.call(command, shell = True)
    os.remove(topoSetDict_path)
    if os.path.isfile(topoSetDict_bak_path):
        os.rename(topoSetDict_bak_path, topoSetDict_path)
    if r != 0:
        print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
        sys.exit(1)

    if interactive:
        x_fine = True if input('x方向に細かくしますか ？ (y/n) > ').strip().lower() == 'y' else False
        y_fine = True if input('y方向に細かくしますか ？ (y/n) > ').strip().lower() == 'y' else False
        z_fine = True if input('z方向に細かくしますか ？ (y/n) > ').strip().lower() == 'y' else False

    refineMeshDict_path = os.path.join('system', 'refineMeshDict')
    refineMeshDict_bak_path = refineMeshDict_path + '_bak'
    if os.path.isfile(refineMeshDict_path):
        os.rename(refineMeshDict_path, refineMeshDict_bak_path)
    with open(refineMeshDict_path, 'w') as f:
        f.write('FoamFile\n'
            '{\n'
            '\tversion\t2.0;\n'
            '\tformat\tascii;\n'
            '\tclass\tdictionary;\n'
            '\tlocation\t"system";\n'
            '\tobject\trefineMeshDict;\n'
            '}\n'
            'set\tc0;\n'
            'coordinateSystem\tglobal;\n'
            'globalCoeffs\n'
            '{\n'
            '\ttan1\t(1 0 0);\n'
            '\ttan2\t(0 1 0);\n'
            '}\n'
            'directions\t(')
        if x_fine:
            f.write(' tan1')
        if y_fine:
            f.write(' tan2')
        if z_fine:
            f.write(' normal')
        f.write(' );\n'
            'useHexTopology\tno;\n'
            'geometricCut\tyes;\n'
            'writeMesh\tno;\n')
    command = 'refineMesh -overwrite'
    r = subprocess.call(command, shell = True)
    os.remove(refineMeshDict_path)
    if os.path.isfile(refineMeshDict_bak_path):
        os.rename(refineMeshDict_bak_path, refineMeshDict_path)
    if r != 0:
        print(f'{command}で失敗しました．よく分かる人に相談して下さい．')
        sys.exit(1)

    if converted_millimeter_into_meter:
        misc.writeConvertedMillimeterIntoMeter()
    else:
        if interactive:
            print(f'元のメッシュの範囲は{box[0][0]} <= x <= {box[0][1]},'
                f' {box[1][0]} <= y <= {box[1][1]}, {box[2][0]} <= z <= {box[2][1]}です．')
            scaleMesh_0p001 = True if input('この長さの単位はミリメートルですか？'
                ' (y/n, yだと1/1000倍してメートルに直します．) > ').strip().lower() == 'y' else False
        if scaleMesh_0p001:
            misc.convertMillimeterIntoMeter()
    misc.removePatchesHavingNoFaces() # フェイスを1つも含まないパッチを取り除く
    misc.execCheckMesh()

    if interactive:
        exec_paraFoam = True if input('\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam, ambient = 0.0, diffuse = 1.0)

    rmObjects.removeInessentials()
