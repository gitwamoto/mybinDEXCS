#!/usr/bin/env python
# -*- coding: utf-8 -*-
# snappyHexMeshを実行.py
# by Yukiharu Iwamoto
# 2026/5/12 9:57:46 AM

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
from utilities import rmObjects
from utilities import dictParse

two_dimensional = False
blockMeshDict_path = os.path.join('system', 'blockMeshDict')
blockMeshDict_3D_path = blockMeshDict_path + '_3D'
snappyHexMeshDict_path = os.path.join('system', 'snappyHexMeshDict')
snappyHexMeshDict_3D_path = snappyHexMeshDict_path + '_3D'

def handler(signum, frame):
    if two_dimensional:
        if os.path.isfile(blockMeshDict_3D_path):
            os.rename(blockMeshDict_3D_path, blockMeshDict_path) # can overwrite
        if os.path.isfile(snappyHexMeshDict_3D_path):
            os.rename(snappyHexMeshDict_3D_path, snappyHexMeshDict_path) # can overwrite
    if os.path.isdir('0_bak'):
        if os.path.isdir('0'):
            shutil.rmtree('0')
        shutil.move('0_bak', '0')
    rmObjects.removeInessentials()
    sys.exit(1)

def makeBlockMeshDict(max_cell_size, bounding_box, front_name, back_name):
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
        if os.path.isfile(blockMeshDict_path):
            os.rename(blockMeshDict_path, blockMeshDict_3D_path) # can overwrite
    else:
        z_min = bounding_box[2] - 0.5*max_cell_size
        z_max = bounding_box[5] + 0.5*max_cell_size
        n_z = max(int((z_max - z_min)/max_cell_size + 0.5), 1)
    with open(blockMeshDict_path, 'w') as f:
        f.write('FoamFile\n'
            '{\n'
            '\tversion\t2.0;\n'
            '\tformat\tascii;\n'
            '\tclass\tdictionary;\n'
            '\tlocation\t"system";\n'
            '\tobject\tblockMeshDict;\n'
            '}\n'
            '\n'
            'scale\t1;\n'
            '\n'
            '//     7 ------- 6\n'
            '//   / |       / |\n'
            '// 4 ------- 5   |\n'
            '// |   |     |   |\n'
            '// |   3 --- | - 2\n'
            '// | /       | /\n'
            '// 0 ------- 1\n'
            'vertices\n'
            '(\n'
            f'\t({x_min} {y_min} {z_min})\n'
            f'\t({x_max} {y_min} {z_min})\n'
            f'\t({x_max} {y_max} {z_min})\n'
            f'\t({x_min} {y_max} {z_min})\n'
            f'\t({x_min} {y_min} {z_max})\n'
            f'\t({x_max} {y_min} {z_max})\n'
            f'\t({x_max} {y_max} {z_max})\n'
            f'\t({x_min} {y_max} {z_max})\n'
            ');\n'
            '\n'
            'blocks\n'
            '(\n'
            f'\thex (0 1 2 3 4 5 6 7) ({n_x} {n_y} {n_z}) simpleGrading (1 1 1)\n'
            ');\n'
            '\n'
            'edges\t();\n'
            '\n'
            'boundary\n'
            '(\n'
            '\tbMXMin\n'
            '\t{\n'
            '\t\ttype\tpatch;\n'
            '\t\tfaces\t((0 4 7 3));\n'
            '\t}\n'
            '\tbMXMax\n'
            '\t{\n'
            '\t\ttype\tpatch;\n'
            '\t\tfaces\t((2 6 5 1));\n'
            '\t}\n'
            '\tbMYMin\n'
            '\t{\n'
            '\t\ttype\tpatch;\n'
            '\t\tfaces\t((1 5 4 0));\n'
            '\t}\n'
            '\tbMYMax\n'
            '\t{\n'
            '\t\ttype\tpatch;\n'
            '\t\tfaces\t((3 7 6 2));\n'
            '\t}\n')
        if two_dimensional:
            f.write(f'\t{front_name}\n'
                '\t{\n'
                '\t\ttype\tempty;\n'
                '\t\tfaces\t((0 3 2 1));\n'
                '\t}\n'
                f'\t{back_name}\n'
                '\t{\n'
                '\t\ttype\tempty;\n'
                '\t\tfaces\t((4 5 6 7));\n'
                '\t}\n')
        else:
            f.write('\tbMZMin\n'
                '\t{\n'
                '\t\ttype\tpatch;\n'
                '\t\tfaces\t((0 3 2 1));\n'
                '\t}\n'
                '\tbMZMax\n'
                '\t{\n'
                '\t\ttype\tpatch;\n'
                '\t\tfaces\t((4 5 6 7));\n'
                '\t}\n')
        f.write(');\n'
            '\n'
            'mergePatchPairs\t();\n')
        os.chmod(blockMeshDict_path, 0o0666)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler) # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)

    front_name = 'front'
    back_name = 'back'
    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = False
        exec_paraFoam = False
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

    if not os.path.isfile(snappyHexMeshDict_path):
        print(f'エラー: ファイル{snappyHexMeshDict_path}がありません．')
        sys.exit(1)
    if float(misc.latestTime()) != 0.0:
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
                domains = max(int(input('計算領域を何個に分割して並列計算しますか？'
                    f' ({threads}個まで, 1だと普通の計算) > ').strip()), 1)
                break
            except ValueError:
                pass
        two_dimensional = True if input('\n2次元メッシュを作りますか？\n'
            '*** 2次元メッシュでは，empty境界がx-y平面に平行でないといけません． (y/n) > '
            ).strip().lower() == 'y' else False
        if two_dimensional:
            front_name = input('(zが大きい)前側patchの名前を決めて下さい． (Enterのみ: front) > ').strip() or 'front'
            back_name = input('(zが小さい)後側patchの名前を決めて下さい． (Enterのみ: back) > ').strip() or 'back'
    domains = min(domains, threads)

    snappyHexMeshDict = dictParse.DictParser(file_name = snappyHexMeshDict_path)

    # CUSTOM_OPTIONS
    # {
    #   maxCellSize	10; // used to generate blockMeshDict
    #   boundingBox	((-150.0 -280.0 -30.0) (150.0 700.0 170.0)); // used to generate blockMeshDict
    # }
    CUSTOM_OPTIONS = snappyHexMeshDict.find_element([{'type': 'block', 'key': 'CUSTOM_OPTIONS'}])['element']
    makeBlockMeshDict(
        max_cell_size = float(dictParse.find_element([{'type': 'dictionary', 'key': 'maxCellSize'},
            {'except type': 'ignorable'}], parent = CUSTOM_OPTIONS)['element']['value']),
        bounding_box = [float(i['element']['value']) for i in
            dictParse.find_all_elements([{'type': 'dictionary', 'key': 'boundingBox'}, {'type': 'list'},
                {'type': 'list'}, {'except type': 'ignorable|list_start|list_end'}], parent = CUSTOM_OPTIONS)],
        front_name = front_name, back_name = back_name)

    # geometry
    # {
	#   // geometry_stl_block
    #   STL_NAME.stl // stl_file_name
    #   {
    #     type triSurfaceMesh;
    #     name STL_NAME; // geometry_stl_name
    #   }
    #   ...
    geometry_stl_name = None
    for b in snappyHexMeshDict.find_all_elements([{'type': 'block', 'key': 'geometry'}, {'type': 'block'}]):
        if b['element']['key'].endswith('.stl'): # STLファイルは1つにまとめられていると仮定
            geometry_stl_block = b['element']
            stl_file_name = b['element']['key']
            n = dictParse.find_element([{'type': 'dictionary', 'key': 'name'},
                {'except type': 'ignorable'}], parent = b['element'])['element']
            if n is not None:
                geometry_stl_name = n['value'] # 最終的なパッチ名は nameの値 + _ + STL内のsolid名 になります。
            break

    if two_dimensional:
        # castellatedMeshControls
        # {
        #   refinementSurfaces
        #   {
        #     STL_NAME // geometry_stl_name
		#     {
		#       regions
		#       {
		#         PATCH_NAME
		#         {
		#           level (0 1); // (min max)
		#           patchInfo {type	empty;}
		#         }
        #         ...
        empty_list = []
        path_list = [{'type': 'block', 'key': 'castellatedMeshControls'},
            {'type': 'block', 'key': 'refinementSurfaces'}]
        if geometry_stl_name is not None:
            path_list += [{'type': 'block', 'key': geometry_stl_name}, {'type': 'block', 'key': 'regions'}]
        path_list.append({'type': 'block'})
        for b in reversed(snappyHexMeshDict.find_all_elements(path_list)):
            if dictParse.find_element([{'type': 'block', 'key': 'patchInfo'}, {'type': 'dictionary', 'key': 'type'},
                {'except type': 'ignorable'}], parent = b['element'])['element']['value'] == 'empty':
                empty_list.append(b['key'])
                del b['parent'][b['index']]
        stl_2D_file_name = os.path.splitext(stl_file_name)[0] + '_2D.stl'
        should_write = True
        with open(os.path.join('constant', 'triSurface', stl_2D_file_name), 'w') as f:
            for line in open(os.path.join('constant', 'triSurface', stl_file_name), 'r'):
                if 'endsolid' in line and line.split()[-1] in empty_list:
                    should_write = True
                elif 'solid' in line and line.split()[-1] in empty_list:
                    should_write = False
                elif should_write:
                    f.write(line)
        geometry_stl_block['value'] = stl_2D_file_name
        os.rename(snappyHexMeshDict_path, snappyHexMeshDict_3D_path) # can overwrite
        with open(snappyHexMeshDict_path, 'w') as f:
            f.write(dictParse.normalize(string = snappyHexMeshDict.file_string())[0])

    command = 'blockMesh'
    if subprocess.call(command, shell = True) != 0:
        print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
        sys.exit(1)
    if two_dimensional:
        os.rename(blockMeshDict_path, blockMeshDict_path + '_2D') # can overwrite
        if os.path.isfile(blockMeshDict_3D_path):
            os.rename(blockMeshDict_3D_path, blockMeshDict_path) # can overwrite

    if domains != 1:
        rmObjects.removeProcessorDirs()
        decomposeParDict_path = os.path.join('system', 'decomposeParDict')
        decomposeParDict_bak_path = f'{decomposeParDict_path}_bak'
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
        command = 'decomposePar -noZero -noFunctionObjects'
        r = subprocess.call(command, shell = True)
        if r == 0:
            command = f'mpirun -np {domains} snappyHexMesh -parallel -overwrite | tee snappyHexMesh.log'
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
        command = 'snappyHexMesh -overwrite | tee snappyHexMesh.log'
        if subprocess.call(command, shell = True) != 0:
            print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
            sys.exit(1)

    if two_dimensional:
        os.rename(snappyHexMeshDict_path, snappyHexMeshDict_path + '_2D') # can overwrite
        os.rename(snappyHexMeshDict_3D_path, snappyHexMeshDict_path) # can overwrite

    if geometry_stl_name is not None:
        prefix = geometry_stl_name + '_'
        len_prefix = len(prefix)
        boundary_path = os.path.join('constant', 'polyMesh', 'boundary')
        boundary = dictParse.DictParser(file_name = boundary_path)
        for p in boundary.find_all_elements([{'type': 'list'}, {'type': 'block'}]):
            if p['element']['key'].startswith(prefix):
                p['element']['key'] = p['element']['key'][len_prefix:]
        with open(boundary_path, 'w') as f:
            f.write(dictParse.normalize(string = boundary.file_string())[0])

    misc.convertMillimeterIntoMeter()
    misc.removePatchesHavingNoFaces() # フェイスを1つも含まないパッチを取り除く
    if two_dimensional:
        command = 'flattenMesh'
        if subprocess.call(command, shell = True) != 0:
            print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
            sys.exit(1)
        subprocess.call(os.path.join(os.path.dirname(os.path.abspath(__file__)), '2次元メッシュに.py') +
            f' -f {front_name} -b {back_name} -s', shell = True)

    regionProperties_path = os.path.join('constant', 'regionProperties')
    if snappyHexMeshDict.find_element([{'type': 'block', 'key': 'castellatedMeshControls'},
        {'type': 'dictionary', 'key': 'locationsInMesh'}])['element'] is not None:
        for i in glob.iglob(os.path.join('constant', '*' + os.sep)):
            i += 'polyMesh' # i/polyMeshというパスのフォルダがあるはず
            if os.path.isdir(i):
                shutil.rmtree(i)
        if os.path.isdir('0'):
            shutil.move('0', '0_bak')
        command = 'splitMeshRegions -cellZones -overwrite' 
        if subprocess.call(command, shell = True) != 0:
            # 0/
            # +-- regionA/
            # |   +-- cellToregion
            # +-- regionB/
            # |   +-- cellToregion
            # :
            # +-- cellToregion
            print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
            sys.exit(1)
        regions = sorted([os.path.basename(os.path.dirname(i))
            for i in glob.iglob(os.path.join('constant', '*' + os.sep)) if os.path.isdir(i + 'polyMesh')])
        if interactive:
            fluid_regions = input(' '.join(regions) +
                ' の中から，流体側の領域名全てをスペース区切りで指定して下さい． > ').split()
        solid_regions = sorted(set(regions) - set(fluid_regions)) # list
        with open(regionProperties_path, 'w') as f:
            f.write('FoamFile\n'
                '{\n'
                '\tversion\t2.0;\n'
                '\tformat\tascii;\n'
                '\tclass\tdictionary;\n'
                '\tlocation\t"constant";\n'
                '\tobject\tregionProperties;\n'
                '}\n'
                'regions\n'
                '(\n'
                f'\tsolid\t({" ".join(solid_regions)})\n'
                f'\tfluid\t({" ".join(fluid_regions)})\n'
                ');\n')
        for i0_bak in glob.iglob(os.path.join('0_bak', '*')):
            i_name = os.path.basename(i0_bak)
            i0 = os.path.join('0', i_name)
            if os.path.isfile(i0_bak) and i_name != 'cellToRegion':
                if os.path.isfile(i0): # i0 = 0/i_nameというパスを持つファイルまたはフォルダを消す
                    os.remove(i0)
                elif os.path.isdir(i0):
                    os.rmtree(i0)
                shutil.move(i0_bak, '0') # can't overwrite, 0_bak/i_name -> 0/i_name
                parser = dictParse.DictParser(file_name = i0) # i0 is file
                for i in parser.find_all_elements([{'type': 'directive', 'key': '#include'}]):
                    n = dictParse.find_element([{'type': 'string'}], parent = i['element'])
                    if n['element']['value'].startswith('"../'):
                        n['element']['value'] = '"../' + n['element']['value'][1:]
                string = dictParse.normalize(string = parser.file_string())[0]
                for r in regions:
                    if not os.path.isdir(os.path.join('0_bak', r)):
                        with open(os.path.join('0', r, i_name)) as f:
                            f.write(string)
            elif os.path.isdir(i0_bak) and os.path.isdir(i0):
                for j0_bak in glob.iglob(os.path.join(i0_bak, '*')):
                    j_name = os.path.basename(j0_bak)
                    j0 = os.path.join(i0, j_name)
                    if os.path.isfile(j0): # j0 = 0_bak/i_name/jnameというパスを持つファイルまたはフォルダを消す
                        os.remove(j0)
                    elif os.path.isdir(j0):
                        os.rmtree(j0)
                    shutil.move(j0_bak, i0) # can't overwrite, 0_bak/i_name/jname -> 0/i_name/j_name
        shutil.rmtree('0_bak')
        for r in glob.iglob(os.path.join('system', '*' + os.sep)):
            # system/
            # +-- regionA/
            # |   +-- fvSolution
            # |   +-- fvSchemes
            # +-- regionB/
            # |   +-- fvSolution
            # :   +-- fvSchemes
            fvSolution_path = os.path.join(r, 'fvSolution')
            if os.path.isfile(fvSolution_path):
                parser = dictParse.DictParser(file_name = fvSolution_path)
                contents = parser.find_all_elements([{'except type': 'ignorable|separator'}])
                for c in contents:
                    if c['element']['type'] == 'block' and c['element']['key'] == 'FoamFile':
                        del c['parent'][c['index']]
                if len(contents) == 0:
                    shutil.copy(os.path.join('system', 'fvSolution'), r) # can overwrite
                    shutil.copy(os.path.join('system', 'fvSchemes'), r) # can overwrite
        misc.correctLocation()
    elif os.path.isfile(regionProperties_path):
        os.remove(regionProperties_path)

    if not two_dimensional:
        misc.execCheckMesh()
        sets = os.path.join('constant', 'polyMesh', 'sets')
        if os.path.isdir(sets):
            shutil.rmtree(sets)

    if interactive:
        exec_paraFoam = True if input('\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam, ambient = 0.0, diffuse = 1.0)

    rmObjects.removeInessentials()
