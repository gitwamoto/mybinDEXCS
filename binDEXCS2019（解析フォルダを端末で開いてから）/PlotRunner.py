#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PlotRunner.py
# by Yukiharu Iwamoto
# 2026/2/21 9:03:36 PM

import subprocess
import sys
import re

def run_foam_solver(solver_name):
    # ソルバーをサブプロセスとして実行（標準出力をパイプで取得）
    process = subprocess.Popen(
        ['stdbuf', '-oL', solver_name], # stdbuf -oL はバッファリングを防ぎ、リアルタイム性を高める
        stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT,
        text = True, # 出力を文字列として扱う
        bufsize = 1 # Python側でも行単位でバッファリング
    )

    try:
        # iter(process.stdout.readline, '') は readline() を
        # 空文字（プロセス終了）が返るまで繰り返す Pythonic な書き方です
        for line in iter(process.stdout.readline, ''):
            # 1. 端末へそのまま表示（PyFOAMの挙動）
            sys.stdout.write(line)
            sys.stdout.flush()

            # 2. アクションの判定（例：残差の監視など）
            if "Time =" in line:
                # ここに解析ロジック
                pass

    except KeyboardInterrupt:
        print("\n[Terminating solver...]")
        process.terminate()
    finally:
        process.wait()

import subprocess
import sys
import re
import matplotlib.pyplot as plt

def run_foam_live_plot(solver_name):
    # --- 1. データ格納用のリスト ---
    times = []
    residuals = {} # フィールドごとの残差
    cont_errors = {"local": [], "global": [], "cumulative": []}
    courant_nums = {"max": [], "mean": []}

    # --- 2. 正規表現パターン ---
    # Time (横軸)
    re_time = re.compile(r"^Time = (\d+\.?\d*)")
    # 残差 (Final residualのみ抽出)
    re_resid = re.compile(r"Solving for (\w+),.*Final residual = ([\d.e+-]+)")
    # 連続の式誤差
    re_cont = re.compile(r"time step continuity errors : sum local = ([\d.e+-]+), global = ([\d.e+-]+), cumulative = ([\d.e+-]+)")
    # クーラン数
    re_courant = re.compile(r"Courant Number mean: ([\d.e+-]+) max: ([\d.e+-]+)")

    # --- 3. Matplotlib の設定 ---
    plt.ion() # インタラクティブモードON
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
    plt.subplots_adjust(hspace=0.3)

    # ソルバー起動
    process = subprocess.Popen(
        ["stdbuf", "-oL", solver_name],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )

    try:
        current_t = None
        for line in iter(process.stdout.readline, ""):
            # 1. 標準出力をそのまま表示
            sys.stdout.write(line)
            sys.stdout.flush()

            # 2. データの抽出
            m_time = re_time.match(line)
            if m_time:
                current_t = float(m_time.group(1))
                times.append(current_t)
                # 新しいTimeステップに入った際、グラフを更新（例：10ステップごと）
                if len(times) % 10 == 0:
                    update_plots(ax1, ax2, ax3, times, residuals, cont_errors, courant_nums)

            m_resid = re_resid.search(line)
            if m_resid:
                field, val = m_resid.groups()
                residuals.setdefault(field, []).append(float(val))

            m_cont = re_cont.search(line)
            if m_cont:
                cont_errors["local"].append(float(m_cont.group(1)))
                cont_errors["global"].append(float(m_cont.group(2)))

            m_courant = re_courant.search(line)
            if m_courant:
                courant_nums["mean"].append(float(m_courant.group(1)))
                courant_nums["max"].append(float(m_courant.group(2)))

    except KeyboardInterrupt:
        process.terminate()
    finally:
        process.wait()
        plt.ioff()
        plt.show()

def update_plots(ax1, ax2, ax3, times, residuals, cont_errors, courant_nums):
    # 残差プロット (対数軸)
    ax1.clear()
    for field, vals in residuals.items():
        # 長さをtimesに合わせる（簡易処理）
        ax1.plot(times[:len(vals)], vals, label=field)
    ax1.set_yscale('log')
    ax1.set_ylabel('Final Residual')
    ax1.legend(loc='upper right', fontsize='small')
    ax1.grid(True, which="both", ls="-", alpha=0.5)

    # 連続の式誤差
    ax2.clear()
    if cont_errors["local"]:
        ax2.plot(times[:len(cont_errors["local"])], cont_errors["local"], label='local')
        ax2.set_yscale('log')
        ax2.set_ylabel('Cont. Error')
        ax2.legend(loc='upper right')

    # クーラン数
    ax3.clear()
    if courant_nums["max"]:
        ax3.plot(times[:len(courant_nums["max"])], courant_nums["max"], label='max')
        ax3.plot(times[:len(courant_nums["mean"])], courant_nums["mean"], label='mean')
        ax3.set_ylabel('Courant Number')
        ax3.set_xlabel('Time [s]')
        ax3.legend(loc='upper right')

    plt.pause(0.01) # 描画を反映させるための短い一時停止

#if __name__ == "__main__":
#    run_foam_live_plot("simpleFoam")

import subprocess
import sys
import re
import matplotlib.pyplot as plt

def trigger_action(iteration, residuals):
    """
    残差が目標値を下回ったときに実行されるカスタムアクション
    """
    print(f"\n{'!'*40}")
    print(f"検知: Iteration {iteration} で全残差が閾値を下回りました。")
    print(f"現在の残差: {residuals}")
    print(f"{'!'*40}\n")
    
    # 例1: 計算を安全に終了させる (OpenFOAMに停止を命令するファイルを生成)
    # with open("comms/finish", "w") as f: f.write("stop")
    
    # 例2: 独自の事後処理スクリプトを走らせる
    # subprocess.run(["python3", "post_process.py"])
    
    return True # 計算を止める場合はTrueを返す

def run_foam_with_action(solver_name, threshold=1e-5):
    # --- 1. 正規表現の設定 ---
    re_time = re.compile(r"^Time = (\d+)")
    # サブイタレーションの最後（Final residual）をキャプチャ
    re_resid = re.compile(r"Solving for (\w+),.*Final residual = ([\d.e+-]+)")

    # データ格納
    current_residuals = {}
    times = []
    
    # ソルバー起動 (バッファリング無効化)
    process = subprocess.Popen(
        ["stdbuf", "-oL", solver_name],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )

    print(f"監視開始: ターゲット残差 = {threshold}")

    try:
        current_t = None
        for line in iter(process.stdout.readline, ""):
            # 1. 端末へ出力（必須要件）
            sys.stdout.write(line)
            sys.stdout.flush()

            # 2. Timeの更新を検知
            m_time = re_time.match(line)
            if m_time:
                # 前のTimeステップの結果で判定を行う
                if current_residuals:
                    # 全てのフィールド（p, U, k等）が閾値以下かチェック
                    if all(v < threshold for v in current_residuals.values()):
                        stop_needed = trigger_action(current_t, current_residuals)
                        if stop_needed:
                            print("[INFO] アクションに基づき、ソルバーを終了します。")
                            process.terminate()
                            break
                
                current_t = int(m_time.group(1))
                # 次のステップのために残差をクリア
                current_residuals = {}

            # 3. 残差の抽出
            m_resid = re_resid.search(line)
            if m_resid:
                field, val = m_resid.groups()
                current_residuals[field] = float(val)

    except KeyboardInterrupt:
        process.terminate()
    finally:
        process.wait()

#if __name__ == "__main__":
#    # 使いかた: 第2引数に目標残差を設定
#    run_foam_with_action("simpleFoam", threshold=1e-6)