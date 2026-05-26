#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PlotRunner.py
# by Yukiharu Iwamoto
# 2026/5/26 9:53:22 AM

import os
import sys
import re
import glob
import shutil
import signal
import subprocess
import filecmp
import matplotlib.pyplot as plt
from utilities import misc
from utilities import appendEntries
from utilities import rmObjects
from utilities import dictParse

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

def plot_runner(application):
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
        ax.set_xmargin(0)
        ax.set_ymargin(0)
        return fig, ax

    pat = re.compile(
        # 残差
        r'Solving for (?P<parameter>[a-zA-Z0-9_.]+), Initial residual = [0-9.e+\-]+, '
        r'Final residual = (?P<final_residual>[\d.e+\-]+)' '|'
        # 連続の式の誤差
        r'continuity errors : sum local = (?P<continuity_local>[0-9.e+\-]+), '
        r'global = (?P<continuity_global>[0-9.e+\-]+)' '|'
        # クーラン数
        r'Courant Number mean: (?P<courant_mean>[0-9.e+\-]+) max: (?P<courant_max>[0-9.e+\-]+)'
    )
    plot_data = {
        'residual': {}, # {'U': [...], 'p': [...], ...}
        'continuity': {'sum local': [], 'abs global': []}
    }
    fig_res, ax_res = set_subplot('iteration', 'final residual', True)
    fig_cont, ax_cont = set_subplot('iteration', 'continuity error', True)
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
        'courant': True
    }
    iteration = 0
    iteration_start = 1
    plot_freq = 10 # グラフ更新頻度

    def monitor(iteration, plot_data, plt_fig, plt_ax, plt_line2d):
        for data_key in plot_data:
            for k in plot_data[data_key]:
                plt_line2d[data_key][k].set_data(range(1, iteration + 1),
                    plot_data[data_key][k]) # 線を更新
            plt_ax[data_key].relim() # 表示範囲の自動調整
            plt_ax[data_key].autoscale_view()
            plt_fig[data_key].canvas.draw() # 新しいデータを画面に描く
            plt.pause(0.01)
            plt_fig[data_key].savefig(f'{data_key}.png')

    try:
        with open(f'{application}.log', 'w') as f_log:
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
                    if iteration >= iteration_start and iteration%plot_freq == 0:
                        for data_key in plot_data:
                            monitor(iteration, plot_data, plt_fig, plt_ax, plt_line2d)
                    iteration += 1
                    for k in plot_data['residual']:
                        new_time['residual'][k] = True
                    new_time['continuity'] = new_time['courant'] = True

                s = pat.search(line)
                if s.lastgroup == 'final_residual':
                    par = s.group('parameter')
                    res = float(s.group('final_residual'))
                    if iteration == iteration_start and par not in plot_data['residual']: # 初回発見時に辞書を自動構築
                        plot_data['residual'][par] = []
                        plt_line2d['residual'][par] = ax.plot([], [],
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
                elif s.lastgroup == 'courant_max':
                    mn = float(s.group('courant_mean'))
                    mx = float(s.group('courant_max'))
                    if iteration == iteration_start:
                        plot_data['courant'] = {'mean': [], 'max': []}
                        fig_courant, ax_courant = set_subplot('iteration', 'Courant number', True)
                        plt_fig['courant'] = fig_courant
                        plt_ax['courant'] = ax_courant
                        plt_line2d['courant']['mean'] = ax.plot([], [],
                            linestyle = line_styles[0], label = par)[0] # グラフ用の線も動的に作成
                        plt_line2d['courant']['max'] = ax.plot([], [],
                            linestyle = line_styles[0], label = par)[1] # グラフ用の線も動的に作成
                        plt_ax['courant'].legend(loc = 'best') # ax.plotを呼び出した後
                        new_time['courant'] = True
                    if new_time['courant']
                        plot_data['courant']['mean'].append(mn) # データの追加
                        plot_data['courant']['max'].append(mx)
                        new_time['courant'] = False
                    else:
                        plot_data['courant']['mean'][-1] = mn # データの更新
                        plot_data['courant']['max'][-1] = mx

            process.stdout.close()

    except:
        print(sys.exc_info())
        process.terminate()

    finally:
        if process.poll() is None:
            process.wait()
         monitor(iteration, plot_data, plt_fig, plt_ax, plt_line2d)
        plt.ioff()

#def run_foam_live_plot(solver_name):
#    # --- 1. データ格納用のリスト ---
#    times = []
#    residuals = {} # フィールドごとの残差
#    cont_errors = {"local": [], "global": [], "cumulative": []}
#    courant_nums = {"max": [], "mean": []}
#
#    # --- 2. 正規表現パターン ---
#    # Time (横軸)
#    re_time = re.compile(r"^Time = (\d+\.?\d*)")
#    # 残差 (Final residualのみ抽出)
#    re_resid = re.compile(r"Solving for (\w+),.*Final residual = ([\d.e+-]+)")
#    # 連続の式誤差
#    re_cont = re.compile(r"time step continuity errors : sum local = ([\d.e+-]+), global = ([\d.e+-]+), cumulative = ([\d.e+-]+)")
#    # クーラン数
#    re_courant = re.compile(r"Courant Number mean: ([\d.e+-]+) max: ([\d.e+-]+)")
#
#    # --- 3. Matplotlib の設定 ---
#    plt.ion() # インタラクティブモードON
#    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
#    plt.subplots_adjust(hspace=0.3)
#
#    # ソルバー起動
#    process = subprocess.Popen(
#        ["stdbuf", "-oL", solver_name],
#        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
#    )
#
#    try:
#        current_t = None
#        for line in iter(process.stdout.readline, ""):
#            # 1. 標準出力をそのまま表示
#            sys.stdout.write(line)
#            sys.stdout.flush()
#
#            # 2. データの抽出
#            m_time = re_time.match(line)
#            if m_time:
#                current_t = float(m_time.group(1))
#                times.append(current_t)
#                # 新しいTimeステップに入った際、グラフを更新（例：10ステップごと）
#                if len(times) % 10 == 0:
#                    update_plots(ax1, ax2, ax3, times, residuals, cont_errors, courant_nums)
#
#            m_resid = re_resid.search(line)
#            if m_resid:
#                field, val = m_resid.groups()
#                residuals.setdefault(field, []).append(float(val))
#
#            m_cont = re_cont.search(line)
#            if m_cont:
#                cont_errors["local"].append(float(m_cont.group(1)))
#                cont_errors["global"].append(float(m_cont.group(2)))
#
#            m_courant = re_courant.search(line)
#            if m_courant:
#                courant_nums["mean"].append(float(m_courant.group(1)))
#                courant_nums["max"].append(float(m_courant.group(2)))
#
#    except KeyboardInterrupt:
#        process.terminate()
#    finally:
#        process.wait()
#        plt.ioff()
#        plt.show()
#
#def update_plots(ax1, ax2, ax3, times, residuals, cont_errors, courant_nums):
#    # 残差プロット (対数軸)
#    ax1.clear()
#    for field, vals in residuals.items():
#        # 長さをtimesに合わせる（簡易処理）
#        ax1.plot(times[:len(vals)], vals, label=field)
#    ax1.set_yscale('log')
#    ax1.set_ylabel('Final Residual')
#    ax1.legend(loc='upper right', fontsize='small')
#    ax1.grid(True, which="both", ls="-", alpha=0.5)
#
#    # 連続の式誤差
#    ax2.clear()
#    if cont_errors["local"]:
#        ax2.plot(times[:len(cont_errors["local"])], cont_errors["local"], label='local')
#        ax2.set_yscale('log')
#        ax2.set_ylabel('Cont. Error')
#        ax2.legend(loc='upper right')
#
#    # クーラン数
#    ax3.clear()
#    if courant_nums["max"]:
#        ax3.plot(times[:len(courant_nums["max"])], courant_nums["max"], label='max')
#        ax3.plot(times[:len(courant_nums["mean"])], courant_nums["mean"], label='mean')
#        ax3.set_ylabel('Courant Number')
#        ax3.set_xlabel('Time [s]')
#        ax3.legend(loc='upper right')
#
#    plt.pause(0.01) # 描画を反映させるための短い一時停止
#
##if __name__ == "__main__":
##    run_foam_live_plot("simpleFoam")
#
#def trigger_action(iteration, residuals):
#    """
#    残差が目標値を下回ったときに実行されるカスタムアクション
#    """
#    print(f"\n{'!'*40}")
#    print(f"検知: Iteration {iteration} で全残差が閾値を下回りました。")
#    print(f"現在の残差: {residuals}")
#    print(f"{'!'*40}\n")
#    
#    # 例1: 計算を安全に終了させる (OpenFOAMに停止を命令するファイルを生成)
#    # with open("comms/finish", "w") as f: f.write("stop")
#    
#    # 例2: 独自の事後処理スクリプトを走らせる
#    # subprocess.run(["python3", "post_process.py"])
#    
#    return True # 計算を止める場合はTrueを返す
#
#def run_foam_with_action(solver_name, threshold=1e-5):
#    # --- 1. 正規表現の設定 ---
#    re_time = re.compile(r"^Time = (\d+)")
#    # サブイタレーションの最後（Final residual）をキャプチャ
#    re_resid = re.compile(r"Solving for (\w+),.*Final residual = ([\d.e+-]+)")
#
#    # データ格納
#    current_residuals = {}
#    times = []
#    
#    # ソルバー起動 (バッファリング無効化)
#    process = subprocess.Popen(
#        ["stdbuf", "-oL", solver_name],
#        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
#    )
#
#    print(f"監視開始: ターゲット残差 = {threshold}")
#
#    try:
#        current_t = None
#        for line in iter(process.stdout.readline, ""):
#            # 1. 端末へ出力（必須要件）
#            sys.stdout.write(line)
#            sys.stdout.flush()
#
#            # 2. Timeの更新を検知
#            m_time = re_time.match(line)
#            if m_time:
#                # 前のTimeステップの結果で判定を行う
#                if current_residuals:
#                    # 全てのフィールド（p, U, k等）が閾値以下かチェック
#                    if all(v < threshold for v in current_residuals.values()):
#                        stop_needed = trigger_action(current_t, current_residuals)
#                        if stop_needed:
#                            print("[INFO] アクションに基づき、ソルバーを終了します。")
#                            process.terminate()
#                            break
#                
#                current_t = int(m_time.group(1))
#                # 次のステップのために残差をクリア
#                current_residuals = {}
#
#            # 3. 残差の抽出
#            m_resid = re_resid.search(line)
#            if m_resid:
#                field, val = m_resid.groups()
#                current_residuals[field] = float(val)
#
#    except KeyboardInterrupt:
#        process.terminate()
#    finally:
#        process.wait()

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
        # 実行部分
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

    plot_runner(misc.getApplication())

    terminate()
