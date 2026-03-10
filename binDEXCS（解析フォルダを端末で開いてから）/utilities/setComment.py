#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setComment.py
# by Yukiharu Iwamoto
# 2021/1/28 3:19:51 PM

import os
import re

def comment(line, tail_regexp_wo_n):
    # 全角スペースは\sでは捕まえられない
    if re.search(tail_regexp_wo_n + r'[\s　]*\n?$', line) and not re.match(r'\s*//', line):
        line = '//' + line
    return line

def uncomment(line, tail_regexp_wo_n):
    # 全角スペースは\sでは捕まえられない
    if re.search(tail_regexp_wo_n + r'[\s　]*\n?$', line) and re.match(r'\s*//', line):
        line = re.sub(r'^(\s*)(?:\s*//)+', r'\1', line)
    return line

if __name__ == '__main__':
    print(comment('////12345 // 6\n', '// 6'))
    print(uncomment('   // // 12345 // 6\n', '6'))
