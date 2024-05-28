#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 2次元メッシュに.py
# by Yukiharu Iwamoto
# 2024/5/28 12:29:20 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行
# -b back_name -> 後側patchの名前をback_nameにする．このオプションがない場合はbackと言う名前になる
# -f front_name -> 前側patchの名前をfront_nameにする．このオプションがない場合はfrontと言う名前になる
# -p -> paraFoamを実行する
# -s -> constant/polyMesh/boundaryに // converted millimeter into meter と書かれていない時にメッシュの長さを1/1000倍する
# -w -> wedge境界にする

import os
import sys
import signal
import subprocess
import shutil
from utilities import misc
from utilities import listFile
from utilities.dictParse import DictParser, DictParserList
from utilities import rmObjects

def makeExtrudeMeshDict(z_thickness, front_name, back_name, wedge):
    with open(os.path.join('system', 'extrudeMeshDict'), 'w') as f:
        f.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tdictionary;\n')
        f.write('\tlocation\t"system";\n')
        f.write('\tobject\textrudeMeshDict;\n')
        f.write('}\n')
        f.write('constructFrom\tpatch;\n')
        f.write('sourceCase\t".";\n')
        f.write('sourcePatches\t({});\n'.format(front_name))
        f.write('exposedPatchName\t{};\n'.format(back_name))
        f.write('flipNormals\tfalse;\n')
        if wedge: # wedge境界
            f.write('extrudeModel\twedge;\n')
            f.write('nLayers\t1;\n')
            f.write('expansionRatio\t1.0;\n')
            f.write('sectorCoeffs\n')
            f.write('{\n')
            f.write('\taxisPt\t(0 0 0);\n')
            f.write('\taxis\t(1 0 0);\n')
            f.write('\tangle\t2;\t// [degrees]\n')
            f.write('}\n')
            f.write('mergeFaces\tfalse;\n')
            f.write('mergeTol\t1.0e-10;\n')
            print('wedgeのくさび角は2度に設定しています．')
        else: # empty境界
            f.write('extrudeModel\tlinearNormal;\n')
            f.write('nLayers\t1;\n')
            f.write('expansionRatio\t1.0;\n')
            f.write('linearNormalCoeffs\n')
            f.write('{\n')
            f.write('\tthickness\t{};\n'.format(z_thickness))
            f.write('}\n')
            f.write('mergeFaces\tfalse;\n')
            f.write('mergeTol\t0;\n')

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = exec_paraFoam = scaleMesh_0p001 = wedge = False
        front_name = 'front'
        back_name = 'back'
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-N': # Non-interactive
                pass
            elif sys.argv[i] == '-b':
                i += 1
                back_name = sys.argv[i]
            elif sys.argv[i] == '-f':
                i += 1
                front_name = sys.argv[i]
            elif sys.argv[i] == '-p':
                exec_paraFoam = True
            elif sys.argv[i] == '-s':
                scaleMesh_0p001 = True
            elif sys.argv[i] == '-w':
                wedge = True
            i += 1

    boundary = os.path.join('constant', 'polyMesh', 'boundary')
    if not os.path.isfile(boundary):
        print('エラー: {}ファイルがありません．'.format(boundary))
        sys.exit(1)
    if os.path.isdir('dynamicCode'):
        shutil.rmtree('dynamicCode')
    converted_millimeter_into_meter = misc.isConvertedMillimeterIntoMeter()

    print('xy平面に平行なpatchを押し出して2次元メッシュまたはwedge境界を作ります．')

    bouding_box = misc.bounding_box_of_calculation_range(os.path.join('constant', 'polyMesh', 'points'))[1]
    z_back, z_front = bouding_box[2]

    if interactive:
        plist = listFile.patchList()
        patches = ' '.join(plist)
        sys.stdout.write('2次元メッシュに使う(z = {}にある)patchの名前を教えて下さい． ( {} の中から選択'.format(z_front, patches))
        if 'front' in plist:
            front_name = (raw_input if sys.version_info.major <= 2 else input)(', Enterのみ: front) > ').strip()
            if front_name == '':
                front_name = 'front'
        else:
            front_name = (raw_input if sys.version_info.major <= 2 else input)(') > ').strip()
        sys.stdout.write('押し出したpatchの裏側にあるpatchの名前を決めて下さい． ( {} の中から選択'.format(patches))
        if 'back' in plist:
            back_name = (raw_input if sys.version_info.major <= 2 else input)(', Enterのみ: back) > ').strip()
            if back_name == '':
                back_name = 'back'
        else:
            back_name = (raw_input if sys.version_info.major <= 2 else input)(') > ').strip()
        wedge = True if (raw_input if sys.version_info.major <= 2 else input)(
            'wedge (くさび) 境界にしますか？ (y/n, 多くの場合nのはず) > ').strip().lower() == 'y' else False
        if not converted_millimeter_into_meter:
            print('元のメッシュの範囲は{} <= x <= {}, {} <= y <= {}, {} <= z <= {}です．'.format(
                bouding_box[0][0], bouding_box[0][1], bouding_box[1][0], bouding_box[1][1],
                bouding_box[2][0], bouding_box[2][1]))
            scaleMesh_0p001 = True if (raw_input if sys.version_info.major <= 2 else input)(
                'この長さの単位はミリメートルですか？ (y/n, yだと1/1000倍してメートルに直します．) > '
                ).strip().lower() == 'y' else False

    if not os.path.isdir('system'):
        os.mkdir('system')
    makeExtrudeMeshDict(z_front - z_back, front_name, back_name, wedge)

    command = "transformPoints -translate '(0 0 {})'".format(-z_front)
    if subprocess.call(command, shell = True) != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)

    command = 'extrudeMesh'
    if subprocess.call(command, shell = True) != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)

    if converted_millimeter_into_meter:
        misc.writeConvertedMillimeterIntoMeter()
    elif scaleMesh_0p001:
        misc.convertLengthUnitInMillimeterToMeter()

    misc.removePatchesHavingNoFaces() # フェイスを1つも含まないパッチを取り除く
    misc.execCheckMesh()
    sets = os.path.join('constant', 'polyMesh', 'sets')
    if os.path.isdir(sets):
        shutil.rmtree(sets)

    if interactive:
        exec_paraFoam = True if (raw_input if sys.version_info.major <= 2 else input)(
            '\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam)

    rmObjects.removeInessentials()
