#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 計算.py
# by Yukiharu Iwamoto
# 2026/5/13 9:12:56 AM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行
# -d -> 0秒以外のフォルダがある場合，それらを消す．つまり0秒から計算をやり直す
# -e -> 計算が発散した場合，緩和係数を小さくして計算を続ける
# -f -> system/controlDictに書かれているfunctionsを全て計算中に実行するように，controlDictを書き変える
# （現在は無効なオプション）-o -> 初期流れ場をpotentialFoamで作成する
# -p -> paraFoamを実行する
# -r domains -> 計算領域をdomains個に分割して並列計算を行う．1だと普通の計算

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
import filecmp
from utilities import misc
from utilities import appendEntries
from utilities import rmObjects
from utilities import dictParse

domains = 1
sigFpe_is_found = False
controlDict_path = os.path.join('system', 'controlDict')
regionProperties_path = os.path.join('constant', 'regionProperties')
boundary_path = os.path.join('constant', 'polyMesh', 'boundary')

def handler(signum, frame):
    if domains != 1:
        command = 'reconstructPar -newTimes -noFunctionObjects'
        if os.path.exists(regionProperties_path):
            command += ' -allRegions'
        subprocess.call(command, shell = True)
        rmObjects.removeProcessorDirs('noLatest')
    if os.path.isdir('0_bak'):
        if os.path.isdir('0'):
            shutil.rmtree('0')
        shutil.move('0_bak', '0')
    rmObjects.removeInessentials()
    sys.exit(1)

def potentialFoam(latest_time):
    p_potentialflow_path = os.path.join(latest_time, 'p_potentialflow')
    p_path = os.path.join(latest_time, 'p')
    p_bak_path = os.path.join(latest_time, 'p_bak')
    if domains == 1:
        has_p_potentialflow = os.path.isfile(p_potentialflow_path)
    else:
        has_p_potentialflow = False
        for d in glob.iglob('processor*' + os.sep):
            try:
                int(d[len('processor'):-len(os.sep)])
                pp = os.path.join(d, p_potentialflow_path)
                if os.path.isfile(pp):
                    has_p_potentialflow = True
                    os.rename(pp, os.path.join(d, p_path))
            except:
                pass
    if has_p_potentialflow:
        if os.path.isfile(p_path):
            os.rename(p_path, p_bak_path)
        if os.path.isfile(p_potentialflow_path):
            os.rename(p_potentialflow_path, p_path)
    command = (('potentialFoam' if domains == 1 else f'mpirun -np {domains} potentialFoam -parallel') +
        ' -writep -writePhi -noFunctionObjects | tee potentialFoam.log')
    if subprocess.call(command, shell = True) == 0:
        if os.path.isfile(p_bak_path):
            changeDictionaryDict_path = os.path.join('system', 'changeDictionaryDict')
            changeDictionaryDict_bak_path = f'{changeDictionaryDict_path}_bak'
            if os.path.isfile(changeDictionaryDict_path):
                os.rename(changeDictionaryDict_path, changeDictionaryDict_bak_path)
            with open(changeDictionaryDict_path, 'w') as f:
                f.write('FoamFile\n'
                    '{\n'
                    '\tversion\t2.0;\n'
                    '\tformat\tascii;\n'
                    '\tclass\tdictionary;\n'
                    '\tlocation\t"system";\n'
                    '\tobject\tchangeDictionaryDict;\n'
                    '}\n'
                    '\n'
                    'p\n'
                    '{\n')
                f.write(dictParse.DictParser(file_name = p_bak_path).find_element(
                    [{'type': 'block'}, {'key': 'boundaryField'}])['element'].file_string(indent_level = 1))
                f.write('\n'
                    '}\n')
            command = (('changeDictionary' if domains == 1 else f'mpirun -np {domains} changeDictionary -parallel') +
                ' -enableFunctionEntries')
            if subprocess.call(command, shell = True) == 0:
                os.remove(changeDictionaryDict_path)
            else:
                print('エラー: potentialFoamは成功しましたが，pの境界条件を希望するものに修正できませんでした．')
                if os.path.isdir('0_bak'):
                    if os.path.isdir('0'):
                        shutil.rmtree('0')
                    shutil.move('0_bak', '0')
                sys.exit(1)
            if os.path.isfile(changeDictionaryDict_bak_path):
                os.rename(changeDictionaryDict_bak_path, changeDictionaryDict_path)
            os.remove(p_bak_path)
        if domains != 1:
            command = f"reconstructPar -withZero -time '{latest_time}' -noFunctionObjects"
            if os.path.exists(regionProperties_path):
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

def reset_relaxationFactors_in_fvSolution():
    def reset_relaxationFactors_in(path):
        fvSolution_path = os.path.join(path, 'fvSolution')
        if os.path.islink(fvSolution_path):
            return

        fvSolution = dictParse.DictParser(file_name = fvSolution_path)

        relaxationFactors = fvSolution.find_element([{'type': 'block', 'key': 'relaxationFactors'}])['element']
        if relaxationFactors is None:
            return
        for k in ('equations', 'fields'):
            block = relaxationFactors.find_element([{'type': 'block', 'key': k}])['element']
            if block is None:
                continue
            for i in block.find_all_elements([{'type': 'dictionary'}]):
                i = i['element']
                comment = i.find_element([{'type': 'line_comment|block_comment'}], reverse = True)
                if (comment['element'] is not None or
                    re.search(r'DECREASED\s+IN\s+RESPONCE\s+TO\s+FLOATING\s+POINT\s+ERROR',
                        comment['element']['value'].upper()) is not None):
                    continue
                del comment['parent'][comment['index']]
                calc = i.find_element([{'type': 'directive', 'key': '#calc'}])['element']
                if calc is None:
                    continue
                value = re.match(r'"\(([^)]+)', calc.find_element([{'type': 'string'}])['element']['value'])
                if value is None:
                    continue
                calc['parent'][calc['index']:calc['index'] + 1] = dictParse.DictParser(string =
                    value[1])['value']
            block.set_blank_line(number_of_blank_lines = 0)

        string = dictParse.normalize(string = fvSolution.file_string())[0]
        if fvSolution.string != string:
#            os.rename(fvSolution_path, f'{fvSolution_path}_bak')
            with open(fvSolution_path, 'w') as f:
                f.write(string)

    if os.path.isdir('system'):
        reset_relaxationFactors_in('system')
    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
        reset_relaxationFactors_in(d)

def change_relaxationFactors_in_controlDict(exponent):
    def change_relaxationFactors_in(path):
        fvSolution_path = os.path.join(path, 'fvSolution')
        if os.path.islink(fvSolution_path):
            return

        fvSolution = dictParse.DictParser(file_name = fvSolution_path)

        tail_index = fvSolution.find_element([{'except type': 'whitespace|linebreak|separator'}],
            reverse = True, index_not_found = len(fvSolution['value']) - 1)['index'] + 1

        relaxationFactors = fvSolution.find_element([{'type': 'block', 'key': 'relaxationFactors'}])['element']
        if relaxationFactors is None:
            linebreak_and_relaxationFactors = dictParse.DictParser(string =
                '\n'
                '\n'
                'relaxationFactors\n'
                '{\n'
                '}')['value']
            fvSolution['value'][tail_index:tail_index] = linebreak_and_relaxationFactors
            tail_index += len(linebreak_and_relaxationFactors)
            relaxationFactors = linebreak_and_relaxationFactors[-1]
        relaxationFactors_start = relaxationFactors.find_element([{'type': 'block_start'}])['index'] + 1

        fields = relaxationFactors.find_element([{'type': 'block', 'key': 'fields'}])['element']
        if fields is None:
            linebreak_and_fields = dictParse.DictParser(string =
                '\n'
                '\tfields // p = p^{old} + \\alpha (p - p^{old})\n'
                '\t{\n'
                '\t\t"p|p_rgh"\t1.0;\n'
                '\t\trho\t1.0;\n'
                '\t}')['value']
            relaxationFactors['value'][relaxationFactors_start:relaxationFactors_start] = linebreak_and_fields
            fields = linebreak_and_fields[-1]
        else:
            fields['value'][:fields.find_element([{'type': 'block_start'}])['index']
                ] = dictParse.DictParser(string = ' // p = p^{old} + \\alpha (p - p^{old})\n')['value']

        equations = relaxationFactors.find_element([{'type': 'block', 'key': 'equations'}])['element']
        if equations is None:
            linebreak_and_equations = dictParse.DictParser(string =
                '\n'
                '\tequations // A_P/\\alpha u_P + \\sum_N A_N u_N = s + (1/\\alpha - 1) A_P u_P^{old}\n'
                '\t{\n'
                '\t\tU\t1.0;\n'
                '\t\t"k|epsilon|omega"\t1.0;\n'
                '\t}')['value']
            relaxationFactors['value'][relaxationFactors_start:relaxationFactors_start] = linebreak_and_equations
            equations = linebreak_and_equations[-1]
        else:
            equations['value'][:equations.find_element(
                [{'type': 'block_start'}])['index']] = dictParse.DictParser(string =
                    ' // A_P/\\alpha u_P + \\sum_N A_N u_N = s + (1/\\alpha - 1) A_P u_P^{old}\n')['value']

        relaxationFactors.set_blank_line(number_of_blank_lines = 0)

        c = 0.5**exponent
        for block in (equations, fields):
            for param in block.find_all_elements([{'type': 'dictionary'}]):
                value = param['element'].find_element([{'type': 'word|float|integer'}])['element']
                if value is None:
                    continue
                value['parent'][value['index']:] = dictParse.DictParser(string =
                    f'#calc "({value["element"]["value"]})*{c}";'
                    ' // DECREASED IN RESPONCE TO FLOATING POINT ERROR\n')['value']
            block.set_blank_line(number_of_blank_lines = 0)

        string = dictParse.normalize(string = fvSolution.file_string())[0]
        if fvSolution.string != string:
#            os.rename(fvSolution_path, f'{fvSolution_path}_bak')
            with open(fvSolution_path, 'w') as f:
                f.write(string)

    reset_relaxationFactors_in_fvSolution()
    if os.path.isdir('system'):
        change_relaxationFactors_in('system')
    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
        change_relaxationFactors_in(d)

def calculate():
    for i in ('PyFoam*', '*.logfile', '*.logfile.restart*', 'log.*'):
        for f in glob.iglob(i):
            os.remove(f)

    command = ('pyFoamPlotRunner.py '
        '--hardcopy '
        '--non-persist '
        '--no-pickled-file '
        '--with-courant '
        '--with-deltat '
        '--frequency=10.0 ')
    if domains != 1:
        command += '--autosense-parallel '
    application = misc.getApplication()
    command += application
    subprocess.call(command, shell = True)

    with open(f'PyFoamRunner.{application}.logfile', 'r') as f:
        s = f.read()
    global sigFpe_is_found
    sigFpe_is_found = False if s.rfind('Foam::sigFpe::sigHandler(int)') == -1 else True
    i = s.find('\nCreate mesh for time = ')
    if i == -1:
        return -10
    i += len('\nCreate mesh for time = ')
    time_begin = float(s[i:s.find('\n', i)])
    i = s.find('\nTime = ', i)
    if i == -1:
        return 0
    i += len('\nTime = ')
    time_next = float(s[i:s.find('\n', i)])
    if time_next == time_begin:
        return -1
    i = s.rfind('\nTime = ') + len('\nTime = ') # not find but rfind!
    time_end = float(s[i:s.find('\n', i)])
    return int((time_end - time_begin)/(time_next - time_begin))

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler) # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = False
        delete_folders_except_for_zero = False
        decrease_relaxationFactors_after_fpe = False
        enable_all_function_objects = False
#        exec_potentialFoam = False
        exec_paraFoam = False
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-N': # Non-interactive
                pass
            elif sys.argv[i] == '-d':
                delete_folders_except_for_zero = True
            elif sys.argv[i] == '-e':
                decrease_relaxationFactors_after_fpe = True
            elif sys.argv[i] == '-f':
                enable_all_function_objects = True
#            elif sys.argv[i] == '-o':
#                exec_potentialFoam = True
            elif sys.argv[i] == '-p':
                exec_paraFoam = True
            elif sys.argv[i] == '-r':
                i += 1
                domains = max(int(sys.argv[i]), 1)
            i += 1

    fvSolution_path = os.path.join('system', 'fvSolution')
    for i in (controlDict_path, fvSolution_path, boundary_path):
        if not os.path.isfile(i):
            print(f'エラー: ファイル{i}がありません．')
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
        def has_diff(dcmp):
            # 左右どちらかにしかないファイル、または内容が異なるファイルがあるか
            if dcmp.left_only or dcmp.right_only or dcmp.diff_files:
                return True
            # サブディレクトリを再帰的にチェック
            return any(has_diff(sub_dcmp) for sub_dcmp in dcmp.subdirs.values())
        # 実行部分
        if has_diff(filecmp.dircmp('0', '0_bak')):
            print('エラー: あるはずがないフォルダ 0_bak があります．'
                'フォルダ 0 と 0_bak を比較して，正しい方を 0 に置き換えてから再実行して下さい．')
            sys.exit(1)
        else:
            shutil.rmtree('0_bak')

    shutil.copytree('0', '0_bak')
    reset_relaxationFactors_in_fvSolution()

    if os.path.isdir('processor0'):
        command = 'reconstructPar -newTimes -noFunctionObjects'
        if os.path.exists(regionProperties_path):
            command += ' -allRegions'
        subprocess.call(command, shell = True)
    latest_time = misc.latestTime()
    if latest_time is None:
        print('エラー: 結果フォルダがありません．')
        if os.path.isdir('0_bak'):
            if os.path.isdir('0'):
                shutil.rmtree('0')
            shutil.move('0_bak', '0')
        sys.exit(1)
    if float(latest_time) != 0.0:
        if interactive:
            delete_folders_except_for_zero = True if input('0秒以外のフォルダがあります．'
                '消して0秒からやり直しますか？ (y/n) > ').strip().lower() == 'y' else False
        if delete_folders_except_for_zero:
            subprocess.call('foamListTimes -rm -noZero', shell = True)
            rmObjects.removeProcessorDirs()
            latest_time = '0'
        else:
            rmObjects.removeProcessorDirs(option = '' if not os.path.isdir(os.path.join('processor0', latest_time))
                else 'noLatest')

    renumberMesh_was_done = misc.isRenumberMeshDone()
    if not renumberMesh_was_done:
        misc.renumberMesh()

    for i in ('dynamicCode', 'postProcessing', 'logs'):
        if os.path.isdir(i):
            shutil.rmtree(i)
    rmObjects.removeLogPlotPngs()
    rmObjects.removePyFoamPlots()

    threads = misc.cpu_count()
    if interactive:
        while True:
            try:
                domains = max(int(input('計算領域を何個に分割して並列計算しますか？ '
                    f'({threads}個まで, 1だと普通の計算) > ').strip()), 1)
                break
            except ValueError:
                pass
    domains = min(domains, threads)

    appendEntries.intoFvSolution()
    appendEntries.intoFvSchemes()
    appendEntries.intoControlDict()
    for f in ('potentialFoam.log', 'potentialFoam.logfile'):
        if os.path.isfile(f):
            os.remove(f)
#    if interactive:
#        print('初期流れ場をpotentialFoamで作成しますか？')
#        exec_potentialFoam = True if input('もしp_potentialflowという名前のファイルがある場合，'
#            'そのファイルに書かれている境界条件をpの境界条件に使います． (y/n) > ').strip().lower() == 'y' else False

    enable_function_list, disable_function_list = misc.controlDictFunctionsList()
    if len(enable_function_list) + len(disable_function_list) > 0:
        print(f'ファイル{controlDict_path}のfunctionsで')
        if len(enable_function_list) > 0:
            print('  実行されるものは' + ', '.join(enable_function_list))
        if len(disable_function_list) > 0:
            print('  実行されないものは' + ', '.join(disable_function_list))
        print('です．')
        if interactive:
            enable_all_function_objects = True if input(f'全てを実行するように{controlDict_path}を書き換えますか？'
                ' (y/n, 多くの場合nのはず) > ').strip().lower() == 'y' else False
            decrease_relaxationFactors_after_fpe = True if input(f'計算が発散した場合，ファイル{fvSolution_path}の'
                'relaxationFactorsを小さくして計算を続けますか？ (y/n) > ').strip().lower() == 'y' else False

    if not enable_all_function_objects:
        misc.setEnabledInControlDictFunctions(enabled = False)

    if domains != 1:
        processor_dirs = set()
        for d in glob.iglob('processor*' + os.sep):
            try:
                processor_dirs.add(int(d[len('processor'):-len(os.sep)]))
            except:
                pass
        if len(processor_dirs) != domains or processor_dirs != set(range(domains)):
            for d in processor_dirs:
                shutil.rmtree(f'processor{d}')
        if not os.path.isdir('processor0'):
            decomposeParDict_path = os.path.join('system', 'decomposeParDict')
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
            for d in glob.iglob(os.path.join('system', '*' + os.sep)):
                if os.path.isfile(os.path.join(d, 'fvSolution')):
                    os.chdir(d)
                    if os.path.exists('decomposeParDict'):
                        os.remove('decomposeParDict')
                    os.symlink(os.path.join(os.pardir, 'decomposeParDict'), 'decomposeParDict') # can't overwrite
                    os.chdir(os.path.join(os.pardir, os.pardir))
            command = 'decomposePar -latestTime -noFunctionObjects'
            if os.path.exists(regionProperties_path):
                command += ' -allRegions'
            if subprocess.call(command, shell = True) != 0:
                print(f'エラー: {command}で失敗しました．よく分かる人に相談して下さい．')
                if os.path.isdir('0_bak'):
                    if os.path.isdir('0'):
                        shutil.rmtree('0')
                    shutil.move('0_bak', '0')
                sys.exit(1)

#    if exec_potentialFoam:
#        potentialFoam(latest_time)

    for trial in range(5):
        calculate()
        if domains != 1:
            command = 'reconstructPar -newTimes -noFunctionObjects'
            if os.path.exists(regionProperties_path):
                command += ' -allRegions'
            subprocess.call(command, shell = True)
            rmObjects.removeProcessorDirs('noLatest')
        if not decrease_relaxationFactors_after_fpe or not sigFpe_is_found:
            break
        change_relaxationFactors_in_controlDict(trial + 1)
    if sigFpe_is_found:
        print('\n計算が発散して終了しました．\n'
            '「DEXCS OpenFOAM メモ」(0_OpenFOAMメモ.pdf) の「発散する場合の対処法」の部分を見れば発散が回避できるかもしれません．')

    if os.path.isdir('0_bak'):
        if os.path.isdir('0'):
            shutil.rmtree('0')
        shutil.move('0_bak', '0')

    if interactive:
        exec_paraFoam = True if input('\nparaFoamを実行しますか？ (y/n) > ').strip().lower() == 'y' else False
    misc.execParaFoam(touch_only = not exec_paraFoam)

    rmObjects.removeInessentials()
    sys.exit(2 if sigFpe_is_found else 0)
