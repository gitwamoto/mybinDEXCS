#!/usr/bin/env python
# -*- coding: utf-8 -*-
# misc.py
# by Yukiharu Iwamoto
# 2026/5/12 3:17:15 PM

import glob
import os
import sys
import re
import subprocess
import numpy as np
# このファイルの中の関数を呼び出すプログラムから，このファイルを含むフォルダが見えるようにする．
if os.path.dirname(__file__) not in sys.path:
    sys.path.append(os.path.dirname(__file__))
import dictParse

binDEXCS_path = os.path.expanduser('~/Desktop/binDEXCS（解析フォルダを端末で開いてから）') # dakuten.py -j -f <path> で濁点を結合しておく

if os.path.exists('/opt/OpenFOAM/OpenFOAM-v1906/etc/bashrc'):
    dexcs_version = '2019'
elif os.path.exists('/usr/lib/openfoam/openfoam2106/etc/bashrc'):
    dexcs_version = '2021'
else:
    dexcs_version = None
assert dexcs_version is not None

def showDirForPresentAnalysis(file = __file__, path = os.getcwd()):
    # https://qiita.com/PruneMazui/items/8a023347772620025ad6
    print(f'\033[7;1m----- 現在の解析フォルダは {path} です． -----\033[m')
    # https://joppot.info/2013/12/17/235, http://tldp.org/HOWTO/Xterm-Title-3.html
    print(f'\033]2;{path} - {os.path.basename(file)}\007')

def execParaFoam(touch_only = False, ambient = 1.0, diffuse = 0.0):
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
        setParaViewAmbientDiffuse(ambient, diffuse)
        subprocess.call('paraFoam', shell = True)
    setParaViewAmbientDiffuse(ambient, diffuse)

def setParaViewAmbientDiffuse(ambient = 1.0, diffuse = 0.0):
    paraview_json_home = os.path.expanduser('~/.config/ParaView/ParaView-UserSettings.json')
    with open(paraview_json_home, 'r') as f:
        s = f.read()
    t = re.sub(r'"Ambient"\s*:\s*[0-9.]+', f'"Ambient" : {ambient}',
            re.sub(r'"Diffuse"\s*:\s*[0-9.]+', '"Diffuse" : {diffuse}', s))
    if s != t:
        with open(paraview_json_home, 'w') as f:
            f.write(t)

def execCheckMesh():
    for f in ('checkMesh.log', 'checkMesh.logfile'):
        if os.path.isfile(f):
            os.remove(f)
    command = 'checkMesh -noFunctionObjects | tee checkMesh.log'
    if subprocess.call(command, shell = True) != 0:
        print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
        sys.exit(1)
    print(f'{command}が終わりました．\033[3;4;5m全ての項目のチェック結果がOKでないとたぶん計算がうまくいきません．\033[m')

def setTimeBeginEnd(action):
    first_time = float(firstTime())
    latest_time = float(latestTime())
    while True:
        time_begin = input(f'{action}を開始する時間を入力して下さい． '
            f'({first_time} ~ {latest_time} または l (= {latest_time}), Enterのみ: {first_time}) > ').strip()
        if time_begin == '':
            time_begin = '-inf'
            break
        elif time_begin.lower().startswith('l'):
            time_begin = 'latestTime'
            break
        else:
            try:
                time_begin = str(float(time_begin))
                break
            except ValueError:
                pass
    while True:
        time_end = input(f'{action}を終了する時間を入力して下さい． (Enterのみ: {latest_time}) > ').strip()
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
    return subprocess.check_output('foamDictionary -entry application -value system/controlDict',
        shell = True, encoding = 'UTF-8').rstrip()

def execPostProcess(time_begin = '-inf', time_end = 'inf', noZero = True, func = None, region = None, solver = True):
    if solver:
        command = getApplication() + ' -postProcess'
    else:
        command = 'postProcess'
    if func is not None:
        command += f' -func "{func}"'
    if region is not None:
        command += f' -region {region}'
    if noZero:
        command += ' -noZero'
    if time_begin.lower().startswith('l') or time_end.lower().startswith('l'):
        command += ' -latestTime'
    elif float(time_begin) != float('-inf') or float(time_end) != float('inf'):
        command += " -time '"
        if float(time_begin) != float('-inf'):
            command += time_begin
        command += ':'
        if float(time_end) != float('inf'):
            command += time_end
        command += "'"
    if subprocess.call(command, shell = True) != 0:
        print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
        sys.exit(1)
    if func is None:
        setEnabledInControlDictFunctions(enabled = False)
    return command

def writeCommentInBoundary(comment):
    boundary_path = os.path.join('constant', 'polyMesh', 'boundary')
    boundary = dictParse.DictParser(file_name = boundary_path)
    i = boundary.find_element([{'except type': 'whitespace|linebreak'}],
        start = boundary.find_element([{'type': 'list'}])['index'] - 1,
        reverse = True, index_not_found = 0)['index']
    boundary['value'][i:i] = dictParse.DictParser(string =
        f'\n// {comment}' if i > 0 else f'// {comment}\n')['value']
    with open(boundary_path, 'w') as f:
        f.write(dictParse.normalize(string = boundary.file_string())[0])

def removePatchesHavingNoFaces():
    converted_millimeter_into_meter = isConvertedMillimeterIntoMeter()
    createPatchDict = os.path.join('system', 'createPatchDict')
    createPatchDict_bak = f'{createPatchDict}_bak'
    if os.path.isfile(createPatchDict):
        os.rename(createPatchDict, createPatchDict_bak)
    with open(createPatchDict, 'w') as f:
        f.write('FoamFile\n'
            '{\n'
            '\tversion\t2.0;\n'
            '\tformat\tascii;\n'
            '\tclass\tdictionary;\n'
            '\tlocation\t"system";\n'
            '\tobject\tcreatePatchDict;\n'
            '}\n'
            'pointSync\tfalse;\n'
            'patches\t();\n')
    command = 'createPatch -overwrite'
    r = subprocess.call(command, shell = True)
    os.remove(createPatchDict)
    if os.path.isfile(createPatchDict_bak):
        os.rename(createPatchDict_bak, createPatchDict)
    if r != 0:
        print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
        sys.exit(1)
    if converted_millimeter_into_meter:
        writeCommentInBoundary('converted millimeter into meter')

def isConvertedMillimeterIntoMeter():
    boundary_path = os.path.join('constant', 'polyMesh', 'boundary')
    with open(boundary_path, 'r') as f:
        s = f.read()
    return s.find('// converted millimeter into meter') != -1

def writeConvertedMillimeterIntoMeter():
    writeCommentInBoundary('converted millimeter into meter')

def convertMillimeterIntoMeter():
    command = 'transformPoints -scale 0.001'
    if subprocess.call(command, shell = True) != 0:
        print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
        sys.exit(1)
    writeConvertedMillimeterIntoMeter()
    print('長さの単位をミリメートルからメートルに変換しました．')

def isRenumberMeshDone():
    boundary_path = os.path.join('constant', 'polyMesh', 'boundary')
    with open(boundary_path, 'r') as f:
        s = f.read()
    return s.find('// renumberMesh was done') != -1

def writeRenumberMeshWasDone():
    writeCommentInBoundary('renumberMesh was done')

def renumberMesh():
    converted_millimeter_into_meter = isConvertedMillimeterIntoMeter()
    command = 'renumberMesh -overwrite'
    if subprocess.call(command, shell = True) != 0:
        print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
        sys.exit(1)
    writeRenumberMeshWasDone()
    if converted_millimeter_into_meter:
        writeConvertedMillimeterIntoMeter()

def bounding_box_of_calculation_range(points_path):
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
    return n, tuple((p_min[i], p_max[i]) for i in range(3))

def texteditwx_works_well():
    if subprocess.call(os.path.join(binDEXCS_path, 'texteditwx.py') + ' -h',
        stdout = open('/dev/null', 'w'), shell = True) != 0:
        print('texteditwx.pyでエラーが発生しました．おそらく必要なモジュールがないためです．端末で')
        print('sudo apt install -y python-pexpect python-pyperclip')
        print('を行ってからもう一度やり直して下さい．')
        return False
    else:
        return True

def correctLocation():
    def correctLocationIn(file_name):
        os.chmod(file_name, 0o0666) # 誰でも（所有者・グループ・その他全員）読み書きができるが、実行権限（x）はない
        parser = dictParse.DictParser(file_name = file_name)
        FoamFile = parser.find_element([{'type': 'block', 'key': 'FoamFile'}])['element']
        if FoamFile is None:
            return
        location = FoamFile.find_element([{'type': 'dictionary', 'key': 'location'}])['element']
        if location is not None:
            i = location.find_element([{'except type': 'ignorable'}])
            i['parent']['value'][i['index']:i['index'] + 1] = dictParse.DictParser(string =
                '"' + os.path.dirname(file_name) + '"')['value']
        string = dictParse.normalize(string = parser.file_string())[0]
        if parser.string != string:
#            os.rename(file_name, f'{file_name}_bak')
            with open(file_name, 'w') as f:
                f.write(string)

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

def cpu_count():
    if sys.version_info.major <= 2:
        import multiprocessing
        return multiprocessing.cpu_count()
    else:
        return len(os.sched_getaffinity(0))

def volFieldList(path = os.curdir):
    fields = []
    for i in os.listdir(path):
        tmp = os.path.join(path, i)
        if os.path.isfile(tmp) and os.sep + '.' not in tmp:
            vol_field = False
            for line in open(tmp, 'r'):
                if 'volScalarField' in line or 'volVectorField' in line:
                    vol_field = True
                    break
                elif 'surfaceScalarField' in line or 'surfaceVectorField' in line:
                    break
            if vol_field:
                fields.append(i)
    return fields

def firstTime(path = os.curdir):
    t = timesFolders(path)
    return None if len(t) == 0 else t[0]

def latestTime(path = os.curdir):
    t = timesFolders(path)
    return None if len(t) == 0 else t[-1]

def timesFolders(path = os.curdir):
    times = []
    for i in os.listdir(path):
        if os.path.isdir(os.path.join(path, i)):
            try:
                times.append([i, float(i)])
            except:
                pass
    return [i[0] for i in sorted(times, key = lambda x: x[1])]

def setEnabledInControlDictFunctions(enabled = True, type_name = None, path = os.curdir):
    controlDict_path = os.path.join(path, 'system', 'controlDict')
    controlDict = dictParse.DictParser(file_name = controlDict_path)

    functions = controlDict.find_element([{'type': 'block', 'key': 'functions'}])['element']
    if function is None:
        return
    yesno = 'yes' if enabled else 'no'
    for f in functions.find_all_elements([{'type': 'block'}]):
        f = f['element']
        t = f.find_element([{'type': 'dictionary', 'key': 'type'}])
        if t['element'] is None:
            print(f'エラー: ファイル{controlDict_path}のfunctionsで，typeがない項目があります．')
            sys.exit(1)
        if type_name is not None and t['element'].find_element(
            [{'type': 'word', 'value': type_name}])['element'] is None:
            continue
        e = f.find_element([{'type': 'dictionary', 'key': 'enabled'}])['element']
        if e is None:
            i = f.find_element([{'type': 'dictionary', 'except key': 'libs'}],
                start = t['index'] + 1, index_not_found = t['index'])['index'] + 1
            f['value'][i:i] = dictParse.DictParser(string = '\n'
                f'enabled\t{yesno}; yesで実行\n')['value']
        else:
            e['value'][e.find_element([{'type': 'word'}])['index']] = yesno

    string = dictParse.normalize(string = controlDict.file_string())[0]
    if type_name is None:
        if enabled:
            string = dictParse.re_sub_in_comments(
                r'//[ \t]*!!DISABLED!![ \t]*(#includeFunc)(?=[ \t])', r'\1', string)
        else:
            string = dictParse.re_sub_except_comments(
                r'(?<!\S)(#includeFunc)(?=[ \t])', r'// !!DISABLED!! \1', string)
    else:
        if enabled:
            string = dictParse.re_sub_in_comments(
                f'//[ \\t]*!!DISABLED!![ \\t]*(#includeFunc[ \\t]+{type_name})', r'\1', string)
        else:
            string = dictParse.re_sub_except_comments(
                f'(?<!\\S)(#includeFunc[ \\t]+{type_name})', r'// !!DISABLED!! \1', string)
    if controlDict.string != string:
#        os.rename(controlDict_path, f'{controlDict_path}_bak')
        with open(controlDict_path, 'w') as f:
            f.write(string)

def controlDictFunctionsList(path = os.curdir):
    controlDict_path = os.path.join(path, 'system', 'controlDict')
    controlDict = dictParse.DictParser(file_name = controlDict_path)

    enable_function_list = []
    disable_function_list = []
    functions = controlDict.find_element([{'type': 'block', 'key': 'functions'}])['element']
    if function is None:
        return enable_function_list, disable_function_list
    for f in functions.find_all_elements([{'type': 'block'}]):
        f = f['element']
        t = f.find_element([{'type': 'dictionary', 'key': 'type'}])['element']
        if t is None:
            print(f'エラー: ファイル{controlDict_path}のfunctionsで，typeがない項目があります．')
            sys.exit(1)
        type_name = t.find_element([{'type': 'word'}])['element']['value']
        e = f.find_element([{'type': 'dictionary', 'key': 'enabled'}])['element']
        if (e is None or e.find_element([{'type': 'word'}])['element']['value'] in ('yes', 'true', 'on')):
            enable_function_list.append(type_name)
        else:
            disable_function_list.append(type_name)

    string = dictParse.normalize(string = controlDict.file_string())[0]
    enable_function_list.extend(
        dictParse.re_findall_except_comments(r'(?<!\S)#includeFunc\s+([^;]+);', string))
    disable_function_list.extend(
        dictParse.re_findall_in_comments(r'//\s*!!DISABLED!!\s*(#includeFunc\s+([^;]+);', string))
    return enable_function_list, disable_function_list

if __name__ == '__main__':
    print('firstTime = ' + firstTime())
    print('latestTime = ' + latestTime())

if __name__ == '__main__':
#    showDirForPresentAnalysis()
#    execParaFoam()
    texteditwx_works_well()
