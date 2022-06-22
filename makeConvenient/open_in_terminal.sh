#!/bin/bash
# open_in_terminal.sh
# by Yukiharu Iwamoto
# 2022/6/18 7:02:42 PM

# 引数をつけて実行すると，sudoコマンドを行わなくなる．

if [ -e /opt/OpenFOAM/OpenFOAM-v1906/etc/bashrc ]; then
	dexcs_version=2019
elif [ -e /usr/lib/openfoam/openfoam2106/etc/bashrc ]; then
	dexcs_version=2021
else
	zenity --error --text='未対応のDEXCSのバージョンです．' --width=500
	exit 1
fi

cd $(dirname $0)

if [ $# -eq 0 ]; then
	imsudoer=true
else
	imsudoer=false
fi

if $imsudoer && [ "$dexcs_version" = '2021' ]; then
	sudo ln -s /usr/bin/python3 /usr/bin/python
fi

if $imsudoer; then
	sudo python resources/makeConvenient.py
else
	python resources/makeConvenient.py imnotsudoer
fi

echo
echo '必要なプログラムをダウンロード中...'

# ----------------------------------------------------------

apt_installed=$(apt list --installed)

if [ "$dexcs_version" = '2019' ]; then
	# aptでインストールして欲しくないもの
	if $imsudoer; then
		for p in python-numpy python-scipy python-matplotlib python-wxgtk3.0 python-GPyOpt python-openpyxl python-requests; do
			# installed in /usr/lib/python2.7/dist-packages
			if echo "$apt_installed" | grep --quiet "$p"/; then
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
			gedit-plugins wxmaxima handbrake; do
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
		if [ ! -e /usr/local/lib/python2.7/dist-packages/GPy-1.9.9*-info ]; then
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

	if ! echo $snap_installed | grep --quiet notepadqq; then
		sudo snap install notepadqq --devmode
	fi

else # 2021
	# aptでインストールして欲しくないもの
	if $imsudoer; then
		for p in python3-numpy python3-scipy python3-matplotlib libwxgtk3.0-gtk3-0v5 python3-openpyxl python3-requests; do
			# installed in /usr/local/lib/python3.8/dist-packages
			if echo "$apt_installed" | grep --quiet "$p"/; then
				sudo apt purge -y "$p"
				sudo apt autoremove -y
			fi
		done
	fi

	# pipのインストール
	if $imsudoer && ! echo "$apt_installed" | grep --quiet python3-pip/; then
		sudo apt install -y python3-pip
		sudo apt autoremove -y
	fi

	# aptでインストールして欲しいので，pipでインストールされていたら消しておく
	for p in pexpect pyperclip chardet xlrd Pillow urllib3; do
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
	for p in numpy scipy matplotlib zenhan GPyOpt GPy geomdl openpyxl requests; do
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
	if $imsudoer; then
		for p in python3-tk \
			python3-pexpect python3-pyperclip python3-chardet python3-xlrd python3-pil python3-urllib3 \
			libsdl2-2.0-0 libgtk-3-dev \
			gedit-plugins wxmaxima handbrake notepadqq; do
			if ! echo "$apt_installed" | grep --quiet "$p"/; then
				sudo apt install -y "$p"
				sudo apt autoremove -y
			fi
		done
	fi

	# sudo pipでインストールして欲しいもの
	if $imsudoer; then
		for p in numpy scipy matplotlib zenhan GPyOpt geomdl openpyxl requests; do
			if [ ! -e /usr/local/lib/python3.8/dist-packages/"$p" ]; then
				sudo pip install "$p"
			fi
		done
		if [ ! -e /usr/local/lib/python3.8/dist-packages/GPy-1.9.9*-info ]; then
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
	if [ "$key" = 'computer-icon-visible' -a "$dexcs_version" = '2019' ]; then
		: # do nothing
	elif [ "$(gsettings get $entry $key)" != 'true' ]; then
		gsettings set $entry $key 'true'
	fi
done

# 壁紙の設定
key=/org/gnome/desktop/background/picture-uri
if [ "$dexcs_version" = '2019' ]; then
	dexcs_wall_paper="'file:///usr/share/backgrounds/dexcs-desktop-1.jpg'"
else # 2021
	dexcs_wall_paper="'file:///opt/DEXCS/backgrounds/dexcs-desktop-1.jpeg'"
fi
if [ "$(dconf read $key)" = "$dexcs_wall_paper" ]; then
	dconf write $key "'file:///usr/share/backgrounds/ubuntu-default-greyscale-wallpaper.png'"
fi
key=/org/gnome/desktop/screensaver/picture-uri
if [ "$(dconf read $key)" = "$dexcs_wall_paper" ]; then
	dconf write $key "'file:///usr/share/backgrounds/ubuntu-default-greyscale-wallpaper.png'"
fi

# Dockのアイコンサイズ変更
key=/org/gnome/shell/extensions/dash-to-dock/dash-max-icon-size
if [ $(dconf read $key) -gt 24 ]; then
	dconf write $key 24
fi

# デスクトップ上の時計表示の設定
for key in '/org/gnome/desktop/interface/clock-show-date' '/org/gnome/desktop/interface/clock-show-seconds'; do
	if [ "$(dconf read $key)" != 'true' ]; then
		dconf write $key 'true'
	fi
done

if $imsudoer && [ $(apt list --upgradable | wc -l) -gt 1 ]; then
	sudo apt update
	sudo apt upgrade -y
fi

# 更新したFreeCADのconfigファイルは~/.config/FreeCADにある．
if [ "$dexcs_version" = '2021' -a -d "~/.config/FreeCAD" -a ! -e "~/.config/FreeCAD/user.cfg_orig" ]; then
	mv "~/.config/FreeCAD/user.cfg" "~/.config/FreeCAD/user.cfg_orig"
	cp -f "~/.FreeCAD/user.cfg" "~/.config/FreeCAD/user.cfg"
fi

# ----------------------------------------------------------

cd -

