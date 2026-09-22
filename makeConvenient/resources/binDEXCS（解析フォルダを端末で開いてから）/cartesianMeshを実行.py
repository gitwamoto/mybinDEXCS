#!/usr/bin/env python
# -*- coding: utf-8 -*-
# cartesianMeshを実行.py
# by Yukiharu Iwamoto
# 2026/9/20 7:56:05 PM

# ---- オプション ----
# なし -> インタラクティブモードで実行．オプションが1つでもあると非インタラクティブモードになる
# -N -> 非インタラクティブモードで実行
# -2 cartesian2DMeshで2次元メッシュを作る．emptyのpatchはx-y平面に平行でなければならない
# -b back_name -> 【-2オプションがある時のみ有効】(zが大きい)後側patchの名前をback_nameにする．
#                 このオプションがない場合，backという名前になる．
# -d domains -> 計算領域をdomains個に分割して並列計算を行う，1だと普通の計算
# -f front_name -> 【-2オプションがある時のみ有効】(zが大きい)前側patchの名前をfront_nameにする．
#                  このオプションがない場合，frontという名前になる．
# -p -> paraFoamを実行する

import os
import sys
import signal
import shutil
import re
import glob
from utilities import misc
from utilities import rmObjects
from utilities import dictParse


interactive = False
two_dimensional = False
front_name = "front"
back_name = "back"
domains = 1
exec_paraFoam = False
cases_path = "cases_for_cfmesh"
pat_region_boundary = re.compile(  # マルチリージョン解析の時の領域境界名のパターン
    "(?P<region_from>(?:(?!__).)+)__to__(?P<region_to>(?:(?!__).)+)(?P<number>__[0-9]+)?"
)
meshDict_path = os.path.join("system", "meshDict")
meshDict_3D_path = meshDict_path + "_3D"


def handler(signum, frame):
    if two_dimensional and os.path.isfile(meshDict_3D_path):
        os.rename(meshDict_3D_path, meshDict_path)  # can overwrite
    rmObjects.removeInessentials()
    sys.exit(1)


def preparation():
    if not os.path.isfile(meshDict_path):
        print(f"エラー: {meshDict_path}ファイルがありません．")
        sys.exit(1)

    if os.path.isdir("dynamicCode"):
        shutil.rmtree("dynamicCode")
    rmObjects.removeProcessorDirs()
    for f in (
        "cartesianMesh.log",
        "cartesianMesh.logfile",
        "cartesian2DMesh.log",
        "cartesian2DMesh.logfile",
    ):
        if os.path.isfile(f):
            os.remove(f)


def cartesianMesh():
    controlDict_path = os.path.join("system", "controlDict")
    if not os.path.isfile(
        controlDict_path
    ):  # controlDictがないとcartesianMeshが動かない
        with open(controlDict_path, "w") as f:
            f.write(
                "FoamFile\n"
                "{\n"
                "\tversion\t2.0;\n"
                "\tformat\tascii;\n"
                "\tclass\tdictionary;\n"
                '\tlocation\t"system";\n'
                "\tobject\tcontrolDict;\n"
                "}\n"
                "deltaT\t1;\n"
                "writeControl\ttimeStep;\n"
                "writeInterval\t1;\n"
            )

    meshDict = dictParse.DictParser(file_name=meshDict_path)

    # renameBoundary
    # {
    #   newPatchNames
    #   {
    #     PATCH_NAME
    #     {
    #       newName PATCH_NAME;
    #       type empty;
    #     }
    #     ...
    empty_list = []
    for p in meshDict.find_all_elements(
        [
            {"type": "block", "key": "renameBoundary"},
            {"type": "block", "key": "newPatchNames"},
            {"type": "block"},
        ]
    ):
        p = p["element"]
        if (
            p.find_element([{"type": "dictionary", "key": "type"}, {"type": "word"}])[
                "element"
            ]["value"]
            == "empty"
        ):
            empty_list.append(
                p.find_element(
                    [{"type": "dictionary", "key": "newName"}, {"type": "word"}]
                )["element"]["value"]
            )

    if two_dimensional:
        # surfaceFile "constant/triSurface/FMS_NAME.fms"; // (mandatory)
        surfaceFile = meshDict.find_element(
            [{"type": "dictionary", "key": "surfaceFile"}, {"type": "string"}]
        )["element"]
        stl_file_name_wo_ext = os.path.splitext(surfaceFile["value"].strip('"'))[
            0
        ]  # .fmsを取り除く
        stl_2D_file_name = f"{stl_file_name_wo_ext}_2D.stl"  # 2次元の場合はfmsファイルでなくても十分であることが多い
        should_write = True
        with open(stl_2D_file_name, "w") as f:
            for line in open(f"{stl_file_name_wo_ext}.stl", "r"):
                if "endsolid" in line and line.split()[-1] in empty_list:
                    should_write = True
                elif "solid" in line and line.split()[-1] in empty_list:
                    should_write = False
                elif should_write:
                    f.write(line)
        surfaceFile["value"] = f'"{stl_2D_file_name}"'
        os.rename(meshDict_path, meshDict_3D_path)  # can overwrite
        with open(meshDict_path, "w") as f:
            f.write(dictParse.normalize(string=meshDict.file_string())[0])

    def mappedWall_treatment(boundary):
        for p in boundary.find_all_elements(
            [
                {
                    "type": "list",
                },
                {"type": "block"},
            ]
        ):
            p = p["element"]
            t = p.find_element(
                [{"type": "dictionary", "key": "type"}, {"except type": "ignorable"}]
            )["element"]
            if (
                t["value"] == "mappedWall"
                and p.find_element([{"type": "dictionary"}, {"key": "sampleRegion"}])[
                    "element"
                ]
                is None
                and p.find_element([{"type": "dictionary"}, {"key": "samplePatch"}])[
                    "element"
                ]
                is None
            ):
                m = pat_region_boundary.match(p["key"])
                block_end = p.find_element([{"type": "block_end"}], reverse=True)[
                    "index"
                ]
                p["value"][block_end:block_end] = dictParse.DictParser(
                    string="sampleMode\tnearestPatchFaceAMI;\n"
                    f"sampleRegion\t{m['region_to']}; // 相手の領域名\n"
                    f"samplePatch\t{m['region_to']}__to__{m['region_from']}"
                    f"{'' if m['number'] is None else m['number']}; // 相手のパッチ名\n"
                )["value"]

    cfMesh = "cartesian2DMesh" if two_dimensional else "cartesianMesh"
    if domains != 1:
        rmObjects.removeProcessorDirs()
        decomposeParDict_path = os.path.join("system", "decomposeParDict")
        decomposeParDict_bak_path = f"{decomposeParDict_path}_bak"
        if os.path.isfile(decomposeParDict_path):
            os.rename(decomposeParDict_path, decomposeParDict_bak_path)
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
                "method\tscotch;\n"  # 複雑な形状や境界条件がある場合に最適．デフォルトで推奨されることが多い．
            )
        succeed = misc.execCommand(["preparePar", "-noFunctionObjects"])[1] == 0
        if succeed:
            succeed = (
                misc.execCommand(
                    [
                        "mpirun",
                        "-np",
                        f"{domains}",
                        cfMesh,
                        "-parallel",
                        "-noFunctionObjects",
                    ],
                    f"{cfMesh}.log",
                )[1]
                == 0
            )
        if succeed:
            pat = re.compile(r"(?:\./)?processor([0-9]+)/$")
            for p in glob.iglob(f"processor[0-9]*{os.sep}"):
                if pat.match(p):
                    boundary_path = os.path.join(p, "constant", "polyMesh", "boundary")
                    boundary = dictParse.DictParser(file_name=boundary_path)
                    mappedWall_treatment(boundary)
                    string = dictParse.normalize(string=boundary.file_string())[0]
                    if boundary.string != string:
#                        os.rename(boundary_path, f'{boundary_path}_bak')
                        with open(boundary_path, "w") as f:
                            f.write(string)
            succeed = (
                misc.execCommand(
                    [
                        "reconstructParMesh",
                        "-constant",  # -constantは，constantディレクトリ内のファイルも再構築する．
                        "-mergeTol",
                        "1.0e-06",
                        "-noFunctionObjects",
                    ]
                )[1]
                == 0
            )
        rmObjects.removeProcessorDirs()
        if os.path.isfile(decomposeParDict_bak_path):
            os.rename(decomposeParDict_bak_path, decomposeParDict_path)
        if not succeed:
            sys.exit(1)
    elif misc.execCommand([cfMesh, "-noFunctionObjects"], f"{cfMesh}.log")[1] != 0:
        sys.exit(1)

    boundary_path = os.path.join("constant", "polyMesh", "boundary")
    boundary = dictParse.DictParser(file_name=boundary_path)
    if two_dimensional:
        os.rename(meshDict_path, meshDict_path + "_2D")  # can overwrite
        os.rename(meshDict_3D_path, meshDict_path)  # can overwrite
        boundary.find_element(
            [{"type": "list"}, {"type": "block", "key": "topEmptyFaces"}]
        )["element"]["key"] = front_name
        boundary.find_element(
            [{"type": "list"}, {"type": "block", "key": "bottomEmptyFaces"}]
        )["element"]["key"] = back_name
    mappedWall_treatment(boundary)
    string = dictParse.normalize(string=boundary.file_string())[0]
    if boundary.string != string:
#            os.rename(boundary_path, f'{boundary_path}_bak')
        with open(boundary_path, "w") as f:
            f.write(string)

    misc.convertMillimeterIntoMeter()
    misc.removePatchesHavingNoFaces()  # フェイスを1つも含まないパッチを取り除く
    if two_dimensional and misc.execCommand(["flattenMesh"])[1] != 0:
        sys.exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handler)  # Ctrl+Cで行う処理
    misc.showDirForPresentAnalysis(__file__)

    if len(sys.argv) == 1:
        interactive = True
    else:
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == "-N":  # Non-interactive
                pass
            elif sys.argv[i] == "-2":
                two_dimensional = True
            elif sys.argv[i] == "-b":
                i += 1
                back_name = sys.argv[i]
            elif sys.argv[i] == "-d":
                i += 1
                domains = max(int(sys.argv[i]), 1)
            elif sys.argv[i] == "-f":
                i += 1
                front_name = sys.argv[i]
            elif sys.argv[i] == "-p":
                exec_paraFoam = True
            i += 1

    cwd = os.getcwd()  # 絶対パス
    if os.path.isdir(cases_path):
        # glob.iglob() は、デフォルトでは現在の作業ディレクトリ（カレントディレクトリ）からの相対パスを基準にイテレーターを保持して評価します。
        for c in glob.iglob(os.path.join(cases_path, f"*{os.sep}")):
            os.chdir(c)
            preparation()
            os.chdir(cwd)
    else:
        preparation()

    threads = misc.cpu_count()
    if interactive:
        while True:
            try:
                domains = max(
                    int(
                        input(
                            "計算領域を何個に分割して並列計算しますか？ "
                            f"({threads}個まで, 1だと普通の計算) > "
                        ).strip()
                    ),
                    1,
                )
                break
            except ValueError:
                pass
        two_dimensional = (
            True
            if input(
                "\ncartesian2DMeshで2次元メッシュを作りますか？\n"
                "*** 2次元メッシュでは，empty境界がx-y平面に平行でないといけません． (y/n) > "
            )
            .strip()
            .lower()
            == "y"
            else False
        )
        if two_dimensional:
            front_name = (
                input(
                    "(zが大きい)前側patchの名前を決めて下さい． (Enterのみ: front) > "
                ).strip()
                or "front"
            )
            back_name = (
                input(
                    "(zが小さい)後側patchの名前を決めて下さい． (Enterのみ: back) > "
                ).strip()
                or "back"
            )
    domains = min(domains, threads)

    if os.path.isdir(cases_path):
        # glob.iglob() は、デフォルトでは現在の作業ディレクトリ（カレントディレクトリ）からの相対パスを基準にイテレーターを保持して評価します。
        for c in glob.iglob(os.path.join(cases_path, f"*{os.sep}")):
            os.chdir(c)
            cartesianMesh()
            os.chdir(cwd)
    else:
        cartesianMesh()

    if os.path.isdir(cases_path):
        # glob.iglob() は、デフォルトでは現在の作業ディレクトリ（カレントディレクトリ）からの相対パスを基準にイテレーターを保持して評価します。
        for c in glob.iglob(os.path.join(cases_path, f"*{os.sep}")):
            os.chdir(c)
            misc.execCheckMesh()
            rmObjects.removeInessentials()
            os.chdir(cwd)
            dst = os.path.join(cwd, "constant", os.path.basename(os.path.normpath(c)))
            os.makedirs(dst, exist_ok=True)
            dst_polyMesh = os.path.join(dst, "polyMesh")
            if os.path.isdir(dst_polyMesh):
                shutil.rmtree(dst_polyMesh)
            shutil.move(os.path.join(cwd, c, "constant", "polyMesh"), dst)
    else:
        misc.execCheckMesh()
        rmObjects.removeInessentials()
        cartesianMesh()

    if interactive:
        exec_paraFoam = (
            True
            if input("\nparaFoamを実行しますか？ (y/n) > ").strip().lower() == "y"
            else False
        )
    misc.execParaFoam(touch_only=not exec_paraFoam, ambient=0.0, diffuse=1.0)
