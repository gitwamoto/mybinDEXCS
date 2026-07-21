#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 計算.py
# by Yukiharu Iwamoto
# 2026/7/21 10:04:30 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行
# -0 -> 0秒以外のフォルダがある場合，それらを消す．つまり0秒から計算をやり直す
# -d domains -> 計算領域をdomains個に分割して並列計算を行う．1だと普通の計算
# -f -> system/controlDictに書かれているfunctionsを全て計算中に実行するように，controlDictを書き変える
# -p -> paraFoamを実行する
# -r -> 残差が落ちにくい時に緩和係数を変化させる

# ---- 戻り値 ----
# 0: 正常終了
# 1: 発散で終了

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
import numpy as np
import math
from utilities import misc
from utilities import appendEntries
from utilities import rmObjects
from utilities import dictParse

# To do:
# クーラン数から時間ステップのコントロール

# plt.rcParams['figure.figsize'] = (6.0, 3.6) # (width, height), デフォルト値は環境によりますが、多くの場合は (6.4, 4.8) です。

relaxationFactor_lower_limit = 0.3  # 緩和係数の下限値
relaxationFactor_delta_usual = 0.01  # 通常時における緩和係数の変化量の絶対値
relaxationFactor_delta_restart = 0.05  # 通常時における緩和係数の変化量の絶対値
domains = 1
regionProperties_path = os.path.join("constant", "regionProperties")
decomposeParDict_path = os.path.join("system", "decomposeParDict")
pat_residual = re.compile(r"(?P<parameter>\S+)( \((?P<region>[^)]+)\))?")
pat_remark = re.compile(
    "// .+, [0-9]{4}/[0-9]{2}/[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{6})?"
)


def remark_string(remark):
    return f"// {remark}, {datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')}"  # YYYY/mm/dd HH:MM:SS.ffffff


def handler(signum, frame):
    if domains != 1:
        recosntructPar()
        rmObjects.removeProcessorDirs("noLatest")
    restore_zero_folder()
    sys.exit(1)


def decomposePar():
    with open(decomposeParDict_path, "w") as f:
        f.write(
            "FoamFile\n"
            "{\n"
            "\tversion\t2.0;\n"
            "\tformat\tascii;\n"
            "\tclass\tdictionary;\n"
            '\tlocation\t"system";\n'
            "\tobject\tdecomposeParDict;\n"
            "}\n"
            f"numberOfSubdomains\t{domains};\n"
            "method\tscotch;\n"
        )  # 複雑な形状や境界条件がある場合に最適．デフォルトで推奨されることが多い．
    for d in glob.iglob(os.path.join("system", f"*{os.sep}")):
        if os.path.isfile(os.path.join(d, "fvSolution")):
            os.chdir(d)
            if os.path.exists("decomposeParDict"):
                os.remove("decomposeParDict")
            os.symlink(
                os.path.join(os.pardir, "decomposeParDict"), "decomposeParDict"
            )  # can't overwrite
            os.chdir(os.path.join(os.pardir, os.pardir))
    command_args = ["decomposePar", "-latestTime", "-noFunctionObjects"]
    if os.path.exists(regionProperties_path):
        command_args.append("-allRegions")
    if misc.execCommand(command_args)[1] != 0:
        restore_zero_folder()
        sys.exit(1)
    print()


def recosntructPar():
    command_args = ["reconstructPar", "-newTimes", "-noFunctionObjects"]
    if os.path.exists(regionProperties_path):
        command_args.append("-allRegions")
    misc.execCommand(command_args)
    print()


def restore_zero_folder():
    if os.path.isdir("0_bak"):
        if os.path.isdir("0"):
            shutil.rmtree("0")
        shutil.move("0_bak", "0")
    rmObjects.removeInessentials()


def plot_runner(application, start_time, relax_delta=0.01, relax_lower_limit=0.3):
    # グラフの初期設定
    plt.ion()  # インタラクティブモードON
    line_styles = ["-", "--", "-."]

    # 出力の例
    # #################### simpleFoam ####################
    # Time = 1
    #
    # smoothSolver:  Solving for Ux, Initial residual = 1, Final residual = 0.031923, No Iterations 2
    # ...
    # time step continuity errors : sum local = 5.59162e-05, global = -8.44928e-07, cumulative = -8.44928e-07
    # smoothSolver:  Solving for epsilon, Initial residual = 0.120126, Final residual = 0.00622115, No Iterations 3
    # ...
    # ExecutionTime = 3.87 s  ClockTime = 4 s
    #
    # #################### pisoFoam ####################
    # Time = 0.005
    #
    # Courant Number mean: 0 max: 0
    # smoothSolver:  Solving for Ux, Initial residual = 1, Final residual = 1.1324e-06, No Iterations 5
    # ...
    # GAMG:  Solving for p, Initial residual = 1, Final residual = 0.0378382, No Iterations 2
    # ...
    # time step continuity errors : sum local = 2.15891e-10, global = -4.29423e-21, cumulative = -3.63249e-21
    # smoothSolver:  Solving for epsilon, Initial residual = 0.0108884, Final residual = 7.58625e-07, No Iterations 3
    # ...
    # ExecutionTime = 0.01 s  ClockTime = 0 s
    #
    # #################### chtMultiRegionSimpleFoam ####################
    # Time = 1
    #
    #
    # Solving for fluid region air
    # DILUPBiCGStab:  Solving for Ux, Initial residual = 1, Final residual = 0.00867447, No Iterations 1
    # ...
    # Min/max T:300 300.018
    # GAMG:  Solving for p_rgh, Initial residual = 1, Final residual = 0.00834252, No Iterations 12
    # time step continuity errors : sum local = 0.0425249, global = -0.00394851, cumulative = -0.00394851
    # Min/max rho:1.17074 1.17081
    # DILUPBiCGStab:  Solving for epsilon, Initial residual = 0.0396654, Final residual = 0.000135803, No Iterations 1
    # ...
    #
    # Solving for fluid region porous
    # DILUPBiCGStab:  Solving for Ux, Initial residual = 1, Final residual = 0.0058807, No Iterations 1
    # ...
    # Min/max T:349.984 400
    # GAMG:  Solving for p_rgh, Initial residual = 0.999996, Final residual = 0.00637825, No Iterations 9
    # time step continuity errors : sum local = 0.00103378, global = 0.000459295, cumulative = -0.00348922
    # Min/max rho:1000 1000
    # ExecutionTime = 19.74 s  ClockTime = 19 s
    #
    # #################### chtMultiRegionFoam ####################
    # Region: bottomWater Courant Number mean: 0.00017208904 max: 0.00082499996
    # Region: topAir Courant Number mean: 0.015 max: 0.015000002
    # Region: heater Diffusion Number mean: 0.00036111112 max: 0.0020000002
    # ...
    # deltaT = 0.001200048
    # # Region: ...からdeltaT = ...までの表示，なぜか最初のイタレーションだけ2回出る．
    # Time = 0.00120005
    #
    #
    # Solving for fluid region bottomWater
    # diagonal:  Solving for rho, Initial residual = 0, Final residual = 0, No Iterations 0
    # ...
    # Min/max T:300 300
    # GAMG:  Solving for p_rgh, Initial residual = 0.82697398, Final residual = 0.0020761791, No Iterations 3
    # ...
    # time step continuity errors (bottomWater): sum local = 3.6798664e-12, global = -6.7095022e-13, cumulative = -7.9347451e-07
    #
    # Solving for fluid region topAir
    # diagonal:  Solving for rho, Initial residual = 0, Final residual = 0, No Iterations 0
    # ...
    # Min/max T:300 300
    # GAMG:  Solving for p_rgh, Initial residual = 0.87372342, Final residual = 0.0068026541, No Iterations 2
    # ...
    # time step continuity errors (topAir): sum local = 7.8740942e-12, global = -6.6329409e-12, cumulative = 2.228493e-06
    #
    # Solving for solid region heater
    # DICPCG:  Solving for h, Initial residual = 1, Final residual = 3.0205594e-07, No Iterations 1
    # Min/max T:300 500
    #
    # Solving for solid region leftSolid
    # DICPCG:  Solving for h, Initial residual = 1, Final residual = 2.4555091e-08, No Iterations 2
    # Min/max T:300 300
    #
    # Solving for solid region rightSolid
    # DICPCG:  Solving for h, Initial residual = 1, Final residual = 2.4599615e-08, No Iterations 2
    # Min/max T:300 300
    # ExecutionTime = 0.02 s  ClockTime = 0 s

    pat = re.compile(
        # 残差
        r": +Solving for +(?P<parameter>[^ ,]+), Initial residual = [0-9.e+\-]+, "
        r"Final residual = (?P<final_residual>[\d.e+\-]+)"
        "|"
        # 連続の式の誤差
        r"^time step continuity errors *(?:[^ :]*): sum local = (?P<continuity_local>[0-9.e+\-]+), "
        r"global = (?P<continuity_global>[0-9.e+\-]+)"
        "|"
        # クーラン数，1未満が理想
        r"^(?:Region: (?P<Courant_region>\S+) )?"
        r"Courant Number mean: (?P<Courant_mean>[0-9.e+\-]+) max: (?P<Courant_max>[0-9.e+\-]+)"
        "|"
        # 拡散数，0.5未満が理想
        r"^Region: (?P<Diffusion_region>\S+) "
        r"Diffusion Number mean: (?P<Diffusion_mean>[0-9.e+\-]+) max: (?P<Diffusion_max>[0-9.e+\-]+)"
        "|"
        # 領域
        r"^Solving for \S+ region (?P<region>\S+)"
    )
    plot_data = {
        "residual": {},  # {'U': [...], 'p': [...], ...}
        "continuity": {},  # {'sum local': [], 'abs global': []}
    }
    plt_fig = {}
    plt_ax = {}
    plt_line2d = {}

    def set_subplot(data_key, xlabel, ylabel, window_title, logscale=True):
        ncol = math.ceil(len(plot_data[data_key]) / 16.0)
        fig, ax = plt.subplots(figsize=(4.8 + ncol * 1.2, 3.6))  # (width, height)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        if logscale:
            ax.set_yscale("log")
        ax.tick_params(axis="both", direction="in", which="both", top=True, right=True)
        ax.grid(
            True, which="both", linestyle="--", alpha=0.5
        )  # グリッドの追加（見やすさ向上のため）
        fig.canvas.manager.set_window_title(window_title)
        plt_line2d[data_key] = {
            k: ax.plot([], [], linestyle=line_styles[i % len(line_styles)], label=k)[0]
            for i, k in enumerate(plot_data[data_key])
        }
        #        ax.legend(loc = 'best') # ax.plotを呼び出した後
        ax.legend(
            bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0, ncol=ncol
        )
        fig.tight_layout()
        plt_fig[data_key] = fig
        plt_ax[data_key] = ax

    def set_subplots():
        set_subplot(
            data_key="residual",
            xlabel="iteration",
            ylabel="final residual",
            window_title="iteration histories of final residuals",
            logscale=True,
        )
        set_subplot(
            data_key="continuity",
            xlabel="iteration",
            ylabel="continuity error",
            window_title="iteration histories of continuity errors",
            logscale=True,
        )
        if "Courant" in plot_data:
            set_subplot(
                data_key="Courant",
                xlabel="iteration",
                ylabel="Courant number",
                window_title="iteration histories of Courant numbers",
                logscale=True,
            )
        if "Diffusion" in plot_data:
            set_subplot(
                data_key="Diffusion",
                xlabel="iteration",
                ylabel="Diffusion number",
                window_title="iteration histories of Diffusion numbers",
                logscale=True,
            )

    start_time = float(start_time)
    history_path = f"{application}_history.txt"
    history_title_prefix = "# iteration\ttime [s]"
    iteration = 0
    if os.path.isfile(history_path):
        if start_time == 0.0:
            os.remove(history_path)
        else:
            old_history_path = f"{application}_old_history.txt"
            os.rename(history_path, old_history_path)
            with open(old_history_path, "r") as f_in, open(history_path, "w") as f_out:
                for line in f_in:
                    if line.startswith("#"):
                        if line.startswith(history_title_prefix):
                            data_ord = [
                                i.split(maxsplit=1)
                                for i in line[len(history_title_prefix) :]
                                .strip()
                                .split("\t")
                            ]
                            l_data_ord = len(data_ord)
                            for data_key, k in data_ord:
                                plot_data.setdefault(data_key, {})[k] = []
                            set_subplots()
                        f_out.write(line)
                        continue
                    stripped = line.strip()
                    if len(stripped) == 0:
                        continue
                    cols = stripped.split("\t")
                    if l_data_ord == len(cols) - 2:
                        for (data_key, k), v in zip(data_ord, cols[2:]):
                            plot_data[data_key][k].append(float(v))
                    if float(cols[1]) > start_time:
                        break
                    iteration = int(cols[0])
                    f_out.write(line)
            os.remove(old_history_path)
    iteration_start = iteration + 1
    plot_freq = 10  # グラフ更新頻度

    def monitor():
        for data_key in plot_data:
            #            message = ''
            for k in plot_data[data_key]:
                #                l = len(plot_data[data_key][k])
                #                if l != iteration:
                #                    message += f"(WARNING) iteration = {iteration} != len(['{data_key}']['{k}']) = {l}\n"
                #                plt_line2d[data_key][k].set_data(range(1, l + 1), plot_data[data_key][k]) # 線を更新
                plt_line2d[data_key][k].set_data(
                    range(1, len(plot_data[data_key][k]) + 1), plot_data[data_key][k]
                )  # 線を更新
            #            if len(message) > 0:
            #                sys.stdout.write(f'\n{message}\n')
            #                sys.stdout.flush() # リアルタイム反映のため
            plt_ax[data_key].relim()  # 表示範囲の自動調整
            plt_ax[data_key].autoscale_view()
            plt_fig[data_key].canvas.draw()  # 新しいデータを画面に描く
            plt.pause(0.01)
            plt_fig[data_key].savefig(f"{data_key}.png")

    res_eval_freq = 10  # 残差評価頻度
    res_crit = 0.001  # これよりも残差が大きい，小さい時に緩和係数の増減基準を切り替える
    res_flat = 0.01  # これよりも残差変化率の絶対値が小さければ，残差減少が鈍いと見なす

    def relax_delta_sign(recent_residuals):
        recent_residuals = np.array(recent_residuals)
        res_mean = np.mean(recent_residuals)
        res_slope = np.polyfit(
            np.arange(recent_residuals.shape[0]), np.log10(recent_residuals), 1
        )[0]
        s = np.heaviside(res_mean - res_crit, 0.0)
        return -s * np.heaviside(res_slope, 0.0) + (1.0 - s) * (
            np.heaviside(res_flat - abs(res_slope), 0.0)
            - np.heaviside(res_slope - res_flat, 0.0)
        )

    result = "success"  # 無事に終了できたときにTrueを返すフラグ
    time = "0"
    region = None

    try:
        print()
        command_args = [
            "stdbuf",
            "-oL",
        ]  # stdbuf -oL はバッファリングを防ぎ、リアルタイム性を高める
        if domains > 1:
            command_args.extend(["mpirun", "-np", f"{domains}"])
            # -u (unbuffered) は、mpirun に対して「出力をバッファリングせずにすぐ吐き出せ」と指示します
        command_args.append(application)
        if domains > 1:
            command_args.append("-parallel")
        process = subprocess.Popen(  # ソルバーをサブプロセスとして実行（標準出力をパイプで取得）
            command_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,  # 出力を文字列として扱う
            bufsize=1,  # Python側でも行単位でバッファリング
        )

        with (
            open(f"{application}.log", "w") as f_log,
            open(history_path, "a") as f_history,
        ):
            f_history.write(
                f"# {application} {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n"
            )  # YYYY/mm/dd HH:MM:SS
            # iter(process.stdout.readline, '') は readline() を
            # 空文字（プロセス終了）が返るまで繰り返す Pythonic な書き方です
            for line in iter(process.stdout.readline, ""):
                if (
                    line.startswith("Using #calc at ")
                    or line.startswith("Using #codeStream with ")
                    or "/dynamicCode/" in line
                    or "ln: ./lnInclude" in line
                    or ": codeStreamTemplate.C" in line
                ):
                    continue
                sys.stdout.write(line)  # 端末へそのまま表示
                sys.stdout.flush()  # リアルタイム反映のため
                f_log.write(line)  # ログをファイル保存
                f_log.flush()  # リアルタイム反映のため

                if "not enough slots available in" in line:
                    result = "not enough slots"

                if line.startswith("Time = ") or "solution converged in" in line:
                    # ここはまだ古いiteration回目の繰り返し
                    if iteration == 1:
                        set_subplots()
                        f_history.write(history_title_prefix)
                        for data_key in plot_data:
                            for k in plot_data[data_key]:
                                f_history.write(f"\t{data_key} {k}")
                        f_history.write("\n")
                    if iteration >= iteration_start:
                        f_history.write(f"{iteration}\t{time}")
                        for data_key in plot_data:
                            for k in plot_data[data_key]:
                                f_history.write(
                                    f"\t{plot_data[data_key][k][iteration - 1]}"
                                )
                        f_history.write("\n")
                        f_history.flush()  # リアルタイム反映のため
                        if iteration % plot_freq == 0:
                            monitor()
                    if line.startswith("Time = "):
                        if iteration > 0 and iteration % res_eval_freq == 0:
                            remark = remark_string(f"time = {time}")
                            for k, v in plot_data["residual"].items():
                                if len(v) < res_eval_freq:
                                    continue
                                s = relax_delta_sign(v[-res_eval_freq:])
                                if s == 0.0:
                                    continue
                                change_relaxationFactor_in_fvSolution(
                                    param_name=k,
                                    remark=remark,
                                    delta=s * relax_delta,
                                    lower_limit=relax_lower_limit,
                                )
                        iteration += 1  # ここから新しいiteration回目の繰り返し
                        time = line[7:].strip()
                    continue
                elif "Foam::sigFpe::sigHandler(int)" in line:
                    result = "floating point error"  # 発散
                    continue

                s = pat.search(line)
                if s is None:
                    continue
                if s.lastgroup == "final_residual":
                    par = s.group("parameter")
                    if region is not None:
                        par += f" ({region})"
                        par += f" ({region})"
                    res = float(s.group("final_residual"))
                    if (
                        iteration == 1 and par not in plot_data["residual"]
                    ):  # 初回発見時に辞書を自動構築
                        plot_data["residual"][par] = []
                    if len(plot_data["residual"][par]) < iteration:
                        plot_data["residual"][par].append(res)  # データの追加
                    else:
                        plot_data["residual"][par][-1] = res  # データの更新
                elif s.lastgroup == "continuity_global":
                    loc_value = float(s.group("continuity_local"))
                    glob_balue = abs(float(s.group("continuity_global")))
                    loc_key = "sum local"
                    glob_key = "abs global"
                    if region is not None:
                        loc_key += f" ({region})"
                        glob_key += f" ({region})"
                    if iteration == 1:
                        plot_data["continuity"] = {loc_key: [], glob_key: []}
                    if len(plot_data["continuity"][loc_key]) < iteration:
                        plot_data["continuity"][loc_key].append(
                            loc_value
                        )  # データの追加
                        plot_data["continuity"][glob_key].append(glob_balue)
                    else:
                        plot_data["continuity"][loc_key][-1] = loc_value  # データの更新
                        plot_data["continuity"][glob_key][-1] = glob_balue
                elif s.lastgroup == "Courant_max":
                    mean_value = float(s.group("Courant_mean"))
                    max_value = float(s.group("Courant_max"))
                    region = s.group("Courant_region")
                    mean_key = "mean"
                    max_key = "max"
                    iteration2 = iteration
                    if region is not None:
                        mean_key += f" ({region})"
                        max_key += f" ({region})"
                        iteration2 += 1
                    if iteration2 == 1:
                        plot_data.setdefault("Courant", {}).update(
                            {mean_key: [], max_key: []}
                        )
                    if len(plot_data["Courant"][mean_key]) < iteration2:
                        plot_data["Courant"][mean_key].append(mean_value)
                        plot_data["Courant"][max_key].append(max_value)
                    else:
                        plot_data["Courant"][mean_key][-1] = mean_value
                        plot_data["Courant"][max_key][-1] = max_value
                elif s.lastgroup == "Diffusion_max":
                    mean_value = float(s.group("Diffusion_max"))
                    max_value = float(s.group("Diffusion_mean"))
                    region = s.group("Diffusion_region")
                    mean_key = f"mean ({region})"
                    max_key = f"max ({region})"
                    if iteration == 0:
                        plot_data.setdefault("Diffusion", {}).update(
                            {mean_key: [], max_key: []}
                        )
                    if len(plot_data["Diffusion"][mean_key]) < iteration + 1:
                        plot_data["Diffusion"][mean_key].append(mean_value)
                        plot_data["Diffusion"][max_key].append(max_value)
                    else:
                        plot_data["Diffusion"][mean_key][-1] = mean_value
                        plot_data["Diffusion"][max_key][-1] = max_value
                elif s.lastgroup == "region":
                    region = s.group("region")

            process.stdout.close()

    except:
        print()
        print(sys.exc_info())
        process.terminate()

    finally:
        if process.poll() is None:  # 子プロセスが終了しているかどうかを調べます
            process.wait()  # 子プロセスが終了するまで待ちます
            # process.poll()やprocess.wait()でprocess.returncodeにリターンコードを設定する
        if iteration > 1:
            monitor()
        plt.ioff()
        plt.close("all")

    return result, plot_data


def reset_relaxationFactors_in_fvSolution():
    processed = []

    def reset_relaxationFactors_in(path):
        fvSolution_path = os.path.abspath(os.path.join(path, "fvSolution"))
        if os.path.islink(fvSolution_path):
            fvSolution_path = os.path.realpath(fvSolution_path)
            if fvSolution_path in processed:
                return
        processed.append(fvSolution_path)

        fvSolution = dictParse.DictParser(file_name=fvSolution_path)
        relaxationFactors = fvSolution.find_element(
            [{"type": "block", "key": "relaxationFactors"}]
        )["element"]
        if relaxationFactors is None:
            return
        for k in ("equations", "fields"):
            block = relaxationFactors.find_element([{"type": "block", "key": k}])[
                "element"
            ]
            if block is None:
                continue
            for i in reversed(block.find_all_elements([{"type": "dictionary"}])):
                comment = i["element"].find_element(
                    [{"type": "line_comment"}], reverse=True
                )["element"]
                if (
                    comment is not None
                    and pat_remark.search(comment["value"]) is not None
                ):
                    del i["parent"][i["index"]]
            block.set_blank_line(number_of_blank_lines=0)

        string = dictParse.normalize(string=fvSolution.file_string())[0]
        if fvSolution.string != string:
            #            os.rename(fvSolution_path, f'{fvSolution_path}_bak')
            with open(fvSolution_path, "w") as f:
                f.write(string)

    if os.path.isdir("system"):
        reset_relaxationFactors_in("system")
    for r in glob.iglob(os.path.join("system", f"*{os.sep}")):
        reset_relaxationFactors_in(r)


def change_relaxationFactor_in_fvSolution(
    param_name, remark, delta=-0.01, lower_limit=0.3
):
    s = pat_residual.search(param_name)
    if s["region"] is None:
        fvSolution_path = os.path.join("system", "fvSolution")
    else:
        fvSolution_path = os.path.join("system", s["region"], "fvSolution")
    if os.path.islink(fvSolution_path):
        fvSolution_path = os.path.realpath(fvSolution_path)

    param_name = s["parameter"]
    if param_name in ("Ux", "Uy", "Uz"):
        param_name = "U"
    cat, value = misc.getRelaxationFactor(param_name, fvSolution_path)
    if cat is None:
        return
    new_value = min(1.0, max(lower_limit, value + delta))
    if value == new_value:
        return

    # appendEntries.intoFvSolution()を実行していることを想定
    fvSolution = dictParse.DictParser(file_name=fvSolution_path)
    relaxationFactors = fvSolution.find_element(
        [{"type": "block", "key": "relaxationFactors"}]
    )["element"]
    block = relaxationFactors.find_element([{"type": "block", "key": f"{cat}"}])[
        "element"
    ]
    block_end = block.find_element([{"type": "block_end"}], reverse=True)
    i = block.find_element(
        [{"type": "dictionary", "key": param_name}],
        start=block_end["index"],
        reverse=True,
    )["element"]
    comment = i.find_element([{"type": "line_comment"}], reverse=True)["element"]
    if comment is not None and comment["value"].endswith(remark):
        return
    if not remark.startswith("// "):
        remark = f"// {remark}"
    block_end["parent"][block_end["index"] : block_end["index"]] = dictParse.DictParser(
        string=f"\n{param_name}\t{new_value}; {remark}\n"
    )["value"]
    block.set_blank_line(number_of_blank_lines=0)

    with open(fvSolution_path, "w") as f:
        f.write(dictParse.normalize(string=fvSolution.file_string())[0])


def getRelaxationFactors(param_names):
    relax_factors = []
    for k in param_names:
        s = pat_residual.search(k)
        if s["region"] is None:
            fvSolution_path = os.path.abspath(os.path.join("system", "fvSolution"))
        else:
            fvSolution_path = os.path.abspath(
                os.path.join("system", s["region"], "fvSolution")
            )
        p = s["parameter"]
        if p in ("Uy", "Uz"):
            continue
        elif p == "Ux":
            p = "U"
            k = k.replace("Ux", "U", 1)
        value = misc.getRelaxationFactor(p, fvSolution_path)[1]
        if value is not None:
            relax_factors.append({"param": k, "value": value})
    return relax_factors


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handler)  # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        interactive = False
        delete_folders_except_for_zero = False
        enable_all_function_objects = False
        change_relaxation_factors = False
        exec_paraFoam = False
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == "-N":  # Non-interactive
                pass
            elif sys.argv[i] == "-0":
                delete_folders_except_for_zero = True
            elif sys.argv[i] == "-d":
                i += 1
                domains = max(int(sys.argv[i]), 1)
            elif sys.argv[i] == "-f":
                enable_all_function_objects = True
            elif sys.argv[i] == "-p":
                exec_paraFoam = True
            elif sys.argv[i] == "-r":
                change_relaxation_factors = True
            i += 1

    controlDict_path = os.path.join("system", "controlDict")
    fvSolution_path = os.path.join("system", "fvSolution")
    boundary_path = os.path.join("constant", "polyMesh", "boundary")
    for i in (controlDict_path, fvSolution_path, boundary_path):
        if not os.path.isfile(i):
            print(f"エラー: {i}ファイルがありません．")
            sys.exit(1)

    for p in ("*.foam", "*.OpenFOAM", "*.blockMesh"):
        for f in glob.iglob(p):
            os.remove(f)
    if os.path.isdir("dynamicCode"):
        shutil.rmtree("dynamicCode")
    misc.execParaFoam(touch_only=True)
    misc.correctLocation()

    for f in glob.iglob(os.path.join("0", "*.old")):
        shutil.move(f, f[:-4])

    if os.path.isdir("0_bak"):

        def has_diff(dcmp):
            # 左右どちらかにしかないファイル、または内容が異なるファイルがあるか
            if dcmp.left_only or dcmp.right_only or dcmp.diff_files:
                return True
            # サブディレクトリを再帰的にチェック
            return any(has_diff(sub_dcmp) for sub_dcmp in dcmp.subdirs.values())

        if has_diff(filecmp.dircmp("0", "0_bak")):
            print(
                "エラー: あるはずがない0_bakフォルダがあります．"
                "0フォルダと0_bakフォルダを比較して，正しい方を0フォルダに置き換えてから再実行して下さい．"
            )
            sys.exit(1)
        else:
            shutil.rmtree("0_bak")

    shutil.copytree("0", "0_bak")

    if os.path.isdir("processor0"):
        recosntructPar()
        rmObjects.removeProcessorDirs("noLatest")
    latest_time = misc.latestTime()
    if latest_time is None:
        print("エラー: 結果フォルダがありません．")
        if os.path.isdir("0_bak"):
            if os.path.isdir("0"):
                shutil.rmtree("0")
            shutil.move("0_bak", "0")
        sys.exit(1)
    if float(latest_time) != 0.0:
        if interactive:
            delete_folders_except_for_zero = (
                True
                if input(
                    "\n0秒以外のフォルダがあります．"
                    "消して0秒からやり直しますか？ (y/n) > "
                )
                .strip()
                .lower()
                == "y"
                else False
            )
        if delete_folders_except_for_zero:
            misc.execCommand(["foamListTimes", "-rm", "-noZero"])
            rmObjects.removeProcessorDirs()
            latest_time = "0"
        else:
            rmObjects.removeProcessorDirs(
                option=""
                if not os.path.isdir(os.path.join("processor0", latest_time))
                else "noLatest"
            )

    renumberMesh_was_done = misc.isRenumberMeshDone()
    if not renumberMesh_was_done:
        misc.renumberMesh()

    for i in ("dynamicCode", "postProcessing", "logs"):
        if os.path.isdir(i):
            shutil.rmtree(i)
    rmObjects.removeLogPlotPngs()

    threads = misc.cpu_count()
    if interactive:
        while True:
            try:
                domains = max(
                    int(
                        input(
                            "\n計算領域を何個に分割して並列計算しますか？ "
                            f"({threads}個まで, 1だと普通の計算) > "
                        ).strip()
                    ),
                    1,
                )
                break
            except ValueError:
                pass
    domains = min(domains, threads)

    appendEntries.intoFvSolution()
    appendEntries.intoFvSchemes()
    appendEntries.intoControlDict()
    for f in ("potentialFoam.log", "potentialFoam.logfile"):
        if os.path.isfile(f):
            os.remove(f)

    enable_function_list, disable_function_list = misc.controlDictFunctionsList()
    if len(enable_function_list) + len(disable_function_list) > 0:
        print(f"\n{controlDict_path}ファイルのfunctionsで")
        if len(enable_function_list) > 0:
            print("  実行されるものは")
            for i in enable_function_list:
                print(f"  - {i}")
        if len(disable_function_list) > 0:
            print("  実行されないものは")
            for i in disable_function_list:
                print(f"  - {i}")
        print("です．")
        if interactive:
            enable_all_function_objects = (
                True
                if input(
                    f"全てを実行するように{controlDict_path}ファイルを書き換えますか？"
                    " (y/n, 多くの場合nのはず) > "
                )
                .strip()
                .lower()
                == "y"
                else False
            )
            change_relaxation_factors = (
                True
                if input(
                    f"\n残差が落ちにくい時に，{fvSolution_path}ファイルの緩和係数"
                    "（relaxationFactors）を変化させますか？ (y/n) > "
                )
                .strip()
                .lower()
                == "y"
                else False
            )

    if enable_all_function_objects:
        misc.setEnabledInControlDictFunctions(enabled=True)

    if change_relaxation_factors:
        reset_relaxationFactors_in_fvSolution()

    if domains != 1:
        should_rm_processor_dirs = False
        processor_dirs = set()
        for d in glob.iglob(f"processor*{os.sep}"):
            try:
                processor_dirs.add(int(d[len("processor") : -len(os.sep)]))
            except:
                pass
        if processor_dirs != set(range(domains)):
            should_rm_processor_dirs = True
        if not should_rm_processor_dirs and os.path.isfile(decomposeParDict_path):
            numberOfSubdomains = dictParse.DictParser(
                file_name=decomposeParDict_path
            ).find_element(
                [
                    {"type": "dictionary", "key": "numberOfSubdomains"},
                    {"type": "integer"},
                ]
            )["element"]
            if (
                numberOfSubdomains is not None
                and int(numberOfSubdomains["value"]) != domains
            ):
                should_rm_processor_dirs = True
        if should_rm_processor_dirs:
            for d in processor_dirs:
                shutil.rmtree(f"processor{d}")
        if not os.path.isdir("processor0"):
            decomposePar()

    application = misc.getApplication()
    while True:
        start_time = misc.latestTime()
        result, plot_data = plot_runner(
            application=application,
            start_time=start_time,
            relax_delta=relaxationFactor_delta_usual,
            relax_lower_limit=relaxationFactor_lower_limit,
        )
        relax_factors = getRelaxationFactors(plot_data["residual"].keys())
        if domains != 1 and os.path.isdir("processor0"):
            recosntructPar()

        if result == "success" or not change_relaxation_factors:
            break
        elif result == "not enough slots":
            rmObjects.removeProcessorDirs()
            domains -= 1
            decomposePar()
            continue

        max_relax_factor = 1.0
        if len(relax_factors) > 0:
            max_relax_factor = max([i["value"] for i in relax_factors])

        if max_relax_factor <= relaxationFactor_lower_limit:
            if float(start_time) != 0.0:
                for d in glob.iglob(f"processor*{os.sep}"):
                    shutil.rmtree(os.path.join(d, start_time))
                shutil.rmtree(start_time)  # ひとつ前の記録時間に戻ってリスタート
            else:
                break
        else:
            remark = remark_string("restart")
            for k in plot_data["residual"].keys():
                change_relaxationFactor_in_fvSolution(
                    param_name=k,
                    remark=remark,
                    delta=-relaxationFactor_delta_restart,
                    lower_limit=relaxationFactor_lower_limit,
                )
            rmObjects.removeLogPlotPngs()
            os.remove(f"{application}.log")

    rmObjects.removeProcessorDirs("noLatest")
    restore_zero_folder()

    if plot_data["continuity"]:
        cont_max = max(
            [
                v[-1]
                for k, v in plot_data["continuity"].items()
                if k.startswith("sum local")
            ]
        )
        res_max = max([v[-1] for v in plot_data["residual"].values()])
        print(
            "\n最後の計算における\n"
            f"  連続の式の局所誤差の最大値は{cont_max}\n"
            f"  残差の最大値は{res_max}\n"
            "でした．"
        )

    if result == "success":
        print("\n計算が無事に終了しました．")
        if change_relaxation_factors:
            print("最終的な緩和係数（relaxationFactors）は以下になりました：")
            for i in relax_factors:
                print(f"  {i['param']}: {i['value']}")
    else:
        if change_relaxation_factors:
            print(
                "\n\033[3;4;5m(ERROR) 緩和係数（relaxationFactors）を下限の"
                f"{relaxationFactor_lower_limit}まで下げても計算が発散します．\033[m"
            )
        else:
            print("\n\033[3;4;5m(ERROR) 計算が発散しました．\033[m")
        print(
            "\033[3;4;5m「DEXCS OpenFOAM メモ」(0_OpenFOAMメモ.pdf) "
            "の「発散する場合の対処法」の部分を見れば発散が回避できるかもしれません．\033[m"
        )

    if interactive:
        exec_paraFoam = (
            True
            if input("\nparaFoamを実行しますか？ (y/n) > ").strip().lower() == "y"
            else False
        )
    misc.execParaFoam(touch_only=not exec_paraFoam)

    rmObjects.removeInessentials()
    sys.exit(0 if result == "success" else 1)
