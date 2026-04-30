#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 2次元メッシュに.py
# by Yukiharu Iwamoto
# 2026/4/30 5:32:50 PM

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
from utilities import rmObjects
from utilities import dictParse

def makeExtrudeMeshDict(z_thickness, front_name, back_name, wedge):
    with open(os.path.join('system', 'extrudeMeshDict'), 'w') as f:
        f.write('FoamFile\n'
            '{\n'
            '\tversion\t2.0;\n'
            '\tformat\tascii;\n'
            '\tclass\tdictionary;\n'
            '\tlocation\t"system";\n'
            '\tobject\textrudeMeshDict;\n'
            '}\n'
            'constructFrom\tpatch;\n'
            'sourceCase\t".";\n'
            f'sourcePatches\t({front_name});\n'
            f'exposedPatchName\t{back_name};\n'
            'flipNormals\tfalse;\n')
        if wedge: # wedge境界
            f.write('extrudeModel\twedge;\n'
                'nLayers\t1;\n'
                'expansionRatio\t1.0;\n'
                'sectorCoeffs\n'
                '{\n'
                '\taxisPt\t(0 0 0);\n'
                '\taxis\t(1 0 0);\n'
                '\tangle\t2;\t// [degrees]\n'
                '}\n'
                'mergeFaces\tfalse;\n'
                'mergeTol\t1.0e-10;\n')
            print('wedgeのくさび角は2度に設定しています．')
        else: # empty境界
            f.write('extrudeModel\tlinearNormal;\n'
                'nLayers\t1;\n'
                'expansionRatio\t1.0;\n'
                'linearNormalCoeffs\n'
                '{\n'
                '\tthickness\t{z_thickness};\n'
                '}\n'
                'mergeFaces\tfalse;\n'
                'mergeTol\t0;\n')

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
        print(f'エラー: ファイル{boundary}がありません．')
        sys.exit(1)
    if os.path.isdir('dynamicCode'):
        shutil.rmtree('dynamicCode')
    converted_millimeter_into_meter = misc.isConvertedMillimeterIntoMeter()

    print('xy平面に平行なpatchを押し出して2次元メッシュまたはwedge境界を作ります．')

    bouding_box = misc.bounding_box_of_calculation_range(os.path.join('constant', 'polyMesh', 'points'))[1]
    z_back, z_front = bouding_box[2]

    if interactive:
        patches = [i['element']['key'] for i in dictParse.DictParser2(file_name =
            os.path.join('constant', 'polyMesh', 'boundary')).find_all_elements(
                [{'type': 'list'}, {'type': 'block'}])]
        space_delimited_patches = ' '.join(patches)
        sys.stdout.write(f'2次元メッシュに使う(z = {z_front}にある)patchの名前を教えて下さい．'
            f' ( {space_delimited_patches} の中から選択')
        if 'front' in patches:
            front_name = input(', Enterのみ: front) > ').strip() or 'front'
        else:
            front_name = input(') > ').strip()
        sys.stdout.write('押し出したpatchの裏側にあるpatchの名前を決めて下さい．'
            f' ( {space_delimited_patches} の中から選択')
        if 'back' in patches:
            back_name = input(', Enterのみ: back) > ').strip() or 'back'
        else:
            back_name = input(') > ').strip()
        wedge = True if input('wedge (くさび) 境界にしますか？ '
            '(y/n, 多くの場合nのはず) > ').strip().lower() == 'y' else False
        if not converted_millimeter_into_meter:
            print(f'元のメッシュの範囲は{bouding_box[0][0]} <= x <= {bouding_box[0][1]},'
                f' {bouding_box[1][0]} <= y <= {bouding_box[1][1]},'
                f' {bouding_box[2][0]} <= z <= {bouding_box[2][1]}です．')
            scaleMesh_0p001 = True if input('この長さの単位はミリメートルですか？'
                ' (y/n, yだと0.001倍してメートルに直します．) > ').strip().lower() == 'y' else False

    if not os.path.isdir('system'):
        os.mkdir('system')
    makeExtrudeMeshDict(z_front - z_back, front_name, back_name, wedge)

    command = f"transformPoints -translate '(0 0 {-z_front})'"
    if subprocess.call(command, shell = True) != 0:
        print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
        sys.exit(1)

    command = 'extrudeMesh'
    if subprocess.call(command, shell = True) != 0:
        print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
        sys.exit(1)

    if converted_millimeter_into_meter:
        misc.writeConvertedMillimeterIntoMeter()
    elif scaleMesh_0p001:
        misc.convertMillimeterIntoMeter()

    misc.removePatchesHavingNoFaces() # フェイスを1つも含まないパッチを取り除く
    misc.execCheckMesh()
    sets = os.path.join('constant', 'polyMesh', 'sets')
    if os.path.isdir(sets):
        shutil.rmtree(sets)

    if interactive:
        exec_paraFoam = True if input('\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam, ambient = 0.0, diffuse = 1.0)

    rmObjects.removeInessentials()
