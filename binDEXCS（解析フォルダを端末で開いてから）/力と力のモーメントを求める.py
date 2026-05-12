#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 力と力のモーメントを求める.py
# by Yukiharu Iwamoto
# 2026/5/12 2:11:23 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行．system/controlDictのfunctionsにforcesに関する指示を書き込んでいることが前提
# -b time_begin: 力の計算を開始する時間をtime_beginにする．指定しない場合は最も小さい値を持つ時間になる
#                time_beginにlを指定すると，最も大きい値を持つ時間になる
# -e time_end: 力の計算を終了する時間をtime_endにする．指定しない場合は最も大きい値を持つ時間になる
# -0: 0秒のデータを含める
# -j: 力の計算を実行せず，postProcessingフォルダ内にある過去の結果を消去するだけ

import math
import sys
import signal
import subprocess
import os
import shutil
import glob
import re
import matplotlib.pyplot as plt
from utilities import misc
from utilities import rmObjects
from utilities import dictParse
binDEXCS_path = os.path.expanduser('~/Desktop/binDEXCS（解析フォルダを端末で開いてから）') # dakuten.py -j -f <path> で濁点を結合しておく
sys.path.append(binDEXCS_path)

def appropriate_tick(xmin, xmax, n):
    tmp = abs(xmax - xmin)/(n + 0.01)
    tick = 10.0**math.floor(math.log10(tmp))
    tmp /= tick # 1 <= tmp < 10
    for i in (1.0, 2.0, 2.5, 5.0):
        if tmp < i:
            return i*tick
    return 10.0*tick

def handler(signum, frame):
    misc.setEnabledInControlDictFunctions(enabled = False)
    rmObjects.removeInessentials()
    sys.exit(1)

def append_functions_in_controlDict(controlDict_path):
    controlDict = dictParse.DictParser(file_name = controlDict_path)
    functions = controlDict.find_element([{'type': 'block', 'key': 'functions'}])['element']
    if functions is None:
        linebreak_and_functions = dictParse.DictParser(string =
            '\n'
            '\n'
            'functions\n'
            '{\n'
            '}').elements
        tail_index = controlDict.find_element([{'except type': 'whitespace|linebreak|separator'}],
            reverse = True, index_not_found = len(controlDict.elements) - 1)['index'] + 1
        controlDict.elements[tail_index:tail_index] = linebreak_and_functions
        functions = linebreak_and_functions[-1]

    block_end = dictParse.find_element([{'type': 'block_end'}], parent = functions, reverse = True)
    patches = ' '.join([i['element']['key'] for i in dictParse.DictParser(file_name =
        os.path.join('constant', 'polyMesh', 'boundary')).find_all_elements(
            [{'type': 'list'}, {'type': 'block'}])])
    block_end['parent'][block_end['index']:block_end['index']] = dictParse.DictParser(string =
        '\n'
        '\t// patchにかかる力を求める．\n'
        '\t// 少なくともpatches(B)は修正する必要がある．\n'
        '\t// 複数の条件に対して求めたい場合，\n'
        '\t// forces\n'
        '\t// {\n'
        '\t//     ...\n'
        '\t// }\n'
        '\t// の部分をコピーして使えば良い．\n'
        '\tforces // <- (A) postProcessingフォルダ内に作られるフォルダの名前，他と重複してはいけない！\n'
        '\t{\n'
        '\t\ttype\tforces;\n'
        '\t\tlibs\t("libforces.so");\n'
        '\t\tenabled\tyes; // yesで実行\n'
        f'\t\tpatches\t({patches}); // <- (B) 複数のpatchを指定すると，それらにまとめてかかる力を求める．\n'
        '\t\trho\trhoInf; // 非圧縮性流体の場合のみ使用\n'
        '\t\trhoInf\t1; // 非圧縮性流体の場合，この密度がかけられて力の単位N（ニュートン）になる．\n'
        '\t\tlog\tyes;\n'
        '\t\twriteControl\ttimeStep;\n'
        '\t\twriteInterval\t1;\n'
        '\t\tCofR\t(0 0 0); // モーメントを求める中心の(x y z)座標\n'
        '\t}').elements
    functions.set_blank_line(number_of_blank_lines = 1)

    string = dictParse.normalize(string = controlDict.file_string())[0]
    os.rename(controlDict_path, f'{controlDict_path}_bak')
    with open(controlDict_path, 'w') as f:
        f.write(string)

    print(f'\n\033[3;4;5mファイル{controlDict_path}のfunctionsにforcesに関するテンプレートを追加して，'
        'texteditwx.pyで開いています．')
    print('説明コメントを読んで，自分が行いたいことに合わせてテンプレートを書き換えて下さい．')
    print('書き換えたら保存して，texteditwx.pyを終了して下さい．\033[m\n')
    subprocess.call(f'{os.path.join(binDEXCS_path, "texteditwx.py")} {controlDict_path}', shell = True)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler) # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)
    if misc.texteditwx_works_well() == False:
        exit(1)

    just_delete_previous_files = False
    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = False
        forces_is_written = True # <- 書き込めていないと非インタラクティブにできるわけがない
        time_begin, time_end, noZero = '-inf', 'inf', True
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-N': # Non-interactive
                pass
            elif sys.argv[i] == '-b':
                i += 1
                time_begin = sys.argv[i]
            elif sys.argv[i] == '-e':
                i += 1
                time_end = sys.argv[i]
            elif sys.argv[i] == '-0':
                noZero = False
            elif sys.argv[i] == '-j':
                just_delete_previous_files = True
            i += 1

    controlDict_path = os.path.join('system', 'controlDict')
    if not os.path.isfile(controlDict_path):
        print(f'エラー: ファイル{controlDict_path}がありません．')
        sys.exit(1)

    forces_related_folders_txt = os.path.join('postProcessing', '_forces_related_folders.txt')
    if os.path.isdir('postProcessing') and os.path.isfile(forces_related_folders_txt):
        for line in open(forces_related_folders_txt, 'r'):
            tmp = os.path.join('postProcessing', line.rstrip())
            if os.path.isdir(tmp):
                shutil.rmtree(tmp)
        os.remove(forces_related_folders_txt)
    if just_delete_previous_files:
        sys.exit(0) # 正常終了

    misc.setEnabledInControlDictFunctions(enabled = False)
    misc.setEnabledInControlDictFunctions(enabled = True, type_name = 'forces')
    if interactive:
        forces_is_written = True if input(f'ファイル{controlDict_path}の内容を確認して下さい．'
            'functionsにforcesに関する指示が書き込まれていますか？ (y/n) > ').strip().lower() == 'y' else False
        if not forces_is_written:
            append_functions_in_controlDict(controlDict_path)

    controlDict = DictParser(file_name = controlDict_path)
    types = controlDict.find_all_elements([{'type': 'block', 'key': 'functions'}, {'type': 'block'},
        {'type': 'dictionary', 'key': 'type'}])
    forces_dir_list = [i['parent']['key'] for i in types if dictParse.find_element([{'type': 'word'}],
        parent = i['element'])['element'] == 'forces']
    if len(forces_dir_list) == 0:
        print(f'エラー: ファイル{controlDict_path}でforcesに関する指示がありません．')
        sys.exit(1)

    if interactive:
        time_begin, time_end, noZero = misc.setTimeBeginEnd('力の計算')
    # https://develop.openfoam.com/Development/openfoam/-/tree/maintenance-v1906/src/functionObjects/forces/forces
    misc.execPostProcess(time_begin, time_end, noZero)

    with open(forces_related_folders_txt, 'w') as f:
        for forces_dir in forces_dir_list:
            f.write(forces_dir + '\n')

    for forces_dir in forces_dir_list:
        force_dat = moment_dat = None
        pdir = os.path.join('postProcessing', forces_dir)
        # postProcessing/forces_dir/0/
        for d in glob.iglob(os.path.join(pdir, '*' + os.sep)):
            try:
                float(os.path.basename(os.path.dirname(d)))
                shutil.move(os.path.join(d, 'force.dat'), pdir)
                shutil.move(os.path.join(d, 'moment.dat'), pdir)
                force_dat = os.path.join(pdir, 'force.dat')
                moment_dat = os.path.join(pdir, 'moment.dat')
                shutil.rmtree(d)
                break
            except:
                pass
        if force_dat is None or moment_dat is None:
            continue
        t_min = float('inf')
        t_max = -t_min
        F_min = t_min
        F_max = t_max
        t_list = []
        Fx_list = []
        Fy_list = []
        Fz_list = []
        forces_tab_txt = os.path.join(pdir, forces_dir + '_tab.txt')
        with open(force_dat, 'r') as ff:
            with open(moment_dat, 'r') as fm:
                with open(forces_tab_txt, 'w') as fw:
                    while True:
                        linef = ff.readline()
                        linem = fm.readline()
                        if not linef:
                            break
                        if re.match('#\\s*Time\\s+', linef):
                            fw.write('#Time\tFx\tFy\tFz\tTx\tTy\tTz\n')
                        elif linef[0] == '#':
                            fw.write(re.sub('\\s+(?!$)', '\t', re.sub('[()]', '',
                                re.sub('^#\\s+', '#', linef))).rstrip() + '\n')
                        else:
                            linef = re.sub('[()]', '', linef).split()
                            t = float(linef[0])
                            t_max = max(t_max, t)
                            t_min = min(t_min, t)
                            Fx = float(linef[1])
                            Fy = float(linef[2])
                            Fz = float(linef[3])
                            F_max = max(F_max, Fx, Fy, Fz)
                            F_min = min(F_min, Fx, Fy, Fz)
                            linem = re.sub('[()]', '', linem).split()
                            t_list.append(t)
                            Fx_list.append(Fx)
                            Fy_list.append(Fy)
                            Fz_list.append(Fz)
                            fw.write('{:g}\t{:g}\t{:g}\t{:g}\t{:g}\t{:g}\t{:g}\n'.format(
                                t, Fx, Fy, Fz, float(linem[1]), float(linem[2]), float(linem[3])))
        plt.plot(t_list, Fx_list, label = 'Fx')
        plt.plot(t_list, Fy_list, label = 'Fy')
        plt.plot(t_list, Fz_list, label = 'Fz')
        plt.xlabel('time [s]', fontsize = 16)
        plt.ylabel('forces', fontsize = 16)
        tick = appropriate_tick(t_min, t_max, 5)
        t_max = tick*math.ceil(t_max/tick - 0.01)
        t_min = tick*math.floor(t_min/tick + 0.01)
        plt.xlim(t_min, t_max)
        plt.xticks([t_min + i*tick for i in range(int((t_max - t_min)/tick + 1.1))])
        tick = appropriate_tick(F_min, F_max, 5)
        F_max = tick*math.ceil(F_max/tick - 0.01)
        F_min = tick*math.floor(F_min/tick + 0.01)
        plt.ylim(F_min, F_max)
        plt.yticks([F_min + i*tick for i in range(int((F_max - F_min)/tick + 1.1))])
        plt.tick_params(which = 'both', direction = 'in', labelsize = 14)
        plt.tick_params(length = 10, which = 'major')
        plt.tick_params(length = 5, which = 'minor')
        plt.legend(loc = 'best', prop = {'size': 16}, framealpha = 0.2)
        forces_png = os.path.join(pdir, forces_dir + '.png')
        plt.savefig(forces_png)
        plt.clf()
        subprocess.call('xdg-open ' + forces_png, shell = True)
        print('\nグラフは{}, 結果は{}に保存しました．'.format(forces_png, forces_tab_txt))

    rmObjects.removeInessentials()
