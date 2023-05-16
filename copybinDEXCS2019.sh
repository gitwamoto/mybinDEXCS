#!/bin/bash
# copybinDEXCS2019.sh
# by Yukiharu Iwamoto
# 2023/5/14 4:04:12 PM

# ダブルクリックしても
#     +-------------------------------------------------------------+
#     |  "copybinDEXCS2019.sh"を実行しますか? それとも内容を表示しますか?  |
#     +-------------------------------------------------------------+
# という内容のウインドウが表示されず，単にテキストエディタが開く場合の対処法
# (1) copybinDEXCS2019.sh を右クリック→「プロパティ」→「アクセス権」
# (2) 「プログラムとして実行可能」をチェック

# 引数をつけて実行すると，sudoコマンドを行わなくなる．

RSYNC_OPTION='--delete'

if [ -e /opt/OpenFOAM/OpenFOAM-v1906/etc/bashrc ]; then
	dexcs_version=2019
elif [ -e /usr/lib/openfoam/openfoam2106/etc/bashrc ]; then
	dexcs_version=2021
else
	zenity --error --text='未対応のDEXCSのバージョンです．' --width=500
	exit 1
fi

if [ $# -eq 0 ]; then
	imsudoer=true
else
	imsudoer=false
fi

wget_from_google_drive() {
	# $1: id
	# $2: path to a file to save
	cookie=$(mktemp /tmp/cookie.XXXXXXX)
	document=$(mktemp /tmp/document.XXXXXXX)
	wget --no-check-certificate --save-cookies="$cookie" --output-document="$document" \
		'https://drive.google.com/uc?export=download&id='"$1"
	if grep --quiet 'Google Drive - Virus scan warning' "$document" ; then
		# https://qiita.com/IsHYuhi/items/e4afc0163019343d9664
		code=$(awk '/_warning_/ {print $NF}' "$cookie")
		if [ -z "$code" ]; then # zオプションは文字列の長さが0の時にtrueになります。
			code=$(grep -E -o 'id='\"'downloadForm'\"' action='\"'[^'\"']+' "$document" | \
			awk -F ';' '{for(i = 1; i <= NF; i++){if(substr($i, 1, 8) == '\"'confirm='\"') print substr($i, 9)}}')
		fi
		wget --no-check-certificate --load-cookies="$cookie" --output-document="$document" \
			'https://drive.google.com/uc?export=download&confirm='"$code"'&id='"$1"
	fi
	if [ -s "$document" ]; then # -s -> True if a file size is greater than 0
		mv -f "$document" "$2"
	else
		rm "$document"
	fi
	rm "$cookie"
}

cd ~

# dakuten.py -j -f <path> で濁点を結合しておく
binDEXCS=binDEXCS2019（解析フォルダを端末で開いてから）

if [ ! -d Desktop/"$binDEXCS" ]; then
	mkdir Desktop/"$binDEXCS"
fi

((trial=0))
for d in /mnt/DEXCS2-6left_student /mnt/DEXCS2-6right_student; do
	if [ -d "$d" ] && [ -n "$(ls -A $d)" ]; then
		rsync -av "$RSYNC_OPTION" \
			--exclude '.*DS_Store' \
			--exclude '._*' \
			--exclude '~*' \
			--exclude '*.pyc' \
			"$d"/Desktop/"$binDEXCS"/ Desktop/"$binDEXCS"
		chmod -R +x Desktop/"$binDEXCS"/*.py

		rsync -av "$RSYNC_OPTION" \
			--include '*.FCMacro' \
			--include 'sHM.png' \
			--exclude '*' \
			"$d"/.FreeCAD/ .FreeCAD
		chmod -R +x .FreeCAD/*.FCMacro

		rsync -av "$d"/マニュアル/bin/copybinDEXCS2019.sh Desktop/copybinDEXCS2019.sh
		chmod +x Desktop/copybinDEXCS2019.sh

		rsync -av "$RSYNC_OPTION" \
			--exclude '.*DS_Store' \
			--exclude '._*' \
			--exclude '~*' \
			"$d"/Desktop/matplotlibwx/ Desktop/matplotlibwx
		chmod -R +x Desktop/matplotlibwx/*.py

		break
	fi
	((++trial))
done
if [ "$trial" -eq 2 ]; then
	[ ! -d Desktop/"$binDEXCS"/utilities ] && mkdir -p Desktop/"$binDEXCS"/utilities
	[ ! -d Desktop/"$binDEXCS" ] && mkdir -p Desktop/"$binDEXCS"
	wget_from_google_drive 1596JB5DuJCLQ5eNSR20wozdogL0PcdhH Desktop/$binDEXCS/0_OPENFOAMメモ.pdf
	wget_from_google_drive 1O0xabYFdpEKFXWdik_kHgCW5kZCXMsqQ Desktop/$binDEXCS/0秒以外のフォルダを消す.py
	wget_from_google_drive 1bUYUJyfJGNYVyMfxEL_B9cxR5OV9hCNs Desktop/$binDEXCS/乱流量を求める.py
	wget_from_google_drive 1HfkMstMaSuLRuTRAPVrYL0WnQoT1TgIy Desktop/$binDEXCS/力と力のモーメントを求める.py
	wget_from_google_drive 16Ke7AuF_CfwYS4scFLiIccvF2BWhzmfQ Desktop/$binDEXCS/logファイルをプロット.py
	wget_from_google_drive 1NPeUGslGYdUQpv4rb69VzBhdZoBBUv7f Desktop/$binDEXCS/半角に出来る文字は全て半角に.py
	wget_from_google_drive 1AZdFg1FXmKi0gtFjGmweOWYiZC8gkQ9t Desktop/$binDEXCS/improveMeshQualityを実行.py
	wget_from_google_drive 1rdetKPUgTBUVOhO8i0JTBGX5uVxEMK68 Desktop/$binDEXCS/cartesianMeshを実行.py
	wget_from_google_drive 1ctGaq95vPK0gYe8SFJyKVkEhq4Fqh0BM Desktop/$binDEXCS/snappyHexMeshを実行.py
	wget_from_google_drive 1A6Syfx__Ngs3HttGsivLdeFDoNSi4vzn Desktop/$binDEXCS/0秒以外を除いてコピーを作る.py
	wget_from_google_drive 1O7VAOuWV73jjCb-UEvfvACbe_tB4Iy6w Desktop/$binDEXCS/paraFoamを実行.py
	wget_from_google_drive 1NPSVATLVMrlrFnYPDS2AKEZTGbB90vAS Desktop/$binDEXCS/Qと渦度を求める.py
	wget_from_google_drive 1HeKQk3aluZfavHFqg3ft4_ECDt-dGrcw Desktop/$binDEXCS/patchを平面に.py
	wget_from_google_drive 1aM4B3Ssc8Ub5UOEer3-bAjAQU2-LSK_T Desktop/$binDEXCS/2次元メッシュに.py
	wget_from_google_drive 1gxHFYl56-hIl4CnmmFbTudsws_9WZxGE Desktop/$binDEXCS/格子点数と領域の大きさを調べる.py
	wget_from_google_drive 1avGyL_QpvH_KtzxsUNSxIaQ1AE1QFfdy Desktop/$binDEXCS/メッシュを細かく.py
	wget_from_google_drive 11_Qo45wsYY_IABYiFUmI4WE4bHGIk7vG Desktop/$binDEXCS/0秒フォルダにpatchを追加する.py
	wget_from_google_drive 1SUqv8Z3s0PDyzBG_m6R57I-dSaBO8I-Q Desktop/$binDEXCS/blockMeshを実行.py
	wget_from_google_drive 1QqbALVvOS8cakMudoW9eSZsgnN76XLtA Desktop/$binDEXCS/texteditwx.py
	wget_from_google_drive 1MZhuezL1x9d1gNB1geL_Nz0R0Y44o4s5 Desktop/$binDEXCS/他の結果からコピー.py
	wget_from_google_drive 1dIic7DHUKeKT7JNZxd_pLKCndGw4igXO Desktop/$binDEXCS/結果を抽出.py
	wget_from_google_drive 1BPCkDUifcNN3tDd_gsYmllmzKPDps5D1 Desktop/$binDEXCS/流量を求める.py
	wget_from_google_drive 1aHUD_HCg-9Ub3c35EnbG_mKhvn-89Ts6 Desktop/$binDEXCS/壁面熱流束を求める.py
	wget_from_google_drive 1tvpjoVxYVoe3_Y-gZqX8x3OqZv6FRoUX Desktop/$binDEXCS/include文を取り除く.py
	wget_from_google_drive 1CBeji5JEIo5xEpuq9a85FB0-KuwHgn5p Desktop/$binDEXCS/patchをまとめる.py
	wget_from_google_drive 1VgsYV8_OsFEAXqfhy6o8kLeG1KFkvVly Desktop/$binDEXCS/patchの面積平均または積分.py
	wget_from_google_drive 1pI_ZZiHm7XokV9IhOb77FHZ0CWSdG2Cu Desktop/$binDEXCS/yPlusを求める.py
	wget_from_google_drive 1673HCAhKRkwSBkynqX8waeO-gYprh47g Desktop/$binDEXCS/並列計算結果をまとめる.py
	wget_from_google_drive 13HSry5dA_2hywy2-nkNStXUOVuxwFagW Desktop/$binDEXCS/計算.py
	wget_from_google_drive 1LfRALz1JvCaYok8huxudrgwUlYJ_60U_ Desktop/$binDEXCS/時間平均流れ場を作る.py
	wget_from_google_drive 1vOLOZx8RZR0JylFtOpqjyf2S1_J0fV5Z Desktop/$binDEXCS/連続計算雛形.py
	wget_from_google_drive 1AI0QrrdOwN5XggAW4J6Wfpk7tZa3Z1VQ Desktop/$binDEXCS/境界条件の雛形をコピー.py
	wget_from_google_drive 1Du9xl7lobSfGBtVIimv8zQRV5ifu89dP Desktop/$binDEXCS/境界条件あれこれ.txt
	wget_from_google_drive 1qbvXSlIu09F3dVOVETo5KSwuMNS4l0Ol Desktop/$binDEXCS/include文を差し込む.py
	wget_from_google_drive 14Y4CGlgsN0qoFoSS7dGXiYhU67slrDwd Desktop/$binDEXCS/ミリをメートルに.py
	wget_from_google_drive 1z7JPwhTj-26AbxTLmpl-7BpMp_XBUfOQ Desktop/$binDEXCS/壁面せん断応力を求める.py
	wget_from_google_drive 18DWWfO_I2Gojpcby6FdFuk5cbIAGIp96 Desktop/$binDEXCS/インデント.py
	wget_from_google_drive 1GHE33gBH1dHjDqDCxXnKF3EKdmOCAtRk Desktop/$binDEXCS/setFieldsを実行.py
	wget_from_google_drive 1O0hrNP6bj-jwQjaXT69rtrSY1RglbWQa Desktop/$binDEXCS/utilities/misc.py
	wget_from_google_drive 1S3pdWSIuSLUjEbuEIecaW042coH4LNVZ Desktop/$binDEXCS/utilities/setComment.py
	wget_from_google_drive 1LhXjHS_0HNymORcpJIsYkYCKZ8Q7BCxl Desktop/$binDEXCS/utilities/showDir.py
	wget_from_google_drive 1jb06YGS7OvfBT4ASGVAtXhn8Pw0dtnVR Desktop/$binDEXCS/utilities/folderTime.py
	wget_from_google_drive 1PHerHpi3L7lOe18CQTogsqiiRJQzLC2e Desktop/$binDEXCS/utilities/listFile.py
	wget_from_google_drive 1tyQMVVyLRPjA0N0iFZK8JPtgCBxV5KzF Desktop/$binDEXCS/utilities/dictFormat.py
	wget_from_google_drive 1YZWTR8iblvrqhiWT1w44_KcndapNdHfe Desktop/$binDEXCS/utilities/appendEntries.py
	wget_from_google_drive 1rh06w_zNtWWJ0Aag62MbDfyvALB2rzHu Desktop/$binDEXCS/utilities/__init__.py
	wget_from_google_drive 1-ZEi-Ehd1ZYlFx-Z-OfaWsBi5IxJVztM Desktop/$binDEXCS/utilities/dakuten.py
	wget_from_google_drive 10ofPlxneyeRgVzXZLxUdciTzgKk4VdLI Desktop/$binDEXCS/utilities/dictParse.py
	wget_from_google_drive 1iuFE9qyxkGTxcPJKZzudm8Eh2rUkmJr- Desktop/$binDEXCS/utilities/setFuncsInCD.py
	wget_from_google_drive 1hhFK8NCEZLPPF_vSeghXCQ-f46NjRHiJ Desktop/$binDEXCS/utilities/findMaxMin.py
	wget_from_google_drive 1w0bsKNYeAVpRkvvnc-pSHIoopXX21fZ8 Desktop/$binDEXCS/utilities/ofpolymesh.py
	wget_from_google_drive 1T9_ho0VzVybJWFNeXDNuEWj-uHDg76US Desktop/$binDEXCS/utilities/rmObjects.py
	chmod -R +x Desktop/"$binDEXCS"/*.py

	wget_from_google_drive 1gytDK8yaXPUAvSGrb15Bkp2jZOZrB0Zj .FreeCAD/makeSnappyHexMeshSetting.FCMacro
	wget_from_google_drive 1dj_Dr6y7NLrxJYgBcrtGFpkeiTR1xfYG .FreeCAD/exportStl.FCMacro
	wget_from_google_drive 1cJG_D5inJlXUy8MBmAHz_XaUMAxn6ecO .FreeCAD/sHM.png
	wget_from_google_drive 1yLCXnuKOfok0Tk_bAd4Jpgcm_H8wktfQ .FreeCAD/makeCfMeshSetting.FCMacro
	chmod -R +x .FreeCAD/*.FCMacro

	wget_from_google_drive 1jMzyuvw-LYFf7pu7gWm-UpT4wJAAP1Iu Desktop/copybinDEXCS2019.sh
	chmod +x Desktop/copybinDEXCS2019.sh

	[ ! -d Desktop/matplotlibwx/locale/en/LC_MESSAGES ] && mkdir -p Desktop/matplotlibwx/locale/en/LC_MESSAGES
	[ ! -d Desktop/matplotlibwx ] && mkdir -p Desktop/matplotlibwx

	wget_from_google_drive 18jsRVeShgjhvKi_X6m9z-JQKlHkedDnT Desktop/matplotlibwx/matplotlibwx.py
	wget_from_google_drive 1tf9r2pP1ArCoSUrSONDlnAuWq6uiOyax Desktop/matplotlibwx/modules_needed.txt
	wget_from_google_drive 1xVuaz179QpwFxb2Xf0zJFkn1x0HT_plC Desktop/matplotlibwx/locale/en/LC_MESSAGES/messages.mo
	wget_from_google_drive 1nVIKZy5nm-jzfDIAGLfczyvCY1D924ZV Desktop/matplotlibwx/locale/en/LC_MESSAGES/messages.po
	chmod -R +x Desktop/matplotlibwx/*.py
fi

cd -

# update importDXF.py
if [ "$dexcs_version" = '2019' ] && [ ! -f /usr/local/Mod/Draft/importDXF.py.orig ]; then
	sudo mv /usr/local/Mod/Draft/importDXF.py /usr/local/Mod/Draft/importDXF.py.orig
	((trial = 0))
	for d in /mnt/DEXCS2-6left_student /mnt/DEXCS2-6right_student; do
		if [ -d "$d" ] && [ -n "$(ls -A $d)" ]; then
			sudo rsync -av "$d"/マニュアル/bin/importDXF.py /usr/local/Mod/Draft/importDXF.py
			break
		fi
		((++trial))
	done
	if [ "$trial" -eq 2 ]; then
		sudo wget_from_google_drive 1_4pM92PhkaZHRAk09PoL-5pqZyZPg4dn /usr/local/Mod/Draft/importDXF.py
	fi
fi

if [ -e ~/Desktop/makeConvenient ]; then
	rm -r ~/Desktop/makeConvenient
fi

python -c "
import os

dexcs_version = '"$dexcs_version"'

bookmarks = os.path.expanduser('~/.config/gtk-3.0/bookmarks')
with open(bookmarks, 'r') as f:
    s_orig = f.read().rstrip() + '\n'
s = s_orig
tut = ('file:///opt/OpenFOAM/OpenFOAM-v1906/tutorials\n' if dexcs_version == '2019' else
    'file:///usr/lib/openfoam/openfoam2106/tutorials\n')
if tut not in s:
    i = s.find('file:///mnt/DEXCS2-6\n')
    if i == -1:
        s += tut
    else:
        s = s[:i] + tut + s[i:]
Yd = 'file:///mnt/Y_drive\n'
if Yd not in s:
    i = s.find('file:///mnt/Z_drive\n')
    if i == -1:
        s += Yd
    else:
        s = s[:i] + Yd + s[i:]
IS_student = 'file:///mnt/DEXCS2-6IS_student\n'
if IS_student not in s:
    i = s.find('file:///mnt/DEXCS2-6left_ExtraHD\n')
    if i == -1:
        s += IS_student
    else:
        s = s[:i] + IS_student + s[i:]
IS_ExtraHD = 'file:///mnt/DEXCS2-6IS_ExtraHD\n'
if IS_ExtraHD not in s:
    i = s.find(Yd)
    s = s[:i] + IS_ExtraHD + s[i:]
if s != s_orig:
    with open(bookmarks, 'w') as f:
        f.write(s)

BD_alias = 'alias BD=\'xdg-open ~/Desktop/binDEXCS2019（解析フォルダを端末で開いてから）'
if dexcs_version == '2021':
    BD_alias += '*'
BD_alias += '\'\n'
run_functions = '. \$WM_PROJECT_DIR/bin/tools/RunFunctions\n'
mc_definition = ('mc() {\n' +
'  if [ \"\$#\" -eq 0 ]; then\n' +
'    eq=\"\$(xsel --clipboard --output)\"\n' +
'  else\n' +
'    eq=\"\$1\"\n' +
'  fi\n' +
'  r=\$(maxima --very-quiet --batch-string=\"\$eq;\" | awk \'\$0 != \"\"{sub(\"  - \", \"  -\"); print \$0}\')\n' +
'  echo -e \"\$r\" \n' +
'  echo -e \"\$r\" | awk \'END{sub(\"^ *\", \"\"); printf \$0}\' | xsel --clipboard\n' +
'}\n')
bashrc = os.path.expanduser('~/.bashrc')
with open(bashrc, 'r') as f:
    s = f.read().rstrip() + '\n'
if BD_alias not in s:
    with open(bashrc, 'a') as f:
        f.write(BD_alias)
if run_functions not in s:
    with open(bashrc, 'a') as f:
        f.write(run_functions)
if 'mc()' not in s:
    with open(bashrc, 'a') as f:
        f.write('\n' + mc_definition)

paraview_json_home = os.path.expanduser('~/.config/ParaView/ParaView-UserSettings.json')
with open(paraview_json_home, 'r') as f:
    s = f.read()
if '\"GeometryRepresentation\"' not in s or '\"UnstructuredGridRepresentation\"' not in s or \"sources\" not in s:
    with open(paraview_json_home, 'w') as f:
        f.write('{\n' +
            '\t\"lookup_tables\" : \n' +
            '\t{\n' +
            '\t\t\"PVLookupTable\" : \n' +
            '\t\t{\n' +
            '\t\t\t\"ColorSpace\" : 1,\n' +
            '\t\t\t\"NanColor\" : \n\t\t\t[\n' +
            '\t\t\t\t0.49803921568600001,\n' +
            '\t\t\t\t0.49803921568600001,\n' +
            '\t\t\t\t0.49803921568600001\n' +
            '\t\t\t],\n' +
            '\t\t\t\"RGBPoints\" : \n' +
            '\t\t\t[\n' +
            '\t\t\t\t0.0,\n\t\t\t\t0.0,\n\t\t\t\t0.0,\n' +
            '\t\t\t\t1.0,\n\t\t\t\t1.0,\n\t\t\t\t1.0,\n' +
            '\t\t\t\t0.0,\n\t\t\t\t0.0\n\t\t\t]\n' +
            '\t\t}\n' +
            '\t},\n' +
            '\t\"misc\" : \n' +
            '\t{\n' +
            '\t\t\"ColorPalette\" : \n' +
            '\t\t{\n' +
            '\t\t\t\"BackgroundColor\" : \n' +
            '\t\t\t[\n\t\t\t\t1.0,\n\t\t\t\t1.0,\n\t\t\t\t1.0\n\t\t\t],\n' +
            '\t\t\t\"ForegroundColor\" : \n' +
            '\t\t\t[\n\t\t\t\t0.0,\n\t\t\t\t0.0,\n\t\t\t\t0.0\n\t\t\t],\n' +
            '\t\t\t\"TextAnnotationColor\" : \n' +
            '\t\t\t[\n\t\t\t\t0.0,\n\t\t\t\t0.0,\n\t\t\t\t0.0\n\t\t\t]\n' +
            '\t\t}\n' +
            '\t},\n' +
            '\t\"representations\" : \n' +
            '\t{\n' +
            '\t\t\"GeometryRepresentation\" : \n' +
            '\t\t{\n' +
            '\t\t\t\"Ambient\" : 1.0,\n' +
            '\t\t\t\"AmbientColor\" : \n' +
            '\t\t\t[\n\t\t\t\t0.0,\n\t\t\t\t0.0,\n\t\t\t\t0.0\n\t\t\t],\n' +
            '\t\t\t\"BlockColorsDistinctValues\" : 12,\n' +
            '\t\t\t\"Diffuse\" : 0.0,\n' +
            '\t\t\t\"SelectionCellLabelFontFile\" : \"\",\n' +
            '\t\t\t\"SelectionPointLabelFontFile\" : \"\"\n' +
            '\t\t},\n' +
            '\t\t\"UnstructuredGridRepresentation\" : \n' +
            '\t\t{\n' +
            '\t\t\t\"Ambient\" : 1.0,\n' +
            '\t\t\t\"AmbientColor\" : \n' +
            '\t\t\t[\n\t\t\t\t0.0,\n\t\t\t\t0.0,\n\t\t\t\t0.0\n\t\t\t],\n' +
            '\t\t\t\"BlockColorsDistinctValues\" : 12,\n' +
            '\t\t\t\"Diffuse\" : 0.0,\n' +
            '\t\t\t\"SelectionCellLabelFontFile\" : \"\",\n' +
            '\t\t\t\"SelectionPointLabelFontFile\" : \"\"\n' +
            '\t\t}\n' +
            '\t},\n' +
            '\t\"sources\" : \n' +
            '\t{\n' +
            '\t\t\"PVFoamReader\" : \n' +
            '\t\t{\n' +
            '\t\t\t\"ZeroTime\" : 0\n' +
            '\t\t}\n' +
            '\t}\n' +
            '}')

macro_home_user_cfg = os.path.expanduser('~/.FreeCAD/user.cfg')
with open(macro_home_user_cfg, 'r') as f:
    s = f.read()
if 'makeSnappyHexMeshSetting' not in s:
    if dexcs_version == '2019':
        s = ('<?xml version="\""1.0"\"" encoding="\""UTF-8"\"" standalone="\""no"\"" ?>\n<FCParameters>\n<FCParamGroup Name="\""Root"\"">\n<FCParamGroup Name="\""BaseApp"\"">\n<FCParamGroup Name="\""Preferences"\"">\n<FCParamGroup Name="\""Units"\"">\n<FCInt Name="\""UserSchema"\"" Value="\""0"\""/>\n<FCInt Name="\""Decimals"\"" Value="\""2"\""/>\n<FCInt Name="\""FracInch"\"" Value="\""2"\""/></FCParamGroup>\n<FCParamGroup Name="\""Macro"\"">\n<FCText Name="\""MacroPath"\"">/home/dexcs/.FreeCAD/</FCText>\n<FCBool Name="\""LocalEnvironment"\"" Value="\""1"\""/>\n<FCBool Name="\""RecordGui"\"" Value="\""1"\""/>\n<FCBool Name="\""GuiAsComment"\"" Value="\""1"\""/>\n<FCBool Name="\""ScriptToPyConsole"\"" Value="\""1"\""/>\n<FCBool Name="\""ScriptToFile"\"" Value="\""0"\""/>\n<FCText Name="\""ScriptFile"\"">FullScript.FCScript</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""Mod"\"">\n<FCParamGroup Name="\""OpenSCAD"\""/>\n<FCParamGroup Name="\""Draft"\"">\n<FCText Name="\""snapModes"\"">111111111101111</FCText>\n<FCFloat Name="\""maxsegmentlength"\"" Value="\""1.000000000000"\""/>\n<FCBool Name="\""dxfAllowDownload"\"" Value="\""0"\""/>\n<FCBool Name="\""dxftext"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfImportPoints"\"" Value="\""0"\""/>\n<FCBool Name="\""dxflayout"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfstarblocks"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfGetOriginalColors"\"" Value="\""0"\""/>\n<FCBool Name="\""joingeometry"\"" Value="\""0"\""/>\n<FCBool Name="\""groupLayers"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfproject"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfStdSize"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfUseDraftVisGroups"\"" Value="\""0"\""/>\n<FCBool Name="\""importDxfHatches"\"" Value="\""0"\""/>\n<FCBool Name="\""renderPolylineWidth"\"" Value="\""0"\""/>\n<FCBool Name="\""DiscretizeEllipses"\"" Value="\""1"\""/>\n<FCBool Name="\""dxfmesh"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfCreatePart"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfCreateDraft"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfCreateSketch"\"" Value="\""1"\""/>\n<FCText Name="\""TeighaFileConverter"\""/>\n<FCInt Name="\""svgstyle"\"" Value="\""0"\""/>\n<FCInt Name="\""svg_export_style"\"" Value="\""0"\""/>\n<FCBool Name="\""SvgLinesBlack"\"" Value="\""1"\""/>\n<FCBool Name="\""ocaareas"\"" Value="\""1"\""/>\n<FCInt Name="\""precision"\"" Value="\""6"\""/>\n<FCInt Name="\""dimPrecision"\"" Value="\""2"\""/>\n<FCFloat Name="\""tolerance"\"" Value="\""0.050000000000"\""/>\n<FCText Name="\""constructiongroupname"\"">構造物</FCText>\n<FCInt Name="\""UiMode"\"" Value="\""1"\""/>\n<FCInt Name="\""defaultWP"\"" Value="\""0"\""/>\n<FCBool Name="\""copymode"\"" Value="\""1"\""/>\n<FCBool Name="\""selectBaseObjects"\"" Value="\""0"\""/>\n<FCBool Name="\""UsePartPrimitives"\"" Value="\""0"\""/>\n<FCBool Name="\""fillmode"\"" Value="\""1"\""/>\n<FCUInt Name="\""constructioncolor"\"" Value="\""746455039"\""/>\n<FCInt Name="\""gridEvery"\"" Value="\""10"\""/>\n<FCInt Name="\""gridSize"\"" Value="\""100"\""/>\n<FCFloat Name="\""gridSpacing"\"" Value="\""1.000000000000"\""/>\n<FCInt Name="\""modsnap"\"" Value="\""1"\""/>\n<FCInt Name="\""modalt"\"" Value="\""2"\""/>\n<FCInt Name="\""modconstrain"\"" Value="\""0"\""/>\n<FCBool Name="\""showSnapBar"\"" Value="\""1"\""/>\n<FCBool Name="\""hideSnapBar"\"" Value="\""0"\""/>\n<FCBool Name="\""alwaysSnap"\"" Value="\""1"\""/>\n<FCBool Name="\""grid"\"" Value="\""1"\""/>\n<FCBool Name="\""alwaysShowGrid"\"" Value="\""1"\""/>\n<FCInt Name="\""linewidth"\"" Value="\""2"\""/>\n<FCInt Name="\""HatchPatternResolution"\"" Value="\""128"\""/>\n<FCText Name="\""svgDashedLine"\"">0.09,0.05</FCText>\n<FCText Name="\""svgDashdotLine"\"">0.09,0.05,0.02,0.05</FCText>\n<FCText Name="\""svgDottedLine"\"">0.02,0.02</FCText>\n<FCText Name="\""template"\""/>\n<FCText Name="\""patternFile"\""/>\n<FCInt Name="\""snapStyle"\"" Value="\""0"\""/>\n<FCBool Name="\""saveonexit"\"" Value="\""0"\""/>\n<FCBool Name="\""showPlaneTracker"\"" Value="\""0"\""/>\n<FCUInt Name="\""color"\"" Value="\""255"\""/>\n<FCUInt Name="\""snapcolor"\"" Value="\""4294967295"\""/>\n<FCFloat Name="\""textheight"\"" Value="\""0.200000000000"\""/>\n<FCFloat Name="\""extlines"\"" Value="\""0.300000000000"\""/>\n<FCFloat Name="\""arrowsize"\"" Value="\""0.100000000000"\""/>\n<FCFloat Name="\""dimspacing"\"" Value="\""0.050000000000"\""/>\n<FCText Name="\""textfont"\""/>\n<FCText Name="\""FontFile"\""/>\n<FCInt Name="\""dimstyle"\"" Value="\""0"\""/>\n<FCInt Name="\""dimsymbol"\"" Value="\""0"\""/>\n<FCInt Name="\""dimorientation"\"" Value="\""0"\""/>\n<FCBool Name="\""showUnit"\"" Value="\""1"\""/>\n<FCBool Name="\""dxfShowDialog"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfUseLegacyImporter"\"" Value="\""1"\""/>\n<FCBool Name="\""dxfExportBlocks"\"" Value="\""1"\""/>\n<FCBool Name="\""svgDisableUnitScaling"\"" Value="\""0"\""/>\n<FCFloat Name="\""dxfScaling"\"" Value="\""1.000000000000"\""/>\n<FCText Name="\""ClonePrefix"\"">Clone of</FCText>\n<FCFloat Name="\""svgDiscretization"\"" Value="\""0.000000000000"\""/>\n<FCBool Name="\""dxfUseLegacyExporter"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Part"\"">\n<FCParamGroup Name="\""General"\"">\n<FCInt Name="\""WriteSurfaceCurveMode"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""IGES"\"">\n<FCInt Name="\""Unit"\"" Value="\""0"\""/>\n<FCBool Name="\""BrepMode"\"" Value="\""0"\""/>\n<FCBool Name="\""SkipBlankEntities"\"" Value="\""1"\""/>\n<FCText Name="\""Company"\""/>\n<FCText Name="\""Author"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""STEP"\"">\n<FCInt Name="\""Unit"\"" Value="\""0"\""/>\n<FCText Name="\""Scheme"\"">AP214IS</FCText>\n<FCText Name="\""Company"\""/>\n<FCText Name="\""Author"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Boolean"\"">\n<FCBool Name="\""CheckModel"\"" Value="\""0"\""/>\n<FCBool Name="\""RefineModel"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCInt Name="\""GridLinePattern"\"" Value="\""3855"\""/>\n<FCBool Name="\""AddBaseObjectName"\"" Value="\""1"\""/>\n<FCFloat Name="\""MeshDeviation"\"" Value="\""0.500000000000"\""/>\n<FCFloat Name="\""MeshAngularDeflection"\"" Value="\""28.500000000000"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Sketcher"\"">\n<FCParamGroup Name="\""Elements"\"">\n<FCBool Name="\""Auto-switch to edge"\"" Value="\""1"\""/>\n<FCBool Name="\""Extended Naming"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""General"\"">\n<FCBool Name="\""ShowGrid"\"" Value="\""1"\""/>\n<FCBool Name="\""GridSnap"\"" Value="\""0"\""/>\n<FCBool Name="\""AutoConstraints"\"" Value="\""1"\""/>\n<FCBool Name="\""HideDependent"\"" Value="\""1"\""/>\n<FCBool Name="\""ShowLinks"\"" Value="\""1"\""/>\n<FCBool Name="\""ShowSupport"\"" Value="\""1"\""/>\n<FCBool Name="\""RestoreCamera"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""SolverAdvanced"\""/>\n<FCBool Name="\""ExpandedMessagesWidget"\"" Value="\""1"\""/>\n<FCBool Name="\""ExpandedSolverAdvancedWidget"\"" Value="\""0"\""/>\n<FCBool Name="\""ExpandedEditControlWidget"\"" Value="\""0"\""/>\n<FCBool Name="\""ExpandedConstraintsWidget"\"" Value="\""1"\""/>\n<FCBool Name="\""ExpandedElementsWidget"\"" Value="\""1"\""/>\n<FCBool Name="\""AutoRecompute"\"" Value="\""0"\""/>\n<FCBool Name="\""ShowDialogOnDistanceConstraint"\"" Value="\""1"\""/>\n<FCBool Name="\""ContinuousCreationMode"\"" Value="\""1"\""/>\n<FCBool Name="\""ShowSolverAdvancedWidget"\"" Value="\""0"\""/>\n<FCBool Name="\""HideInternalAlignment"\"" Value="\""1"\""/>\n<FCBool Name="\""ExtendedConstraintInformation"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""PartDesign"\"">\n<FCBool Name="\""RefineModel"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Mesh"\"">\n<FCBool Name="\""TwoSideRendering"\"" Value="\""0"\""/>\n<FCBool Name="\""ShowBoundingBox"\"" Value="\""0"\""/>\n<FCUInt Name="\""MeshColor"\"" Value="\""3435973887"\""/>\n<FCUInt Name="\""LineColor"\"" Value="\""255"\""/>\n<FCUInt Name="\""BackfaceColor"\"" Value="\""3435973887"\""/>\n<FCInt Name="\""MeshTransparency"\"" Value="\""0"\""/>\n<FCInt Name="\""LineTransparency"\"" Value="\""0"\""/>\n<FCBool Name="\""VertexPerNormals"\"" Value="\""0"\""/>\n<FCFloat Name="\""CreaseAngle"\"" Value="\""0.000000000000"\""/>\n<FCFloat Name="\""MaxDeviationExport"\"" Value="\""0.001000000000"\""/>\n<FCBool Name="\""ExportAmfCompressed"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Raytracing"\"">\n<FCText Name="\""ProjectPath"\""/>\n<FCText Name="\""PovrayExecutable"\""/>\n<FCText Name="\""LuxrenderExecutable"\""/>\n<FCText Name="\""CameraName"\"">TempCamera.inc</FCText>\n<FCText Name="\""PartName"\"">TempPart.inc</FCText>\n<FCFloat Name="\""MeshDeviation"\"" Value="\""0.100000000000"\""/>\n<FCBool Name="\""NotWriteVertexNormals"\"" Value="\""0"\""/>\n<FCBool Name="\""WriteUVCoordinates"\"" Value="\""0"\""/>\n<FCInt Name="\""OutputWidth"\"" Value="\""800"\""/>\n<FCInt Name="\""OutputHeight"\"" Value="\""600"\""/>\n<FCText Name="\""OutputParameters"\"">+P +A</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""Fem"\"">\n<FCText Name="\""ccxBinaryPath"\"">/usr/bin/ccx</FCText>\n<FCText Name="\""WorkingDir"\"">/home/dexcs/Desktop/test</FCText>\n<FCInt Name="\""AnalysisType"\"" Value="\""0"\""/>\n<FCBool Name="\""UseInternalEditor"\"" Value="\""1"\""/>\n<FCText Name="\""ExternalEditorPath"\""/>\n<FCInt Name="\""NumberOfEigenmode"\"" Value="\""10"\""/>\n<FCFloat Name="\""EigenmodeHighLimit"\"" Value="\""1000000.000000000000"\""/>\n<FCFloat Name="\""EigenmodeLowLimit"\"" Value="\""0.000000000000"\""/>\n<FCBool Name="\""UseBuiltInMaterials"\"" Value="\""1"\""/>\n<FCBool Name="\""UseMaterialsFromConfigDir"\"" Value="\""1"\""/>\n<FCBool Name="\""UseMaterialsFromCustomDir"\"" Value="\""1"\""/>\n<FCText Name="\""CustomMaterialsDir"\""/>\n<FCText Name="\""z88BinaryPath"\""/>\n<FCBool Name="\""RestoreResultDialog"\"" Value="\""1"\""/>\n<FCBool Name="\""KeepResultsOnReRun"\"" Value="\""0"\""/>\n<FCParamGroup Name="\""Ccx"\"">\n<FCInt Name="\""Solver"\"" Value="\""0"\""/>\n<FCInt Name="\""AnalysisType"\"" Value="\""0"\""/>\n<FCInt Name="\""AnalysisNumCPUs"\"" Value="\""1"\""/>\n<FCBool Name="\""NonlinearGeometry"\"" Value="\""0"\""/>\n<FCBool Name="\""UseNonCcxIterationParam"\"" Value="\""0"\""/>\n<FCBool Name="\""StaticAnalysis"\"" Value="\""1"\""/>\n<FCInt Name="\""AnalysisMaxIterations"\"" Value="\""2000"\""/>\n<FCFloat Name="\""AnalysisTimeInitialStep"\"" Value="\""0.010000000000"\""/>\n<FCFloat Name="\""AnalysisTime"\"" Value="\""1.000000000000"\""/>\n<FCInt Name="\""EigenmodesCount"\"" Value="\""10"\""/>\n<FCFloat Name="\""EigenmodeHighLimit"\"" Value="\""1000000.000000000000"\""/>\n<FCFloat Name="\""EigenmodeLowLimit"\"" Value="\""0.000000000000"\""/>\n<FCBool Name="\""UseInternalEditor"\"" Value="\""1"\""/>\n<FCText Name="\""ExternalEditorPath"\""/>\n<FCText Name="\""ccxBinaryPath"\"">/usr/bin/ccx</FCText>\n<FCBool Name="\""UseStandardCcxLocation"\"" Value="\""1"\""/>\n<FCBool Name="\""SplitInputWriter"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""General"\"">\n<FCText Name="\""WorkingDir"\"">/tmp</FCText>\n<FCText Name="\""z88BinaryPath"\""/>\n<FCBool Name="\""UseBuiltInMaterials"\"" Value="\""1"\""/>\n<FCBool Name="\""UseMaterialsFromConfigDir"\"" Value="\""1"\""/>\n<FCBool Name="\""UseMaterialsFromCustomDir"\"" Value="\""1"\""/>\n<FCText Name="\""CustomMaterialsDir"\""/>\n<FCBool Name="\""RestoreResultDialog"\"" Value="\""1"\""/>\n<FCBool Name="\""KeepResultsOnReRun"\"" Value="\""0"\""/>\n<FCBool Name="\""HideConstraint"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Gmsh"\"">\n<FCBool Name="\""UseStandardGmshLocation"\"" Value="\""1"\""/>\n<FCText Name="\""gmshBinaryPath"\"">/usr/bin/gmsh</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""Z88"\"">\n<FCBool Name="\""UseStandardZ88Location"\"" Value="\""1"\""/>\n<FCText Name="\""z88BinaryPath"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Elmer"\""/></FCParamGroup>\n<FCParamGroup Name="\""Arch"\"">\n<FCText Name="\""ifcRootElement"\"">IfcProduct</FCText>\n<FCText Name="\""ifcSkip"\""/>\n<FCInt Name="\""ifcImportModeArch"\"" Value="\""0"\""/>\n<FCInt Name="\""ifcImportModeStruct"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcShowDialog"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcDebug"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcCreateClones"\"" Value="\""1"\""/>\n<FCBool Name="\""ifcSeparateOpenings"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcGetExtrusions"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcPrefixNumbers"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcMergeMaterials"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcImportProperties"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcExportAsBrep"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcUseDaeOptions"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcJoinCoplanarFacets"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcStoreUid"\"" Value="\""1"\""/>\n<FCBool Name="\""ifcSerialize"\"" Value="\""0"\""/>\n<FCInt Name="\""ColladaSegsPerEdge"\"" Value="\""1"\""/>\n<FCInt Name="\""ColladaSegsPerRadius"\"" Value="\""2"\""/>\n<FCFloat Name="\""ColladaScalingFactor"\"" Value="\""1.000000000000"\""/>\n<FCFloat Name="\""ColladaTessellation"\"" Value="\""1.000000000000"\""/>\n<FCFloat Name="\""ColladaGrading"\"" Value="\""0.300000000000"\""/>\n<FCInt Name="\""ColladaMesher"\"" Value="\""0"\""/>\n<FCBool Name="\""ColladaSecondOrder"\"" Value="\""0"\""/>\n<FCBool Name="\""ColladaOptimize"\"" Value="\""1"\""/>\n<FCBool Name="\""ColladaAllowQuads"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcSplitLayers"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcExport2D"\"" Value="\""1"\""/>\n<FCBool Name="\""ifcFitViewOnImport"\"" Value="\""0"\""/>\n<FCBool Name="\""IfcExportFreeCADProperties"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcCompress"\"" Value="\""1"\""/>\n<FCBool Name="\""DisableIfcRectangleProfileDef"\"" Value="\""0"\""/>\n<FCBool Name="\""IfcImportFreeCADProperties"\"" Value="\""0"\""/>\n<FCBool Name="\""getStandardCase"\"" Value="\""0"\""/>\n<FCBool Name="\""IfcAddDefaultSite"\"" Value="\""0"\""/>\n<FCBool Name="\""IfcAddDefaultBuilding"\"" Value="\""1"\""/>\n<FCBool Name="\""IfcAddDefaultStorey"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Import"\"">\n<FCParamGroup Name="\""hSTEP"\"">\n<FCBool Name="\""ReadShapeCompoundMode"\"" Value="\""0"\""/>\n<FCBool Name="\""Scheme_203"\"" Value="\""0"\""/>\n<FCBool Name="\""Scheme_214"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCBool Name="\""ExportHiddenObject"\"" Value="\""0"\""/>\n<FCBool Name="\""ExportLegacy"\"" Value="\""0"\""/>\n<FCBool Name="\""ExportKeepPlacement"\"" Value="\""0"\""/>\n<FCBool Name="\""ImportHiddenObject"\"" Value="\""0"\""/>\n<FCBool Name="\""UseLinkGroup"\"" Value="\""0"\""/>\n<FCBool Name="\""UseBaseName"\"" Value="\""0"\""/>\n<FCBool Name="\""ReduceObjects"\"" Value="\""0"\""/>\n<FCBool Name="\""ExpandCompound"\"" Value="\""0"\""/>\n<FCBool Name="\""ShowProgress"\"" Value="\""0"\""/>\n<FCInt Name="\""ImportMode"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Start"\"">\n<FCText Name="\""AutoloadModule"\"">StartWorkbench</FCText>\n<FCUInt Name="\""BackgroundColor1"\"" Value="\""1331197183"\""/>\n<FCUInt Name="\""BackgroundTextColor"\"" Value="\""4294703103"\""/>\n<FCUInt Name="\""PageColor"\"" Value="\""4294967295"\""/>\n<FCUInt Name="\""PageTextColor"\"" Value="\""255"\""/>\n<FCUInt Name="\""BoxColor"\"" Value="\""3722305023"\""/>\n<FCUInt Name="\""LinkColor"\"" Value="\""65535"\""/>\n<FCUInt Name="\""BackgroundColor2"\"" Value="\""2141107711"\""/>\n<FCText Name="\""Template"\""/>\n<FCText Name="\""BackgroundImage"\""/>\n<FCText Name="\""ShowCustomFolder"\""/>\n<FCBool Name="\""InWeb"\"" Value="\""0"\""/>\n<FCBool Name="\""InBrowser"\"" Value="\""1"\""/>\n<FCBool Name="\""ShowNotes"\"" Value="\""0"\""/>\n<FCBool Name="\""ShowExamples"\"" Value="\""1"\""/>\n<FCBool Name="\""closeStart"\"" Value="\""0"\""/>\n<FCBool Name="\""DoNotShowOnOpen"\"" Value="\""0"\""/>\n<FCBool Name="\""ShowForum"\"" Value="\""0"\""/>\n<FCBool Name="\""UseStyleSheet"\"" Value="\""0"\""/>\n<FCBool Name="\""NewFileGradient"\"" Value="\""0"\""/>\n<FCText Name="\""FontFamily"\""/>\n<FCInt Name="\""FontSize"\"" Value="\""13"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""CfdOF"\"">\n<FCText Name="\""InstallationPath"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Material"\"">\n<FCParamGroup Name="\""Resources"\""/>\n<FCParamGroup Name="\""Cards"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Path"\""/>\n<FCParamGroup Name="\""BIM"\""/>\n<FCParamGroup Name="\""TechDraw"\"">\n<FCParamGroup Name="\""General"\""/>\n<FCParamGroup Name="\""Rez"\""/>\n<FCParamGroup Name="\""Decorations"\""/>\n<FCParamGroup Name="\""Files"\""/>\n<FCParamGroup Name="\""Colors"\""/>\n<FCParamGroup Name="\""Labels"\""/>\n<FCParamGroup Name="\""PAT"\""/>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""Bitmaps"\"">\n<FCText Name="\""CustomPath0"\"">/home/dexcs/.FreeCAD/</FCText>\n<FCText Name="\""CustomPath1"\"">/opt/TreeFoam/icons/</FCText>\n<FCParamGroup Name="\""Theme"\""/></FCParamGroup>\n<FCParamGroup Name="\""General"\"">\n<FCText Name="\""AutoloadModule"\"">StartWorkbench</FCText>\n<FCInt Name="\""AutoloadTab"\"" Value="\""-1"\""/>\n<FCBool Name="\""ShowSplasher"\"" Value="\""1"\""/>\n<FCInt Name="\""ToolbarIconSize"\"" Value="\""24"\""/>\n<FCText Name="\""Language"\"">Japanese</FCText>\n<FCText Name="\""FileOpenSavePath"\"">/home/dexcs</FCText>\n<FCText Name="\""FileImportFilter"\"">Supported formats ( *.3ds *.FCMacro *.FCMat *.FCScript *.asc *.ast *.bdf *.bmp *.bms *.brep *.brp *.cnc *.csg *.csv *.dae *.dat *.dwg *.dxf *.emn *.frd *.gc *.gcad *.gcode *.ifc *.iges *.igs *.inc *.inp *.iv *.jpg *.json *.med *.meshjson *.meshyaml *.nc *.ncc *.ngc *.obj *.oca *.off *.pcd *.plmxml *.ply *.png *.pov *.py *.smf *.step *.stl *.stp *.stpZ *.stpz *.svg *.svgz *.tap *.unv *.vrml *.vtk *.vtu *.wrl *.wrl.gz *.wrz *.xdmf *.xlsx *.xml *.xpm *.yaml *.z88 *.zip)</FCText>\n<FCText Name="\""FileExportFilter"\"">STL Mesh (*.stl *.ast)</FCText>\n<FCBool Name="\""PythonWordWrap"\"" Value="\""1"\""/>\n<FCBool Name="\""ConfirmAll"\"" Value="\""0"\""/>\n<FCInt Name="\""TreeViewMode"\"" Value="\""0"\""/></FCParamGroup>\n<FCParamGroup Name="\""Document"\"">\n<FCBool Name="\""CreateNewDoc"\"" Value="\""0"\""/>\n<FCInt Name="\""CompressionLevel"\"" Value="\""3"\""/>\n<FCBool Name="\""UsingUndo"\"" Value="\""1"\""/>\n<FCInt Name="\""MaxUndoSize"\"" Value="\""20"\""/>\n<FCBool Name="\""SaveTransactions"\"" Value="\""0"\""/>\n<FCBool Name="\""TransactionsDiscard"\"" Value="\""0"\""/>\n<FCBool Name="\""SaveThumbnail"\"" Value="\""0"\""/>\n<FCBool Name="\""CreateBackupFiles"\"" Value="\""1"\""/>\n<FCInt Name="\""CountBackupFiles"\"" Value="\""1"\""/>\n<FCBool Name="\""DuplicateLabels"\"" Value="\""0"\""/>\n<FCInt Name="\""prefLicenseType"\"" Value="\""0"\""/>\n<FCText Name="\""prefLicenseUrl"\"">http://en.wikipedia.org/wiki/All_rights_reserved</FCText>\n<FCText Name="\""prefAuthor"\""/>\n<FCBool Name="\""prefSetAuthorOnSave"\"" Value="\""0"\""/>\n<FCText Name="\""prefCompany"\""/>\n<FCBool Name="\""RecoveryEnabled"\"" Value="\""1"\""/>\n<FCBool Name="\""AutoSaveEnabled"\"" Value="\""1"\""/>\n<FCInt Name="\""AutoSaveTimeout"\"" Value="\""15"\""/>\n<FCBool Name="\""AddThumbnailLogo"\"" Value="\""1"\""/>\n<FCBool Name="\""NoPartialLoading"\"" Value="\""0"\""/>\n<FCBool Name="\""CanAbortRecompute"\"" Value="\""0"\""/></FCParamGroup>\n<FCParamGroup Name="\""OutputWindow"\"">\n<FCBool Name="\""checkLogging"\"" Value="\""0"\""/>\n<FCBool Name="\""checkWarning"\"" Value="\""1"\""/>\n<FCBool Name="\""checkError"\"" Value="\""1"\""/>\n<FCUInt Name="\""colorText"\"" Value="\""255"\""/>\n<FCUInt Name="\""colorLogging"\"" Value="\""65535"\""/>\n<FCUInt Name="\""colorWarning"\"" Value="\""4289331455"\""/>\n<FCUInt Name="\""colorError"\"" Value="\""4278190335"\""/>\n<FCBool Name="\""RedirectPythonOutput"\"" Value="\""1"\""/>\n<FCBool Name="\""RedirectPythonErrors"\"" Value="\""1"\""/>\n<FCBool Name="\""checkShowReportViewOnWarningOrError"\"" Value="\""1"\""/></FCParamGroup>\n<FCParamGroup Name="\""TreeView"\"">\n<FCUInt Name="\""TreeEditColor"\"" Value="\""4294902015"\""/>\n<FCUInt Name="\""TreeActiveColor"\"" Value="\""3873898495"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Editor"\"">\n<FCInt Name="\""TabSize"\"" Value="\""4"\""/>\n<FCBool Name="\""EnableLineNumber"\"" Value="\""1"\""/>\n<FCBool Name="\""EnableFolding"\"" Value="\""1"\""/>\n<FCInt Name="\""IndentSize"\"" Value="\""4"\""/>\n<FCBool Name="\""Tabs"\"" Value="\""1"\""/>\n<FCBool Name="\""Spaces"\"" Value="\""0"\""/>\n<FCUInt Name="\""Text"\"" Value="\""0"\""/>\n<FCUInt Name="\""Bookmark"\"" Value="\""16776960"\""/>\n<FCUInt Name="\""Breakpoint"\"" Value="\""4278190080"\""/>\n<FCUInt Name="\""Keyword"\"" Value="\""65280"\""/>\n<FCUInt Name="\""Comment"\"" Value="\""11141120"\""/>\n<FCUInt Name="\""Block comment"\"" Value="\""2694882304"\""/>\n<FCUInt Name="\""Number"\"" Value="\""65280"\""/>\n<FCUInt Name="\""String"\"" Value="\""4278190080"\""/>\n<FCUInt Name="\""Character"\"" Value="\""4278190080"\""/>\n<FCUInt Name="\""Class name"\"" Value="\""4289331200"\""/>\n<FCUInt Name="\""Define name"\"" Value="\""4289331200"\""/>\n<FCUInt Name="\""Operator"\"" Value="\""2694882304"\""/>\n<FCUInt Name="\""Python output"\"" Value="\""2863300352"\""/>\n<FCUInt Name="\""Python error"\"" Value="\""4278190080"\""/>\n<FCUInt Name="\""Current line highlight"\"" Value="\""3772833792"\""/>\n<FCInt Name="\""FontSize"\"" Value="\""10"\""/>\n<FCText Name="\""Font"\"">Abyssinica SIL</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""Browser"\""/>\n<FCParamGroup Name="\""MainWindow"\"">\n<FCBool Name="\""TiledBackground"\"" Value="\""0"\""/>\n<FCText Name="\""StyleSheet"\""/></FCParamGroup>\n<FCParamGroup Name="\""View"\"">\n<FCText Name="\""NavigationStyle"\"">Gui::CADNavigationStyle</FCText>\n<FCInt Name="\""OrbitStyle"\"" Value="\""1"\""/>\n<FCInt Name="\""AntiAliasing"\"" Value="\""0"\""/>\n<FCBool Name="\""ZoomAtCursor"\"" Value="\""0"\""/>\n<FCBool Name="\""InvertZoom"\"" Value="\""1"\""/>\n<FCFloat Name="\""ZoomStep"\"" Value="\""0.200000000000"\""/>\n<FCBool Name="\""CornerCoordSystem"\"" Value="\""1"\""/>\n<FCBool Name="\""ShowFPS"\"" Value="\""0"\""/>\n<FCBool Name="\""UseAutoRotation"\"" Value="\""1"\""/>\n<FCFloat Name="\""EyeDistance"\"" Value="\""5.000000000000"\""/>\n<FCBool Name="\""EnableBacklight"\"" Value="\""0"\""/>\n<FCUInt Name="\""BacklightColor"\"" Value="\""4294967295"\""/>\n<FCInt Name="\""BacklightIntensity"\"" Value="\""100"\""/>\n<FCBool Name="\""Perspective"\"" Value="\""0"\""/>\n<FCBool Name="\""Orthographic"\"" Value="\""1"\""/>\n<FCUInt Name="\""BackgroundColor"\"" Value="\""336897023"\""/>\n<FCUInt Name="\""BackgroundColor2"\"" Value="\""859006463"\""/>\n<FCUInt Name="\""BackgroundColor3"\"" Value="\""2543299327"\""/>\n<FCUInt Name="\""BackgroundColor4"\"" Value="\""1869583359"\""/>\n<FCBool Name="\""Simple"\"" Value="\""0"\""/>\n<FCBool Name="\""Gradient"\"" Value="\""1"\""/>\n<FCBool Name="\""UseBackgroundColorMid"\"" Value="\""0"\""/>\n<FCBool Name="\""EnablePreselection"\"" Value="\""1"\""/>\n<FCBool Name="\""EnableSelection"\"" Value="\""1"\""/>\n<FCUInt Name="\""HighlightColor"\"" Value="\""3789624575"\""/>\n<FCUInt Name="\""SelectionColor"\"" Value="\""481107199"\""/>\n<FCUInt Name="\""DefaultShapeColor"\"" Value="\""3435973887"\""/>\n<FCUInt Name="\""DefaultShapeLineColor"\"" Value="\""421075455"\""/>\n<FCInt Name="\""DefaultShapeLineWidth"\"" Value="\""2"\""/>\n<FCUInt Name="\""DefaultShapeVertexColor"\"" Value="\""421075455"\""/>\n<FCInt Name="\""DefaultShapeVertexWidth"\"" Value="\""2"\""/>\n<FCUInt Name="\""BoundingBoxColor"\"" Value="\""4294967295"\""/>\n<FCUInt Name="\""SketchEdgeColor"\"" Value="\""4294967295"\""/>\n<FCUInt Name="\""SketchVertexColor"\"" Value="\""4294967295"\""/>\n<FCUInt Name="\""EditedEdgeColor"\"" Value="\""4294967295"\""/>\n<FCUInt Name="\""EditedVertexColor"\"" Value="\""4280680703"\""/>\n<FCUInt Name="\""ConstructionColor"\"" Value="\""56575"\""/>\n<FCUInt Name="\""ExternalColor"\"" Value="\""3425924095"\""/>\n<FCUInt Name="\""FullyConstrainedColor"\"" Value="\""16711935"\""/>\n<FCUInt Name="\""ConstrainedIcoColor"\"" Value="\""4280680703"\""/>\n<FCUInt Name="\""NonDrivingConstrDimColor"\"" Value="\""2555903"\""/>\n<FCUInt Name="\""ConstrainedDimColor"\"" Value="\""4280680703"\""/>\n<FCInt Name="\""DefaultSketcherVertexWidth"\"" Value="\""2"\""/>\n<FCUInt Name="\""CursorTextColor"\"" Value="\""65535"\""/>\n<FCInt Name="\""EditSketcherFontSize"\"" Value="\""17"\""/>\n<FCUInt Name="\""AnnotationTextColor"\"" Value="\""3418866943"\""/>\n<FCInt Name="\""EditSketcherMarkerSize"\"" Value="\""7"\""/>\n<FCFloat Name="\""PickRadius"\"" Value="\""5.000000000000"\""/>\n<FCBool Name="\""UseVBO"\"" Value="\""0"\""/>\n<FCInt Name="\""CornerNaviCube"\"" Value="\""1"\""/>\n<FCInt Name="\""MarkerSize"\"" Value="\""11"\""/>\n<FCBool Name="\""DisableTouchTilt"\"" Value="\""1"\""/>\n<FCBool Name="\""DragAtCursor"\"" Value="\""0"\""/>\n<FCBool Name="\""ShowNaviCube"\"" Value="\""1"\""/>\n<FCText Name="\""NewDocumentCameraOrientation"\"">Top</FCText>\n<FCBool Name="\""RandomColor"\"" Value="\""0"\""/>\n<FCInt Name="\""RenderCache"\"" Value="\""0"\""/>\n<FCFloat Name="\""NewDocumentCameraScale"\"" Value="\""100.000000000000"\""/>\n<FCBool Name="\""DimensionsVisible"\"" Value="\""1"\""/></FCParamGroup>\n<FCParamGroup Name="\""PropertyView"\"">\n<FCInt Name="\""LastTabIndex"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""DAGView"\"">\n<FCBool Name="\""Enabled"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Websites"\"">\n<FCText Name="\""UserForum"\"">http://forum.freecadweb.org</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""Placement"\"">\n<FCInt Name="\""RotationMethod"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""DockWindows"\"">\n<FCParamGroup Name="\""TreeView"\"">\n<FCBool Name="\""Enabled"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""PropertyView"\"">\n<FCBool Name="\""Enabled"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""DAGView"\"">\n<FCBool Name="\""Enabled"\"" Value="\""0"\""/>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""Dialog"\""/>\n<FCParamGroup Name="\""??????"\"">\n<FCBool Name="\""CanAbortRecompute"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Expression"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Macro"\"">\n<FCParamGroup Name="\""Macros"\"">\n<FCParamGroup Name="\""Std_Macro_0"\"">\n<FCText Name="\""Script"\"">showSolidInfo.FCMacro</FCText>\n<FCText Name="\""Menu"\"">showSolidInfo</FCText>\n<FCText Name="\""Tooltip"\"">オブジェクトの表面積・体積・重心を表示します</FCText>\n<FCText Name="\""WhatsThis"\"">オブジェクトの表面積・体積・重心を表示します</FCText>\n<FCText Name="\""Statustip"\"">オブジェクトの表面積・体積・重心を表示します</FCText>\n<FCText Name="\""Pixmap"\"">bulb</FCText>\n<FCText Name="\""Accel"\"">Ctrl+I</FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_1"\"">\n<FCText Name="\""Script"\"">runGridEditor.py</FCText>\n<FCText Name="\""Menu"\"">gridEditor</FCText>\n<FCText Name="\""Tooltip"\"">gridEditorの起動</FCText>\n<FCText Name="\""WhatsThis"\"">gridEditorの起動</FCText>\n<FCText Name="\""Statustip"\"">gridEditorの起動</FCText>\n<FCText Name="\""Pixmap"\"">gridEditor</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_10"\"">\n<FCText Name="\""Script"\"">runParaview.py</FCText>\n<FCText Name="\""Menu"\"">runParaview</FCText>\n<FCText Name="\""Tooltip"\"">paraFoamの起動</FCText>\n<FCText Name="\""WhatsThis"\"">paraFoamの起動</FCText>\n<FCText Name="\""Statustip"\"">paraFoamの起動</FCText>\n<FCText Name="\""Pixmap"\"">pqAppIcon22</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_11"\"">\n<FCText Name="\""Script"\"">runTreefoam.py</FCText>\n<FCText Name="\""Menu"\"">runTreefoam</FCText>\n<FCText Name="\""Tooltip"\"">treefoam を起動します</FCText>\n<FCText Name="\""WhatsThis"\"">treefoam を起動します</FCText>\n<FCText Name="\""Statustip"\"">treefoam を起動します</FCText>\n<FCText Name="\""Pixmap"\"">treefoam48</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_12"\"">\n<FCText Name="\""Script"\"">runClearCase.py</FCText>\n<FCText Name="\""Menu"\"">runClearCase</FCText>\n<FCText Name="\""Tooltip"\"">計算結果を削除して、caseを初期化します</FCText>\n<FCText Name="\""WhatsThis"\"">計算結果を削除して、caseを初期化します</FCText>\n<FCText Name="\""Statustip"\"">計算結果を削除して、caseを初期化します</FCText>\n<FCText Name="\""Pixmap"\"">iniCase</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_13"\"">\n<FCText Name="\""Script"\"">runJgp.py</FCText>\n<FCText Name="\""Menu"\"">runJGPlot</FCText>\n<FCText Name="\""Tooltip"\"">jgpファイルの適合</FCText>\n<FCText Name="\""WhatsThis"\"">jgpファイルの適合</FCText>\n<FCText Name="\""Statustip"\"">jgpファイルの適合</FCText>\n<FCText Name="\""Pixmap"\"">Plot_workbench_icon</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_14"\"">\n<FCText Name="\""Script"\"">checkCaseFileName.py</FCText>\n<FCText Name="\""Menu"\"">checkCase</FCText>\n<FCText Name="\""Tooltip"\"">解析ケースファイルの確認</FCText>\n<FCText Name="\""WhatsThis"\"">解析ケースファイルの確認</FCText>\n<FCText Name="\""Statustip"\"">解析ケースファイルの確認</FCText>\n<FCText Name="\""Pixmap"\"">check16</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_15"\"">\n<FCText Name="\""Script"\"">makeSnappyHexMeshSetting.FCMacro</FCText>\n<FCText Name="\""Menu"\"">makeSnappyHexMeshSetting</FCText>\n<FCText Name="\""Tooltip"\"">snappyHexMesh用設定ファイルを作成します</FCText>\n<FCText Name="\""WhatsThis"\"">snappyHexMesh用設定ファイルを作成します</FCText>\n<FCText Name="\""Statustip"\"">snappyHexMesh用設定ファイルを作成します</FCText>\n<FCText Name="\""Pixmap"\"">sHM</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_2"\"">\n<FCText Name="\""Script"\"">makeCfMeshSetting.FCMacro</FCText>\n<FCText Name="\""Menu"\"">makeCfMeshSetting</FCText>\n<FCText Name="\""Tooltip"\"">cfMesh用設定ファイルを作成します</FCText>\n<FCText Name="\""WhatsThis"\"">cfMesh用設定ファイルを作成します</FCText>\n<FCText Name="\""Statustip"\"">cfMesh用設定ファイルを作成します</FCText>\n<FCText Name="\""Pixmap"\"">logo-72px</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_3"\"">\n<FCText Name="\""Script"\"">exportStl.FCMacro</FCText>\n<FCText Name="\""Menu"\"">exportStl</FCText>\n<FCText Name="\""Tooltip"\"">stlファイル（アスキー形式）を作成します</FCText>\n<FCText Name="\""WhatsThis"\"">stlファイル（アスキー形式）を作成します</FCText>\n<FCText Name="\""Statustip"\"">stlファイル（アスキー形式）を作成します</FCText>\n<FCText Name="\""Pixmap"\"">Tree_Dimension</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_4"\"">\n<FCText Name="\""Script"\"">solverSet.py</FCText>\n<FCText Name="\""Menu"\"">solverSet</FCText>\n<FCText Name="\""Tooltip"\"">新規にcaseを作成、又はsolverやmeshを入れ替え</FCText>\n<FCText Name="\""WhatsThis"\"">新規にcaseを作成、又はsolverやmeshを入れ替え</FCText>\n<FCText Name="\""Statustip"\"">新規にcaseを作成、又はsolverやmeshを入れ替え</FCText>\n<FCText Name="\""Pixmap"\"">createChange24</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_5"\"">\n<FCText Name="\""Script"\"">editConstantFolder.py</FCText>\n<FCText Name="\""Menu"\"">editConstantFolder</FCText>\n<FCText Name="\""Tooltip"\"">Propertiesの編集</FCText>\n<FCText Name="\""WhatsThis"\"">Propertiesの編集</FCText>\n<FCText Name="\""Statustip"\"">Propertiesの編集</FCText>\n<FCText Name="\""Pixmap"\"">editDict</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_6"\"">\n<FCText Name="\""Script"\"">editSystemFolder.py</FCText>\n<FCText Name="\""Menu"\"">editSystemFolder</FCText>\n<FCText Name="\""Tooltip"\"">Dict（system）の編集</FCText>\n<FCText Name="\""WhatsThis"\"">Dict（system）の編集</FCText>\n<FCText Name="\""Statustip"\"">Dict（system）の編集</FCText>\n<FCText Name="\""Pixmap"\"">editDict-sys</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_7"\"">\n<FCText Name="\""Script"\"">runSolver.py</FCText>\n<FCText Name="\""Menu"\"">runSolver</FCText>\n<FCText Name="\""Tooltip"\"">solverを起動</FCText>\n<FCText Name="\""WhatsThis"\"">solverを起動</FCText>\n<FCText Name="\""Statustip"\"">solverを起動</FCText>\n<FCText Name="\""Pixmap"\"">runSolver</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_8"\"">\n<FCText Name="\""Script"\"">runPlotWatcher.py</FCText>\n<FCText Name="\""Menu"\"">runPlotWatcher</FCText>\n<FCText Name="\""Tooltip"\"">plotWatcherの起動</FCText>\n<FCText Name="\""WhatsThis"\"">plotWatcherの起動</FCText>\n<FCText Name="\""Statustip"\"">plotWatcherの起動</FCText>\n<FCText Name="\""Pixmap"\"">plotWatcher</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_9"\"">\n<FCText Name="\""Script"\"">runParalel.py</FCText>\n<FCText Name="\""Menu"\"">runParallel</FCText>\n<FCText Name="\""Tooltip"\"">並列処理</FCText>\n<FCText Name="\""WhatsThis"\"">並列処理</FCText>\n<FCText Name="\""Statustip"\"">並列処理</FCText>\n<FCText Name="\""Pixmap"\"">parallel</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""Workbench"\"">\n<FCParamGroup Name="\""PartDesignWorkbench"\"">\n<FCParamGroup Name="\""Toolbar"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""StartWorkbench"\"">\n<FCParamGroup Name="\""Toolbar"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""CompleteWorkbench"\"">\n<FCParamGroup Name="\""Toolbar"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""DraftWorkbench"\"">\n<FCParamGroup Name="\""Toolbar"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Global"\"">\n<FCParamGroup Name="\""Toolbar"\"">\n<FCParamGroup Name="\""Custom_1"\"">\n<FCText Name="\""Name"\"">DEXCS</FCText>\n<FCBool Name="\""Active"\"" Value="\""1"\""/>\n<FCText Name="\""Std_Macro_4"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_2"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_15"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_14"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_11"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_1"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_5"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_6"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_12"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_7"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_8"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_9"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_10"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_13"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_3"\"">FreeCAD</FCText>\n<FCText Name="\""Draft_Downgrade"\"">DraftTools</FCText>\n<FCText Name="\""Part_Fuse"\"">Part</FCText>\n<FCText Name="\""Std_Macro_0"\"">FreeCAD</FCText>\n</FCParamGroup>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""FemWorkbench"\"">\n<FCParamGroup Name="\""Toolbar"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""PartWorkbench"\"">\n<FCParamGroup Name="\""Toolbar"\""/>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""MainWindow"\"">\n<FCParamGroup Name="\""Toolbars"\"">\n<FCBool Name="\""File"\"" Value="\""1"\""/>\n<FCBool Name="\""Macro"\"" Value="\""1"\""/>\n<FCBool Name="\""View"\"" Value="\""1"\""/>\n<FCBool Name="\""Navigation"\"" Value="\""0"\""/>\n<FCBool Name="\""Part Design"\"" Value="\""1"\""/>\n<FCBool Name="\""Sketcher geometries"\"" Value="\""1"\""/>\n<FCBool Name="\""Sketcher constraints"\"" Value="\""1"\""/>\n<FCBool Name="\""Sketcher tools"\"" Value="\""1"\""/>\n<FCBool Name="\""DEXCS"\"" Value="\""1"\""/>\n<FCBool Name="\""DEXCS1"\"" Value="\""1"\""/>\n<FCBool Name="\""Solids"\"" Value="\""1"\""/>\n<FCBool Name="\""Part tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Boolean"\"" Value="\""1"\""/>\n<FCBool Name="\""Measure"\"" Value="\""1"\""/>\n<FCBool Name="\""Draft tray"\"" Value="\""0"\""/>\n<FCBool Name="\""Part"\"" Value="\""1"\""/>\n<FCBool Name="\""Drawings"\"" Value="\""1"\""/>\n<FCBool Name="\""Raytracing"\"" Value="\""1"\""/>\n<FCBool Name="\""Drafting"\"" Value="\""1"\""/>\n<FCBool Name="\""Draft creation tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Draft modification tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Draft Snap"\"" Value="\""0"\""/>\n<FCBool Name="\""Custom1"\"" Value="\""1"\""/>\n<FCBool Name="\""TestTools"\"" Value="\""1"\""/>\n<FCBool Name="\""Image"\"" Value="\""1"\""/>\n<FCBool Name="\""Arch tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Draft tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Draft mod tools"\"" Value="\""1"\""/>\n<FCBool Name="\""FEM"\"" Value="\""1"\""/>\n<FCBool Name="\""Drawing"\"" Value="\""1"\""/>\n<FCBool Name="\""Workbench"\"" Value="\""1"\""/>\n<FCBool Name="\""Mesh tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Post Processing"\"" Value="\""1"\""/>\n<FCBool Name="\""Part Design Helper"\"" Value="\""1"\""/>\n<FCBool Name="\""Part Design Modeling"\"" Value="\""1"\""/>\n<FCBool Name="\""Sketcher"\"" Value="\""1"\""/>\n<FCBool Name="\""Sketcher B-spline tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Model"\"" Value="\""1"\""/>\n<FCBool Name="\""Mechanical Constraints"\"" Value="\""1"\""/>\n<FCBool Name="\""Thermal Constraints"\"" Value="\""1"\""/>\n<FCBool Name="\""Mesh"\"" Value="\""1"\""/>\n<FCBool Name="\""Fluid Constraints"\"" Value="\""1"\""/>\n<FCBool Name="\""Solve"\"" Value="\""1"\""/>\n<FCBool Name="\""Results"\"" Value="\""1"\""/>\n<FCBool Name="\""Structure"\"" Value="\""1"\""/>\n<FCBool Name="\""Electrostatic Constraints"\"" Value="\""1"\""/>\n<FCBool Name="\""Sketcher virtual space"\"" Value="\""1"\""/>\n<FCBool Name="\""CFD"\"" Value="\""1"\""/>\n<FCBool Name="\""CfdOF"\"" Value="\""1"\""/>\n<FCBool Name="\""Utilities"\"" Value="\""1"\""/>\n<FCBool Name="\""DEXCS-N"\"" Value="\""1"\""/>\n<FCBool Name="\""Project Setup"\"" Value="\""1"\""/>\n<FCBool Name="\""Tool Commands"\"" Value="\""1"\""/>\n<FCBool Name="\""New Operations"\"" Value="\""1"\""/>\n<FCBool Name="\""Path Modification"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""DockWindows"\"">\n<FCBool Name="\""Std_ReportView"\"" Value="\""1"\""/>\n<FCBool Name="\""Std_TreeView"\"" Value="\""0"\""/>\n<FCBool Name="\""Std_PropertyView"\"" Value="\""0"\""/>\n<FCBool Name="\""Std_SelectionView"\"" Value="\""0"\""/>\n<FCBool Name="\""Std_CombiView"\"" Value="\""1"\""/>\n<FCBool Name="\""Std_PythonView"\"" Value="\""1"\""/>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""Workbenches"\"">\n<FCText Name="\""Enabled"\"">ArchWorkbench,CompleteWorkbench,DraftWorkbench,DrawingWorkbench,FemWorkbench,ImageWorkbench,InspectionWorkbench,MeshWorkbench,NoneWorkbench,OpenSCADWorkbench,PartDesignWorkbench,PartWorkbench,PathWorkbench,PointsWorkbench,RaytracingWorkbench,ReverseEngineeringWorkbench,RobotWorkbench,SketcherWorkbench,SpreadsheetWorkbench,StartWorkbench,TestWorkbench,WebWorkbench,SurfaceWorkbench,TechDrawWorkbench,</FCText>\n<FCText Name="\""Disabled"\""></FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""History"\"">\n<FCParamGroup Name="\""SketchGridSize"\"">\n<FCText Name="\""Hist0"\"">10.000000 mm</FCText>\n<FCText Name="\""Hist1"\"">10 mm</FCText>\n<FCText Name="\""Hist2"\"">10.000000 mm</FCText>\n<FCText Name="\""Hist3"\"">10 mm</FCText>\n<FCText Name="\""Hist4"\"">10.00 mm</FCText>\n<FCText Name="\""Hist5"\"">10 mm</FCText></FCParamGroup>\n<FCParamGroup Name="\""SketcherLength"\"">\n<FCText Name="\""Hist0"\"">7 mm</FCText>\n<FCText Name="\""Hist1"\"">3 mm</FCText>\n<FCText Name="\""Hist2"\"">18 mm</FCText>\n<FCText Name="\""Hist3"\"">40 mm</FCText>\n<FCText Name="\""Hist4"\"">4 mm</FCText>\n<FCText Name="\""Hist5"\"">50 mm</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""SketcherAngle"\"">\n<FCText Name="\""Hist0"\"">359.999 °</FCText>\n<FCText Name="\""Hist1"\"">0.00 °</FCText>\n<FCText Name="\""Hist2"\"">-10.00 °</FCText>\n<FCText Name="\""Hist3"\"">30 °</FCText>\n<FCText Name="\""Hist4"\"">45 °</FCText>\n<FCText Name="\""Hist5"\"">135 °</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""PadLength"\"">\n<FCText Name="\""Hist0"\"">10.00 mm</FCText>\n<FCText Name="\""Hist1"\"">271.73 mm</FCText>\n<FCText Name="\""Hist2"\"">280.00 mm</FCText>\n<FCText Name="\""Hist3"\"">250 mm</FCText></FCParamGroup>\n<FCParamGroup Name="\""PadLength2"\"">\n<FCText Name="\""Hist0"\"">100.00 mm</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""PadOffset"\"">\n<FCText Name="\""Hist0"\"">0.00 mm</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""PocketLength"\"">\n<FCText Name="\""Hist0"\"">10 mm</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""PocketLength2"\"">\n<FCText Name="\""Hist0"\"">100.00 mm</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""PocketOffset"\"">\n<FCText Name="\""Hist0"\"">0.00 mm</FCText>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""LogLevels"\"">\n<FCInt Name="\""Default"\"" Value="\""2"\""/>\n<FCInt Name="\""Path.Area"\"" Value="\""0"\""/></FCParamGroup>\n<FCParamGroup Name="\""Spaceball"\"">\n<FCParamGroup Name="\""Motion"\""/>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""Tux"\"">\n<FCParamGroup Name="\""NavigationIndicator"\"">\n<FCBool Name="\""Compact"\"" Value="\""0"\""/>\n<FCBool Name="\""Tooltip"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""PersistentToolbars"\"">\n<FCParamGroup Name="\""User"\"">\n<FCParamGroup Name="\""StartWorkbench"\"">\n<FCBool Name="\""Saved"\"" Value="\""1"\""/>\n<FCText Name="\""Top"\"">Break,File,Workbench,Macro,View,Structure</FCText>\n<FCText Name="\""Left"\"">DEXCS</FCText>\n<FCText Name="\""Right"\""/>\n<FCText Name="\""Bottom"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""PartWorkbench"\"">\n<FCBool Name="\""Saved"\"" Value="\""1"\""/>\n<FCText Name="\""Top"\"">Break,File,Workbench,Macro,Structure,Solids,Part tools,Boolean,Break,Measure,View</FCText>\n<FCText Name="\""Left"\"">DEXCS</FCText>\n<FCText Name="\""Right"\""/>\n<FCText Name="\""Bottom"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""FemWorkbench"\""/>\n<FCParamGroup Name="\""CompleteWorkbench"\""/>\n<FCParamGroup Name="\""MeshWorkbench"\""/>\n<FCParamGroup Name="\""PartDesignWorkbench"\""/>\n<FCParamGroup Name="\""SketcherWorkbench"\""/>\n<FCParamGroup Name="\""DraftWorkbench"\"">\n<FCBool Name="\""Saved"\"" Value="\""1"\""/>\n<FCText Name="\""Top"\"">Break,File,Workbench,Macro,Break,View,Structure,Draft Snap,Break,Draft tray,Draft modification tools,Draft creation tools</FCText>\n<FCText Name="\""Left"\"">DEXCS</FCText>\n<FCText Name="\""Right"\""/>\n<FCText Name="\""Bottom"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""DrawingWorkbench"\""/>\n<FCParamGroup Name="\""CfdWorkbench"\""/>\n<FCParamGroup Name="\""CfdOFWorkbench"\""/>\n<FCParamGroup Name="\""NoneWorkbench"\""/>\n<FCParamGroup Name="\""PathWorkbench"\""/>\n<FCParamGroup Name="\""ImageWorkbench"\""/>\n</FCParamGroup>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""Plugins"\"">\n<FCParamGroup Name="\""addonsRepository"\"">\n<FCBool Name="\""readWarning"\"" Value="\""1"\""/>\n</FCParamGroup>\n</FCParamGroup>\n</FCParamGroup>\n</FCParameters>\n')
    else: # 2021
        s = ('<?xml version="\""1.0"\"" encoding="\""UTF-8"\"" standalone="\""no"\"" ?>\n<FCParameters>\n<FCParamGroup Name="\""Root"\"">\n<FCParamGroup Name="\""BaseApp"\"">\n<FCParamGroup Name="\""LogLevels"\"">\n<FCInt Name="\""Default"\"" Value="\""2"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Preferences"\"">\n<FCParamGroup Name="\""General"\"">\n<FCText Name="\""FileOpenSavePath"\"">/home/dexcs/Desktop/shareVM/DEXCS2021/Desktop/DEXCS/cfMeshTutorials/backStep</FCText>\n<FCText Name="\""LastModule"\"">FemWorkbench</FCText>\n<FCText Name="\""AutoloadModule"\"">dexcsCfdOFWorkbench</FCText>\n<FCBool Name="\""ShowSplasher"\"" Value="\""1"\""/>\n<FCBool Name="\""PythonWordWrap"\"" Value="\""1"\""/>\n<FCInt Name="\""ToolbarIconSize"\"" Value="\""24"\""/>\n<FCText Name="\""FileExportFilter"\"">BREP format (*.brep *.brp)</FCText>\n<FCText Name="\""FileImportFilter"\"">Supported formats ( *.3ds *.FCMacro *.FCMat *.FCScript *.asc *.ast *.bdf *.bmp *.bms *.brep *.brp *.cnc *.csg *.csv *.dae *.dat *.dwg *.dxf *.emn *.frd *.gc *.gcad *.gcode *.html *.ifc *.iges *.igs *.inc *.inp *.iv *.jpg *.json *.med *.meshjson *.meshyaml *.nc *.ncc *.ngc *.obj *.oca *.off *.pcd *.plmxml *.ply *.png *.pov *.py *.shp *.smf *.step *.stl *.stp *.stpZ *.stpz *.svg *.svgz *.tap *.unv *.vrml *.vtk *.vtu *.wrl *.wrl.gz *.wrz *.xdmf *.xhtml *.xlsx *.xml *.xpm *.yaml *.z88 *.zip)</FCText>\n<FCBool Name="\""ConfirmAll"\"" Value="\""0"\""/>\n<FCBool Name="\""RecentIncludesImported"\"" Value="\""1"\""/>\n<FCBool Name="\""RecentIncludesExported"\"" Value="\""0"\""/>\n<FCText Name="\""Language"\"">Japanese</FCText>\n<FCText Name="\""BackgroundAutoloadModules"\"">DraftWorkbench</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""Units"\"">\n<FCInt Name="\""UserSchema"\"" Value="\""0"\""/>\n<FCInt Name="\""Decimals"\"" Value="\""2"\""/>\n<FCInt Name="\""FracInch"\"" Value="\""8"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Macro"\"">\n<FCText Name="\""MacroPath"\"">/home/dexcs/.FreeCAD</FCText>\n<FCBool Name="\""LocalEnvironment"\"" Value="\""1"\""/>\n<FCBool Name="\""RecordGui"\"" Value="\""1"\""/>\n<FCBool Name="\""GuiAsComment"\"" Value="\""1"\""/>\n<FCBool Name="\""ScriptToPyConsole"\"" Value="\""1"\""/>\n<FCBool Name="\""ScriptToFile"\"" Value="\""0"\""/>\n<FCText Name="\""ScriptFile"\"">FullScript.FCScript</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""Mod"\"">\n<FCParamGroup Name="\""OpenSCAD"\""/>\n<FCParamGroup Name="\""Import"\"">\n<FCParamGroup Name="\""hSTEP"\"">\n<FCBool Name="\""ReadShapeCompoundMode"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCBool Name="\""ExportHiddenObject"\"" Value="\""0"\""/>\n<FCBool Name="\""ExportLegacy"\"" Value="\""0"\""/>\n<FCBool Name="\""ExportKeepPlacement"\"" Value="\""0"\""/>\n<FCBool Name="\""ImportHiddenObject"\"" Value="\""0"\""/>\n<FCBool Name="\""UseLinkGroup"\"" Value="\""0"\""/>\n<FCBool Name="\""UseBaseName"\"" Value="\""0"\""/>\n<FCBool Name="\""ReduceObjects"\"" Value="\""0"\""/>\n<FCBool Name="\""ExpandCompound"\"" Value="\""0"\""/>\n<FCBool Name="\""ShowProgress"\"" Value="\""0"\""/>\n<FCInt Name="\""ImportMode"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Start"\"">\n<FCText Name="\""AutoloadModule"\"">StartWorkbench</FCText>\n<FCUInt Name="\""BackgroundColor1"\"" Value="\""1331197183"\""/>\n<FCUInt Name="\""BackgroundTextColor"\"" Value="\""4294703103"\""/>\n<FCUInt Name="\""PageColor"\"" Value="\""4294967295"\""/>\n<FCUInt Name="\""PageTextColor"\"" Value="\""255"\""/>\n<FCUInt Name="\""BoxColor"\"" Value="\""3722305023"\""/>\n<FCUInt Name="\""LinkColor"\"" Value="\""65535"\""/>\n<FCUInt Name="\""BackgroundColor2"\"" Value="\""2141107711"\""/>\n<FCText Name="\""Template"\""/>\n<FCText Name="\""BackgroundImage"\""/>\n<FCText Name="\""ShowCustomFolder"\""/>\n<FCBool Name="\""InWeb"\"" Value="\""0"\""/>\n<FCBool Name="\""InBrowser"\"" Value="\""1"\""/>\n<FCBool Name="\""ShowNotes"\"" Value="\""0"\""/>\n<FCBool Name="\""ShowExamples"\"" Value="\""1"\""/>\n<FCBool Name="\""closeStart"\"" Value="\""0"\""/>\n<FCBool Name="\""DoNotShowOnOpen"\"" Value="\""0"\""/>\n<FCBool Name="\""ShowForum"\"" Value="\""0"\""/>\n<FCBool Name="\""UseStyleSheet"\"" Value="\""0"\""/>\n<FCBool Name="\""NewFileGradient"\"" Value="\""0"\""/>\n<FCBool Name="\""ShowTips"\"" Value="\""1"\""/>\n<FCText Name="\""FontFamily"\""/>\n<FCInt Name="\""FontSize"\"" Value="\""13"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Part"\"">\n<FCParamGroup Name="\""General"\"">\n<FCInt Name="\""WriteSurfaceCurveMode"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""IGES"\"">\n<FCInt Name="\""Unit"\"" Value="\""0"\""/>\n<FCBool Name="\""BrepMode"\"" Value="\""0"\""/>\n<FCBool Name="\""SkipBlankEntities"\"" Value="\""1"\""/>\n<FCText Name="\""Company"\""/>\n<FCText Name="\""Author"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""STEP"\"">\n<FCInt Name="\""Unit"\"" Value="\""0"\""/>\n<FCText Name="\""Scheme"\"">AP214IS</FCText>\n<FCText Name="\""Company"\""/>\n<FCText Name="\""Author"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Boolean"\"">\n<FCBool Name="\""CheckModel"\"" Value="\""0"\""/>\n<FCBool Name="\""RefineModel"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCBool Name="\""AddBaseObjectName"\"" Value="\""0"\""/>\n<FCFloat Name="\""MeshDeviation"\"" Value="\""0.500000000000"\""/>\n<FCFloat Name="\""MeshAngularDeflection"\"" Value="\""28.500000000000"\""/>\n<FCBool Name="\""TwoSideRendering"\"" Value="\""1"\""/>\n<FCInt Name="\""GridLinePattern"\"" Value="\""3855"\""/>\n<FCParamGroup Name="\""CheckGeometry"\"">\n<FCBool Name="\""RunBOPCheck"\"" Value="\""0"\""/>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""Fem"\"">\n<FCParamGroup Name="\""Ccx"\"">\n<FCInt Name="\""Solver"\"" Value="\""0"\""/>\n<FCInt Name="\""AnalysisType"\"" Value="\""0"\""/>\n<FCInt Name="\""AnalysisNumCPUs"\"" Value="\""1"\""/>\n<FCBool Name="\""NonlinearGeometry"\"" Value="\""0"\""/>\n<FCBool Name="\""UseNonCcxIterationParam"\"" Value="\""0"\""/>\n<FCBool Name="\""StaticAnalysis"\"" Value="\""1"\""/>\n<FCInt Name="\""AnalysisMaxIterations"\"" Value="\""2000"\""/>\n<FCFloat Name="\""AnalysisTimeInitialStep"\"" Value="\""0.010000000000"\""/>\n<FCFloat Name="\""AnalysisTime"\"" Value="\""1.000000000000"\""/>\n<FCBool Name="\""BeamShellOutput"\"" Value="\""0"\""/>\n<FCInt Name="\""EigenmodesCount"\"" Value="\""10"\""/>\n<FCFloat Name="\""EigenmodeHighLimit"\"" Value="\""1000000.000000000000"\""/>\n<FCFloat Name="\""EigenmodeLowLimit"\"" Value="\""0.000000000000"\""/>\n<FCBool Name="\""UseInternalEditor"\"" Value="\""1"\""/>\n<FCText Name="\""ExternalEditorPath"\""/>\n<FCBool Name="\""UseStandardCcxLocation"\"" Value="\""1"\""/>\n<FCText Name="\""ccxBinaryPath"\"">/home/dexcs/CalculiX/CalculiX/ccx_2.16/src/ccx_2.16</FCText>\n<FCBool Name="\""SplitInputWriter"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Elmer"\"">\n<FCBool Name="\""UseStandardElmerLocation"\"" Value="\""1"\""/>\n<FCText Name="\""elmerBinaryPath"\""/>\n<FCBool Name="\""UseStandardGridLocation"\"" Value="\""1"\""/>\n<FCText Name="\""gridBinaryPath"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Z88"\"">\n<FCBool Name="\""UseStandardZ88Location"\"" Value="\""1"\""/>\n<FCText Name="\""z88BinaryPath"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""General"\"">\n<FCBool Name="\""AnalysisGroupMeshing"\"" Value="\""1"\""/>\n<FCBool Name="\""RestoreResultDialog"\"" Value="\""1"\""/>\n<FCBool Name="\""KeepResultsOnReRun"\"" Value="\""0"\""/>\n<FCBool Name="\""HideConstraint"\"" Value="\""0"\""/>\n<FCBool Name="\""UseTempDirectory"\"" Value="\""0"\""/>\n<FCBool Name="\""UseBesideDirectory"\"" Value="\""1"\""/>\n<FCBool Name="\""UseCustomDirectory"\"" Value="\""0"\""/>\n<FCText Name="\""CustomDirectoryPath"\""/>\n<FCBool Name="\""OverwriteSolverWorkingDirectory"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Abaqus"\"">\n<FCInt Name="\""AbaqusElementChoice"\"" Value="\""0"\""/>\n<FCBool Name="\""AbaqusWriteGroups"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""InOutVtk"\"">\n<FCInt Name="\""ImportObject"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Gmsh"\"">\n<FCBool Name="\""UseStandardGmshLocation"\"" Value="\""0"\""/>\n<FCText Name="\""gmshBinaryPath"\"">/opt/gmsh-4.8.0-Linux64/bin/gmsh</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""mystran"\"">\n<FCBool Name="\""UseStandardMystranLocation"\"" Value="\""1"\""/>\n<FCText Name="\""MystranBinaryPath"\""/>\n<FCBool Name="\""writeCommentsToInputFile"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Mystran"\""/></FCParamGroup>\n<FCParamGroup Name="\""Draft"\"">\n<FCFloat Name="\""dxfScaling"\"" Value="\""1.000000000000"\""/>\n<FCFloat Name="\""maxsegmentlength"\"" Value="\""5.000000000000"\""/>\n<FCBool Name="\""dxfShowDialog"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfUseLegacyImporter"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfUseLegacyExporter"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfAllowDownload"\"" Value="\""0"\""/>\n<FCBool Name="\""dxftext"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfImportPoints"\"" Value="\""0"\""/>\n<FCBool Name="\""dxflayout"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfstarblocks"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfGetOriginalColors"\"" Value="\""0"\""/>\n<FCBool Name="\""joingeometry"\"" Value="\""0"\""/>\n<FCBool Name="\""groupLayers"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfStdSize"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfUseDraftVisGroups"\"" Value="\""1"\""/>\n<FCBool Name="\""importDxfHatches"\"" Value="\""0"\""/>\n<FCBool Name="\""renderPolylineWidth"\"" Value="\""0"\""/>\n<FCBool Name="\""DiscretizeEllipses"\"" Value="\""1"\""/>\n<FCBool Name="\""dxfmesh"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfExportBlocks"\"" Value="\""1"\""/>\n<FCBool Name="\""dxfproject"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfCreatePart"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfCreateDraft"\"" Value="\""0"\""/>\n<FCBool Name="\""dxfCreateSketch"\"" Value="\""1"\""/>\n<FCText Name="\""TeighaFileConverter"\""/>\n<FCFloat Name="\""svgDiscretization"\"" Value="\""0.000000000000"\""/>\n<FCInt Name="\""svgstyle"\"" Value="\""0"\""/>\n<FCInt Name="\""svg_export_style"\"" Value="\""0"\""/>\n<FCBool Name="\""svgDisableUnitScaling"\"" Value="\""0"\""/>\n<FCBool Name="\""SvgLinesBlack"\"" Value="\""1"\""/>\n<FCBool Name="\""ocaareas"\"" Value="\""0"\""/>\n<FCInt Name="\""precision"\"" Value="\""6"\""/>\n<FCFloat Name="\""tolerance"\"" Value="\""0.050000000000"\""/>\n<FCText Name="\""ClonePrefix"\""/>\n<FCText Name="\""constructiongroupname"\"">コンストラクション</FCText>\n<FCInt Name="\""defaultWP"\"" Value="\""0"\""/>\n<FCBool Name="\""AutogroupAddGroups"\"" Value="\""0"\""/>\n<FCBool Name="\""focusOnLength"\"" Value="\""0"\""/>\n<FCBool Name="\""useSupport"\"" Value="\""0"\""/>\n<FCBool Name="\""fillmode"\"" Value="\""1"\""/>\n<FCBool Name="\""selectBaseObjects"\"" Value="\""0"\""/>\n<FCBool Name="\""copymode"\"" Value="\""0"\""/>\n<FCBool Name="\""UsePartPrimitives"\"" Value="\""0"\""/>\n<FCUInt Name="\""constructioncolor"\"" Value="\""746455039"\""/>\n<FCText Name="\""inCommandShortcutCycleSnap"\"">"\`"</FCText>\n<FCText Name="\""inCommandShortcutSnap"\"">S</FCText>\n<FCText Name="\""inCommandShortcutRelative"\"">R</FCText>\n<FCText Name="\""inCommandShortcutClose"\"">O</FCText>\n<FCText Name="\""inCommandShortcutContinue"\"">T</FCText>\n<FCText Name="\""inCommandShortcutIncreaseRadius"\"">[</FCText>\n<FCText Name="\""inCommandShortcutDecreaseRadius"\"">]</FCText>\n<FCText Name="\""inCommandShortcutSubelementMode"\"">D</FCText>\n<FCText Name="\""inCommandShortcutFill"\"">L</FCText>\n<FCText Name="\""inCommandShortcutCopy"\"">P</FCText>\n<FCText Name="\""inCommandShortcutSelectEdge"\"">E</FCText>\n<FCText Name="\""inCommandShortcutLength"\"">H</FCText>\n<FCText Name="\""inCommandShortcutWipe"\"">W</FCText>\n<FCText Name="\""inCommandShortcutExit"\"">A</FCText>\n<FCText Name="\""inCommandShortcutAddHold"\"">Q</FCText>\n<FCText Name="\""inCommandShortcutSetWP"\"">U</FCText>\n<FCText Name="\""inCommandShortcutRestrictX"\"">X</FCText>\n<FCText Name="\""inCommandShortcutRestrictY"\"">Y</FCText>\n<FCText Name="\""RestrictZ"\"">Z</FCText>\n<FCBool Name="\""DisplayStatusbarSnapWidget"\"" Value="\""1"\""/>\n<FCBool Name="\""DisplayStatusbarScaleWidget"\"" Value="\""0"\""/>\n<FCInt Name="\""gridEvery"\"" Value="\""10"\""/>\n<FCInt Name="\""gridSize"\"" Value="\""100"\""/>\n<FCInt Name="\""DraftEditMaxObjects"\"" Value="\""5"\""/>\n<FCInt Name="\""DraftEditPickRadius"\"" Value="\""20"\""/>\n<FCFloat Name="\""gridSpacing"\"" Value="\""1.000000000000"\""/>\n<FCInt Name="\""modsnap"\"" Value="\""1"\""/>\n<FCInt Name="\""modalt"\"" Value="\""2"\""/>\n<FCInt Name="\""modconstrain"\"" Value="\""0"\""/>\n<FCBool Name="\""showSnapBar"\"" Value="\""1"\""/>\n<FCBool Name="\""hideSnapBar"\"" Value="\""0"\""/>\n<FCBool Name="\""alwaysSnap"\"" Value="\""1"\""/>\n<FCBool Name="\""grid"\"" Value="\""1"\""/>\n<FCBool Name="\""alwaysShowGrid"\"" Value="\""1"\""/>\n<FCBool Name="\""gridBorder"\"" Value="\""1"\""/>\n<FCUInt Name="\""gridColor"\"" Value="\""842157055"\""/>\n<FCInt Name="\""HatchPatternResolution"\"" Value="\""128"\""/>\n<FCText Name="\""svgDashedLine"\"">0.09,0.05</FCText>\n<FCText Name="\""svgDashdotLine"\"">0.09,0.05,0.02,0.05</FCText>\n<FCText Name="\""svgDottedLine"\"">0.02,0.02</FCText>\n<FCText Name="\""template"\""/>\n<FCText Name="\""patternFile"\""/>\n<FCInt Name="\""snapStyle"\"" Value="\""0"\""/>\n<FCBool Name="\""saveonexit"\"" Value="\""0"\""/>\n<FCBool Name="\""showPlaneTracker"\"" Value="\""0"\""/>\n<FCBool Name="\""preserveFaceColor"\"" Value="\""0"\""/>\n<FCBool Name="\""preserveFaceNames"\"" Value="\""0"\""/>\n<FCUInt Name="\""snapcolor"\"" Value="\""4294967295"\""/>\n<FCInt Name="\""dimPrecision"\"" Value="\""2"\""/>\n<FCFloat Name="\""textheight"\"" Value="\""0.200000000000"\""/>\n<FCFloat Name="\""extlines"\"" Value="\""0.300000000000"\""/>\n<FCFloat Name="\""extovershoot"\"" Value="\""0.000000000000"\""/>\n<FCFloat Name="\""dimovershoot"\"" Value="\""0.000000000000"\""/>\n<FCFloat Name="\""arrowsize"\"" Value="\""0.100000000000"\""/>\n<FCFloat Name="\""dimspacing"\"" Value="\""0.050000000000"\""/>\n<FCText Name="\""textfont"\""/>\n<FCText Name="\""FontFile"\""/>\n<FCInt Name="\""dimstyle"\"" Value="\""0"\""/>\n<FCInt Name="\""dimsymbol"\"" Value="\""0"\""/>\n<FCInt Name="\""dimorientation"\"" Value="\""0"\""/>\n<FCBool Name="\""showUnit"\"" Value="\""1"\""/>\n<FCFloat Name="\""HatchPatternSize"\"" Value="\""1.000000000000"\""/>\n<FCText Name="\""overrideUnit"\""/>\n<FCInt Name="\""gridTransparency"\"" Value="\""0"\""/>\n<FCBool Name="\""coloredGridAxes"\"" Value="\""1"\""/>\n<FCText Name="\""inCommandShortcutGlobal"\"">G</FCText></FCParamGroup>\n<FCParamGroup Name="\""Arch"\"">\n<FCInt Name="\""ifcMulticore"\"" Value="\""0"\""/>\n<FCText Name="\""ifcRootElement"\"">IfcProduct</FCText>\n<FCText Name="\""ifcSkip"\""/>\n<FCInt Name="\""ifcImportModeArch"\"" Value="\""0"\""/>\n<FCInt Name="\""ifcImportModeStruct"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcShowDialog"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcDebug"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcCreateClones"\"" Value="\""1"\""/>\n<FCBool Name="\""ifcSeparateOpenings"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcGetExtrusions"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcSplitLayers"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcPrefixNumbers"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcMergeMaterials"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcImportProperties"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcAllowInvalid"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcFitViewOnImport"\"" Value="\""0"\""/>\n<FCBool Name="\""IfcImportFreeCADProperties"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcReplaceProject"\"" Value="\""0"\""/>\n<FCInt Name="\""ifcExportModel"\"" Value="\""0"\""/>\n<FCInt Name="\""ifcUnit"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcExportAsBrep"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcUseDaeOptions"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcJoinCoplanarFacets"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcStoreUid"\"" Value="\""1"\""/>\n<FCBool Name="\""ifcSerialize"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcExport2D"\"" Value="\""1"\""/>\n<FCBool Name="\""IfcExportFreeCADProperties"\"" Value="\""0"\""/>\n<FCBool Name="\""ifcCompress"\"" Value="\""1"\""/>\n<FCBool Name="\""DisableIfcRectangleProfileDef"\"" Value="\""0"\""/>\n<FCBool Name="\""getStandardCase"\"" Value="\""0"\""/>\n<FCBool Name="\""IfcAddDefaultSite"\"" Value="\""0"\""/>\n<FCBool Name="\""IfcAddDefaultBuilding"\"" Value="\""1"\""/>\n<FCBool Name="\""IfcAddDefaultStorey"\"" Value="\""0"\""/>\n<FCInt Name="\""ColladaSegsPerEdge"\"" Value="\""1"\""/>\n<FCInt Name="\""ColladaSegsPerRadius"\"" Value="\""2"\""/>\n<FCFloat Name="\""ColladaScalingFactor"\"" Value="\""1.000000000000"\""/>\n<FCFloat Name="\""ColladaTessellation"\"" Value="\""1.000000000000"\""/>\n<FCFloat Name="\""ColladaGrading"\"" Value="\""0.300000000000"\""/>\n<FCInt Name="\""ColladaMesher"\"" Value="\""0"\""/>\n<FCBool Name="\""ColladaSecondOrder"\"" Value="\""0"\""/>\n<FCBool Name="\""ColladaOptimize"\"" Value="\""1"\""/>\n<FCBool Name="\""ColladaAllowQuads"\"" Value="\""0"\""/>\n<FCInt Name="\""MaxComputeAreas"\"" Value="\""20"\""/>\n<FCInt Name="\""ReferenceCheckInterval"\"" Value="\""60"\""/>\n<FCFloat Name="\""ConversionTolerance"\"" Value="\""0.001000000000"\""/>\n<FCFloat Name="\""CutLineThickness"\"" Value="\""2.000000000000"\""/>\n<FCFloat Name="\""SymbolLineThickness"\"" Value="\""0.600000000000"\""/>\n<FCFloat Name="\""patternScale"\"" Value="\""0.010000000000"\""/>\n<FCText Name="\""archHiddenPattern"\"">30, 10</FCText>\n<FCText Name="\""BimServerUrl"\"">http://localhost:8082</FCText>\n<FCInt Name="\""IfcVersion"\"" Value="\""0"\""/>\n<FCBool Name="\""autoJoinWalls"\"" Value="\""1"\""/>\n<FCBool Name="\""joinWallSketches"\"" Value="\""0"\""/>\n<FCBool Name="\""archRemoveExternal"\"" Value="\""0"\""/>\n<FCBool Name="\""applyconstructionStyle"\"" Value="\""0"\""/>\n<FCBool Name="\""MoveWithHost"\"" Value="\""0"\""/>\n<FCBool Name="\""MoveBase"\"" Value="\""0"\""/>\n<FCBool Name="\""UseMaterialColor"\"" Value="\""1"\""/>\n<FCBool Name="\""ConversionFast"\"" Value="\""1"\""/>\n<FCBool Name="\""ConversionFlat"\"" Value="\""0"\""/>\n<FCBool Name="\""ConversionCut"\"" Value="\""1"\""/>\n<FCBool Name="\""ShowVRMDebug"\"" Value="\""0"\""/>\n<FCBool Name="\""BimServerBrowser"\"" Value="\""0"\""/>\n<FCBool Name="\""surveyUnits"\"" Value="\""1"\""/>\n<FCInt Name="\""WindowTransparency"\"" Value="\""85"\""/>\n<FCInt Name="\""StairsSteps"\"" Value="\""17"\""/>\n<FCInt Name="\""defaultSpaceTransparency"\"" Value="\""85"\""/>\n<FCFloat Name="\""WallWidth"\"" Value="\""200.000000000000"\""/>\n<FCFloat Name="\""WallHeight"\"" Value="\""3000.000000000000"\""/>\n<FCFloat Name="\""StructureLength"\"" Value="\""100.000000000000"\""/>\n<FCFloat Name="\""StructureWidth"\"" Value="\""100.000000000000"\""/>\n<FCFloat Name="\""StructureHeight"\"" Value="\""1000.000000000000"\""/>\n<FCFloat Name="\""RebarDiameter"\"" Value="\""6.000000000000"\""/>\n<FCFloat Name="\""RebarOffset"\"" Value="\""30.000000000000"\""/>\n<FCFloat Name="\""WindowWidth"\"" Value="\""1000.000000000000"\""/>\n<FCFloat Name="\""WindowHeight"\"" Value="\""1000.000000000000"\""/>\n<FCFloat Name="\""WindowThickness"\"" Value="\""100.000000000000"\""/>\n<FCFloat Name="\""StairsLength"\"" Value="\""4500.000000000000"\""/>\n<FCFloat Name="\""StairsWidth"\"" Value="\""1000.000000000000"\""/>\n<FCFloat Name="\""StairsHeight"\"" Value="\""3000.000000000000"\""/>\n<FCFloat Name="\""PanelLength"\"" Value="\""1000.000000000000"\""/>\n<FCFloat Name="\""PanelWidth"\"" Value="\""1000.000000000000"\""/>\n<FCFloat Name="\""PanelThickness"\"" Value="\""10.000000000000"\""/>\n<FCFloat Name="\""PipeDiameter"\"" Value="\""50.000000000000"\""/>\n<FCInt Name="\""defaultSpaceStyle"\"" Value="\""2"\""/>\n<FCBool Name="\""WallSketches"\"" Value="\""1"\""/>\n<FCUInt Name="\""WallColor"\"" Value="\""3604403967"\""/>\n<FCUInt Name="\""StructureColor"\"" Value="\""2527705855"\""/>\n<FCUInt Name="\""RebarColor"\"" Value="\""3111475967"\""/>\n<FCUInt Name="\""WindowColor"\"" Value="\""556614399"\""/>\n<FCUInt Name="\""WindowGlassColor"\"" Value="\""1572326399"\""/>\n<FCUInt Name="\""PanelColor"\"" Value="\""3416289279"\""/>\n<FCUInt Name="\""ColorHelpers"\"" Value="\""674321151"\""/>\n<FCUInt Name="\""defaultSpaceColor"\"" Value="\""4280090879"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""PartDesign"\"">\n<FCBool Name="\""RefineModel"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Material"\"">\n<FCParamGroup Name="\""Resources"\"">\n<FCBool Name="\""UseBuiltInMaterials"\"" Value="\""1"\""/>\n<FCBool Name="\""UseMaterialsFromConfigDir"\"" Value="\""1"\""/>\n<FCBool Name="\""UseMaterialsFromCustomDir"\"" Value="\""1"\""/>\n<FCText Name="\""CustomMaterialsDir"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Cards"\"">\n<FCBool Name="\""DeleteDuplicates"\"" Value="\""1"\""/>\n<FCBool Name="\""SortByResources"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCInt Name="\""MaterialEditorWidth"\"" Value="\""441"\""/>\n<FCInt Name="\""MaterialEditorHeight"\"" Value="\""626"\""/>\n<FCBool Name="\""TreeExpandMeta"\"" Value="\""1"\""/>\n<FCBool Name="\""TreeExpandGeneral"\"" Value="\""1"\""/>\n<FCBool Name="\""TreeExpandMechanical"\"" Value="\""1"\""/>\n<FCBool Name="\""TreeExpandThermal"\"" Value="\""1"\""/>\n<FCBool Name="\""TreeExpandElectrical"\"" Value="\""1"\""/>\n<FCBool Name="\""TreeExpandArchitectural"\"" Value="\""1"\""/>\n<FCBool Name="\""TreeExpandRendering"\"" Value="\""1"\""/>\n<FCBool Name="\""TreeExpandVectorRendering"\"" Value="\""1"\""/>\n<FCBool Name="\""TreeExpandCost"\"" Value="\""1"\""/>\n<FCBool Name="\""TreeExpandUserDefined"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Mesh"\"">\n<FCParamGroup Name="\""Asymptote"\"">\n<FCText Name="\""Width"\""/>\n<FCText Name="\""Height"\""/>\n</FCParamGroup>\n<FCBool Name="\""TwoSideRendering"\"" Value="\""0"\""/>\n<FCBool Name="\""ShowBoundingBox"\"" Value="\""0"\""/>\n<FCUInt Name="\""MeshColor"\"" Value="\""3435973887"\""/>\n<FCUInt Name="\""LineColor"\"" Value="\""255"\""/>\n<FCUInt Name="\""BackfaceColor"\"" Value="\""3435973887"\""/>\n<FCInt Name="\""MeshTransparency"\"" Value="\""0"\""/>\n<FCInt Name="\""LineTransparency"\"" Value="\""0"\""/>\n<FCBool Name="\""VertexPerNormals"\"" Value="\""0"\""/>\n<FCFloat Name="\""CreaseAngle"\"" Value="\""0.000000000000"\""/>\n<FCFloat Name="\""MaxDeviationExport"\"" Value="\""1.000000000000"\""/>\n<FCBool Name="\""ExportAmfCompressed"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Sketcher"\"">\n<FCParamGroup Name="\""General"\"">\n<FCParamGroup Name="\""GridSize"\"">\n<FCText Name="\""Hist0"\"">10.00 mm</FCText>\n</FCParamGroup>\n<FCBool Name="\""NotifyConstraintSubstitutions"\"" Value="\""1"\""/>\n<FCBool Name="\""ShowGrid"\"" Value="\""1"\""/>\n<FCBool Name="\""GridSnap"\"" Value="\""0"\""/>\n<FCBool Name="\""AutoConstraints"\"" Value="\""1"\""/>\n<FCBool Name="\""AvoidRedundantAutoconstraints"\"" Value="\""1"\""/>\n<FCInt Name="\""TopRenderGeometryId"\"" Value="\""1"\""/>\n<FCInt Name="\""MidRenderGeometryId"\"" Value="\""2"\""/>\n<FCInt Name="\""LowRenderGeometryId"\"" Value="\""3"\""/>\n<FCBool Name="\""HideDependent"\"" Value="\""1"\""/>\n<FCBool Name="\""ShowLinks"\"" Value="\""1"\""/>\n<FCBool Name="\""ShowSupport"\"" Value="\""1"\""/>\n<FCBool Name="\""RestoreCamera"\"" Value="\""1"\""/>\n<FCBool Name="\""ForceOrtho"\"" Value="\""0"\""/>\n<FCBool Name="\""SectionView"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCBool Name="\""ShowSolverAdvancedWidget"\"" Value="\""0"\""/>\n<FCBool Name="\""RecalculateInitialSolutionWhileDragging"\"" Value="\""1"\""/>\n<FCBool Name="\""LeaveSketchWithEscape"\"" Value="\""1"\""/>\n<FCBool Name="\""AutoRemoveRedundants"\"" Value="\""0"\""/>\n<FCBool Name="\""ShowDialogOnDistanceConstraint"\"" Value="\""1"\""/>\n<FCBool Name="\""ContinuousCreationMode"\"" Value="\""1"\""/>\n<FCBool Name="\""ContinuousConstraintMode"\"" Value="\""1"\""/>\n<FCBool Name="\""HideUnits"\"" Value="\""0"\""/>\n<FCParamGroup Name="\""Elements"\"">\n<FCBool Name="\""Auto-switch to edge"\"" Value="\""1"\""/>\n<FCBool Name="\""Extended Naming"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""SolverAdvanced"\""/>\n<FCBool Name="\""ExpandedMessagesWidget"\"" Value="\""1"\""/>\n<FCBool Name="\""ExpandedSolverAdvancedWidget"\"" Value="\""0"\""/>\n<FCBool Name="\""ExpandedEditControlWidget"\"" Value="\""0"\""/>\n<FCBool Name="\""ExpandedConstraintsWidget"\"" Value="\""1"\""/>\n<FCBool Name="\""ExpandedElementsWidget"\"" Value="\""1"\""/>\n<FCBool Name="\""HideInternalAlignment"\"" Value="\""1"\""/>\n<FCBool Name="\""ExtendedConstraintInformation"\"" Value="\""0"\""/>\n<FCBool Name="\""ShowDimensionalName"\"" Value="\""0"\""/>\n<FCText Name="\""寸法の文字列形式"\"">%N = %V</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""Path"\""/>\n<FCParamGroup Name="\""dexcsCfdOF"\"">\n<FCText Name="\""DefaultOutputPath"\"">model_dir</FCText>\n<FCText Name="\""InstallationPath"\"">/usr/lib/openfoam/openfoam2106</FCText>\n<FCText Name="\""ParaviewPath"\"">/usr/bin/paraview</FCText>\n<FCText Name="\""DefaultTemplateCase"\"">/opt/DEXCS/template/dexcs</FCText></FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""Bitmaps"\"">\n<FCParamGroup Name="\""Theme"\""/>\n<FCText Name="\""CustomPath0"\"">/opt/TreeFoam/icons</FCText>\n<FCText Name="\""CustomPath1"\"">/opt/DEXCS/icons</FCText>\n<FCText Name="\""CustomPath2"\"">/home/dexcs/.FreeCAD</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""View"\"">\n<FCText Name="\""GestureRollFwdCommand"\"">Std_SelForward</FCText>\n<FCText Name="\""GestureRollBackCommand"\"">Std_SelBack</FCText>\n<FCText Name="\""NavigationStyle"\"">Gui::CADNavigationStyle</FCText>\n<FCInt Name="\""AntiAliasing"\"" Value="\""0"\""/>\n<FCInt Name="\""RenderCache"\"" Value="\""0"\""/>\n<FCInt Name="\""TransparentObjectRenderType"\"" Value="\""0"\""/>\n<FCInt Name="\""MarkerSize"\"" Value="\""9"\""/>\n<FCBool Name="\""CornerCoordSystem"\"" Value="\""1"\""/>\n<FCBool Name="\""ShowAxisCross"\"" Value="\""0"\""/>\n<FCBool Name="\""SaveWBbyTab"\"" Value="\""0"\""/>\n<FCBool Name="\""ShowFPS"\"" Value="\""0"\""/>\n<FCBool Name="\""UseVBO"\"" Value="\""0"\""/>\n<FCFloat Name="\""EyeDistance"\"" Value="\""5.000000000000"\""/>\n<FCBool Name="\""EnableBacklight"\"" Value="\""0"\""/>\n<FCUInt Name="\""BacklightColor"\"" Value="\""4294967295"\""/>\n<FCInt Name="\""BacklightIntensity"\"" Value="\""100"\""/>\n<FCBool Name="\""Perspective"\"" Value="\""1"\""/>\n<FCBool Name="\""Orthographic"\"" Value="\""0"\""/>\n<FCInt Name="\""OrbitStyle"\"" Value="\""1"\""/>\n<FCInt Name="\""CornerNaviCube"\"" Value="\""1"\""/>\n<FCBool Name="\""ZoomAtCursor"\"" Value="\""1"\""/>\n<FCBool Name="\""InvertZoom"\"" Value="\""1"\""/>\n<FCBool Name="\""DisableTouchTilt"\"" Value="\""1"\""/>\n<FCFloat Name="\""ZoomStep"\"" Value="\""0.200000000000"\""/>\n<FCBool Name="\""DragAtCursor"\"" Value="\""0"\""/>\n<FCBool Name="\""UseAutoRotation"\"" Value="\""0"\""/>\n<FCFloat Name="\""NewDocumentCameraScale"\"" Value="\""100.000000000000"\""/>\n<FCInt Name="\""NaviStepByTurn"\"" Value="\""8"\""/>\n<FCBool Name="\""ShowNaviCube"\"" Value="\""1"\""/>\n<FCText Name="\""NewDocumentCameraOrientation"\"">Trimetric</FCText>\n<FCUInt Name="\""BackgroundColor"\"" Value="\""336897023"\""/>\n<FCUInt Name="\""BackgroundColor2"\"" Value="\""859006463"\""/>\n<FCUInt Name="\""BackgroundColor3"\"" Value="\""2543299327"\""/>\n<FCUInt Name="\""BackgroundColor4"\"" Value="\""1869583359"\""/>\n<FCBool Name="\""Simple"\"" Value="\""0"\""/>\n<FCBool Name="\""Gradient"\"" Value="\""1"\""/>\n<FCBool Name="\""UseBackgroundColorMid"\"" Value="\""0"\""/>\n<FCBool Name="\""EnablePreselection"\"" Value="\""1"\""/>\n<FCBool Name="\""EnableSelection"\"" Value="\""1"\""/>\n<FCUInt Name="\""HighlightColor"\"" Value="\""3789624575"\""/>\n<FCUInt Name="\""SelectionColor"\"" Value="\""481107199"\""/>\n<FCFloat Name="\""PickRadius"\"" Value="\""5.000000000000"\""/>\n<FCUInt Name="\""DefaultShapeColor"\"" Value="\""3435973887"\""/>\n<FCBool Name="\""RandomColor"\"" Value="\""0"\""/>\n<FCUInt Name="\""DefaultShapeLineColor"\"" Value="\""421075455"\""/>\n<FCInt Name="\""DefaultShapeLineWidth"\"" Value="\""2"\""/>\n<FCUInt Name="\""DefaultShapeVertexColor"\"" Value="\""421075455"\""/>\n<FCInt Name="\""DefaultShapePointSize"\"" Value="\""2"\""/>\n<FCUInt Name="\""BoundingBoxColor"\"" Value="\""4294967295"\""/>\n<FCUInt Name="\""AnnotationTextColor"\"" Value="\""3419130879"\""/>\n<FCInt Name="\""EditSketcherFontSize"\"" Value="\""17"\""/>\n<FCInt Name="\""SegmentsPerGeometry"\"" Value="\""50"\""/>\n<FCUInt Name="\""SketchEdgeColor"\"" Value="\""4294967295"\""/>\n<FCUInt Name="\""SketchVertexColor"\"" Value="\""4294967295"\""/>\n<FCUInt Name="\""EditedEdgeColor"\"" Value="\""4294967295"\""/>\n<FCUInt Name="\""EditedVertexColor"\"" Value="\""4280680703"\""/>\n<FCUInt Name="\""ConstructionColor"\"" Value="\""56575"\""/>\n<FCUInt Name="\""ExternalColor"\"" Value="\""3425924095"\""/>\n<FCUInt Name="\""FullyConstrainedColor"\"" Value="\""16711935"\""/>\n<FCUInt Name="\""ConstrainedIcoColor"\"" Value="\""4280680703"\""/>\n<FCUInt Name="\""NonDrivingConstrDimColor"\"" Value="\""2555903"\""/>\n<FCUInt Name="\""ConstrainedDimColor"\"" Value="\""4280680703"\""/>\n<FCUInt Name="\""ExprBasedConstrDimColor"\"" Value="\""4286523135"\""/>\n<FCUInt Name="\""DeactivatedConstrDimColor"\"" Value="\""2139062271"\""/>\n<FCInt Name="\""DefaultSketcherVertexWidth"\"" Value="\""2"\""/>\n<FCUInt Name="\""CursorTextColor"\"" Value="\""65535"\""/>\n<FCUInt Name="\""CursorCrosshairColor"\"" Value="\""4294967295"\""/>\n<FCUInt Name="\""CreateLineColor"\"" Value="\""3435973887"\""/>\n<FCInt Name="\""RotationMode"\"" Value="\""1"\""/>\n<FCFloat Name="\""BoundingBoxFontSize"\"" Value="\""10.000000000000"\""/>\n<FCFloat Name="\""ViewScalingFactor"\"" Value="\""1.000000000000"\""/>\n<FCUInt Name="\""InvalidSketchColor"\"" Value="\""4285333759"\""/>\n<FCUInt Name="\""InternalAlignedGeoColor"\"" Value="\""2998042623"\""/>\n<FCUInt Name="\""FullyConstraintElementColor"\"" Value="\""2161156351"\""/>\n<FCUInt Name="\""FullyConstraintConstructionElementColor"\"" Value="\""2410282495"\""/>\n<FCUInt Name="\""FullyConstraintInternalAlignmentColor"\"" Value="\""3739142399"\""/>\n<FCUInt Name="\""FullyConstraintConstructionPointColor"\"" Value="\""4287987967"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Document"\"">\n<FCBool Name="\""SaveThumbnail"\"" Value="\""0"\""/>\n<FCBool Name="\""CreateNewDoc"\"" Value="\""0"\""/>\n<FCInt Name="\""CompressionLevel"\"" Value="\""3"\""/>\n<FCBool Name="\""UsingUndo"\"" Value="\""1"\""/>\n<FCInt Name="\""MaxUndoSize"\"" Value="\""20"\""/>\n<FCBool Name="\""SaveTransactions"\"" Value="\""0"\""/>\n<FCBool Name="\""TransactionsDiscard"\"" Value="\""0"\""/>\n<FCInt Name="\""ThumbnailSize"\"" Value="\""128"\""/>\n<FCBool Name="\""AddThumbnailLogo"\"" Value="\""1"\""/>\n<FCBool Name="\""CreateBackupFiles"\"" Value="\""1"\""/>\n<FCInt Name="\""CountBackupFiles"\"" Value="\""1"\""/>\n<FCBool Name="\""UseFCBakExtension"\"" Value="\""0"\""/>\n<FCText Name="\""SaveBackupDateFormat"\"">%Y%m%d-%H%M%S</FCText>\n<FCBool Name="\""DuplicateLabels"\"" Value="\""0"\""/>\n<FCBool Name="\""NoPartialLoading"\"" Value="\""0"\""/>\n<FCInt Name="\""prefLicenseType"\"" Value="\""0"\""/>\n<FCText Name="\""prefLicenseUrl"\"">http://en.wikipedia.org/wiki/All_rights_reserved</FCText>\n<FCText Name="\""prefAuthor"\""/>\n<FCBool Name="\""prefSetAuthorOnSave"\"" Value="\""0"\""/>\n<FCText Name="\""prefCompany"\""/>\n<FCBool Name="\""RecoveryEnabled"\"" Value="\""1"\""/>\n<FCBool Name="\""AutoSaveEnabled"\"" Value="\""1"\""/>\n<FCInt Name="\""AutoSaveTimeout"\"" Value="\""15"\""/>\n<FCBool Name="\""CanAbortRecompute"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""OutputWindow"\"">\n<FCBool Name="\""checkMessage"\"" Value="\""1"\""/>\n<FCBool Name="\""checkLogging"\"" Value="\""0"\""/>\n<FCBool Name="\""checkWarning"\"" Value="\""1"\""/>\n<FCBool Name="\""checkError"\"" Value="\""1"\""/>\n<FCBool Name="\""checkShowReportViewOnWarning"\"" Value="\""1"\""/>\n<FCBool Name="\""checkShowReportViewOnError"\"" Value="\""1"\""/>\n<FCBool Name="\""checkShowReportViewOnNormalMessage"\"" Value="\""0"\""/>\n<FCBool Name="\""checkShowReportViewOnLogMessage"\"" Value="\""0"\""/>\n<FCBool Name="\""checkShowReportTimecode"\"" Value="\""1"\""/>\n<FCUInt Name="\""colorText"\"" Value="\""255"\""/>\n<FCUInt Name="\""colorLogging"\"" Value="\""65535"\""/>\n<FCUInt Name="\""colorWarning"\"" Value="\""4289331455"\""/>\n<FCUInt Name="\""colorError"\"" Value="\""4278190335"\""/>\n<FCBool Name="\""RedirectPythonOutput"\"" Value="\""1"\""/>\n<FCBool Name="\""RedirectPythonErrors"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""DockWindows"\"">\n<FCParamGroup Name="\""TreeView"\"">\n<FCBool Name="\""Enabled"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""PropertyView"\"">\n<FCBool Name="\""Enabled"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""DAGView"\"">\n<FCBool Name="\""Enabled"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""ComboView"\"">\n<FCBool Name="\""Enabled"\"" Value="\""1"\""/>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""TreeView"\"">\n<FCUInt Name="\""TreeEditColor"\"" Value="\""4294902015"\""/>\n<FCUInt Name="\""TreeActiveColor"\"" Value="\""3873898495"\""/>\n<FCBool Name="\""SyncView"\"" Value="\""1"\""/>\n<FCBool Name="\""SyncSelection"\"" Value="\""0"\""/>\n<FCBool Name="\""PreSelection"\"" Value="\""0"\""/>\n<FCBool Name="\""RecordSelection"\"" Value="\""0"\""/>\n<FCBool Name="\""CheckBoxesSelection"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""PropertyView"\"">\n<FCInt Name="\""LastTabIndex"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Editor"\"">\n<FCBool Name="\""EnableLineNumber"\"" Value="\""1"\""/>\n<FCBool Name="\""EnableFolding"\"" Value="\""1"\""/>\n<FCInt Name="\""TabSize"\"" Value="\""4"\""/>\n<FCInt Name="\""IndentSize"\"" Value="\""4"\""/>\n<FCBool Name="\""Tabs"\"" Value="\""1"\""/>\n<FCBool Name="\""Spaces"\"" Value="\""0"\""/>\n<FCUInt Name="\""Text"\"" Value="\""0"\""/>\n<FCUInt Name="\""Bookmark"\"" Value="\""16776960"\""/>\n<FCUInt Name="\""Breakpoint"\"" Value="\""4278190080"\""/>\n<FCUInt Name="\""Keyword"\"" Value="\""65280"\""/>\n<FCUInt Name="\""Comment"\"" Value="\""11141120"\""/>\n<FCUInt Name="\""Block comment"\"" Value="\""2694882304"\""/>\n<FCUInt Name="\""Number"\"" Value="\""65280"\""/>\n<FCUInt Name="\""String"\"" Value="\""4278190080"\""/>\n<FCUInt Name="\""Character"\"" Value="\""4278190080"\""/>\n<FCUInt Name="\""Class name"\"" Value="\""4289331200"\""/>\n<FCUInt Name="\""Define name"\"" Value="\""4289331200"\""/>\n<FCUInt Name="\""Operator"\"" Value="\""2694882304"\""/>\n<FCUInt Name="\""Python output"\"" Value="\""2863300352"\""/>\n<FCUInt Name="\""Python error"\"" Value="\""4278190080"\""/>\n<FCUInt Name="\""Current line highlight"\"" Value="\""3772833792"\""/>\n<FCInt Name="\""FontSize"\"" Value="\""10"\""/>\n<FCText Name="\""Font"\"">Ubuntu</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""MainWindow"\"">\n<FCBool Name="\""TiledBackground"\"" Value="\""0"\""/>\n<FCText Name="\""StyleSheet"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Browser"\""/>\n<FCParamGroup Name="\""NaviCube"\"">\n<FCBool Name="\""NaviRotateToNearest"\"" Value="\""1"\""/>\n<FCInt Name="\""CubeSize"\"" Value="\""132"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Addons"\"">\n<FCInt Name="\""WindowWidth"\"" Value="\""743"\""/>\n<FCInt Name="\""WindowHeight"\"" Value="\""480"\""/>\n<FCInt Name="\""SplitterLeft"\"" Value="\""374"\""/>\n<FCInt Name="\""SplitterRight"\"" Value="\""343"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Placement"\"">\n<FCInt Name="\""RotationMethod"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Dialog"\""/>\n<FCParamGroup Name="\""Expression"\""/>\n<FCParamGroup Name="\""HighDPI"\""/>\n<FCParamGroup Name="\""OpenGL"\"">\n<FCBool Name="\""UseSoftwareOpenGL"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""AppImage"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Macro"\"">\n<FCParamGroup Name="\""Macros"\"">\n<FCParamGroup Name="\""Std_Macro_0"\"">\n<FCText Name="\""Script"\"">showSolidInfo.FCMacro</FCText>\n<FCText Name="\""Menu"\"">showSolidInfo</FCText>\n<FCText Name="\""Tooltip"\"">オブジェクトの表面積・体積・重心を表示します</FCText>\n<FCText Name="\""WhatsThis"\"">オブジェクトの表面積・体積・重心を表示します</FCText>\n<FCText Name="\""Statustip"\"">オブジェクトの表面積・体積・重心を表示します</FCText>\n<FCText Name="\""Pixmap"\"">bulb</FCText>\n<FCText Name="\""Accel"\"">??</FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_1"\"">\n<FCText Name="\""Script"\"">runGridEditor.py</FCText>\n<FCText Name="\""Menu"\"">gridEditor</FCText>\n<FCText Name="\""Tooltip"\"">gridEditorの起動</FCText>\n<FCText Name="\""WhatsThis"\"">gridEditorの起動</FCText>\n<FCText Name="\""Statustip"\"">gridEditorの起動</FCText>\n<FCText Name="\""Pixmap"\"">gridEditor</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_10"\"">\n<FCText Name="\""Script"\"">editConstantFolder.py</FCText>\n<FCText Name="\""Menu"\"">editConstantFolder</FCText>\n<FCText Name="\""Tooltip"\"">Propertiesの編集</FCText>\n<FCText Name="\""WhatsThis"\"">Propertiesの編集</FCText>\n<FCText Name="\""Statustip"\"">Propertiesの編集</FCText>\n<FCText Name="\""Pixmap"\"">editProperties-cons</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_11"\"">\n<FCText Name="\""Script"\"">editSystemFolder.py</FCText>\n<FCText Name="\""Menu"\"">editSystemFolder</FCText>\n<FCText Name="\""Tooltip"\"">Dict（system）の編集</FCText>\n<FCText Name="\""WhatsThis"\"">Dict（system）の編集</FCText>\n<FCText Name="\""Statustip"\"">Dict（system）の編集</FCText>\n<FCText Name="\""Pixmap"\"">editDict-sys</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_12"\"">\n<FCText Name="\""Script"\"">runSolver.py</FCText>\n<FCText Name="\""Menu"\"">runSolver</FCText>\n<FCText Name="\""Tooltip"\"">solverを起動</FCText>\n<FCText Name="\""WhatsThis"\"">solverを起動</FCText>\n<FCText Name="\""Statustip"\"">solverを起動</FCText>\n<FCText Name="\""Pixmap"\"">runSolver</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_13"\"">\n<FCText Name="\""Script"\"">runPlotWatcher.py</FCText>\n<FCText Name="\""Menu"\"">runPlotWatcher</FCText>\n<FCText Name="\""Tooltip"\"">plotWatcherの起動</FCText>\n<FCText Name="\""WhatsThis"\"">plotWatcherの起動</FCText>\n<FCText Name="\""Statustip"\"">plotWatcherの起動</FCText>\n<FCText Name="\""Pixmap"\"">plotWatcher</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_14"\"">\n<FCText Name="\""Script"\"">runParalel.py</FCText>\n<FCText Name="\""Menu"\"">runParallel</FCText>\n<FCText Name="\""Tooltip"\"">並列処理</FCText>\n<FCText Name="\""WhatsThis"\"">並列処理</FCText>\n<FCText Name="\""Statustip"\"">並列処理</FCText>\n<FCText Name="\""Pixmap"\"">parallel</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_15"\"">\n<FCText Name="\""Script"\"">exportFSIinp.FCMacro</FCText>\n<FCText Name="\""Menu"\"">exportFSIinp</FCText>\n<FCText Name="\""Tooltip"\"">FSI用Inpファイルを作成します</FCText>\n<FCText Name="\""WhatsThis"\"">FSI用Inpファイルを作成します</FCText>\n<FCText Name="\""Statustip"\"">FSI用Inpファイルを作成します</FCText>\n<FCText Name="\""Pixmap"\"">CADExchanger_workbench_icon</FCText>\n<FCText Name="\""Accel"\"">??</FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_16"\"">\n<FCText Name="\""Script"\"">Table_GUI.py</FCText>\n<FCText Name="\""Menu"\"">postProcess_GUI</FCText>\n<FCText Name="\""Tooltip"\"">postProcessプロット用GUIエディタ</FCText>\n<FCText Name="\""WhatsThis"\"">postProcessプロット用GUIエディタ</FCText>\n<FCText Name="\""Statustip"\"">postProcessプロット用GUIエディタ</FCText>\n<FCText Name="\""Pixmap"\"">Arch_Schedule</FCText>\n<FCText Name="\""Accel"\"">??</FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_17"\"">\n<FCText Name="\""Script"\"">openOFTerminal.py</FCText>\n<FCText Name="\""Menu"\"">OpenTerminal for OpenFOAM</FCText>\n<FCText Name="\""Tooltip"\"">OpenFOAM端末を起動</FCText>\n<FCText Name="\""WhatsThis"\"">OpenFOAM端末を起動</FCText>\n<FCText Name="\""Statustip"\"">OpenFOAM端末を起動</FCText>\n<FCText Name="\""Pixmap"\"">image_normal</FCText>\n<FCText Name="\""Accel"\"">??</FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_2"\"">\n<FCText Name="\""Script"\"">runParaview.py</FCText>\n<FCText Name="\""Menu"\"">runParaview</FCText>\n<FCText Name="\""Tooltip"\"">paraFoamの起動</FCText>\n<FCText Name="\""WhatsThis"\"">paraFoamの起動</FCText>\n<FCText Name="\""Statustip"\"">paraFoamの起動</FCText>\n<FCText Name="\""Pixmap"\"">paraview</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_3"\"">\n<FCText Name="\""Script"\"">runTreefoam.py</FCText>\n<FCText Name="\""Menu"\"">runTreefoam</FCText>\n<FCText Name="\""Tooltip"\"">treefoam を起動します</FCText>\n<FCText Name="\""WhatsThis"\"">treefoam を起動します</FCText>\n<FCText Name="\""Statustip"\"">treefoam を起動します</FCText>\n<FCText Name="\""Pixmap"\"">treefoam48</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_4"\"">\n<FCText Name="\""Script"\"">runClearCase.py</FCText>\n<FCText Name="\""Menu"\"">runClearCase</FCText>\n<FCText Name="\""Tooltip"\"">計算結果を削除して、caseを初期化します</FCText>\n<FCText Name="\""WhatsThis"\"">計算結果を削除して、caseを初期化します</FCText>\n<FCText Name="\""Statustip"\"">計算結果を削除して、caseを初期化します</FCText>\n<FCText Name="\""Pixmap"\"">iniCase</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_5"\"">\n<FCText Name="\""Script"\"">dexcsPlotTool_gui.py</FCText>\n<FCText Name="\""Menu"\"">dexcsPlotTool</FCText>\n<FCText Name="\""Tooltip"\"">postProcessingファイルのプロット</FCText>\n<FCText Name="\""WhatsThis"\"">postProcessingファイルのプロット</FCText>\n<FCText Name="\""Statustip"\"">postProcessingファイルのプロット</FCText>\n<FCText Name="\""Pixmap"\"">Plot_workbench_icon</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_6"\"">\n<FCText Name="\""Script"\"">checkCaseFileName.py</FCText>\n<FCText Name="\""Menu"\"">checkCase</FCText>\n<FCText Name="\""Tooltip"\"">解析ケースファイルの確認</FCText>\n<FCText Name="\""WhatsThis"\"">解析ケースファイルの確認</FCText>\n<FCText Name="\""Statustip"\"">解析ケースファイルの確認</FCText>\n<FCText Name="\""Pixmap"\"">check16</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_18"\"">\n<FCText Name="\""Script"\"">makeSnappyHexMeshSetting.FCMacro</FCText>\n<FCText Name="\""Menu"\"">makeSnappyHexMeshSetting</FCText>\n<FCText Name="\""Tooltip"\"">snappyHexMesh用設定ファイルを作成します</FCText>\n<FCText Name="\""WhatsThis"\"">snappyHexMesh用設定ファイルを作成します</FCText>\n<FCText Name="\""Statustip"\"">snappyHexMesh用設定ファイルを作成します</FCText>\n<FCText Name="\""Pixmap"\"">sHM</FCText>\n<FCText Name="\""Accel"\""/>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_7"\"">\n<FCText Name="\""Script"\"">makeCfMeshSetting.FCMacro</FCText>\n<FCText Name="\""Menu"\"">makeCfMeshSetting</FCText>\n<FCText Name="\""Tooltip"\"">cfMesh用設定ファイルを作成します</FCText>\n<FCText Name="\""WhatsThis"\"">cfMesh用設定ファイルを作成します</FCText>\n<FCText Name="\""Statustip"\"">cfMesh用設定ファイルを作成します</FCText>\n<FCText Name="\""Pixmap"\"">logo-72px</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_8"\"">\n<FCText Name="\""Script"\"">exportStl.FCMacro</FCText>\n<FCText Name="\""Menu"\"">exportStl</FCText>\n<FCText Name="\""Tooltip"\"">stlファイル（アスキー形式）を作成します</FCText>\n<FCText Name="\""WhatsThis"\"">stlファイル（アスキー形式）を作成します</FCText>\n<FCText Name="\""Statustip"\"">stlファイル（アスキー形式）を作成します</FCText>\n<FCText Name="\""Pixmap"\"">Tree_Dimension</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Std_Macro_9"\"">\n<FCText Name="\""Script"\"">solverSet.py</FCText>\n<FCText Name="\""Menu"\"">solverSet</FCText>\n<FCText Name="\""Tooltip"\"">新規にcaseを作成、又はsolverやmeshを入れ替え</FCText>\n<FCText Name="\""WhatsThis"\"">新規にcaseを作成、又はsolverやmeshを入れ替え</FCText>\n<FCText Name="\""Statustip"\"">新規にcaseを作成、又はsolverやmeshを入れ替え</FCText>\n<FCText Name="\""Pixmap"\"">createChange24</FCText>\n<FCText Name="\""Accel"\""></FCText>\n<FCBool Name="\""System"\"" Value="\""0"\""/>\n</FCParamGroup>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""MainWindow"\"">\n<FCParamGroup Name="\""DockWindows"\"">\n<FCBool Name="\""Std_ReportView"\"" Value="\""1"\""/>\n<FCBool Name="\""Std_SelectionView"\"" Value="\""0"\""/>\n<FCBool Name="\""Std_ComboView"\"" Value="\""1"\""/>\n<FCBool Name="\""Std_PythonView"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""Toolbars"\"">\n<FCBool Name="\""File"\"" Value="\""1"\""/>\n<FCBool Name="\""Workbench"\"" Value="\""1"\""/>\n<FCBool Name="\""Macro"\"" Value="\""1"\""/>\n<FCBool Name="\""View"\"" Value="\""1"\""/>\n<FCBool Name="\""Structure"\"" Value="\""1"\""/>\n<FCBool Name="\""Navigation"\"" Value="\""0"\""/>\n<FCBool Name="\""Draft tray"\"" Value="\""0"\""/>\n<FCBool Name="\""Draft creation tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Draft annotation tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Draft modification tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Draft utility tools"\"" Value="\""1"\""/>\n<FCBool Name="\""DEXCS"\"" Value="\""1"\""/>\n<FCBool Name="\""Draft Snap"\"" Value="\""1"\""/>\n<FCBool Name="\""Solids"\"" Value="\""1"\""/>\n<FCBool Name="\""Part tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Boolean"\"" Value="\""1"\""/>\n<FCBool Name="\""Measure"\"" Value="\""1"\""/>\n<FCBool Name="\""Mesh tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Part Design Helper"\"" Value="\""1"\""/>\n<FCBool Name="\""Part Design Modeling"\"" Value="\""1"\""/>\n<FCBool Name="\""draft_snap_widget"\"" Value="\""0"\""/>\n<FCBool Name="\""Arch tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Drawing"\"" Value="\""1"\""/>\n<FCBool Name="\""OpenSCADTools"\"" Value="\""1"\""/>\n<FCBool Name="\""OpenSCAD Part tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Project Setup"\"" Value="\""1"\""/>\n<FCBool Name="\""Tool Commands"\"" Value="\""1"\""/>\n<FCBool Name="\""New Operations"\"" Value="\""1"\""/>\n<FCBool Name="\""Path Modification"\"" Value="\""1"\""/>\n<FCBool Name="\""Reverse Engineering"\"" Value="\""1"\""/>\n<FCBool Name="\""TestTools"\"" Value="\""1"\""/>\n<FCBool Name="\""Robot"\"" Value="\""1"\""/>\n<FCBool Name="\""Points tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Image"\"" Value="\""1"\""/>\n<FCBool Name="\""Model"\"" Value="\""1"\""/>\n<FCBool Name="\""Electrostatic Constraints"\"" Value="\""1"\""/>\n<FCBool Name="\""Fluid Constraints"\"" Value="\""1"\""/>\n<FCBool Name="\""Geometrical Constraints"\"" Value="\""1"\""/>\n<FCBool Name="\""Mechanical Constraints"\"" Value="\""1"\""/>\n<FCBool Name="\""Thermal Constraints"\"" Value="\""1"\""/>\n<FCBool Name="\""Mesh"\"" Value="\""1"\""/>\n<FCBool Name="\""Solve"\"" Value="\""1"\""/>\n<FCBool Name="\""Results"\"" Value="\""1"\""/>\n<FCBool Name="\""Utilities"\"" Value="\""1"\""/>\n<FCBool Name="\""Sketcher"\"" Value="\""1"\""/>\n<FCBool Name="\""Sketcher geometries"\"" Value="\""1"\""/>\n<FCBool Name="\""Sketcher constraints"\"" Value="\""1"\""/>\n<FCBool Name="\""Sketcher tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Sketcher B-spline tools"\"" Value="\""1"\""/>\n<FCBool Name="\""Sketcher virtual space"\"" Value="\""1"\""/>\n<FCBool Name="\""Mesh modify"\"" Value="\""1"\""/>\n<FCBool Name="\""Mesh boolean"\"" Value="\""1"\""/>\n<FCBool Name="\""Mesh cutting"\"" Value="\""1"\""/>\n<FCBool Name="\""Mesh segmentation"\"" Value="\""1"\""/>\n<FCBool Name="\""Mesh analyze"\"" Value="\""1"\""/>\n<FCBool Name="\""dexcsCfdOF"\"" Value="\""1"\""/>\n<FCBool Name="\""Plot edition tools"\"" Value="\""1"\""/>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""Workbench"\"">\n<FCParamGroup Name="\""Global"\"">\n<FCParamGroup Name="\""Toolbar"\"">\n<FCParamGroup Name="\""Custom_1"\"">\n<FCText Name="\""Name"\"">DEXCS</FCText>\n<FCBool Name="\""Active"\"" Value="\""1"\""/>\n<FCText Name="\""Std_Macro_9"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_7"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_18"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_6"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_3"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_1"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_10"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_11"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_4"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_12"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_13"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_14"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_2"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_5"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_17"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_16"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_15"\"">FreeCAD</FCText>\n<FCText Name="\""Std_Macro_8"\"">FreeCAD</FCText>\n<FCText Name="\""Draft_Downgrade"\"">gui_downgrade</FCText>\n<FCText Name="\""Part_Fuse"\"">Part</FCText>\n<FCText Name="\""Std_Macro_0"\"">FreeCAD</FCText>\n</FCParamGroup>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""CompleteWorkbench"\"">\n<FCParamGroup Name="\""Toolbar"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""DraftWorkbench"\"">\n<FCParamGroup Name="\""Toolbar"\""/>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""Workbenches"\"">\n<FCText Name="\""Enabled"\"">ArchWorkbench,DraftWorkbench,DrawingWorkbench,FemWorkbench,ImageWorkbench,InspectionWorkbench,MeshWorkbench,NoneWorkbench,OpenSCADWorkbench,PartDesignWorkbench,PartWorkbench,PathWorkbench,PointsWorkbench,RaytracingWorkbench,ReverseEngineeringWorkbench,RobotWorkbench,SketcherWorkbench,SpreadsheetWorkbench,StartWorkbench,SurfaceWorkbench,TechDrawWorkbench,TestWorkbench,WebWorkbench,dexcsCfdOFWorkbench,PlotWorkbench,</FCText>\n<FCText Name="\""Disabled"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""History"\"">\n<FCParamGroup Name="\""SketcherLength"\"">\n<FCText Name="\""Hist0"\"">1.25 mm</FCText>\n<FCText Name="\""Hist1"\"">1.50 mm</FCText>\n<FCText Name="\""Hist2"\"">1.25 mm</FCText>\n<FCText Name="\""Hist3"\"">1.50 mm</FCText>\n<FCText Name="\""Hist4"\"">1.25 mm</FCText>\n<FCText Name="\""Hist5"\"">1.50 mm</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""PocketLength"\"">\n<FCText Name="\""Hist0"\"">5.00 mm</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""PocketLength2"\"">\n<FCText Name="\""Hist0"\"">100.00 mm</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""PocketOffset"\"">\n<FCText Name="\""Hist0"\"">0.00 mm</FCText>\n</FCParamGroup>\n<FCParamGroup Name="\""UnitsCalculator"\""/></FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""Tux"\"">\n<FCParamGroup Name="\""NavigationIndicator"\"">\n<FCBool Name="\""Compact"\"" Value="\""0"\""/>\n<FCBool Name="\""Tooltip"\"" Value="\""1"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""PersistentToolbars"\"">\n<FCParamGroup Name="\""User"\"">\n<FCParamGroup Name="\""StartWorkbench"\"">\n<FCBool Name="\""Saved"\"" Value="\""1"\""/>\n<FCText Name="\""Top"\"">Break,File,Workbench,Macro,View,Structure</FCText>\n<FCText Name="\""Left"\"">Break,DEXCS</FCText>\n<FCText Name="\""Right"\""/>\n<FCText Name="\""Bottom"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""DraftWorkbench"\"">\n<FCBool Name="\""Saved"\"" Value="\""1"\""/>\n<FCText Name="\""Top"\"">Break,File,Workbench,Draft creation tools,Macro,View,Structure,Draft tray,Draft annotation tools,Draft utility tools,Draft Snap,Break,Draft modification tools</FCText>\n<FCText Name="\""Left"\"">DEXCS</FCText>\n<FCText Name="\""Right"\""/>\n<FCText Name="\""Bottom"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""PartWorkbench"\"">\n<FCBool Name="\""Saved"\"" Value="\""1"\""/>\n<FCText Name="\""Top"\"">Break,File,Workbench,Macro,View,Structure,Break,Measure,Solids,Boolean,Part tools</FCText>\n<FCText Name="\""Left"\"">DEXCS</FCText>\n<FCText Name="\""Right"\""/>\n<FCText Name="\""Bottom"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""MeshWorkbench"\""/>\n<FCParamGroup Name="\""CompleteWorkbench"\"">\n<FCBool Name="\""Saved"\"" Value="\""1"\""/>\n<FCText Name="\""Top"\"">Break,File,Workbench,Macro,View,Structure</FCText>\n<FCText Name="\""Left"\"">Break,DEXCS</FCText>\n<FCText Name="\""Right"\""/>\n<FCText Name="\""Bottom"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""PartDesignWorkbench"\""/>\n<FCParamGroup Name="\""NoneWorkbench"\""/>\n<FCParamGroup Name="\""ArchWorkbench"\""/>\n<FCParamGroup Name="\""DrawingWorkbench"\""/>\n<FCParamGroup Name="\""InspectionWorkbench"\""/>\n<FCParamGroup Name="\""OpenSCADWorkbench"\""/>\n<FCParamGroup Name="\""PathWorkbench"\""/>\n<FCParamGroup Name="\""ReverseEngineeringWorkbench"\""/>\n<FCParamGroup Name="\""TestWorkbench"\""/>\n<FCParamGroup Name="\""WebWorkbench"\""/>\n<FCParamGroup Name="\""RobotWorkbench"\""/>\n<FCParamGroup Name="\""PointsWorkbench"\""/>\n<FCParamGroup Name="\""ImageWorkbench"\""/>\n<FCParamGroup Name="\""FemWorkbench"\"">\n<FCBool Name="\""Saved"\"" Value="\""1"\""/>\n<FCText Name="\""Top"\"">Break,File,Workbench,Macro,View,Structure,Model,Electrostatic Constraints,Fluid Constraints,Geometrical Constraints,Mechanical Constraints,Thermal Constraints,Break,Solve,Results,Utilities,Mesh</FCText>\n<FCText Name="\""Left"\"">DEXCS</FCText>\n<FCText Name="\""Right"\""/>\n<FCText Name="\""Bottom"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""SketcherWorkbench"\"">\n<FCBool Name="\""Saved"\"" Value="\""1"\""/>\n<FCText Name="\""Top"\"">Break,File,Workbench,Macro,View,Structure,Sketcher,Sketcher geometries,Break,Sketcher tools,Sketcher B-spline tools,Sketcher virtual space,Sketcher constraints</FCText>\n<FCText Name="\""Left"\"">DEXCS</FCText>\n<FCText Name="\""Right"\""/>\n<FCText Name="\""Bottom"\""/>\n</FCParamGroup>\n<FCParamGroup Name="\""PlotWorkbench"\""/>\n<FCParamGroup Name="\""dexcsCfdOFWorkbench"\"">\n<FCBool Name="\""Saved"\"" Value="\""1"\""/>\n<FCText Name="\""Top"\"">Break,File,Workbench,Macro,View,Structure,Break,dexcsCfdOF</FCText>\n<FCText Name="\""Left"\"">DEXCS</FCText>\n<FCText Name="\""Right"\""/>\n<FCText Name="\""Bottom"\""/>\n</FCParamGroup>\n</FCParamGroup>\n</FCParamGroup>\n</FCParamGroup>\n<FCParamGroup Name="\""Plugins"\"">\n<FCParamGroup Name="\""addonsRepository"\"">\n<FCBool Name="\""readWarning"\"" Value="\""1"\""/>\n</FCParamGroup>\n</FCParamGroup>\n</FCParamGroup>\n</FCParameters>\n')
    s = s.replace('dexcs', os.getlogin()).replace('iwamoto', os.getlogin())
    with open(macro_home_user_cfg, 'w') as f:
        f.write(s)
"

if [ -x /opt/OpenFOAM/OpenFOAM-v1906/tutorials/DNS/dnsFoam/boxTurb16/0/U ]; then
	find /opt/OpenFOAM/OpenFOAM-v1906/tutorials -type f -not -name 'All*' -print | xargs chmod a-x
fi

# ----------------------------------------------------------

apt_installed=$(apt list --installed)

if [ "$dexcs_version" = '2019' ]; then
	# aptでインストールして欲しくないもの
	if $imsudoer; then
		for p in python-numpy python-scipy python-matplotlib python-wxgtk3.0 python-GPyOpt python-openpyxl python-requests; do
			if echo "$apt_installed" | grep --quiet "$p"/; then
				# purge -> 設定ファイルも含めてアンインストール
				sudo apt purge -y "$p"
				sudo apt autoremove -y
			fi
		done
	fi

	# pipのインストール
	if $imsudoer && ! echo "$apt_installed" | grep --quiet python-pip/ ; then
		sudo apt install -y python-pip
		sudo apt autoremove -y
	fi

	# aptでインストールして欲しいので，pipでインストールされていたら消しておく
	for p in pexpect pyperclip chardet xlrd Pillow urllib3; do
		if [ -e ~/.local/lib/python2.7/site-packages/"$p" ]; then
			pip uninstall -y "$p"
		fi
		if $imsudoer && [ -e /usr/local/lib/python2.7/dist-packages/"$p" ]; then
			sudo pip uninstall -y "$p"
		fi
	done
	if [ -e ~/.local/lib/python2.7/site-packages/PIL ]; then
		pip uninstall -y pillow
	fi
	if $imsudoer && [ -e /usr/local/lib/python2.7/dist-packages/PIL ]; then
		sudo pip uninstall -y pillow
	fi

	# sudo pipでインストールして欲しいので，localのpipでインストールされていたら消しておく
	for p in numpy scipy matplotlib zenhan GPyOpt GPy geomdl openpyxl requests; do
		if [ -e ~/.local/lib/python2.7/site-packages/"$p" ]; then
			pip uninstall -y "$p"
		fi
	done
	if [ -e ~/.local/lib/python2.7/site-packages/wx ]; then
		pip uninstall -y wxPython
	fi
	if [ -e ~/.local/lib/python2.7/site-packages/stl ]; then
		pip uninstall -y numpy-stl
	fi

	# aptでインストールして欲しいもの
	# 注意: notepadqはaptにないのでsnapでインストール
	if $imsudoer; then
		for p in python-tk \
			python-pexpect python-pyperclip python-chardet python-xlrd python-pil python-urllib3 \
			libsdl2-2.0-0 libgtk-3-dev \
			gedit-plugins wxmaxima handbrake xsel; do
			if ! echo "$apt_installed" | grep --quiet "$p"/; then
				sudo apt install -y "$p"
				sudo apt autoremove -y
			fi
		done
	fi

	# sudo pipでインストールして欲しいもの
	if $imsudoer; then
		for p in numpy scipy matplotlib zenhan GPyOpt geomdl openpyxl requests; do
			if [ ! -e /usr/local/lib/python2.7/dist-packages/"$p" ]; then
				sudo pip install "$p"
			fi
		done
		if [ -z "$(find /usr/local/lib/python2.7/dist-packages/GPy-1.9.9*-info)" ]; then
			sudo pip uninstall -y GPy
			sudo pip install GPy==1.9.9
		fi
		if [ ! -e /usr/local/lib/python2.7/dist-packages/wx ]; then
			sudo pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-18.04 wxPython==4.1.0
		fi
		if [ ! -e /usr/local/lib/python2.7/dist-packages/stl ]; then
			sudo pip install numpy-stl
		fi
	fi

	snap_installed=$(snap list)

	if ! echo "$snap_installed" | grep --quiet notepadqq; then
		sudo snap install notepadqq --devmode
	fi

else # 2021
#	# aptでインストールして欲しくないものは，2022/6/26の時点ではない
#	if $imsudoer; then
#		for p in xxx xxx xxx; do
#			if echo "$apt_installed" | grep --quiet "$p"/; then
#				echo '1: '$p
#				# purge -> 設定ファイルも含めてアンインストール
#				sudo apt purge -y "$p"
#				sudo apt autoremove -y
#			fi
#		done
#	fi

	# pipのインストール
	if $imsudoer && ! echo "$apt_installed" | grep --quiet python3-pip/; then
		sudo apt install -y python3-pip
		sudo apt autoremove -y
	fi

	# aptでインストールして欲しいので，pipでインストールされていたら消しておく
	for p in pexpect pyperclip chardet xlrd Pillow urllib3 numpy scipy matplotlib openpyxl requests; do
		if [ -e ~/.local/lib/python3.8/site-packages/"$p" ]; then
			pip uninstall -y "$p"
		fi
		if $imsudoer && [ -e /usr/local/lib/python3.8/dist-packages/"$p" ]; then
			sudo pip uninstall -y "$p"
		fi
	done
	if [ -e ~/.local/lib/python3.8/site-packages/PIL ]; then
		pip uninstall -y pillow
	fi
	if $imsudoer && [ -e /usr/local/lib/python3.8/dist-packages/PIL ]; then
		sudo pip uninstall -y pillow
	fi

	# sudo pipでインストールして欲しいので，localのpipでインストールされていたら消しておく
	for p in zenhan GPyOpt GPy geomdl openpyxl; do
		if [ -e ~/.local/lib/python3.8/site-packages/"$p" ]; then
			pip uninstall -y "$p"
		fi
	done
	if [ -e ~/.local/lib/python3.8/site-packages/wx ]; then
		pip uninstall -y wxPython
	fi
	if [ -e ~/.local/lib/python3.8/site-packages/stl ]; then
		pip uninstall -y numpy-stl
	fi

	# aptでインストールして欲しいもの
	# python3-numpy python3-scipy python3-matplotlib python3-pyside2.qtnetwork python3-pyside2.qtwebengine
	# python3-pyside2.qtwebenginecore python3-pyside2.qtwebenginewidgets python3-pyside2.qtwebchanne
	# はfreecad-daily-python3で必要
	if $imsudoer; then
		for p in python3-tk \
			python3-pexpect python3-pyperclip python3-chardet python3-xlrd python3-pil python3-urllib3 \
			python3-openpyxl python3-requests libsdl2-2.0-0 libgtk-3-dev \
			python3-numpy python3-scipy python3-matplotlib \
			python3-pyside2.qtnetwork python3-pyside2.qtwebengine python3-pyside2.qtwebenginecore \
			python3-pyside2.qtwebenginewidgets python3-pyside2.qtwebchannel \
			gedit-plugins wxmaxima handbrake notepadqq xsel; do
			if ! echo "$apt_installed" | grep --quiet "$p"/; then
				sudo apt install -y "$p"
				sudo apt autoremove -y
			fi
		done
		if ! echo "$apt_installed" | grep --quiet 'gnome-control-center/'; then
			sudo apt install -y --reinstall gnome-control-center
			sudo apt autoremove -y
		fi
	fi

	# sudo pipでインストールして欲しいもの
	if $imsudoer; then
		for p in zenhan GPyOpt geomdl; do
			if [ ! -e /usr/local/lib/python3.8/dist-packages/"$p" ]; then
				sudo pip install "$p"
			fi
		done
		if [ -z "$(find /usr/local/lib/python3.8/dist-packages/GPy-1.9.9*-info)" ]; then
			sudo pip uninstall -y GPy
			sudo pip install GPy==1.9.9
		fi
		if [ ! -e /usr/local/lib/python3.8/dist-packages/wx ]; then
			sudo pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04 wxPython
			sudo apt install libsdl2-2.0-0
		fi
		if [ ! -e /usr/local/lib/python3.8/dist-packages/stl ]; then
			sudo pip install numpy-stl
		fi
	fi

fi # end of if [ "$dexcs_version" = '2019' ]; then

# デスクトップアイコンの表示設定
if [ "$dexcs_version" = '2019' ]; then
	entry=org.gnome.nautilus.desktop
else # 2021
	entry=org.nemo.desktop
fi
for key in 'computer-icon-visible' 'network-icon-visible' 'volumes-visible' 'home-icon-visible' 'trash-icon-visible'; do
	if [ "$key" = 'computer-icon-visible' ] && [ "$dexcs_version" = '2019' ]; then
		: # do nothing
	elif [ "$(gsettings get $entry $key)" != 'true' ]; then
		gsettings set $entry $key 'true'
	fi
done

# Dockのアイコンサイズ変更
key=/org/gnome/shell/extensions/dash-to-dock/dash-max-icon-size
if [ -z "$(dconf read $key)" ] || [ "$(dconf read $key)" -gt 24 ]; then
	dconf write $key 24
fi

# デスクトップ上の時計表示の設定
for key in '/org/gnome/desktop/interface/clock-show-date' '/org/gnome/desktop/interface/clock-show-seconds'; do
	# $(dconf read $key)が空白になる時のために""で括っている
	if [ "$(dconf read $key)" != 'true' ]; then
		dconf write $key 'true'
	fi
done

if $imsudoer && [ "$(apt list --upgradable | wc -l)" -gt 1 ]; then
	sudo apt update
	sudo apt upgrade -y
fi

# 更新したFreeCADのconfigファイルは~/.config/FreeCADにある．
if [ "$dexcs_version" = '2021' ] && [ -d ~/.config/FreeCAD ] && [ ! -e ~/.config/FreeCAD/user.cfg_orig ]; then
	if [ -e ~/.config/FreeCAD/user.cfg ]; then
		mv ~/.config/FreeCAD/user.cfg ~/.config/FreeCAD/user.cfg_orig
	fi
	cp -f ~/.FreeCAD/user.cfg ~/.config/FreeCAD/user.cfg
fi

# Macから画面共有するための設定
# $(gsettings get org.gnome.Vino require-encryption))が空白になる時のために""で括っている
if [ "$(gsettings get org.gnome.Vino require-encryption)" != 'false' ]; then
	gsettings set org.gnome.Vino require-encryption 'false'
fi

# ----------------------------------------------------------

if $imsudoer; then
	needs_remount=false
	if grep --quiet "133.71.125.179" /etc/fstab ; then
		sudo sed -i -e 's/133.71.125.179/133.71.76.11/g' -e 's/133.71.125.197/133.71.76.12/g' /etc/fstab
		needs_remount=true
	fi
	if ! grep --quiet ",noperm,username" /etc/fstab ; then
		sudo sed -i -e 's/,username/,noperm,username/g' /etc/fstab
		needs_remount=true
	fi
	if ! grep --quiet "133.71.125.166" /etc/fstab ; then
		sudo sed -i -e 's/\/\/133.71.125.173/\/\/133.71.125.166\/Public \/mnt\/Y_drive cifs vers=1.0,uid='"$(whoami)"',gid='"$(whoami)"',noperm,username=studentika,password=0909+nagare,domain=RYUUTAI 0 0\n\/\/133.71.125.173/' /etc/fstab
		needs_remount=true
	fi
	if grep --quiet "0909&nagare" /etc/fstab ; then
		sudo sed -i -e 's/0909&nagare/0909@nagare/g' /etc/fstab
		needs_remount=true
	fi
	if grep --quiet "0909+nagare" /etc/fstab ; then
		sudo sed -i -e 's/0909+nagare/0909@nagare/g' /etc/fstab
		needs_remount=true
	fi
	if ! grep --quiet "133.71.76.16" /etc/fstab ; then
		sudo sed -i -e 's/\/\/133.71.76.11\/ExtraHD/\/\/133.71.76.16\/student \/mnt\/DEXCS2-6IS_student cifs uid='"$(whoami)"',gid='"$(whoami)"',noperm,username=student,password=hello123,domain=RYUUTAI 0 0\n\/\/133.71.76.11\/ExtraHD/' \
			-e 's/\/\/133.71.125.166/\/\/133.71.76.16\/ExtraHD \/mnt\/DEXCS2-6IS_ExtraHD cifs uid='"$(whoami)"',gid='"$(whoami)"',noperm,username=student,password=hello123,domain=RYUUTAI 0 0\n\/\/133.71.125.166/' /etc/fstab
		needs_remount=true
	fi
	if grep --quiet "Y_drive cifs vers=1.0," /etc/fstab ; then
		sudo sed -i -e 's/Y_drive cifs vers=1.0,/Y_drive cifs /g' /etc/fstab
		needs_remount=true
	fi
	if "$needs_remount"; then
		sudo mount -a
	fi
fi

#tips='\n\n[お知らせ] '
tips=''
if [ "$dexcs_version" = '2021' ]; then
	tips='(変更点1) Pythonのバージョンは3です．\n(変更点2) 端末からfreecadを実行するコマンドは，freecad-dailyとfreecadcmd-dailyです．\n(変更点3) Paraviewで取り込むファイルの拡張子が.foamになりました.\n'
fi
zenity --title='終了' --info --text="$tips"'\n(DEXCS ver. '"$dexcs_version"')' --width=500
