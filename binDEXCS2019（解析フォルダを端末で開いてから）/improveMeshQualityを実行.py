#!/usr/bin/env python
# -*- coding: utf-8 -*-
# improveMeshQualityを実行.py
# by Yukiharu Iwamoto
# 2024/5/28 12:01:31 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行
# -p -> paraFoamを実行する
# -s -> constant/polyMesh/boundaryに // converted millimeter into meter と書かれていない時にメッシュの長さを1/1000倍する

import os
import sys
import shutil
import signal
import subprocess
import numpy as np
from struct import pack
from utilities import misc
from utilities.dictParse import DictParser, DictParserList
from utilities import rmObjects

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = exec_paraFoam = scaleMesh_0p001 = False
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-N': # Non-interactive
                pass
            elif sys.argv[i] == '-a':
                i += 1
                patch_name = sys.argv[i]
            elif sys.argv[i] == '-p':
                exec_paraFoam = True
            elif sys.argv[i] == '-s':
                scaleMesh_0p001 = True
            i += 1

    boundary = os.path.join('constant', 'polyMesh', 'boundary')
    faces = os.path.join('constant', 'polyMesh', 'faces')
    for i in (boundary, faces):
        if not os.path.isfile(i):
            print('エラー: {}ファイルがありません．'.format(i))
            sys.exit(1)
    if os.path.isdir('dynamicCode'):
        shutil.rmtree('dynamicCode')
    converted_millimeter_into_meter = misc.isConvertedMillimeterIntoMeter()

    with open(faces, 'r') as f:
        s = f.read()
    if 'faceCompactList' in s:
        pl = s.find('(') + 1
        ph = s[:pl - 2].rfind('\n') + 1
        pf = s.rfind(')')
        n = int(s[ph:pl - 1])
        pr = pl + 4*n
        faces_ranges = np.fromstring(s[pl:pr], dtype = '<u4')
        pl = pr + s[pr:].find(')') + 1
        pr = pl + s[pl:].find('(')
        n = int(s[pl:pr])
        pl = pr + 1
        pr = pl + 4*n
        points_indices = np.fromstring(s[pl:pr], dtype = '<u4')
        faces_data = []
        for i in range(faces_ranges.shape[0] - 1):
            faces_data.append(points_indices[faces_ranges[i]:faces_ranges[i + 1]])
        os.rename(faces, faces + '_bak')
        with open(faces, 'w') as f:
            f.write(s[:ph].replace('faceCompactList', 'faceList'))
            f.write('{}\n(\n'.format(len(faces_data)))
            for i in faces_data:
#                f.write('\n{}\n('.format(i.shape[0]))
                f.write('{}('.format(i.shape[0]))
                for j in i:
                    f.write(pack('<d', j))
                f.write(')\n')
            f.write(s[pf:])

    command = 'improveMeshQuality -noFunctionObjects'
    if subprocess.call(command, shell = True) != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)

    if converted_millimeter_into_meter:
        misc.writeConvertedMillimeterIntoMeter()
    else:
        if interactive:
            box = misc.bounding_box_of_calculation_range(os.path.join('constant', 'polyMesh', 'points'))[1]
            print('元のメッシュの範囲は{} <= x <= {}, {} <= y <= {}, {} <= z <= {}です．'.format(
                box[0][0], box[0][1], box[1][0], box[1][1], box[2][0], box[2][1]))
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
