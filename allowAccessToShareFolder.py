#!/usr/bin/env python
# -*- coding: utf-8 -*-
# allowAccessToShareFolder.py
# by Yukiharu Iwamoto
# 2019/6/3 9:51:55 PM

# 使い方
# (1) 端末で以下を入力し，Enterキーを押す．:
#     sudo python このフォルダまでのパス/allowAccessToShareFolder.py
# (2) パスワードを入力後，Enterキーを押す．

import os
import subprocess
subprocess.call('gpasswd -a %s vboxsf' % os.getlogin(), shell = True)
