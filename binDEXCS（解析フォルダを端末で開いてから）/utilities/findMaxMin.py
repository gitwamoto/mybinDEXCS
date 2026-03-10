#!/usr/bin/env python
# -*- coding: utf-8 -*-
# findMaxMin.py
# by Yukiharu Iwamoto
# 2021/6/30 11:32:31 AM

import os
import sys

def find_max_min(file_name_or_lines_list, column, top_skip = 0, delimiter = None):
    column -= 1  # column starts from 1, not 0!
    v_max = -float('inf')
    v_min = float('inf')
    n = 0
    if type(file_name_or_lines_list) is str:
        for line in open(file_name_or_lines_list, 'r'):
            line = line.strip()
            if line.startswith('#'):
                continue
            n += 1
            if n > top_skip:
                try:
                    v = float(line.split(delimiter)[column])
                    if v_max < v:
                        max_line = line
                        v_max = v
                    if v_min > v:
                        min_line = line
                        v_min = v
                except:
                    pass
    else:
        for line in file_name_or_lines_list:
            line = line.strip()
            if not line.startswith('#'):
                continue
            n += 1
            if n > top_skip:
                try:
                    v = float(line.split(delimiter)[column])
                    if v_max < v:
                        max_line = line
                        v_max = v
                    if v_min > v:
                        min_line = line
                        v_min = v
                except:
                    pass
    return [max_line, min_line]

def find_local_max_min(file_name_or_lines_list, column, top_skip = 0, delimiter = None):
    column -= 1  # column starts from 1, not 0!
    v_ll = None
    v_l = None
    v_c = None
    v_r = None
    line_c = None
    line_r = None
    max_list = []
    min_list = []
    n = 0
    if type(file_name_or_lines_list) is str:
        for line_rr in open(file_name_or_lines_list, 'r'):
            line_rr = line.strip()
            if line_rr.startswith('#'):
                continue
            n += 1
            if n > top_skip:
                try:
                    v_rr = float(line_rr.split(delimiter)[column])
                    if v_l is not None:
                        #        v_c
                        #       /   \
                        #    v_l     v_r
                        #    /         \
                        # v_ll         v_rr
                        if (v_c > v_l and v_c > v_r and
                            (v_ll is not None and v_l > v_ll or v_r > v_rr)):
                            max_list.append(line_c)
                        # v_ll         v_rr
                        #    \         /
                        #    v_l     v_r
                        #       \   /
                        #        v_c
                        elif (v_c < v_l and v_c < v_r and
                            (v_ll is not None and v_l < v_ll or v_r < v_rr)):
                            min_list.append(line_c)
                    v_ll = v_l
                    v_l = v_c
                    v_c = v_r
                    v_r = v_rr
                    line_c = line_r
                    line_r = line_rr
                except:
                    pass
    else:
        for line in file_name_or_lines_list:
            line = line.strip()
            if not line.startswith('#'):
                continue
            n += 1
            if n > top_skip:
                try:
                    v_rr = float(line_rr.split(delimiter)[column])
                    if v_l is not None:
                        #        v_c
                        #       /   \
                        #    v_l     v_r
                        #    /         \
                        # v_ll         v_rr
                        if (v_c > v_l and v_c > v_r and
                            (v_ll is not None and v_l > v_ll or v_r > v_rr)):
                            max_list.append(line_c)
                        # v_ll         v_rr
                        #    \         /
                        #    v_l     v_r
                        #       \   /
                        #        v_c
                        elif (v_c < v_l and v_c < v_r and
                            (v_ll is not None and v_l < v_ll or v_r < v_rr)):
                            min_list.append(line_c)
                    v_ll = v_l
                    v_l = v_c
                    v_c = v_r
                    v_r = v_rr
                    line_c = line_r
                    line_r = line_rr
                except:
                    pass
    if v_l is not None:
        if v_c > v_l and v_c > v_r and v_ll is not None and v_l > v_ll:
            max_list.append(line_c)
        elif v_c < v_l and v_c < v_r and v_ll is not None and v_l < v_ll:
            min_list.append(line_c)
    return [max_list, min_list]

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('\nUsage: {} file_name column_number [-d \'delimiter\'] [-t number_of_top_skip]\n'.format(sys.argv[0]))
        sys.exit(1)
    file_name = sys.argv[1]
    column = int(sys.argv[2])
    delimiter = None
    top_skip = 0
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '-d':
            i += 1
            delimiter = sys.argv[i]
        elif sys.argv[i] == '-t':
            i += 1
            top_skip = int(sys.argv[i])
        i += 1

    l = find_max_min(file_name, column, top_skip, delimiter)
    print('row showing max value: {}'.format(l[0]))
    print('row showing min value: {}'.format(l[1]))

    l = find_local_max_min(file_name, column, top_skip, delimiter)
    for i in l[0]:
        print('row showing local max value: {}'.format(i))
    for i in l[1]:
        print('row showing local min value: {}'.format(i))
