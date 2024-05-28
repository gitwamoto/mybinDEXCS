#!/usr/bin/env python
# -*- coding: utf-8 -*-
# メッシュを細かく.py
# by Yukiharu Iwamoto
# 2024/5/28 12:01:52 PM

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
                    print('-xrで指定されたx_maxまたはx_minが数値ではありません．')
                    sys.exit(1)
            elif sys.argv[i] == '-yr':
                try:
                    i += 1
                    y_max = float(sys.argv[i])
                    i += 1
                    y_min = float(sys.argv[i])
                except:
                    print('-yrで指定されたy_maxまたはy_minがが数値ではありません．')
                    sys.exit(1)
            elif sys.argv[i] == '-zr':
                try:
                    i += 1
                    z_max = float(sys.argv[i])
                    i += 1
                    z_min = float(sys.argv[i])
                except:
                    print('-zrで指定されたz_maxまたはz_minがが数値ではありません．')
                    sys.exit(1)
            elif sys.argv[i] == '-xf':
                x_fine = True
            elif sys.argv[i] == '-yf':
                y_fine = True
            elif sys.argv[i] == '-zf':
                z_fine = True
            i += 1
        if x_max is None or x_min is None or y_max is None or y_min is None or z_max is None or z_min:
            print('細かくする範囲が指定されていません．')
            sys.exit(1)

    boundary = os.path.join('constant', 'polyMesh', 'boundary')
    if not os.path.isfile(boundary):
        print('エラー: %sファイルがありません．' % boundary)
        sys.exit(1)
    converted_millimeter_into_meter = misc.isConvertedMillimeterIntoMeter()

    box = misc.bounding_box_of_calculation_range(os.path.join('constant', 'polyMesh', 'points'))[1]
    if interactive:
        print('細かくする範囲を指定します．')
        while True:
            try:
                r = re.sub(r'[\s,]+', ' ',
                    (raw_input if sys.version_info.major <= 2 else input)(
                    'x方向の最大，最小値x_max x_minをスペース区切りで入力して下さい．' +
                    ' (%g <= x_max, x_min <= %g) > ', box[0]).strip()).split()
                x_max = float(r[0])
                x_min = float(r[1])
            except ValueError:
                pass
        while True:
            try:
                r = re.sub(r'[\s,]+', ' ',
                    (raw_input if sys.version_info.major <= 2 else input)(
                    'y方向の最大，最小値y_max y_minをスペース区切りで入力して下さい．' +
                    ' (%g <= y_max, y_min <= %g) > ', box[1]).strip()).split()
                y_max = float(r[0])
                y_min = float(r[1])
            except ValueError:
                pass
        while True:
            try:
                r = re.sub(r'[\s,]+', ' ',
                    (raw_input if sys.version_info.major <= 2 else input)(
                    'z方向の最大，最小値z_max z_minをスペース区切りで入力して下さい．' +
                    ' (%g <= z_max, z_min <= %g) > ', box[2]).strip()).split()
                z_max = float(r[0])
                z_min = float(r[1])
            except ValueError:
                pass
    if x_max < x_min:
        x_max, x_min = x_min, x_max
    if y_max < y_min:
        y_max, y_min = y_min, y_max
    if z_max < z_min:
        z_max, z_min = z_min, z_max

    topoSetDict = os.path.join('system', 'topoSetDict')
    topoSetDict_bak = topoSetDict + '_bak'
    if os.path.isfile(topoSetDict):
        os.rename(topoSetDict, topoSetDict_bak)
    with open(topoSetDict, 'w') as f:
        f.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tdictionary;\n')
        f.write('\tlocation\t"system";\n')
        f.write('\tobject\ttopoSetDict;\n')
        f.write('}\n')
        f.write('actions\n')
        f.write('(\n')
        f.write('\t{\n')
        f.write('\t\tname\tc0;\n')
        f.write('\t\ttype\tcellSet;\n')
        f.write('\t\taction\tnew;\n')
        f.write('\t\tsource\tboxToCell;\n')
        f.write('\t\tsourceInfo\n')
        f.write('\t\t{\n')
        f.write('\t\t\tbox\t(%g %g %g) (%g %g %g);\n' % (x_min, y_min, z_min, x_max, y_max, z_max))
        f.write('\t\t}\n')
        f.write('\t}\n')
        f.write(');\n')
    command = 'topoSet'
    r = subprocess.call(command, shell = True)
    os.remove(topoSetDict)
    if os.path.isfile(topoSetDict_bak):
        os.rename(topoSetDict_bak, topoSetDict)
    if r != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)

    if interactive:
        x_fine = True if (raw_input if sys.version_info.major <= 2 else input)(
            'x方向に細かくしますか ？ (y/n) > ').strip().lower() == 'y' else False
        y_fine = True if (raw_input if sys.version_info.major <= 2 else input)(
            'y方向に細かくしますか ？ (y/n) > ').strip().lower() == 'y' else False
        z_fine = True if (raw_input if sys.version_info.major <= 2 else input)(
            'z方向に細かくしますか ？ (y/n) > ').strip().lower() == 'y' else False

    refineMeshDict = os.path.join('system', 'refineMeshDict')
    refineMeshDict_bak = refineMeshDict + '_bak'
    if os.path.isfile(refineMeshDict):
        os.rename(refineMeshDict, refineMeshDict_bak)
    with open(refineMeshDict, 'w') as f:
        f.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tdictionary;\n')
        f.write('\tlocation\t"system";\n')
        f.write('\tobject\trefineMeshDict;\n')
        f.write('}\n')
        f.write('set\tc0;\n')
        f.write('coordinateSystem\tglobal;\n')
        f.write('globalCoeffs\n')
        f.write('{\n')
        f.write('\ttan1\t(1 0 0);\n')
        f.write('\ttan2\t(0 1 0);\n')
        f.write('}\n')
        f.write('directions\t(')
        if x_fine:
            f.write(' tan1')
        if y_fine:
            f.write(' tan2')
        if z_fine:
            f.write(' normal')
        f.write(' );\n')
        f.write('useHexTopology\tno;\n')
        f.write('geometricCut\tyes;\n')
        f.write('writeMesh\tno;\n')
    command = 'refineMesh -overwrite'
    r = subprocess.call(command, shell = True)
    os.remove(refineMeshDict)
    if os.path.isfile(refineMeshDict_bak):
        os.rename(refineMeshDict_bak, refineMeshDict)
    if r != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)

    if converted_millimeter_into_meter:
        misc.writeConvertedMillimeterIntoMeter()
    else:
        if interactive:
            print('元のメッシュの範囲は%g <= x <= %g, %g <= y <= %g, %g <= z <= %gです．' %
                (box[0][0], box[0][1], box[1][0], box[1][1], box[2][0], box[2][1]))
            scaleMesh_0p001 = True if (raw_input if sys.version_info.major <= 2 else input)(
                'この長さの単位はミリメートルですか？ (y/n, yだと1/1000倍してメートルに直します．) > '
                ).strip().lower() == 'y' else False
        if scaleMesh_0p001:
            misc.convertLengthUnitInMillimeterToMeter()
    misc.removePatchesHavingNoFaces() # フェイスを1つも含まないパッチを取り除く
    misc.execCheckMesh()

    if interactive:
        exec_paraFoam = True if (raw_input if sys.version_info.major <= 2 else input)(
            '\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam)

    rmObjects.removeInessentials()
