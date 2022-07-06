#!/usr/bin/env python
# -*- coding: utf-8 -*-
# snappyHexMeshを実行.py
# by Yukiharu Iwamoto
# 2022/7/6 4:22:10 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行
# -2 cartesian2DMeshで2次元メッシュを作る．empty境界はx-y平面に平行でなければならない
# -b back_name -> 【-2オプションがある時のみ有効】(zが大きい)後側patchの名前をback_nameにする．
#                 このオプションがない場合，backという名前になる．
# -f front_name -> 【-2オプションがある時のみ有効】(zが大きい)前側patchの名前をfront_nameにする．
#                  このオプションがない場合，frontという名前になる．
# -l 'fluid1 fluid2' -> 【マルチリージョン解析時のみ有効】流体側の領域名全てを'fluid1 fluid2'のように
#                        引用符で囲んだスペース区切りで指定する．
#                        snappyHexMeshDictのlocationsInMeshに書いた名前が領域名になる．
# -p -> paraFoamを実行する
# -r domains -> 計算領域をdomains個に分割して並列計算を行う，1だと普通の計算

import os
import sys
import signal
import subprocess
import shutil
import glob
from utilities import misc
from utilities.dictParse import DictParser, DictParserList
from utilities import rmObjects
from utilities import folderTime

two_dimensional = False
blockMeshDict = os.path.join('system', 'blockMeshDict')
blockMeshDict_3D = blockMeshDict + '_3D'
sHMeshDict = os.path.join('system', 'snappyHexMeshDict')
sHMeshDict_3D = sHMeshDict + '_3D'

def handler(signal, frame):
    if os.path.isdir('0_bak'):
        if os.path.isdir('0'):
            shutil.rmtree('0')
        shutil.move('0_bak', '0')

def makeBlockMeshDict(max_cell_size, bounding_box, front_name = None, back_name = None):
    x_min = bounding_box[0] - 0.5*max_cell_size
    x_max = bounding_box[3] + 0.5*max_cell_size
    y_min = bounding_box[1] - 0.5*max_cell_size
    y_max = bounding_box[4] + 0.5*max_cell_size
    n_x = max(int((x_max - x_min)/max_cell_size + 0.5), 1)
    n_y = max(int((y_max - y_min)/max_cell_size + 0.5), 1)
    if two_dimensional:
        z_min = bounding_box[2]
        z_max = bounding_box[5]
        n_z = 1
        if os.path.isfile(blockMeshDict):
            os.rename(blockMeshDict, blockMeshDict_3D) # can overwrite
    else:
        z_min = bounding_box[2] - 0.5*max_cell_size
        z_max = bounding_box[5] + 0.5*max_cell_size
        n_z = max(int((z_max - z_min)/max_cell_size + 0.5), 1)
    with open(blockMeshDict, 'w') as f:
        f.write('FoamFile\n{')
        f.write('\n\tversion\t2.0;\n')
        f.write('\tformat\tascii;\n')
        f.write('\tclass\tdictionary;\n')
        f.write('\tlocation\t"system";\n')
        f.write('\tobject\tblockMeshDict;\n')
        f.write('}\n') # FoamFile
        f.write('\nscale\t1;\n\n')
        f.write('//     7 ------- 6\n')
        f.write('//   / |       / |\n')
        f.write('// 4 ------- 5   |\n')
        f.write('// |   |     |   |\n')
        f.write('// |   3 --- | - 2\n')
        f.write('// | /       | /\n')
        f.write('// 0 ------- 1\n')
        f.write('vertices\n(\n')
        f.write('\t({} {} {})\n'.format(x_min, y_min, z_min))
        f.write('\t({} {} {})\n'.format(x_max, y_min, z_min))
        f.write('\t({} {} {})\n'.format(x_max, y_max, z_min))
        f.write('\t({} {} {})\n'.format(x_min, y_max, z_min))
        f.write('\t({} {} {})\n'.format(x_min, y_min, z_max))
        f.write('\t({} {} {})\n'.format(x_max, y_min, z_max))
        f.write('\t({} {} {})\n'.format(x_max, y_max, z_max))
        f.write('\t({} {} {})\n'.format(x_min, y_max, z_max))
        f.write(');\n\n')
        f.write('blocks\n(\n')
        f.write('\thex (0 1 2 3 4 5 6 7) ({} {} {}) simpleGrading (1 1 1)\n'.format(n_x, n_y, n_z))
        f.write(');\n\n')
        f.write('edges\n(\n);\n\n')
        f.write('boundary\n(\n')
        f.write('\tbMXMin\n\t{\n\t\ttype\tpatch;\n\t\tfaces\t((0 4 7 3));\n\t}\n')
        f.write('\tbMXMax\n\t{\n\t\ttype\tpatch;\n\t\tfaces\t((2 6 5 1));\n\t}\n')
        f.write('\tbMYMin\n\t{\n\t\ttype\tpatch;\n\t\tfaces\t((1 5 4 0));\n\t}\n')
        f.write('\tbMYMax\n\t{\n\t\ttype\tpatch;\n\t\tfaces\t((3 7 6 2));\n\t}\n')
        if two_dimensional:
            f.write('\t' + front_name + '\n\t{\n\t\ttype\tempty;\n\t\tfaces\t((0 3 2 1));\n\t}\n')
            f.write('\t' + back_name + '\n\t{\n\t\ttype\tempty;\n\t\tfaces\t((4 5 6 7));\n\t}\n')
        else:
            f.write('\tbMZMin\n\t{\n\t\ttype\tpatch;\n\t\tfaces\t((0 3 2 1));\n\t}\n')
            f.write('\tbMZMax\n\t{\n\t\ttype\tpatch;\n\t\tfaces\t((4 5 6 7));\n\t}\n')
        f.write(');\n\n')
        f.write('mergePatchPairs\n(\n);\n')
        os.chmod(blockMeshDict, 0o0666)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler) # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)

    front_name, back_name = 'front', 'back'
    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = exec_paraFoam = two_dimensional = False
        domains = 1
        fluid_regions = []
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
            elif sys.argv[i] == '-l':
                i += 1
                fluid_regions.extend(sys.argv[i].split())
            elif sys.argv[i] == '-p':
                exec_paraFoam = True
            elif sys.argv[i] == '-r':
                i += 1
                domains = max(int(sys.argv[i]), 1)
            i += 1

    if not os.path.isfile(sHMeshDict):
        print('エラー: {}ファイルがありません．'.format(sHMeshDict))
        sys.exit(1)
    if float(folderTime.latestTime()) != 0.0:
        print('エラー: 0秒以外のフォルダがあるとうまくいきません．')
        sys.exit(1)
    if os.path.isdir('dynamicCode'):
        shutil.rmtree('dynamicCode')
    rmObjects.removeProcessorDirs()
    for f in ('snappyHexMesh.log', 'snappyHexMesh.logfile'):
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
            '\n2次元メッシュを作りますか？\n' +
            '*** 2次元メッシュでは，empty境界はx-y平面に平行でなければならなりません． (y/n) > '
            ).strip().lower() == 'y' else False
    domains = min(domains, threads)

    dp_sHMeshDict = DictParser(sHMeshDict)
    max_cell_size = float(dp_sHMeshDict.getValueForKey(['CUSTOM_OPTIONS', 'maxCellSize'])[0])
    x = dp_sHMeshDict.getValueForKey(['CUSTOM_OPTIONS', 'boundingBox'])[0].value()
    #       0                                           1                   2
    # x = [[listp|'', '', ['-20', '', '-20', '', '0']], '', [listp|'', '', ['40', '', '20', '', '1']]]
    bounding_box = [float(i) for i in (x[0].value()[::2] + x[2].value()[::2])]

    stl_file_name_wo_ext = None
    x = dp_sHMeshDict.getValueForKey(['geometry'])
    for y in x:
        if DictParserList.isType(y, DictParserList.BLOCK):
            if y.key().endswith('.stl'):
                for z in y.value():
                    if DictParserList.isType(z, DictParserList.DICT) and z.key() == 'name':
                        stl_file_name_wo_ext = z.value()[0]
                        stl_geometry = y
                        break
    multi_regions = False if dp_sHMeshDict.getIndexOfItem(
        ['castellatedMeshControls', 'locationsInMesh']) is None else True

    if two_dimensional:
        empty_list = []
        x = dp_sHMeshDict.getValueForKey(['castellatedMeshControls', 'refinementSurfaces',
            stl_file_name_wo_ext, 'regions'])
        if x is None:
            print(sHMeshDict + 'にcastellatedMeshControls.refinementSurfaces.' +
                stl_file_name_wo_ext + '.regionsがありません．')
            sys.exit(1)
        i = 0
        while i < len(x):
            found = False
            if DictParserList.isType(x[i], DictParserList.BLOCK):
                for y in x[i].value():
                    if DictParserList.isType(y, DictParserList.BLOCK) and y.key() == 'patchInfo':
                        for z in y.value():
                            if (DictParserList.isType(z, DictParserList.DICT) and z.key() == 'type' and
                                z.value()[0] == 'empty'):
                                empty_list.append(x[i].key())
                                found = True
                                break
                    if found:
                        break
            if found:
                del x[i]
                if x[i] == '\n' and x[i - 1] == '\n':
                    del x[i]
            else:
                i += 1
        stl_2D_file_name = stl_file_name_wo_ext + '_2D.stl'
        should_write = True
        with open(os.path.join('constant', 'triSurface', stl_2D_file_name), 'w') as f2d:
            with open(os.path.join('constant', 'triSurface', stl_file_name_wo_ext + '.stl'), 'r') as f:
                for line in f:
                    if 'endsolid' in line and line.split()[-1] in empty_list:
                        should_write = True
                    elif 'solid' in line and line.split()[-1] in empty_list:
                        should_write = False
                    elif should_write:
                        f2d.write(line)
        stl_geometry.setKey(stl_2D_file_name)
        os.rename(sHMeshDict, sHMeshDict_3D) # can overwrite
        dp_sHMeshDict.writeFile(sHMeshDict)
        if interactive:
            front_name = (raw_input if sys.version_info.major <= 2 else input)(
                '(zが大きい)前側patchの名前を決めて下さい． (Enterのみ: front) > ').strip()
            if front_name == '':
                front_name = 'front'
            back_name = (raw_input if sys.version_info.major <= 2 else input)(
                '(zが小さい)後側patchの名前を決めて下さい． (Enterのみ: back) > ').strip()
            if back_name == '':
                back_name = 'back'

    makeBlockMeshDict(max_cell_size, bounding_box, front_name, back_name)
    command = 'blockMesh'
    if subprocess.call(command, shell = True) != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)
    if two_dimensional:
        os.rename(blockMeshDict, blockMeshDict + '_2D') # can overwrite
        if os.path.isfile(blockMeshDict_3D):
            os.rename(blockMeshDict_3D, blockMeshDict) # can overwrite

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
        command = 'decomposePar -noZero -noFunctionObjects'
        r = subprocess.call(command, shell = True)
        if r == 0:
            command = 'mpirun -np {} snappyHexMesh -parallel -overwrite | tee snappyHexMesh.log'.format(domains)
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
        command = 'snappyHexMesh -overwrite | tee snappyHexMesh.log'
        if subprocess.call(command, shell = True) != 0:
            print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
            sys.exit(1)

    if two_dimensional:
        os.rename(sHMeshDict, sHMeshDict + '_2D') # can overwrite
        os.rename(sHMeshDict_3D, sHMeshDict) # can overwrite

    boundary = os.path.join('constant', 'polyMesh', 'boundary')
    if stl_file_name_wo_ext is not None:
        stl_file_name_wo_ext += '_'
        l = len(stl_file_name_wo_ext)
        dp_boundary = DictParser(boundary)
        for a in dp_boundary.contents:
            if DictParserList.isType(a, DictParserList.LISTP):
                a = a.value()
                break
        for b in a:
            if DictParserList.isType(b, DictParserList.BLOCK) and b.key().startswith(stl_file_name_wo_ext):
                b.setKey(b.key()[l:])
        dp_boundary.writeFile(boundary)

    misc.convertLengthUnitInMillimeterToMeter()
    misc.removePatchesHavingNoFaces() # フェイスを1つも含まないパッチを取り除く
    if two_dimensional:
        command = 'flattenMesh'
        if subprocess.call(command, shell = True) != 0:
            print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
            sys.exit(1)
    regionProperties = os.path.join('constant', 'regionProperties')
    if multi_regions:
        for i in glob.iglob(os.path.join('constant', '*' + os.sep)):
            i += 'polyMesh'
            if os.path.isdir(i):
                shutil.rmtree(i)
        if os.path.isdir('0'):
            shutil.move('0', '0_bak')
        command = 'splitMeshRegions -cellZones -overwrite'
        if subprocess.call(command, shell = True) != 0:
            print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
            sys.exit(1)
        regions = []
        for i in glob.iglob(os.path.join('constant', '*' + os.sep)):
            if os.path.isdir(i + 'polyMesh'):
                regions.append(os.path.basename(os.path.dirname(i)))
        if interactive:
            fluid_regions = (raw_input if sys.version_info.major <= 2 else input)(
                ' '.join(regions) +
                ' の中から，流体側の領域名全てをスペース区切りで指定して下さい． > ').split()
        solid_regions = list(set(regions)^set(fluid_regions))
        with open(regionProperties, 'w') as f:
            f.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tdictionary;\n')
            f.write('\tlocation\t"constant";\n')
            f.write('\tobject\tregionProperties;\n')
            f.write('}\n')
            f.write('regions\n(\n')
            f.write('\tsolid\t(' + ' '.join(solid_regions) + ')\n')
            f.write('\tfluid\t(' + ' '.join(fluid_regions) + ')\n')
            f.write(');\n')
        for i in glob.iglob(os.path.join('0_bak', '*')):
            ib = os.path.basename(i)
            i0 = os.path.join('0', ib)
            if os.path.isfile(i) and ib != 'cellToRegion':
                if os.path.isfile(i0):
                    os.remove(i0)
                elif os.path.isdir(i0):
                    os.rmtree(i0)
                shutil.move(i, '0') # can't overwrite
                dp = DictParser(i0)
                for x in dp.contents:
                    if DictParserList.isType(x, DictParserList.INCLUDE) and x.value().startswith('"../'):
                        x.setValue('"../' + x.value()[1:])
                s = dp.toString()
                for d in regions:
                    if not os.path.isdir(os.path.join('0_bak', d)):
                        with open(os.path.join('0', d, ib), 'w') as f:
                            f.write(s)
            elif os.path.isdir(i) and os.path.isdir(i0):
                for j in glob.iglob(os.path.join(i, '*')):
                    jb = os.path.basename(j)
                    j0 = os.path.join(i0, jb)
                    if os.path.isfile(j0):
                        os.remove(j0)
                    elif os.path.isdir(j0):
                        os.rmtree(j0)
                    shutil.move(j, i0) # can't overwrite
        shutil.rmtree('0_bak')
        for d in glob.iglob(os.path.join('system', '*' + os.sep)):
            fvSolution = os.path.join(d, 'fvSolution')
            if os.path.isfile(fvSolution):
                dp = DictParser(fvSolution)
                while len(dp.contents) > 0:
                    if type(dp.contents[0]) is str or dp.contents[0].key() == 'FoamFile':
                        del dp.contents[0]
                    else:
                        break
                if len(dp.contents) == 0:
                    shutil.copy(os.path.join('system', 'fvSolution'), d) # can overwrite
                    shutil.copy(os.path.join('system', 'fvSchemes'), d) # can overwrite
        misc.correctLocation()
    elif os.path.isfile(regionProperties):
        os.remove(regionProperties)

    misc.execCheckMesh()
    sets = os.path.join('constant', 'polyMesh', 'sets')
    if os.path.isdir(sets):
        shutil.rmtree(sets)

    if interactive:
        exec_paraFoam = True if (raw_input if sys.version_info.major <= 2 else input)(
            '\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam)

    rmObjects.removeInessentials()
