#!/usr/bin/env python
# -*- coding: utf-8 -*-
# improveMeshQualityを実行.py
# by Yukiharu Iwamoto
# 2026/5/12 9:48:00 PM

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
from utilities import rmObjects

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = False
        exec_paraFoam = False
        scaleMesh_0p001 = False
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

    faces_path = os.path.join('constant', 'polyMesh', 'faces')
    for i in (os.path.join('constant', 'polyMesh', 'boundary'), faces_path):
        if not os.path.isfile(i):
            print(f'エラー: ファイル{i}がありません．')
            sys.exit(1)
    if os.path.isdir('dynamicCode'):
        shutil.rmtree('dynamicCode')
    converted_millimeter_into_meter = misc.isConvertedMillimeterIntoMeter()

    with open(faces_path, 'r') as f:
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
        os.rename(faces_path, f'{faces_path}_bak')
        with open(faces_path, 'w') as f:
            f.write(s[:ph].replace('faceCompactList', 'faceList'))
            f.write(f'{len(faces_data)}\n(\n')
            for i in faces_data:
                f.write(f'{i.shape[0]}(')
                for j in i:
                    f.write(pack('<d', j))
                f.write(')\n')
            f.write(s[pf:])

    command = 'improveMeshQuality -noFunctionObjects'
    if subprocess.call(command, shell = True) != 0:
        print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
        sys.exit(1)

    if converted_millimeter_into_meter:
        misc.convertMillimeterIntoMeter()
    else:
        if interactive:
            box = misc.bounding_box_of_calculation_range(os.path.join('constant', 'polyMesh', 'points'))[1]
            print(f'元のメッシュの範囲は{box[0][0]} <= x <= {box[0][1]}, {box[1][0]} <= y <= {box[1][1]}, '
                f'{box[2][0]} <= z <= {box[2][1]}です．')
            scaleMesh_0p001 = True if input('この長さの単位はミリメートルですか？ '
                '(y/n, yだと0.001倍してメートルに直します．) > ').strip().lower() == 'y' else False
        if scaleMesh_0p001:
            misc.convertMillimeterIntoMeter()
    misc.removePatchesHavingNoFaces() # フェイスを1つも含まないパッチを取り除く
    misc.execCheckMesh()

    if interactive:
        exec_paraFoam = True if input('\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam, ambient = 0.0, diffuse = 1.0)

    rmObjects.removeInessentials()
