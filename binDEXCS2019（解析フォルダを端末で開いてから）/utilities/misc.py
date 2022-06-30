#!/usr/bin/env python
# -*- coding: utf-8 -*-
# misc.py
# by Yukiharu Iwamoto
# 2022/6/30 8:24:07 PM

import glob
import os
import sys
import re
import subprocess
import numpy as np
# {
# DEXCS2021だと，以下がないとfrom dictParse import DictParserでエラーが出る
if os.path.dirname(__file__) not in ([i.encode('UTF-8') if type(i) is unicode else i
    for i in sys.path] if sys.version_info.major <= 2 else sys.path):
    sys.path.append(os.path.dirname(__file__))
# }
from dictParse import DictParser
from dictParse import DictParserList
import folderTime
import setFuncsInCD

path_binDEXCS = os.path.expanduser('~/Desktop/binDEXCS2019（解析フォルダを端末で開いてから）') # dakuten.py -j -f <path> で濁点を結合しておく

if os.path.exists('/opt/OpenFOAM/OpenFOAM-v1906/etc/bashrc'):
    dexcs_version = '2019'
elif os.path.exists('/usr/lib/openfoam/openfoam2106/etc/bashrc'):
    dexcs_version = '2021'
else:
    dexcs_version = None
assert dexcs_version is not None

def showDirForPresentAnalysis(file = __file__, path = os.getcwd()):
    # https://qiita.com/PruneMazui/items/8a023347772620025ad6
    print('\033[7;1m----- 現在の解析フォルダは {} です． -----\033[m'.format(path))
    # https://joppot.info/2013/12/17/235, http://tldp.org/HOWTO/Xterm-Title-3.html
    print('\033]2;{} - {}\007'.format(path, os.path.basename(file)))

def execParaFoam(touch_only = False):
    for f in glob.iglob('*.OpenFOAM' if dexcs_version == '2019' else '*.foam'):
        os.remove(f)
    subprocess.call('paraFoam -touch-all', shell = True)
    # Usage: paraFoam [OPTION] [--] [PARAVIEW_OPTION]
    # options:
    #   -block            Use blockMesh reader (.blockMesh extension)
    #   -case <dir>       Specify alternative case directory, default is the cwd
    #   -region <name>    Specify alternative mesh region
    #   -touch            Create the file (eg, .blockMesh, .OpenFOAM, .foam, ...)
    #   -touch-all        Create .blockMesh, .foam, .OpenFOAM files (for all regions)
    #   -touch-proc       Same as '-touch' but for each processor
    #   -vtk              Use VTK builtin OpenFOAM reader (.foam extension)
    #   --help            Display ParaView help
    #   -help             Display short help and exit
    #   -help-full        Display full help and exit
    for p in ('*.blockMesh', '*.foam' if dexcs_version == '2019' else '*.OpenFOAM'):
        for f in glob.iglob(p):
            os.remove(f)
    if not touch_only:
        subprocess.call('paraFoam', shell = True)

def execCheckMesh():
    for f in ('checkMesh.log', 'checkMesh.logfile'):
        if os.path.isfile(f):
            os.remove(f)
    command = 'checkMesh -noFunctionObjects | tee checkMesh.log'
    if subprocess.call(command, shell = True) != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)
    print('{}が終わりました．\033[3;4;5m全ての項目のチェック結果がOKでないとたぶん計算がうまくいきません．\033[m'.format(command))

def setTimeBeginEnd(action):
    first_time = float(folderTime.firstTime())
    latest_time = float(folderTime.latestTime())
    while True:
        time_begin = (raw_input if sys.version_info.major <= 2 else input)(
            '{}を開始する時間を入力して下さい． ({} ~ {}, Enterのみ: {}) > '.format(
            action, first_time, latest_time, first_time)).strip()
        if time_begin == '':
            time_begin = '-inf'
            break
        else:
            try:
                time_begin = str(float(time_begin))
                break
            except ValueError:
                pass
    while True:
        time_end = (raw_input if sys.version_info.major <= 2 else input)(
            '{}を終了する時間を入力して下さい． (Enterのみ: {}) > '.format(action, latest_time)).strip()
        if time_end == '':
            time_end = 'inf'
            break
        else:
            try:
                time_end = str(float(time_end))
                break
            except ValueError:
                pass
    noZero = (False if (raw_input if sys.version_info.major <= 2 else input)(
        '0秒のデータを含めますか？ (y/n, 多くの場合nのはず) > ').strip().lower() == 'y' else True)
    return time_begin, time_end, noZero

def getApplication():
    if sys.version_info.major <= 2:
        return subprocess.check_output('foamDictionary -entry application -value system/controlDict',
            shell = True).rstrip()
    else:
        return subprocess.check_output('foamDictionary -entry application -value system/controlDict',
            shell = True, encoding = 'UTF-8').rstrip()

def execPostProcess(time_begin = '-inf', time_end = 'inf', noZero = True, func = None, region = None, solver = True):
    if solver:
        command = getApplication() + ' -postProcess'
    else:
        command = 'postProcess'
    if func is not None:
        command += ' -func "' + func + '"'
    if region is not None:
        command += ' -region ' + region
    if noZero:
        command += ' -noZero'
    if float(time_begin) != float('-inf') or float(time_end) != float('inf'):
        command += " -time '"
        if float(time_begin) != float('-inf'):
            command += time_begin
        command += ':'
        if float(time_end) != float('inf'):
            command += time_end
        command += "'"
    if subprocess.call(command, shell = True) != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)
    if func is None:
        setFuncsInCD.setAllEnabled(False)
    return command

def removePatchesHavingNoFaces():
    converted_millimeter_into_meter = isConvertedMillimeterIntoMeter()
    createPatchDict = os.path.join('system', 'createPatchDict')
    createPatchDict_bak = createPatchDict + '_bak'
    if os.path.isfile(createPatchDict):
        os.rename(createPatchDict, createPatchDict_bak)
    with open(createPatchDict, 'w') as f:
        f.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tdictionary;\n')
        f.write('\tlocation\t"system";\n')
        f.write('\tobject\tcreatePatchDict;\n')
        f.write('}\n')
        f.write('pointSync\tfalse;\n')
        f.write('patches\t();\n')
    command = 'createPatch -overwrite'
    r = subprocess.call(command, shell = True)
    os.remove(createPatchDict)
    if os.path.isfile(createPatchDict_bak):
        os.rename(createPatchDict_bak, createPatchDict)
    if r != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)
    if converted_millimeter_into_meter:
        writeConvertedMillimeterIntoMeter()

def isConvertedMillimeterIntoMeter():
    boundary = os.path.join('constant', 'polyMesh', 'boundary')
    with open(boundary, 'r') as f:
        s = f.read()
    #           01234567890123456789012345678901234
    i = s.find('// converted millimeter into meter')
    if i != -1:
        if i == 0:
            with open(boundary, 'w') as f:
                f.write(s[34:].lstrip())
            writeConvertedMillimeterIntoMeter()
        return True
    else:
        return False

def writeConvertedMillimeterIntoMeter():
    boundary = os.path.join('constant', 'polyMesh', 'boundary')
    with open(boundary, 'r') as f:
        s = f.read()
    m = re.search(r'// (\* )+//\n', s)
    if m is not None:
        s = s[:m.end()] + '// converted millimeter into meter\n' + s[m.end():]
    else:
        s = s.rstrip() + '\n// converted millimeter into meter\n'
    with open(boundary, 'w') as f:
        f.write(s)

def convertLengthUnitInMillimeterToMeter():
    command = 'transformPoints -scale 0.001'
    if subprocess.call(command, shell = True) != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)
    boundary = os.path.join('constant', 'polyMesh', 'boundary')
    writeConvertedMillimeterIntoMeter()
    print('長さの単位をミリメートルからメートルに変換しました．')

def wasRenumberMeshDone():
    boundary = os.path.join('constant', 'polyMesh', 'boundary')
    with open(boundary, 'r') as f:
        s = f.read()
    #           0123456789012345678901234
    i = s.find('// renumberMesh was done')
    if i != -1:
        if i == 0:
            with open(boundary, 'w') as f:
                f.write(s[24:].lstrip())
            writeRenumberMeshWasDone()
        return True
    else:
        return False

def writeRenumberMeshWasDone():
    boundary = os.path.join('constant', 'polyMesh', 'boundary')
    with open(boundary, 'r') as f:
        s = f.read()
    m = re.search(r'// (\* )+//\n', s)
    if m is not None:
        s = s[:m.end()] + '// renumberMesh was done\n' + s[m.end():]
    else:
        s = s.rstrip() + '\n// renumberMesh was done\n'
    with open(boundary, 'w') as f:
        f.write(s)

def renumberMesh():
    converted_millimeter_into_meter = isConvertedMillimeterIntoMeter()
    command = 'renumberMesh -overwrite'
    if subprocess.call(command, shell = True) != 0:
        print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
        sys.exit(1)
    boundary = os.path.join('constant', 'polyMesh', 'boundary')
    writeRenumberMeshWasDone()
    if converted_millimeter_into_meter:
        writeConvertedMillimeterIntoMeter()

def box_size_of_calculation_range(points_path):
    with open(points_path, 'r') as f:
        s = f.read()
    ph = s.find('(') + 1
    pf = s.rfind(')')
    n = int(s[s[:ph - 2].rfind('\n') + 1:ph - 1])
    if 'binary' in s:
        points_data = np.fromstring(s[ph:ph + 8*3*n], dtype = '<d').reshape(-1, 3)
    else:
        if s[ph] == '\n':
            ph += 1
        points_data = np.fromstring(s[ph:pf].replace('(', '').replace(')', ''), dtype = 'd', sep = ' ').reshape(-1, 3)
        p_min = np.min(points_data, axis = 0)
        p_max = np.max(points_data, axis = 0)
    return tuple((p_min[i], p_max[i]) for i in range(3))

def texteditwx_works_well():
    if subprocess.call(os.path.join(path_binDEXCS, 'texteditwx.py') + ' -h',
        stdout = open('/dev/null', 'w'), shell = True) != 0:
        print('texteditwx.pyでエラーが発生しました．おそらく必要なモジュールがないためです．端末で')
        print('sudo apt install -y python-pexpect python-pyperclip')
        print('を行ってからもう一度やり直して下さい．')
        return False
    else:
        return True

def correctLocation():
    def correctLocationIn(file_name):
        os.chmod(file_name, 0o0666)
        dir_name = os.path.dirname(file_name)
        changed = False
        dp = DictParser(file_name)
        x = dp.getDPLForKey(['FoamFile'])
        if x is not None and DictParserList.isType(x, DictParserList.BLOCK):
            for y in x.value():
                if (DictParserList.isType(y, DictParserList.DICT) and y.key() == 'location' and
                    y.value()[0].strip('"') != dir_name):
                    changed = True
                    y.setValue(['"' + dir_name  +'"'])
                    break
        if changed:
            dp.writeFile(file_name)
    for d in ('0', 'constant', 'system'):
        if os.path.isdir(d):
            for f in glob.iglob(os.path.join(d, '*')):
                if os.path.isfile(f):
                    correctLocationIn(f)
    for d in glob.iglob(os.path.join('0', '*' + os.sep)):
        for f in glob.iglob(os.path.join(d, '*')):
            if os.path.isfile(f):
                correctLocationIn(f)
    for d in glob.iglob(os.path.join('constant', '*' + os.sep)):
        if os.path.isdir(os.path.join(d, 'polyMesh')):
            for f in glob.iglob(os.path.join(d, '*')):
                if os.path.isfile(f):
                    correctLocationIn(f)
    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
        if os.path.isfile(os.path.join(d, 'fvSolution')):
            for f in glob.iglob(os.path.join(d, '*')):
                if os.path.isfile(f):
                    correctLocationIn(f)

if __name__ == '__main__':
#    showDirForPresentAnalysis()
#    execParaFoam()
    texteditwx_works_well()
