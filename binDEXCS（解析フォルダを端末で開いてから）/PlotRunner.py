#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PlotRunner.py
# by Yukiharu Iwamoto
# 2026/5/27 7:29:21 PM

import os
import sys
import re
import glob
import shutil
import signal
import subprocess
import filecmp
from datetime import datetime
import matplotlib.pyplot as plt
from utilities import misc
from utilities import appendEntries
from utilities import rmObjects
from utilities import dictParse

# To do:
# 履歴ファイルを使って，やり直すときにはその時間から始める
# 履歴ファイルの末尾をlatestTimeに合わせる
# 緩和係数のコントロール

domains = 1
regionProperties_path = os.path.join('constant', 'regionProperties')

def handler(signum, frame):
    termination_process()
    sys.exit(1)

def terminate():
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

def get_relaxation_factor(param):
    # 指定された変数が equations と fields のどちらにあるか判定する
    for cat in ('equations', 'fields'):
        try:
            # 実行して値が返ってくればそのカテゴリに属する
            r = float(subprocess.check_output(['foamDictionary', 'system/fvSolution',
                '-entry', f'relaxationFactors.{cat}.{param}', '-value'],
                stderr = subprocess.DEVNULL, text = True))
            return cat, r
        except subprocess.CalledProcessError:
            continue
    return None, None

def plot_runner(application, latest_time):
    # グラフの初期設定
    plt.ion() # インタラクティブモードON
    line_styles = ['-', '--', '-.']

    def set_subplot(xlabel, ylabel, logscale = True):
        fig, ax = plt.subplots()
        ax.set_xlabel(xlabel, fontsize = 12)
        ax.set_ylabel(ylabel, fontsize = 12)
        if logscale:
            ax.set_yscale('log')
        ax.tick_params(axis = 'both', direction = 'in', which = 'both', top = True, right = True)
        ax.grid(True, which = 'both', linestyle = '--', alpha = 0.5) # グリッドの追加（見やすさ向上のため）
#        ax.set_xmargin(0)
#        ax.set_ymargin(0)
        return fig, ax

    pat = re.compile(
        # 残差
        r'Solving for (?P<parameter>[a-zA-Z0-9_.]+), Initial residual = [0-9.e+\-]+, '
        r'Final residual = (?P<final_residual>[\d.e+\-]+)' '|'
        # 連続の式の誤差
        r'continuity errors : sum local = (?P<continuity_local>[0-9.e+\-]+), '
        r'global = (?P<continuity_global>[0-9.e+\-]+)' '|'
        # クーラン数
        r'Courant Number mean: (?P<Courant_mean>[0-9.e+\-]+) max: (?P<Courant_max>[0-9.e+\-]+)'
    )
    plot_data = {
        'residual': {}, # {'U': [...], 'p': [...], ...}
        'continuity': {'sum local': [], 'abs global': []}
    }
    fig_res, ax_res = set_subplot('iteration', 'final residual', True)
    fig_res.canvas.manager.set_window_title('temporal histories of final residuals')
    fig_cont, ax_cont = set_subplot('iteration', 'continuity error', True)
    fig_cont.canvas.manager.set_window_title('temporal histories of continuity errors')
    plt_fig = {'residual': fig_res, 'continuity': fig_cont}
    plt_ax = {'residual': ax_res, 'continuity': ax_cont}
    plt_line2d = {
        'residual' : {}, # {'U': object, 'p': object, ...}
        'continuity': {k: plt_ax['continuity'].plot([], [], linestyle = line_styles[i], label = k)[0]
            for i, k in enumerate(plot_data['continuity'])}
    }
    plt_ax['continuity'].legend(loc = 'best') # ax.plotを呼び出した後
    new_time = { # 時間ステップが更新したか？
        'residual': {}, # {'U': True, 'p': True, ...}
        'continuity': True,
        'Courant': True
    }

    latest_time = float(latest_time)
    history_path = f'{application}_history.txt'
    if os.path.isfile(history_path):
        if latest_time == 0.0:
            os.remove(history_path)
            iteration = 0
        else:
            old_history_path = f'{application}_old_history.txt'
            os.rename(history_path, old_history_path)
            with open(old_history_path, 'r') as f_in, open(history_path, 'w') as f_out:
                for line in f_in:
                    if line.startswith('#'):
                        f_out.write(line)
                        continue
                    stripped = line.strip()
                    if len(stripped) == 0:
                        continue
                    cols = stripped.split('\t')
                    if float(cols[1]) > latest_time:
                        break
                    iteration = int(cols[0])
                    f_out.write(line)
    iteration_start = iteration + 1
    plot_freq = 10 # グラフ更新頻度

    def monitor(iteration, plot_data, plt_fig, plt_ax, plt_line2d):
        for data_key in plot_data:
            for k in plot_data[data_key]:
                assert len(plot_data[data_key][k]) == iteration, (
                    f'iteration = {iteration}, len["data_key"]["k"] = {len(plot_data[data_key][k])}')
                plt_line2d[data_key][k].set_data(range(1, iteration + 1),
                    plot_data[data_key][k]) # 線を更新
            plt_ax[data_key].relim() # 表示範囲の自動調整
            plt_ax[data_key].autoscale_view()
            plt_fig[data_key].canvas.draw() # 新しいデータを画面に描く
            plt.pause(0.01)
            plt_fig[data_key].savefig(f'{data_key}.png')

    try:
        with open(f'{application}.log', 'w') as f_log, open(history_path, 'a') as f_history:
            f_history.write(f'# {application} {datetime.now().strftime("%Y/%m/%d %H:%M:%S")}\n')

            # stdbuf -oL はバッファリングを防ぎ、リアルタイム性を高める
            command =  ['stdbuf', '-oL']
            if domains > 1:
                command.extend(['mpirun', '-np', f'{domains}'])
            command.append(application)
            if domains > 1:
                command.append('-parallel')
            process = subprocess.Popen( # ソルバーをサブプロセスとして実行（標準出力をパイプで取得）
                command,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT,
                text = True, # 出力を文字列として扱う
                bufsize = 1 # Python側でも行単位でバッファリング
            )

            # iter(process.stdout.readline, '') は readline() を
            # 空文字（プロセス終了）が返るまで繰り返す Pythonic な書き方です
            for line in iter(process.stdout.readline, ''):
                sys.stdout.write(line) # 端末へそのまま表示（PyFOAMの挙動）
                sys.stdout.flush() # リアルタイム反映のため
                f_log.write(line) # ログをファイル保存
                f_log.flush() # リアルタイム反映のため

                if line.startswith('Time = '):
                    if iteration < iteration_start:
                        time = line[7:].strip()
                    if iteration == iteration_start:
                        f_history.write(f'# iteration\ttime [s]')
                        for data_key in plot_data:
                            for k in plot_data[data_key]:
                                f_history.write(f'\t{data_key} {k}')
                        f_history.write('\n')
                    if iteration >= iteration_start:
                        f_history.write(f'{iteration}\t{time}')
                        for data_key in plot_data:
                            for k in plot_data[data_key]:
                                f_history.write(f'\t{plot_data[data_key][k][-1]}')
                        f_history.write('\n')
                        f_history.flush() # リアルタイム反映のため
                        if iteration%plot_freq == 0:
                            for data_key in plot_data:
                                monitor(iteration, plot_data, plt_fig, plt_ax, plt_line2d)
                    iteration += 1
                    time = line[7:].strip()
                    for k in plot_data['residual']:
                        new_time['residual'][k] = True
                    new_time['continuity'] = new_time['Courant'] = True

                s = pat.search(line)
                if s is None:
                    continue
                if s.lastgroup == 'final_residual':
                    par = s.group('parameter')
                    res = float(s.group('final_residual'))
                    if iteration == iteration_start and par not in plot_data['residual']: # 初回発見時に辞書を自動構築
                        plot_data['residual'][par] = []
                        plt_line2d['residual'][par] = plt_ax['residual'].plot([], [],
                            linestyle = line_styles[len(plt_line2d['residual'])%len(line_styles)],
                            label = par)[0] # グラフ用の線も動的に作成
                        plt_ax['residual'].legend(loc = 'best') # ax.plotを呼び出した後
                        new_time['residual'][par] = True
                    if new_time['residual'][par]:
                        plot_data['residual'][par].append(res) # データの追加
                        new_time['residual'][par] = False
                    else:
                        plot_data['residual'][par][-1] = res # データの更新
                elif s.lastgroup == 'continuity_global':
                    loc = float(s.group('continuity_local'))
                    glob = abs(float(s.group('continuity_global')))
                    if new_time['continuity']:
                        plot_data['continuity']['sum local'].append(loc) # データの追加
                        plot_data['continuity']['abs global'].append(glob)
                        new_time['continuity'] = False
                    else:
                        plot_data['continuity']['sum local'][-1] = loc # データの更新
                        plot_data['continuity']['abs global'][-1] = glob
                elif s.lastgroup == 'Courant_max':
                    mn = float(s.group('Courant_mean'))
                    mx = float(s.group('Courant_max'))
                    if iteration == iteration_start:
                        plot_data['Courant'] = {'mean': [], 'max': []}
                        fig_Courant, ax_Courant = set_subplot('iteration', 'Courant number', True)
                        fig_Courant.canvas.manager.set_window_title('temporal histories of Courant numbers')
                        plt_fig['Courant'] = fig_Courant
                        plt_ax['Courant'] = ax_Courant
                        plt_line2d['Courant']['mean'] = plt_ax['Courant'].plot([], [],
                            linestyle = line_styles[0], label = par)[0] # グラフ用の線も動的に作成
                        plt_line2d['Courant']['max'] = plt_ax['Courant'].plot([], [],
                            linestyle = line_styles[0], label = par)[1] # グラフ用の線も動的に作成
                        plt_ax['Courant'].legend(loc = 'best') # ax.plotを呼び出した後
                        new_time['Courant'] = True
                    if new_time['Courant']:
                        plot_data['Courant']['mean'].append(mn) # データの追加
                        plot_data['Courant']['max'].append(mx)
                        new_time['Courant'] = False
                    else:
                        plot_data['Courant']['mean'][-1] = mn # データの更新
                        plot_data['Courant']['max'][-1] = mx

            process.stdout.close()

    except:
        print(sys.exc_info())
        process.terminate()

    finally:
        if process.poll() is None:
            process.wait()
        monitor(iteration, plot_data, plt_fig, plt_ax, plt_line2d)
        plt.ioff()

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
                if (comment['element'] is None or
                    re.search(r'DECREASED\s+IN\s+RESPONCE\s+TO\s+FLOATING\s+POINT\s+ERROR',
                        comment['element']['value'].upper()) is None):
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
    for d in glob.iglob(os.path.join('system', f'*{os.sep}')):
        reset_relaxationFactors_in(d)

def change_relaxationFactors_in_fvSolution(exponent):
    def change_relaxationFactors_in(path):
        fvSolution_path = os.path.join(path, 'fvSolution')
        if os.path.islink(fvSolution_path):
            return

        fvSolution = dictParse.DictParser(file_name = fvSolution_path)

        relaxationFactors = fvSolution.find_element([{'type': 'block', 'key': 'relaxationFactors'}])['element']
        if relaxationFactors is None:
            linebreak_and_relaxationFactors = dictParse.DictParser(string =
                '\n'
                '\n'
                'relaxationFactors\n'
                '{\n'
                '}')['value']
            tail_index = fvSolution.find_element([{'except type': 'whitespace|linebreak|separator'}],
                reverse = True, index_not_found = len(fvSolution['value']) - 1)['index'] + 1
            fvSolution['value'][tail_index:tail_index] = linebreak_and_relaxationFactors
#            tail_index += len(linebreak_and_relaxationFactors)
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
    for d in glob.iglob(os.path.join('system', f'*{os.sep}':
        change_relaxationFactors_in(d)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler) # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = False
        delete_folders_except_for_zero = False
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-r':
                i += 1
                domains = max(int(sys.argv[i]), 1)
            i += 1

    controlDict_path = os.path.join('system', 'controlDict')
    fvSolution_path = os.path.join('system', 'fvSolution')
    boundary_path = os.path.join('constant', 'polyMesh', 'boundary')
    for i in (controlDict_path, fvSolution_path, boundary_path):
        if not os.path.isfile(i):
            print(f'エラー: {i}ファイルがありません．')
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

        if has_diff(filecmp.dircmp('0', '0_bak')):
            print('エラー: あるはずがない0_bakフォルダがあります．'
                '0フォルダと0_bakフォルダを比較して，正しい方を0フォルダに置き換えてから再実行して下さい．')
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
        print()
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
            rmObjects.removeProcessorDirs(option = '' if not os.path.isdir(
                os.path.join('processor0', latest_time)) else 'noLatest')

    renumberMesh_was_done = misc.isRenumberMeshDone()
    if not renumberMesh_was_done:
        misc.renumberMesh()

    for i in ('dynamicCode', 'postProcessing', 'logs'):
        if os.path.isdir(i):
            shutil.rmtree(i)
    rmObjects.removeLogPlotPngs()

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

    if domains != 1:
        processor_dirs = set()
        for d in glob.iglob(f'processor*{os.sep}'):
            try:
                processor_dirs.add(int(d[len('processor'):-len(os.sep)]))
            except:
                pass
        if processor_dirs != set(range(domains)):
            for d in processor_dirs:
                shutil.rmtree(f'processor{d}')
        decomposeParDict_path = os.path.join('system', 'decomposeParDict')
        if os.path.isfile(decomposeParDict_path):
            numberOfSubdomains = dictParse.DictParser(file_name = decomposeParDict_path).find_element(
                [{'type': 'dictionary', 'key': 'numberOfSubdomains'}, {'type': 'integer'}])['element']
            if numberOfSubdomains is not None and int(numberOfSubdomains['value']) != domains:
                for d in processor_dirs:
                    shutil.rmtree(f'processor{d}')
        if not os.path.isdir('processor0'):
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
            for d in glob.iglob(os.path.join('system', f'*{os.sep}')):
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

    plot_runner(misc.getApplication(), latest_time)

    terminate()
