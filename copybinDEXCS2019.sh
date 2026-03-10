#!/bin/bash
# copybinDEXCS2019.sh
# by Yukiharu Iwamoto
# 2026/3/9 1:09:34 PM

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

wget_from_github_public() {
	# $1: user
	# $2: repository
	# $3: branch
	# $4: file path
	# $5: path to a file to save
	document=$(mktemp /tmp/document.XXXXXXX)
	wget --no-check-certificate --output-document="$document" "https://raw.githubusercontent.com/$1/$2/$3/$4"
	if [ -s "$document" ]; then # -s -> True if a file size is greater than 0
		mv -f "$document" "$5"
	else
		rm "$document"
	fi
}

cd ~

# dakuten.py -j <path> で濁点を結合しておく
binDEXCS2019=binDEXCS2019（解析フォルダを端末で開いてから）
binDEXCS=binDEXCS（解析フォルダを端末で開いてから）

if [ -d Desktop/"$binDEXCS2019" ] && [ ! -d Desktop/"$binDEXCS" ]; then
	mv Desktop/"$binDEXCS2019" Desktop/"$binDEXCS"
fi
if [ ! -d Desktop/"$binDEXCS" ]; then
	mkdir Desktop/"$binDEXCS"
fi

((trial=0))
for d in /mnt/DEXCS2-6left_student /mnt/DEXCS2-6right_student; do
	if [ -d "$d" ] && [ -n "$(ls -A $d)" ]; then
		rsync -av "$d"/マニュアル/bin/copybinDEXCS.sh Desktop/copybinDEXCS.sh
		chmod +x Desktop/copybinDEXCS.sh
		break
	fi
	((++trial))
done
if [ "$trial" -eq 2 ]; then
	wget_from_github_public gitwamoto mybinDEXCS main copybinDEXCS.sh Desktop/copybinDEXCS.sh
	chmod +x Desktop/copybinDEXCS.sh
fi

cd -

python -c "
import os

dexcs_version = '"$dexcs_version"'

BD_alias = 'alias BD=\'xdg-open ~/Desktop/binDEXCS（解析フォルダを端末で開いてから）'
if dexcs_version == '2021':
    BD_alias += '*'
BD_alias += '\'\n'
bashrc = os.path.expanduser('~/.bashrc')
with open(bashrc, 'r') as f:
    s = f.read().rstrip().replace('binDEXCS2019', 'binDEXCS') + '\n'
if BD_alias not in s:
    with open(bashrc, 'a') as f:
        f.write(BD_alias)
"

Desktop/copybinDEXCS.sh
