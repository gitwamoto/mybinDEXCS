#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 計算.py
# by Yukiharu Iwamoto
# 2021/3/13 10:26:39 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行
# -d -> 0秒以外のフォルダがある場合，それらを消す．つまり0秒から計算をやり直すことになる
# -e -> 計算が発散した場合，時間ステップを小さくして計算を続ける
# -f -> system/controlDictに書かれているfunctionsの内容を計算中に実行する
# （現在は無効なオプション）-o -> 初期流れ場をpotentialFoamで作成する
# -p -> paraFoamを実行する

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
from utilities import misc
from utilities.dictParse import DictParser, DictParserList
from utilities import dictFormat
from utilities import folderTime
from utilities import appendEntries
from utilities import rmObjects

def handler(signal, frame):
    if os.path.isdir('0_bak'):
        if os.path.isdir('0'):
            shutil.rmtree('0')
        shutil.move('0_bak', '0')
    rmObjects.removeInessentials()
    sys.exit(1)

def potentialFoam(latest_time):
    p_potentialflow = os.path.join(latest_time, 'p_potentialflow')
    p_bak = os.path.join(latest_time, 'p_bak')
    if os.path.isfile(p_potentialflow):
        p_orig = os.path.join(latest_time, 'p')
        if os.path.isfile(p_orig):
            os.rename(p_orig, p_bak)
        os.rename(p_potentialflow, p_orig)
    command = 'potentialFoam -writep -writePhi -noFunctionObjects | tee potentialFoam.log'
    if subprocess.call(command, shell = True) == 0:
        if os.path.isfile(p_bak):
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
                dp_p_bak = DictParser(p_bak)
                dp_p_bak.writeContents(dp_p_bak.getDPLForKey(['boundaryField']), f, indent = '\t', last_char = '\n')
                f.write('\n}\n')
            command = 'changeDictionary -enableFunctionEntries'
            if subprocess.call(command, shell = True) == 0:
                os.remove(changeDictionaryDict)
            else:
                print('エラー: potentialFoamは成功しましたが，pの境界条件を希望するものに修正できませんでした．')
                sys.exit(1)
            if os.path.isfile(changeDictionaryDict_bak):
                os.rename(changeDictionaryDict_bak, changeDictionaryDict)
            os.remove(p_bak)
        for d in glob.iglob('*_potentialflow' + os.sep):
            try:
                float(d[:-14 - len(os.sep)])
                shutil.rmtree(d)
            except:
                pass
        shutil.copytree(latest_time, latest_time + '_potentialflow')
    else:
        print('初期流れ場をpotentialFoamで作成できませんでした．')

def calc_steps(logfile):
    with open(logfile, 'r') as f:
        s = f.read()
    sigFpe_is_found = False if s.rfind('Foam::sigFpe::sigHandler(int)') == -1 else True
    i = s.find('\nCreate mesh for time = ') + 24
    if i == -1:
        return -1
    time_begin = float(s[i:s.find('\n', i)])
    i = s.find('\nTime = ', i) + 8
    if i == -1:
        return 0
    time_next = float(s[i:s.find('\n', i)])
    i = s.rfind('\nTime = ') + 8
    time_end = float(s[i:s.find('\n', i)])
    return int((time_end - time_begin)/(time_next - time_begin)), sigFpe_is_found

def decrease_dt_in_controlDict(controlDict, trial):
    dp_controlDict = DictParser(controlDict)
    i_dt_last = i_dt = dp_controlDict.getIndexOfItem(['deltaT'])[0]
    for i in range(i_dt + 1, len(dp_controlDict.contents)):
        x = dp_controlDict.contents[i]
        if DictParserList.isType(x, DictParserList.DICT) and x.key() == 'deltaT':
            i_dt_last = i
    x = dp_controlDict.contents[i_dt_last]
    y = DictParserList(DictParserList.DICT, ['deltaT', '',
        ['#calc "pow(10.0, %d)*$deltaT"' % -trial],
        '/* (DECREASED) time step from ' + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + ' */'])
    if i_dt == i_dt_last or not x[-1].startswith('/* (DECREASED) time step from '):
        dp_controlDict.contents[i_dt_last + 1:i_dt_last + 1] = ['\n', y]
    else:
        z = x.value()[0]
        if DictParserList.isType(z, DictParserList.CALC):
            m = re.match(r'"\s*pow\s*\(10\.0,\s*([+\-.0-9]+)\s*\)\s*\*\s*\$deltaT\s*"$', z.value())
            try:
                if m:
                    p = float(m.group(1)) - 1.0
                    y.setValue(['#calc "pow(10.0, %g)*$deltaT"' % p])
            except:
                pass
        dp_controlDict.contents[i_dt_last] = y
    dp_controlDict.writeFile(controlDict)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler) # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = delete_folders_except_for_zero = decrease_dt_if_fpe_occured = False
        with_function_objects = exec_potentialFoam = exec_paraFoam = False
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
            elif sys.argv[i] == '-o':
                exec_potentialFoam = True
            elif sys.argv[i] == '-p':
                exec_paraFoam = True
            i += 1

    controlDict = os.path.join('system', 'controlDict')
    if not os.path.isfile(controlDict):
        print('エラー: %sファイルがありません．' % controlDict)
        sys.exit(1)

    for p in ('*.foam', '*.OpenFOAM', '*.blockMesh'):
        for f in glob.iglob(p):
            os.remove(f)
    with open(os.path.basename(os.getcwd()) + '.OpenFOAM', 'w'):
        pass

    for f in glob.iglob(os.path.join('0', '*.old')):
        shutil.move(f, f[:-4])
    if os.path.isdir('0_bak'):
        dcmp = filecmp.dircmp('0', '0_bak')
        if len(dcmp.left_only) > 0 or len(dcmp.right_only) > 0 or len(dcmp.diff_files) > 0:
            print('エラー: あるはずがない0_bakフォルダがあります．' +
                '0フォルダと0_bakフォルダを比較して，正しい方を0フォルダに置き換えてから再実行して下さい．')
            sys.exit(1)
    else:
        shutil.copytree('0', '0_bak')

    dp_controlDict = DictParser(controlDict)
    s_old = dp_controlDict.toString()
    startFrom = dp_controlDict.getValueForKey(['startFrom'])
    if startFrom is None:
        print('エラー: %sファイルでstartFromが指定されていません．', controlDict)
        sys.exit(1)
    if startFrom[0] != 'latestTime':
        dp_controlDict.setValueForKey(['startFrom'], ['latestTime'])
        print('!!! %sファイルのstartFromをlatestTimeに書き換えました．' % controlDict)
    for i in range(len(dp_controlDict.contents)):
        x = dp_controlDict.contents[i]
        if (DictParserList.isType(x, DictParserList.DICT) and x.key() == 'deltaT' and
            x[-1].startswith('/* (DECREASED) time step from ')):
            if (i + 1 < len(dp_controlDict.contents) and
                type(dp_controlDict.contents[i + 1]) is str and
                dp_controlDict.contents[i + 1].startswith('\n')):
                dp_controlDict.contents[i + 1] = dp_controlDict.contents[i + 1][1:]
            del dp_controlDict.contents[i]
            break
    dp_controlDict = dictFormat.moveLineToBottom(dp_controlDict)
    s = dp_controlDict.toString()
    if s != s_old:
        with open(controlDict, 'w') as f:
            f.write(s)

    if os.path.isdir('processor0'):
        subprocess.call('reconstructPar -newTimes', shell = True)
    latest_time = folderTime.latestTime()
    if latest_time is None:
        print('エラー: 結果フォルダがありません．')
        sys.exit(1)
    if float(latest_time) != 0.0:
        if interactive:
            sys.stdout.write('0秒以外のフォルダがあります．消して0秒からやり直しますか？ (y/n) > ')
            delete_folders_except_for_zero = True if raw_input().strip().lower() == 'y' else False
        if delete_folders_except_for_zero:
            subprocess.call('foamListTimes -rm -noZero', shell = True)
            rmObjects.removeProcessorDirs()
            latest_time = '0'
        else:
            rmObjects.removeProcessorDirs('noLatest')

    boundary = os.path.join('constant', 'polyMesh', 'boundary')
    if not os.path.isfile(boundary):
        print('エラー: %sファイルがありません．' % boundary)
        sys.exit(1)
    renumberMesh_was_done = False
    for line in open(boundary, 'r'):
        if line.startswith( '// renumberMesh was done'):
            renumberMesh_was_done = True
            break
    if not renumberMesh_was_done:
        command = 'renumberMesh -overwrite'
        if subprocess.call(command, shell = True) != 0:
            print('%sで失敗しました．よく分かる人に相談して下さい．' % command)
            sys.exit(1)
        with open(boundary, 'r') as f:
            s = '// renumberMesh was done\n' + f.read()
        with open(boundary, 'w') as f:
            f.write(s)

    for i in ('dynamicCode', 'postProcessing', 'logs'):
        if os.path.isdir(i):
            shutil.rmtree(i)
    rmObjects.removeLogPlotPngs()
    rmObjects.removePyFoamPlots()

    appendEntries.intoFvSolution()
    appendEntries.intoFvSchemes()
    appendEntries.intoControlDict()
    for f in ('potentialFoam.log', 'potentialFoam.logfile'):
        if os.path.isfile(f):
            os.remove(f)
#    if interactive:
#        print('初期流れ場をpotentialFoamで作成しますか？')
#        sys.stdout.write('もしp_potentialflowという名前のファイルがある場合，' +
#            'そのファイルに書かれている境界条件をpの境界条件に使います． (y/n) > ')
#        exec_potentialFoam = True if raw_input().strip().lower() == 'y' else False
#     if exec_potentialFoam:
#        potentialFoam(latest_time)

    if interactive:
        sys.stdout.write('%sに書かれている' % controlDict +
            'functionsの内容を計算中に実行しますか？ (y/n, 多くの場合nのはず) > ')
        with_function_objects = True if raw_input().strip().lower() == 'y' else False
        sys.stdout.write('計算が発散した場合，時間ステップを小さくして計算を続けますか？ (y/n) > ')
        decrease_dt_if_fpe_occured = True if raw_input().strip().lower() == 'y' else False

    application = misc.get_application(controlDict, dp_controlDict)
    for trial in range(1, 31):
        for i in ('PyFoam*', '*.logfile', '*.logfile.restart*'):
            for f in glob.iglob(i):
                os.remove(f)
        command = ('pyFoamPlotRunner.py ' +
            '--hardcopy ' +
            '--non-persist ' +
            '--no-pickled-file ' +
            '--with-courant ' +
            '--with-deltat ' +
            '--frequency=10.0 ' + application)
        if not with_function_objects:
            command += ' -noFunctionObjects'
        subprocess.call(command, shell = True)
        steps, sigFpe_is_found = calc_steps('PyFoamRunner.' + application + '.logfile')
        if not decrease_dt_if_fpe_occured or not sigFpe_is_found:
            break
        decrease_dt_in_controlDict(controlDict, trial)

    if os.path.isdir('0_bak'):
        if os.path.isdir('0'):
            shutil.rmtree('0')
        shutil.move('0_bak', '0')

    if sigFpe_is_found:
        print('\n計算が発散して終了しました．')
        print('「DEXCS OpenFOAM メモ」 (0_OpenFOAMメモ.pdf) の' +
            '「発散する場合の対処法」の部分を見れば発散が回避できるかもしれません．')

    if interactive:
        sys.stdout.write('\nparaFoamを実行しますか？ (y/n) > ')
        exec_paraFoam = True if raw_input().strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam)

    rmObjects.removeInessentials()
    sys.exit(2 if sigFpe_is_found else 0)
