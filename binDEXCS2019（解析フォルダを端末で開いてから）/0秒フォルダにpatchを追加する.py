#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 0秒フォルダにpatchを追加する.py
# by Yukiharu Iwamoto
# 2026/3/3 7:53:47 PM

# ---- オプションはない ----

# DictParser2で書き直し済み

import os
import signal
import glob
import re
#from utilities import misc
#from utilities import rmObjects
from utilities import dictParse

def append_patches(src, dst):
    src = os.path.join(src, 'polyMesh', 'boundary')
    os.chmod(src, 0o0666) # 誰でも（所有者・グループ・その他全員）読み書きができるが、実行権限（x）はない

    boundary = dictParse.DictParser2(file_name = src)

    patches = boundary.find_all_elements([{'type': 'list'}, {'type': 'block'}])
    patches.sort(key = lambda p: p['element']['key'])

    linebreak = dictParse.DictParser2(string = '\n').elements[0]
    for f in glob.iglob(os.path.join(dst, '*')):
        if not os.path.isfile(f):
            continue
        os.chmod(f, 0o0666)
        f_base = os.path.basename(f)
        if f_base == 'cellToRegion':
            continue

        print('{}を処理中...'.format(f))
        parameter = dictParse.DictParser2(file_name = f)

        if f_base in ('k', 'epsilon', 'omega'):
            internalField = parameter.find_element([{'type': 'dictionary', 'key': 'internalField'}])
            i = parameter.find_element(
                [{'except type': 'whitespace|linebreak'}], start = internalField['index'] - 1, reverse = True)
            if (i['element'] is None or
                i['element']['type'] not in ('line_comment|block_comment') or
                'の初期値' not in i['element']['value']):
                if f_base == 'k':
                    c = ('// 初期値の例\n'
                        '// <内部流/外部流/管内流の場合>\n'
                        '// _U\t〇〇; // 流速 [m/s]\n'
                        '// _k_intensity\t〇〇; // 流速にかかる係数\n'
                        '//   低乱流: 0.001〜0.01 | 一般的な乱流: 0.01〜0.05 | 建築物まわりの流れや大気流: 0.05〜0.10\n'
                        '// _k_init\t#calc "1.5*pow($_k_intensity*$_U,2)"; // kの初期値 [m^2/s^2]\n'
                        '// <管内流の場合>\n'
                        '// _Re\t〇〇; //レイノルズ数\n'
                        '// _k_init\t#calc "1.5*pow(0.16*pow($_Re,-0.125)*$_U,2)"; // kの初期値 [m^2/s^2]\n')
                else:
                    c = ('// 初期値の例\n'
                        '// _k_init\t〇〇; // kの初期値 [m^2/s^2]\n'
                        '// _L\t〇〇; 代表長さ [m]\n'
                        '// _L_mixing\t〇〇; // 乱流渦の代表的な混合距離 [m]\n'
                        '//   内部流: #calc "0.07*$_L" | 外部流: #calc "0.1*$_L"〜#calc "0.01*$_L"\n')
                if f_base == 'epsilon':
                    c += '// _epsilon_init\t#calc "pow(0.09,0.75)*pow($_k_init,1.5)/$_L_mixing"; // epsilonの初期値 [m^2/s^3]\n'
                elif f_base == 'omega':
                    c += '// _omega_init\t#calc "pow($_k_init,0.5)/(pow(0.09,0.25)*$_L_mixing)"; // omegaの初期値 [1/s]\n'
                parameter.elements[
                    internalField['index']:internalField['index']] = dictParse.DictParser2(string = c).elements

        boundaryField = parameter.find_element([{'type': 'block', 'key': 'boundaryField'}])['element']
        if boundaryField is None:
            boundaryField_and_linebreak = dictParse.DictParser2(string =
                'boundaryField\n'
                '{\n'
                '}\n'
                '\n').elements
            footer_index = parameter.find_separators(footer_index_not_found = len(parameter.elements))[1]['index']
            parameter.elements[footer_index:footer_index] = boundaryField_and_linebreak
            boundaryField = boundaryField_and_linebreak[0]
        i = dictParse.find_element([{'type': 'block_end'}], parent = boundaryField, reverse = True)['index']
        boundaryField_end = dictParse.find_element([{'type': 'linebreak'}], parent = boundaryField, start = i - 1,
            reverse = True, index_not_found = i)['index']

        for p in patches:
            i = dictParse.find_element([{'type': 'block', 'key': p['element']['key']}], parent = boundaryField)
            if i['element'] is None:
                v = dictParse.find_element([{'type': 'dictionary', 'key': 'type'},
                    {'except type': 'whitespace|line_comment|block_comment|linebreak'}],
                    parent = p['element'])['element']['value']
                if v not in ('empty', 'symmetryPlane', 'symmetry', 'wedge'):
                    v = 'zeroGradient'
                b = dictParse.DictParser2(string = '\n' +
                    p['element']['key'] + '\n' +
                    '{\n' +
                    'type\t' + v + ';\n' +
                    '}\n').elements
                boundaryField['value'][boundaryField_end:boundaryField_end] = b
                boundaryField_end += len(b)
            else:
                # popで1つ引き抜くので，差し込む場所はboundaryField_end - 1にする．
                i['parent'][boundaryField_end - 1:boundaryField_end - 1] = [linebreak, i['parent'].pop(i['index'])]
                boundaryField_end += 1 # linebreakのぶん増える
        dictParse.set_blank_line(boundaryField, number_of_blank_lines = 1)

        string = dictParse.normalize(string = parameter.file_string(pretty_print = True))[0]
        if parameter.string != string:
#            os.rename(f, f + '_back')
            with open(f, 'w') as f:
                f.write(string)

if __name__ == '__main__':
#    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
#    misc.showDirForPresentAnalysis(__file__)

    regions = []
    for d in glob.iglob(os.path.join('constant', '*' + os.sep)):
        if os.path.isdir(d + 'polyMesh'):
            regions.append(os.path.basename(d[:-len(os.sep)]))
    if len(regions) == 0:
        append_patches(src = 'constant', dst = '0')
    else:
        for i in regions:
            d = os.path.join('0', i)
            if os.path.isdir(d):
                append_patches(src = os.path.join('constant', i), dst = d)

#    rmObjects.removeInessentials()
