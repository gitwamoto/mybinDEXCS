#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 0秒フォルダにpatchを追加する.py
# by Yukiharu Iwamoto
# 2026/3/12 7:46:02 PM

# ---- オプションはない ----

# DictParser2で書き直し済み

import os
import signal
import glob
import re
from utilities import misc
from utilities import rmObjects
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

        print(f'{f}を処理中...')
        parameter = dictParse.DictParser2(file_name = f)

        if f_base in ('k', 'epsilon', 'omega'):
            internalField = parameter.find_element([{'type': 'dictionary', 'key': 'internalField'}])
            i = parameter.find_element([{'type': 'block_comment'}], start = internalField['index'] - 1, reverse = True)
            if i['element'] is None or '初期値の例' not in i['element']['value']:
                if f_base == 'k':
                    c = ('/*\n'
                        '初期値の例\n'
                        '<内部流/外部流/管内流の場合>\n'
                        '_U\t〇〇; // 流速 [m/s]\n'
                        '_k_intensity\t〇〇; // 流速にかかる係数\n'
                        '// 低乱流: 0.001〜0.01 | 一般的な乱流: 0.01〜0.05 | 建築物まわりの流れや大気流: 0.05〜0.10\n'
                        '_k_init\t#calc "1.5*pow($_k_intensity*$_U,2)"; // kの初期値 [m^2/s^2]\n'
                        '<管内流の場合>\n'
                        '_Re\t〇〇; //レイノルズ数\n'
                        '_k_init\t#calc "1.5*pow(0.16*pow($_Re,-0.125)*$_U,2)"; // kの初期値 [m^2/s^2]\n'
                        '*/\n')
                else: # epsilon, omega
                    c = ('/*\n'
                        '初期値の例\n'
                        '_k_init\t〇〇; // kの初期値 [m^2/s^2]\n'
                        '_L\t〇〇; 代表長さ [m]\n'
                        '_L_mixing\t〇〇; // 乱流渦の代表的な混合距離 [m]\n'
                        '// 内部流: #calc "0.07*$_L" | 外部流: #calc "0.1*$_L"〜#calc "0.01*$_L"\n')
                    if f_base == 'epsilon':
                        c += '_epsilon_init\t#calc "pow(0.09,0.75)*pow($_k_init,1.5)/$_L_mixing"; // epsilonの初期値 [m^2/s^3]\n'
                    else: # omega
                        c += '_omega_init\t#calc "pow($_k_init,0.5)/(pow(0.09,0.25)*$_L_mixing)"; // omegaの初期値 [1/s]\n'
                    c += '*/\n'
                parameter.elements[
                    internalField['index']:internalField['index']] = dictParse.DictParser2(string = c).elements

        boundaryField = parameter.find_element([{'type': 'block', 'key': 'boundaryField'}])['element']
        if boundaryField is None:
            linebreak_and_boundaryField = dictParse.DictParser2(string =
                '\n'
                'boundaryField\n'
                '{\n'
                '}\n').elements
            tail_index = parameter.find_element([{'except type': 'whitespace|linebreak|separator'}],
                reverse = True, index_not_found = len(parameter.elements) - 1)['index'] + 1
            parameter.elements[tail_index:tail_index] = linebreak_and_boundaryField
            boundaryField = linebreak_and_boundaryField[1]
        i = dictParse.find_element([{'type': 'block_end'}], parent = boundaryField, reverse = True)['index']
        boundaryField_end = dictParse.find_element([{'type': 'linebreak'}], parent = boundaryField, start = i - 1,
            reverse = True, index_not_found = i)['index']

        for p in patches:
            i = dictParse.find_element([{'type': 'block', 'key': p['element']['key']}], parent = boundaryField)
            if i['element'] is None:
                v = dictParse.find_element([{'type': 'dictionary', 'key': 'type'},
                    {'except type': 'whitespace|line_comment|block_comment|linebreak'}],
                    parent = p['element'])['element']['value']
                s = ('\n' +
                    p['element']['key'] + '\n' +
                    '{\n' +
                    'type\t')
                if v == 'wall':
                    if f_base == 'U':
                        s += ('noSlip;\n'
                            '// U = (0 0 0)に規定\n')
                    elif f_base == 'k':
                        s += ('kqRWallFunction;\n'
                            '// 高レイノルズ数型乱流モデルにおけるk, q, Rの壁面境界条件\n'
                            '// zeroGrdientのラッパー\n'
                            'value\t$internalField; // 実際には使わないけど必要\n')
                    elif f_base == 'epsilon':
                        s += ('epsilonWallFunction;\n'
                            '// epsilonの壁面境界条件\n'
                            'value\t$internalField; // 実際には使わないけど必要\n')
                    elif f_base == 'omega':
                        s += ('omegaWallFunction;\n'
                            '// omegaの壁面境界条件\n'
                            'value\t$internalField; // 実際には使わないけど必要\n')
                    elif f_base == 'p':
                        s += ('zeroGradient\n'
                            '// こう配が0，境界での値 = セル中心での値にする．\n')
                    elif f_base == 'nut':
                        s += ('nutkWallFunction;\n'
                            '// nutの壁面境界条件，標準的\n'
                            '// yPlus = C_mu^0.25*sqrt(k)*y/nuから格子中心のyPlusを求め，\n'
                            '// 対数則領域内に格子中心があるかどうかを判断する．\n'
                            '// ある場合，対数速度分布から得られる壁面せん断応力\n'
                            '// tau_w = mu*kappa*yPlus/log(E*yPlus)*(u/y)\n'
                            '// になるように乱流粘性係数を設定する．\n'
                            '// https://www.slideshare.net/fumiyanozaki96/openfoam-36426892\n'
                            'value\t$internalField; // 実際には使わないけど必要\n')
                    else:
                        s += 'zeroGradient;\n'
                elif f_base == 'nut':
                    s += ('calculated;\n'
                        '// 他の変数から計算可能であることを表す．\n'
                        '// 壁面でない境界におけるnutの境界条件としてよく使われる．\n'
                        'value\t$internalField; // 実際には使わないけど必要\n')
                else:
                    s += (v if v in ('empty', 'symmetryPlane', 'symmetry', 'wedge') else 'zeroGradient') + ';\n'
                b = dictParse.DictParser2(string = s + '}\n').elements
                boundaryField['value'][boundaryField_end:boundaryField_end] = b
                boundaryField_end += len(b)
            else:
                # popで1つ引き抜くので，差し込む場所はboundaryField_end - 1にする．
                i['parent'][boundaryField_end - 1:boundaryField_end - 1] = [linebreak, i['parent'].pop(i['index'])]
                boundaryField_end += 1 # linebreakのぶん増える
        dictParse.set_blank_line(boundaryField, number_of_blank_lines = 1)

        string = dictParse.normalize(string = parameter.file_string(pretty_print = True))[0]
        if parameter.string != string:
#            os.rename(f, f + '_bak')
            with open(f, 'w') as fp:
                fp.write(string)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
    misc.showDirForPresentAnalysis(__file__)

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

    rmObjects.removeInessentials()
