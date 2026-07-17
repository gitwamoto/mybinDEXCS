#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 連続計算雛形.py
# by Yukiharu Iwamoto
# 2026/6/16 9:52:16 PM

import os
import signal
import sys
import shutil
import glob

binDEXCS_path = os.path.expanduser(
    "~/Desktop/binDEXCS（解析フォルダを端末で開いてから）"
)  # dakuten.py -j -f <path> で濁点を結合しておく
if binDEXCS_path not in sys.path:
    sys.path.append(binDEXCS_path)
from utilities import appendEntries
from utilities import dakuten
from utilities import dictParse
from utilities import findMaxMin
from utilities import misc
from utilities import ofpolymesh
from utilities import rmObjects
from utilities import setComment

domains = 32  # 分割領域

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # Ctrl+Cで終了

    dir_name = os.path.abspath(
        os.path.dirname(__file__)
    )  # このファイルがあるフォルダの名前

    # 上書きされているかもしれないファイルを元々のファイルで上書き
    for d in ("elbow_vane01_10", "elbow_vane02_10", "elbow_vane03_10", "elbow_wovane"):
        os.chdir(os.path.join(dir_name, d))

        if os.path.exists("0"):
            shutil.rmtree("0")
        shutil.copytree(os.path.join(dir_name, "elbow_format", "0"), "0")

        shutil.copyfile(
            os.path.join(dir_name, "elbow_format", "setting.txt"), "setting.txt"
        )

        fvSolution = os.path.join("system", "fvSolution")
        shutil.copyfile(os.path.join(dir_name, "elbow_format", fvSolution), fvSolution)

        controlDict = os.path.join("system", "controlDict")
        shutil.copyfile(
            os.path.join(dir_name, "elbow_format", controlDict), controlDict
        )

        turbulenceProperties = os.path.join("constant", "turbulenceProperties")
        shutil.copyfile(
            os.path.join(dir_name, "elbow_format", turbulenceProperties),
            turbulenceProperties,
        )

    # ならし計算
    for d in ("elbow_vane01_10", "elbow_vane02_10", "elbow_vane03_10", "elbow_wovane"):
        os.chdir(os.path.join(dir_name, d))

        if os.path.isdir(
            "dynamicCode"
        ):  # どうせ作り直すので，dynamicCodeフォルダを削除
            shutil.rmtree("dynamicCode")

        with open("setting.txt", "r") as f:
            lines = f.readlines()
        os.rename("setting.txt", "setting_bak.txt")
        for i in range(len(lines)):
            lines[i] = setComment.uncomment(
                setComment.comment(lines[i], "// accurate"), "// shakedown"
            )
            # 行の末尾に// accurateと書かれている行をコメントアウトし，末尾に// shakedownと書かれている行をアンコメントする
            # '// accurate', '// shakedown'の文字は，スペースの個数を含めて完全に一致する必要あり
        with open("setting.txt", "w") as f:
            f.writelines(lines)

        fvSolution = os.path.join("system", "fvSolution")
        with open(fvSolution, "r") as f:
            lines = f.readlines()
        os.rename(fvSolution, f"{fvSolution}_bak")
        for i in range(len(lines)):
            lines[i] = setComment.uncomment(
                setComment.comment(lines[i], "// accurate"), "// shakedown"
            )
            # 行の末尾に// accurateと書かれている行をコメントアウトし，末尾に// shakedownと書かれている行をアンコメントする
            # '// accurate', '// shakedown'の文字は，スペースの個数を含めて完全に一致する必要あり
        with open(fvSolution, "w") as f:
            f.writelines(lines)

        misc.execCommand(
            [os.path.join(binDEXCS_path, "計算.py"), "-d", f"{domains}", "-0", "-r"]
        )
        # ---- 計算.pyのオプション ----
        # なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
        # -N -> 非インタラクティブモードで実行
        # -0 -> 0秒以外のフォルダがある場合，それらを消す．つまり0秒から計算をやり直す
        # -d domains -> 計算領域をdomains個に分割して並列計算を行う．1だと普通の計算
        # -f -> system/controlDictに書かれているfunctionsを全て計算中に実行するように，controlDictを書き変える
        # -p -> paraFoamを実行する
        # -r -> 残差が落ちにくい時に緩和係数を変化させる

    # 正確な計算
    for d in ("elbow_vane01_10", "elbow_vane02_10", "elbow_vane03_10", "elbow_wovane"):
        os.chdir(os.path.join(dir_name, d))

        with open("setting.txt", "r") as f:
            lines = f.readlines()
        os.rename("setting.txt", "setting_bak.txt")
        for i in range(len(lines)):
            lines[i] = setComment.comment(
                setComment.uncomment(lines[i], "// accurate"), "// shakedown"
            )
            # 行の末尾に// accurateと書かれている行をアンコメントし，末尾に// shakedownと書かれている行をコメントアウトする
            # '// accurate', '// shakedown'の文字は，スペースの個数を含めて完全に一致する必要あり
        with open("setting.txt", "w") as f:
            f.writelines(lines)

        fvSolution = os.path.join("system", "fvSolution")
        with open(fvSolution, "r") as f:
            lines = f.readlines()
        os.rename(fvSolution, f"{fvSolution}_bak")
        for i in range(len(lines)):
            lines[i] = setComment.comment(
                setComment.uncomment(lines[i], "// accurate"), "// shakedown"
            )
            # 行の末尾に// accurateと書かれている行をアンコメントし，末尾に// shakedownと書かれている行をコメントアウトする
            # '// accurate', '// shakedown'の文字は，スペースの個数を含めて完全に一致する必要あり
        with open(fvSolution, "w") as f:
            f.writelines(lines)

        misc.execCommand(
            [os.path.join(binDEXCS_path, "計算.py"), "-d", f"{domains}", "-r"]
        )
        # ---- 計算.pyのオプション ----
        # なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
        # -N -> 非インタラクティブモードで実行
        # -0 -> 0秒以外のフォルダがある場合，それらを消す．つまり0秒から計算をやり直す
        # -d domains -> 計算領域をdomains個に分割して並列計算を行う．1だと普通の計算
        # -f -> system/controlDictに書かれているfunctionsを全て計算中に実行するように，controlDictを書き変える
        # -p -> paraFoamを実行する
        # -r -> 残差が落ちにくい時に緩和係数を変化させる
