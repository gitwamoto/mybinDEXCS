#!/usr/bin/env python
# -*- coding: utf-8 -*-
# patchを平面に.py
# by Yukiharu Iwamoto
# 2023/4/30 5:16:18 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -n patch_name -> 平面にしたいpatchの名前をpatch_nameにする
# -p -> paraFoamを実行する
# -s -> constant/polyMesh/boundaryに // converted millimeter into meter と書かれていない時にメッシュの長さを1/1000倍する
# -t patch_type -> 平面にしたいpatchのtypeをpatch_typeに変更する．このオプションがなければ変更しない．
# -x value -> 面のx座標をvalueに固定する
# -y value -> 面のy座標をvalueに固定する
# -z value -> 面のz座標をvalueに固定する

import os
import sys
import signal
import numpy as np
import math
from utilities import misc
from utilities import listFile
from utilities.dictParse import DictParser, DictParserList
from utilities import rmObjects

#def inverse_power_method(A, eps = 1.0e-10):
#    # A.r = lambda*r
#    # A^^(-1).r = 1/lambda*r
#    A_inv = np.linalg.inv(A)
#    r = np.ones(A.shape[0])/math.sqrt(A.shape[0])
#    ev_min = float('inf')
#    while True:
#        Ar = np.dot(A_inv, r)
#        r = Ar/np.linalg.norm(Ar)
#        ev_min_old = ev_min
#        ev_min = 1.0/np.dot(r, Ar)
#        if abs(1.0 - ev_min_old/ev_min) < eps:
#            return ev_min, r
#
#def flatten(points):
#    # obtain a plane
#    # n[0]*(points[0] - gc[0]) + n[1]*(points[1] - gc[1]) + n[2]*(points[2] - gc[2]) = 0
#    # by the least square method
#    gc = np.average(points, axis = 0)
#    x = points - gc
#    A = np.dot(x.T, x)/points.shape[0]
#    n = inverse_power_method(A)[1]
#    removal = int(0.2*points.shape[0])
#    if points.shape[0] - removal > 3:
#        removal_indices = np.argsort(abs(np.dot(x, n)))[-removal:]
#        gc = (points.shape[0]*gc - np.sum(points[removal_indices], axis = 0))/(points.shape[0] - removal_indices.shape[0])
#        x = points - gc
#        x_removal = x[removal_indices]
#        A = (points.shape[0]*A - np.dot(x_removal.T, x_removal))/(points.shape[0] - removal_indices.shape[0])
#        n = inverse_power_method(A)[1]
#    # n[0]*(points[0] - k*n[0] - gc[0]) + n[1]*(points[1] - k*n[1] - gc[1]) + n[2]*(points[2] - k*n[2] - gc[2]) = 0
#    # k = n[0]*(points[0] - gc[0]) + n[1]*(points[1] - gc[1]) + n[2]*(points[2] - gc[2])
#    return points - np.dot(x, n).reshape(-1, 1)*n

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = exec_paraFoam = scaleMesh_0p001 = False
        patch_type = ''
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-n':
                i += 1
                patch_name = sys.argv[i]
            elif sys.argv[i] == '-p':
                exec_paraFoam = True
            elif sys.argv[i] == '-s':
                scaleMesh_0p001 = True
            elif sys.argv[i] == '-t':
                i += 1
                patch_type = sys.argv[i]
            elif sys.argv[i] in ('-x', '-y', '-z'):
                coordinate = 0 if sys.argv[i] == '-x' else (1 if sys.argv[i] == '-y' else 2)
                i += 1
                value = float(sys.argv[i])
            i += 1

    boundary = os.path.join('constant', 'polyMesh', 'boundary')
    faces = os.path.join('constant', 'polyMesh', 'faces')
    points = os.path.join('constant', 'polyMesh', 'points')
    for i in (boundary, faces, points):
        if not os.path.isfile(i):
            print('エラー: {}ファイルがありません．'.format(i))
            sys.exit(1)
    converted_millimeter_into_meter = misc.isConvertedMillimeterIntoMeter()

    print('x, y, z座標をある値に固定することでpatchを平面にします．')

    if interactive:
        patch_name = (raw_input if sys.version_info.major <= 2 else input)(
            ' '.join(listFile.patchList()) + ' の中から平面にしたいpatchの名前を1つ入力して下さい． > ').strip()
        ans = (raw_input if sys.version_info.major <= 2 else input)(
            '座標=値の形式で座標と値を決めて下さい．(例: x=0.0) > ').strip().lower().split('=')
        coordinate = ans[0].strip()
        coordinate = 0 if coordinate == 'x' else (1 if coordinate == 'y' else 2)
        value = float(ans[1])

    nFaces = startFace = -1
    dp = DictParser(boundary)
    s_old = dp.toString()
    for a in dp.contents:
        if DictParserList.isType(a, DictParserList.LISTP):
            a = a.value()
            break
    for b in a:
        if DictParserList.isType(b, DictParserList.BLOCK) and b.key() == patch_name:
            for c in b.value():
                if DictParserList.isType(c, DictParserList.DICT):
                    if c.key() == 'type':
                        if interactive:
                            patch_type = (raw_input if sys.version_info.major <= 2 else input)(
                                patch_name + 'のtypeは' + c.value()[0] + 'です．\n' +
                                'typeを変更する場合は empty , symmetryPlane , wedge のうちのどれか，' +
                                '変更しない場合はEnterのみを入力して下さい． > ').strip()
                        if patch_type not in ('', c.value()[0]):
                            c.setValue([patch_type])
                    if c.key() == 'nFaces':
                        nFaces = int(c.value()[0])
                    elif c.key() == 'startFace':
                        startFace = int(c.value()[0])
            break
    if nFaces == -1 or startFace == -1:
        print('エラー: {}という名前のpatchはありません．'.format(patch_name))
        sys.exit(1)
    s = dp.toString()
    if s != s_old:
        with open(boundary, 'w') as f:
            f.write(s)

    with open(faces, 'r') as f:
        s = f.read()
    ph = s.find('(') + 1
    pf = s.rfind(')')
    n = int(s[s[:ph - 2].rfind('\n') + 1:ph - 1])
    faces_data = []
    if 'binary' in s:
        if 'faceCompactList' in s:
            pr = ph + 4*n
            faces_ranges = np.fromstring(s[ph:pr], dtype = '<u4')
            pl = pr + s[pr:].find(')') + 1
            pr = pl + s[pl:].find('(')
            n = int(s[pl:pr])
            pl = pr + 1
            pr = pl + 4*n
            points_indices = np.fromstring(s[pl:pr], dtype = '<u4')
            for i in range(faces_ranges.shape[0] - 1):
                faces_data.append(points_indices[faces_ranges[i]:faces_ranges[i + 1]])
        else: # faceList
            pr = ph - 1
            for i in range(n):
                pl = pr + 1
                pr = pl + s[pl:].find('(')
                n = int(s[pl:pr])
                pl = pr + 1
                pr = pl + 4*n
                faces_data.append(np.fromstring(s[pl:pr], dtype = '<u4'))
    else:
        points_indices = [i[i.find('(') + 1:] for i in s[ph:pf].split(')')]
        if points_indices[-1] == '':
            del points_indices[-1]
        for i in points_indices:
            faces_data.append(np.fromstring(i, dtype = 'u4', sep = ' '))
    faces_data = list(set([j for i in faces_data[startFace:startFace + nFaces] for j in i]))

    with open(points, 'r') as f:
        s = f.read()
    ph = s.find('(') + 1
    pf = s.rfind(')')
    n = int(s[s[:ph - 2].rfind('\n') + 1:ph - 1])
    if 'binary' in s:
        points_data = np.fromstring(s[ph:ph + 8*3*n], dtype = '<d').reshape(-1, 3)
        points_data[faces_data, coordinate] = value
#        points_data[faces_data] = flatten(points_data[faces_data])
#        os.rename(points, points + '_bak')
        with open(points, 'wb') as f: # can overwrite
            f.write(s[:ph])
            points_data.astype('<d').tofile(f)
            f.write(s[pf:])
    else:
        if s[ph] == '\n':
            ph += 1
        points_data = np.fromstring(s[ph:pf].replace('(', '').replace(')', ''), dtype = 'd', sep = ' ').reshape(-1, 3)
        points_data[faces_data, coordinate] = value
#        points_data[faces_data] = flatten(points_data[faces_data])
#        os.rename(points, points + '_bak')
        with open(points, 'w') as f: # can overwrite
            f.write(s[:ph])
            for i in points_data:
                f.write('({} {} {})\n'.format(i[0], i[1], i[2]))
            f.write(s[pf:])

    if not converted_millimeter_into_meter:
        if interactive:
            box = misc.box_size_of_calculation_range(points)[1]
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
