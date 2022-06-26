#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 計算.py
# by Yukiharu Iwamoto
# 2022/6/26 3:00:42 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行
# -d -> 0秒以外のフォルダがある場合，それらを消す．つまり0秒から計算をやり直す
# -e -> 計算が発散した場合，時間ステップを小さくして計算を続ける
# -f -> system/controlDictに書かれているfunctionsの内容を計算中に実行する
# -i log10_dt_max log10_dt_min -> ならし計算を行う．時間ステップが10^log10_dt_minから10^log10_dt_maxの間を試す
#                                 ※0秒以外のフォルダがあると，ならし計算はできない
# （現在は無効なオプション）-o -> 初期流れ場をpotentialFoamで作成する
# -p -> paraFoamを実行する
# -r domains -> 計算領域をdomains個に分割して並列計算を行う，1だと普通の計算

# ---- 戻り値 ----
# 0: 正常終了
# 1: エラーで終了
# 2: 発散で終了

import os
import shutil
import glob
import sys
import signal
import subprocess
import re
from datetime import datetime
import filecmp
import multiprocessing
import GPyOpt
import numpy as np
from utilities import misc
from utilities.dictParse import DictParser, DictParserList
from utilities import dictFormat
from utilities import folderTime
from utilities import appendEntries
from utilities import rmObjects

domains = 1
with_function_objects = False
sigFpe_is_found = False
controlDict = os.path.join('system', 'controlDict')
regionProperties = os.path.join('constant', 'regionProperties')
boundary = os.path.join('constant', 'polyMesh', 'boundary')
bounds_idle = [
    {'name': 'nAlphaSubCycles', 'type': 'discrete', 'domain': range(1, 21)},
    {'name': 'tolerance', 'type': 'continuous', 'domain': (1.0e-04, 1.0)},
    {'name': 'relTol', 'type': 'continuous', 'domain': (1.0e-04, 1.0)},
    {'name': 'nCorrectors', 'type': 'discrete', 'domain': range(1, 4)},
    {'name': 'momentumPredictor', 'type': 'discrete', 'domain': (0, 1)},
    {'name': 'nNonOrthogonalCorrectors', 'type': 'discrete', 'domain': range(0, 4)},
    {'name': 'relaxationFactors_fields', 'type': 'continuous', 'domain': (0.01, 1.0)},
    {'name': 'relaxationFactors_equations', 'type': 'continuous', 'domain': (0.01, 1.0)},
    {'name': 'deltaT', 'type': 'discrete', 'domain': (None, None)}
]
idle_calc_report_txt = 'idle_calc_report.txt'
best_steps_idle = 0
best_folder_idle = None
best_folder_idle_suffix = '_best_idle_calc'

def handler(signal, frame):
    if domains != 1:
        if best_folder_idle is None:
            command = 'reconstructPar -newTimes -noFunctionObjects'
            if os.path.exists(regionProperties):
                command += ' -allRegions'
            subprocess.call(command, shell = True)
            rmObjects.removeProcessorDirs('noLatest')
        else:
            subprocess.call('foamListTimes -rm -noZero', shell = True)
            if domains != 1:
                rmObjects.removeProcessorDirs('noZero')
            shutil.move(best_folder_idle, best_folder_idle[:-len(best_folder_idle_suffix)])
    if os.path.isdir('0_bak'):
        if os.path.isdir('0'):
            shutil.rmtree('0')
        shutil.move('0_bak', '0')
    rmObjects.removeInessentials()
    sys.exit(1)

def potentialFoam(latest_time):
    p_potentialflow = os.path.join(latest_time, 'p_potentialflow')
    p = os.path.join(latest_time, 'p')
    p_bak = os.path.join(latest_time, 'p_bak')
    if domains == 1:
        has_p_potentialflow = os.path.isfile(p_potentialflow)
    else:
        has_p_potentialflow = False
        #                    0123456789
        for d in glob.iglob('processor*' + os.sep):
            try:
                int(d[9:-len(os.sep)])
                pp = os.path.join(d, p_potentialflow)
                if os.path.isfile(pp):
                    has_p_potentialflow = True
                    os.rename(pp, os.path.join(d, p))
            except:
                pass
    if has_p_potentialflow:
        if os.path.isfile(p):
            os.rename(p, p_bak)
        if os.path.isfile(p_potentialflow):
            os.rename(p_potentialflow, p)
    command = 'potentialFoam' if domains == 1 else 'mpirun -np {} potentialFoam -parallel'.format(domains)
    command += ' -writep -writePhi -noFunctionObjects | tee potentialFoam.log'
    if subprocess.call(command, shell = True) == 0:
        if os.path.isfile(p_bak): # has_p_potentialflow
            changeDictionaryDict = os.path.join('system', 'changeDictionaryDict')
            changeDictionaryDict_bak = changeDictionaryDict + '_bak'
            if os.path.isfile(changeDictionaryDict):
                os.rename(changeDictionaryDict, changeDictionaryDict_bak)
            with open(os.path.join('system', 'changeDictionaryDict'), 'w') as f:
                f.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tdictionary;\n')
                f.write('\tlocation\t"system";\n')
                f.write('\tobject\tchangeDictionaryDict;\n')
                f.write('}\n')
                f.write('p\n')
                f.write('{\n')
                dp = DictParser(p_bak)
                dp.writeContents(dp.getDPLForKey(['boundaryField']), f, indent = '\t', last_char = '\n')
                f.write('\n}\n')
            command = 'changeDictionary' if domains == 1 else 'mpirun -np {} changeDictionary -parallel'.format(domains)
            command += ' -enableFunctionEntries'
            if subprocess.call(command, shell = True) == 0:
                os.remove(changeDictionaryDict)
            else:
                print('エラー: potentialFoamは成功しましたが，pの境界条件を希望するものに修正できませんでした．')
                if os.path.isdir('0_bak'):
                    if os.path.isdir('0'):
                        shutil.rmtree('0')
                    shutil.move('0_bak', '0')
                sys.exit(1)
            if os.path.isfile(changeDictionaryDict_bak):
                os.rename(changeDictionaryDict_bak, changeDictionaryDict)
            os.remove(p_bak)
        if domains != 1:
            command = "reconstructPar -withZero -time '{}' -noFunctionObjects".format(latest_time)
            if os.path.exists(regionProperties):
                command += ' -allRegions'
            subprocess.call(command, shell = True)
            #                 43210987654321
        for d in glob.iglob('*_potentialflow' + os.sep):
            try:
                float(d[:-14 - len(os.sep)])
                shutil.rmtree(d)
            except:
                pass
        shutil.copytree(latest_time, latest_time + '_potentialflow')
    else:
        print('初期流れ場をpotentialFoamで作成できませんでした．')

def calculate():
    for i in ('PyFoam*', '*.logfile', '*.logfile.restart*', 'log.*'):
        for f in glob.iglob(i):
            os.remove(f)
    command = ('pyFoamPlotRunner.py ' +
        '--hardcopy ' +
        '--non-persist ' +
        '--no-pickled-file ' +
        '--with-courant ' +
        '--with-deltat ' +
        '--frequency=10.0 ')
    if domains != 1:
        command += '--autosense-parallel '
    command += misc.getApplication()
    if not with_function_objects:
        command += ' -noFunctionObjects'
    subprocess.call(command, shell = True)
    with open('PyFoamRunner.' + application + '.logfile', 'r') as f:
        s = f.read()
    global sigFpe_is_found
    sigFpe_is_found = False if s.rfind('Foam::sigFpe::sigHandler(int)') == -1 else True
    i = s.find('\nCreate mesh for time = ')
    if i == -1:
        return -10
    i += 24
    time_begin = float(s[i:s.find('\n', i)])
    i = s.find('\nTime = ', i)
    if i == -1:
        return 0
    i += 8
    time_next = float(s[i:s.find('\n', i)])
    if time_next == time_begin:
        return -1
    i = s.rfind('\nTime = ') + 8 # not find but rfind!
    time_end = float(s[i:s.find('\n', i)])
    return int((time_end - time_begin)/(time_next - time_begin))

def make_dict_idle(x):
    return {
        bounds_idle[0]['name']: int(x[0]),
        bounds_idle[1]['name']: x[1],
        bounds_idle[2]['name']: x[2],
        bounds_idle[3]['name']: int(x[3]),
        bounds_idle[4]['name']: 'yes' if x[4] else 'no',
        bounds_idle[5]['name']: int(x[5]),
        bounds_idle[6]['name']: x[6],
        bounds_idle[7]['name']: x[7],
        bounds_idle[8]['name']: x[8],
        'stopAt': 'endTime',
        'endTime': 10000.0*x[8],
        'writeControl': 'timeStep',
        'writeInterval': 10,
        'purgeWrite': 2,
    }

def calculate_idle(x):
    dict_idle = make_dict_idle(x[0])
    modify_dicts_for_idle(dict_idle)
    date_time_now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    with open(idle_calc_report_txt, 'a') as f:
        f.write(date_time_now)
        for b in bounds_idle:
            f.write('\t' + str(dict_idle[b['name']]))
    steps = calculate()
    with open(idle_calc_report_txt, 'a') as f:
        f.write('\t{}\n'.format(steps))
    global best_steps_idle
    if best_steps_idle < steps:
        best_steps_idle = steps
        if domains != 1:
            command = 'reconstructPar -latestTime -noFunctionObjects'
            if os.path.exists(regionProperties):
                command += ' -allRegions'
            subprocess.call(command, shell = True)
        latest_time = folderTime.latestTime()
        if float(latest_time) > 0.0:
            with open(os.path.join(latest_time, idle_calc_report_txt), 'w') as f:
                f.write('datetime: ' + date_time_now + '\n')
                for b in bounds_idle:
                    f.write(b['name'] + ': ' + str(dict_idle[b['name']]) + '\n')
                f.write('steps: {}\n'.format(steps))
            #                     543210987654321
            for d in glob.iglob('*' + best_folder_idle_suffix + os.sep):
                try:
                    float(d[:-15 - len(os.sep)])
                    shutil.rmtree(d)
                except:
                    pass
            global best_folder_idle
            best_folder_idle = latest_time + best_folder_idle_suffix
            shutil.move(latest_time, best_folder_idle)
    subprocess.call('foamListTimes -rm -noZero', shell = True)
    if domains != 1:
        rmObjects.removeProcessorDirs('noZero')
    return steps

def remove_entires_in_DPL(contents, comment):
    i = 0
    while i < len(contents):
        x = contents[i]
        if DictParserList.isType(x, DictParserList.DICT):
            if re.search(comment, x[-1]) is not None:
                del contents[i]
                if i < len(contents) and type(contents[i]) is str and contents[i].startswith('\n'):
                    contents[i] = contents[i][1:]
        elif DictParserList.isType(x, DictParserList.BLOCK):
            remove_entires_in_DPL(x.value(), comment)
        i += 1

def remove_unnecessary_entires_in_controlDict():
    dp = DictParser(controlDict)
    s_old = dp.toString()
    startFrom = dp.getValueForKey(['startFrom'])
    if startFrom is None:
        print('エラー: {}ファイルでstartFromが指定されていません．'.format(controlDict))
        if os.path.isdir('0_bak'):
            if os.path.isdir('0'):
                shutil.rmtree('0')
            shutil.move('0_bak', '0')
        sys.exit(1)
    if startFrom[0] != 'latestTime':
        dp.setValueForKey(['startFrom'], ['latestTime'])
        print('!!! {}ファイルのstartFromをlatestTimeに書き換えました．'.format(controlDict))
    remove_entires_in_DPL(dp.contents, r'^/\* (\(DECREASED\) time step from .+|idle calculation )\*/$')
    dp = dictFormat.moveLineToBottom(dp)
    s = dp.toString()
    if s != s_old:
        with open(controlDict, 'w') as f:
            f.write(s)

def remove_unnecessary_entires_in_fvSolution():
    def remove_unnecessary_entires_in(path):
        if os.path.islink(path):
            return
        dp = DictParser(path)
        s_old = dp.toString()
        remove_entires_in_DPL(dp.contents, r'^/\* idle calculation \*/$')
        dp = dictFormat.moveLineToBottom(dp)
        s = dp.toString()
        if s != s_old:
            with open(path, 'w') as f:
                f.write(s)
    remove_unnecessary_entires_in(os.path.join('system', 'fvSolution'))
    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
        fvSolution = os.path.join(d, 'fvSolution')
        if os.path.isfile(fvSolution):
            remove_unnecessary_entires_in(fvSolution)

def change_dt_in_controlDict(exponent):
    remove_unnecessary_entires_in_controlDict()
    dp = DictParser(controlDict)
    i_dt_last = i_dt = dp.getIndexOfItem(['deltaT'])[0]
    for i in range(i_dt + 1, len(dp.contents)):
        x = dp.contents[i]
        if DictParserList.isType(x, DictParserList.DICT) and x.key() == 'deltaT':
            i_dt_last = i
    x = dp.contents[i_dt_last]
    y = DictParserList(DictParserList.DICT, ['deltaT', '',
        ['#calc "pow(10.0, {})*$deltaT"'.format(exponent)],
        '/* (DECREASED) time step from ' + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + ' */'])
    dp.contents[i_dt_last + 1:i_dt_last + 1] = ['\n', y]
    dp.writeFile(controlDict)

def modify_dicts_for_idle(value_dict):
    remove_unnecessary_entires_in_controlDict()
    remove_unnecessary_entires_in_fvSolution()
    def modify_dicts_for_idle_in(path):
        if os.path.islink(path):
            return
        dp = DictParser(path)
        x = dp.getValueForKey(['solvers'])
        for y in x:
            if DictParserList.isType(y, DictParserList.BLOCK):
                has_nAlphaSubCycles = False
                for z in y.value():
                    if DictParserList.isType(z, DictParserList.DICT) and z.key() == 'nAlphaSubCycles':
                        has_nAlphaSubCycles = True
                        break
                if has_nAlphaSubCycles and 'nAlphaSubCycles' in value_dict:
                    y.value().extend([DictParserList(DictParserList.DICT,
                        ['nAlphaSubCycles', '', [str(value_dict['nAlphaSubCycles'])],
                        '/* idle calculation */']), '\n'])
                for k in ('tolerance', 'relTol'):
                    if k in value_dict:
                        y.value().extend([DictParserList(DictParserList.DICT, [k, '', [str(value_dict[k])],
                            '/* idle calculation */']), '\n'])
        for m in ('SIMPLE', 'PISO', 'PIMPLE'):
            x = dp.getValueForKey([m])
            if x is not None:
                if m in ('PISO', 'PIMPLE'):
                    if 'nCorrectors' in value_dict:
                        x.extend([DictParserList(DictParserList.DICT,
                                ['nCorrectors', '', [str(value_dict['nCorrectors'])],
                                '/* idle calculation */']), '\n'])
                for k in ('momentumPredictor', 'nNonOrthogonalCorrectors'):
                    if k in value_dict:
                        x.extend([DictParserList(DictParserList.DICT, [k, '', [str(value_dict[k])],
                            '/* idle calculation */']), '\n'])
        x = dp.getValueForKey(['relaxationFactors'])
        if x is not None:
            for y in x:
                if DictParserList.isType(y, DictParserList.BLOCK):
                    k = 'relaxationFactors_' + y.key()
                    if k in value_dict:
                        y.value().extend([DictParserList(DictParserList.DICT, ['".*"', '', [str(value_dict[k])],
                            '/* idle calculation */']), '\n'])
        dp.writeFile(path)
    modify_dicts_for_idle_in(os.path.join('system', 'fvSolution'))
    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
        fvSolution = os.path.join(d, 'fvSolution')
        if os.path.isfile(fvSolution):
            modify_dicts_for_idle_in(fvSolution)

    dp = DictParser(controlDict)
    for k in ('stopAt', 'endTime', 'deltaT', 'writeControl', 'writeInterval', 'purgeWrite'):
        if k in value_dict:
            i_last = i = dp.getIndexOfItem([k])[0]
            for j in range(i + 1, len(dp.contents)):
                x = dp.contents[j]
                if DictParserList.isType(x, DictParserList.DICT) and x.key() == k:
                    i_last = j
            dp.contents[i_last + 1:i_last + 1] = [
                '\n', DictParserList(DictParserList.DICT, [k, '', [str(value_dict[k])], '/* idle calculation */'])]
    dp.writeFile(controlDict)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler) # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = delete_folders_except_for_zero = decrease_dt_if_fpe_occured = False
        exec_potentialFoam = exec_paraFoam = idle_calculation = False
        log10_dt_max = log10_dt_min = None
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-N': # Non-interactive
                pass
            elif sys.argv[i] == '-d':
                delete_folders_except_for_zero = True
            elif sys.argv[i] == '-e':
                decrease_dt_if_fpe_occured = True
            elif sys.argv[i] == '-f':
                with_function_objects = True
            elif sys.argv[i] == '-i':
                i += 1
                log10_dt_max = int(sys.argv[i])
                i += 1
                log10_dt_min = int(sys.argv[i])
            elif sys.argv[i] == '-o':
                exec_potentialFoam = True
            elif sys.argv[i] == '-p':
                exec_paraFoam = True
            elif sys.argv[i] == '-r':
                i += 1
                domains = max(int(sys.argv[i]), 1)
            i += 1

    for f in (controlDict, os.path.join('system', 'fvSolution'), boundary):
        if not os.path.isfile(f):
            print('エラー: {}ファイルがありません．'.format(f))
            sys.exit(1)

    for p in ('*.foam', '*.OpenFOAM', '*.blockMesh'):
        for f in glob.iglob(p):
            os.remove(f)
    if os.path.isdir('dynamicCode'):
        shutil.rmtree('dynamicCode')
    misc.execParaFoam(touch_only = True)
    misc.correctLocation()

    for f in glob.iglob(os.path.join('0', '*.old')):
        shutil.move(f, f[:-4])

    if os.path.isdir('0_bak'):
        def count_dcmp(dcmp):
            c = len(dcmp.left_only) + len(dcmp.right_only) + len(dcmp.diff_files)
            for sub_dcmp in dcmp.subdirs.values():
                c += count_dcmp(sub_dcmp)
            return c
        if count_dcmp(filecmp.dircmp('0', '0_bak')) > 0:
            print('エラー: あるはずがない0_bakフォルダがあります．')
            print('0フォルダと0_bakフォルダを比較して，正しい方を0フォルダに置き換えてから再実行して下さい．')
            sys.exit(1)
        else:
            shutil.rmtree('0_bak')

    shutil.copytree('0', '0_bak')
    remove_unnecessary_entires_in_controlDict()
    remove_unnecessary_entires_in_fvSolution()

    if os.path.isdir('processor0'):
        command = 'reconstructPar -newTimes -noFunctionObjects'
        if os.path.exists(regionProperties):
            command += ' -allRegions'
        subprocess.call(command, shell = True)
    latest_time = folderTime.latestTime()
    if latest_time is None:
        print('エラー: 結果フォルダがありません．')
        if os.path.isdir('0_bak'):
            if os.path.isdir('0'):
                shutil.rmtree('0')
            shutil.move('0_bak', '0')
        sys.exit(1)
    if float(latest_time) != 0.0:
        if interactive:
            delete_folders_except_for_zero = True if (raw_input if sys.version_info.major <= 2 else input)(
                '0秒以外のフォルダがあります．消して0秒からやり直しますか？ (y/n) > ').strip().lower() == 'y' else False
        if delete_folders_except_for_zero:
            subprocess.call('foamListTimes -rm -noZero', shell = True)
            rmObjects.removeProcessorDirs()
            latest_time = '0'
        else:
            rmObjects.removeProcessorDirs('' if not os.path.isdir(os.path.join('processor0', latest_time))
                else 'noLatest')

    renumberMesh_was_done = misc.wasRenumberMeshDone()
    if not renumberMesh_was_done:
        misc.renumberMesh()

    for i in ('dynamicCode', 'postProcessing', 'logs'):
        if os.path.isdir(i):
            shutil.rmtree(i)
    rmObjects.removeLogPlotPngs()
    rmObjects.removePyFoamPlots()

    threads = multiprocessing.cpu_count()
    if interactive:
        while True:
            try:
                domains = max(int((raw_input if sys.version_info.major <= 2 else input)(
                    '計算領域を何個に分割して並列計算しますか？ ({}個まで, 1だと普通の計算) > '.format(threads)).strip()), 1)
                break
            except ValueError:
                pass
    domains = min(domains, threads)
    if domains != 1:
        processor_dirs = set()
        #                    0123456789
        for d in glob.iglob('processor*' + os.sep):
            try:
                processor_dirs.add(int(d[9:-len(os.sep)]))
            except:
                pass
        if len(processor_dirs) != domains or processor_dirs != set(range(domains)):
            for d in processor_dirs:
                shutil.rmtree('processor{}'.format(d))
        if not os.path.isdir('processor0'):
            decomposeParDict = os.path.join('system', 'decomposeParDict')
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
            for d in glob.iglob(os.path.join('system', '*' + os.sep)):
                if os.path.isfile(os.path.join(d, 'fvSolution')):
                    os.chdir(d)
                    if os.path.exists('decomposeParDict'):
                        os.remove('decomposeParDict')
                    os.symlink(os.path.join(os.pardir, 'decomposeParDict'), 'decomposeParDict') # can't overwrite
                    os.chdir(os.path.join(os.pardir, os.pardir))
            command = 'decomposePar -latestTime -noFunctionObjects'
            if os.path.exists(regionProperties):
                command += ' -allRegions'
            if subprocess.call(command, shell = True) != 0:
                print('{}で失敗しました．よく分かる人に相談して下さい．'.format(command))
                if os.path.isdir('0_bak'):
                    if os.path.isdir('0'):
                        shutil.rmtree('0')
                    shutil.move('0_bak', '0')
                sys.exit(1)

    appendEntries.intoFvSolution()
    appendEntries.intoFvSchemes()
    appendEntries.intoControlDict()
    for f in ('potentialFoam.log', 'potentialFoam.logfile'):
        if os.path.isfile(f):
            os.remove(f)
#    if interactive:
#        print('初期流れ場をpotentialFoamで作成しますか？')
#        exec_potentialFoam = True if (raw_input if sys.version_info.major <= 2 else input)(
#            'もしp_potentialflowという名前のファイルがある場合，' +
#            'そのファイルに書かれている境界条件をpの境界条件に使います． (y/n) > ').strip().lower() == 'y' else False
#    if exec_potentialFoam:
#        potentialFoam(latest_time)

    if interactive:
        with_function_objects = True if (raw_input if sys.version_info.major <= 2 else input)(
            '{}に書かれている'.format(controlDict) +
            'functionsの内容を計算中に実行しますか？ (y/n, 多くの場合nのはず) > ').strip().lower() == 'y' else False

    if float(latest_time) == 0.0:
        if interactive:
            idle_calculation = True if (raw_input if sys.version_info.major <= 2 else input)(
                'ならし計算を行いますか？ (y/n, どうしても発散する場合に試す価値あり) > '
                ).strip().lower() == 'y' else False
    else:
        idle_calculation = False

    if idle_calculation:
        subprocess.call('foamListTimes -rm -noZero', shell = True)
        if domains != 1:
            rmObjects.removeProcessorDirs('noZero')
        if interactive:
            while True:
                try:
                    log10_dt_max = int((raw_input if sys.version_info.major <= 2 else input)(
                        'log10(時間ステップの最大値)を整数で入力して下さい． > '))
                    break
                except ValueError:
                    pass
            while True:
                try:
                    log10_dt_min = int((raw_input if sys.version_info.major <= 2 else input)(
                        'log10(時間ステップの最小値)を整数で入力して下さい． > '))
                    break
                except ValueError:
                    pass
        if log10_dt_max < log10_dt_min:
            log10_dt_max, log10_dt_min = log10_dt_min, log10_dt_max
        d = {'name': 'deltaT', 'type': 'discrete', 'domain': 10.0**np.arange(log10_dt_min, log10_dt_max + 1)}
        if bounds_idle[-1]['name'] == 'deltaT':
            bounds_idle[-1] = d
        else:
            bounds_idle.append(d)
        with open(idle_calc_report_txt, 'w') as f:
            f.write('#datetime')
            for b in bounds_idle:
                f.write('\t{}'.format(b['name']))
            f.write('\tsteps\n')
        myBopt = GPyOpt.methods.BayesianOptimization(f = calculate_idle, domain = bounds_idle,
            model_type = 'GP', initial_design_numdata = 5, acquisition_type ='EI', maximize = True)
        myBopt.run_optimization(max_iter = 100)
        print('\nならし計算が終了しました．')
        if best_folder_idle is not None:
            latest_time = best_folder_idle[:-len(best_folder_idle_suffix)]
            shutil.move(best_folder_idle, latest_time)
            print('ベイズ最適化の履歴は{}に保存され，最も発散しにくかった計算条件による結果は{}秒のフォルダに保存されています．'.format(
                idle_calc_report_txt, latest_time))
        else:
            print('ベイズ最適化の履歴は{}に保存されています．'.format(idle_calc_report_txt) +
                'system/controlDictのwriteIntervalが大きかったせいか，最も発散しにくかった計算条件による結果は保存されていません．')
    else:
        if interactive:
            decrease_dt_if_fpe_occured = True if (raw_input if sys.version_info.major <= 2 else input)(
                '計算が発散した場合，時間ステップを小さくして計算を続けますか？ (y/n) > '
                ).strip().lower() == 'y' else False
        for trial in range(30):
            calculate()
            if domains != 1:
                command = 'reconstructPar -newTimes -noFunctionObjects'
                if os.path.exists(regionProperties):
                    command += ' -allRegions'
                subprocess.call(command, shell = True)
                rmObjects.removeProcessorDirs('noLatest')
            if not decrease_dt_if_fpe_occured or not sigFpe_is_found:
                break
            change_dt_in_controlDict(-trial - 1)
        if sigFpe_is_found:
            print('\n計算が発散して終了しました．')
            print('「DEXCS OpenFOAM メモ」 (0_OpenFOAMメモ.pdf) の' +
                '「発散する場合の対処法」の部分を見れば発散が回避できるかもしれません．')

    if os.path.isdir('0_bak'):
        if os.path.isdir('0'):
            shutil.rmtree('0')
        shutil.move('0_bak', '0')

    if interactive:
        exec_paraFoam = True if (raw_input if sys.version_info.major <= 2 else input)(
            '\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam)

    rmObjects.removeInessentials()
    sys.exit(2 if sigFpe_is_found else 0)
