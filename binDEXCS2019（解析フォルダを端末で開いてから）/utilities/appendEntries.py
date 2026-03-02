#!/usr/bin/env python
# -*- coding: utf-8 -*-
# appendEntries.py
# by Yukiharu Iwamoto
# 2026/3/2 6:32:18 PM

import os
import sys
import glob
# {
# DEXCS2021だと，以下がないとfrom dictParse import DictParserでエラーが出る
if os.path.dirname(__file__) not in ([i.encode('UTF-8') if type(i) is unicode else i
    for i in sys.path] if sys.version_info.major <= 2 else sys.path):
    sys.path.append(os.path.dirname(__file__))
# }

# DictParser
from dictParse import DictParser
from dictParse import DictParserList
import dictFormat

# DictParser2
import re
import dictParse

def intoFvSolution():
    def intoFvSolutionIn(path):
        fvSolution_path = os.path.join(path, 'fvSolution')
        if os.path.islink(fvSolution_path):
            return
        os.chmod(fvSolution_path, 0o0666)
        dictParse.normalize(file_name = fvSolution_path)

        fvSolution = dictParse.DictParser2(file_name = fvSolution_path)

        # solvers/Phi
        solvers = fvSolution.find_element([{'type': 'block', 'key': 'solvers'}])['element']
        if solvers is not None:
            params = ','.join([i['element']['key'] for i in
                dictParse.find_all_elements([{'type': 'block'}], parent = solvers)])
            if 'Phi' not in params and ('p' in params or 'p_rgh' in params):
                block_end = dictParse.find_element([{'type': 'block_end'}], parent = solvers, reverse = True)
                block_end['parent'][block_end['index']:block_end['index']] = dictParse.DictParser2(string =
                    '\n' +
                    'Phi\n' +
                    '{\n' +
                    ('$p' if re.search('p(?!_rgh)', params) else '$p_rgh') + ';\n' +
                    '}\n').elements
            dictParse.set_blank_line(solvers, number_of_blank_lines = 1)

        footer = fvSolution.find_separators()[1]
        if footer is None:
            footer_index = len(fvSolution.elements)
        else:
            footer_index = footer['index']

        # potentialFlow
        potentialFlow = fvSolution.find_element([{'type': 'block', 'key': 'potentialFlow'}])['element']
        if potentialFlow is None:
            potentialFlow = dictParse.DictParser2(string =
                'potentialFlow\n' +
                '{\n' +
                'nNonOrthogonalCorrectors\t10;\n' +
                '}\n' +
                '\n').elements
            fvSolution.elements[footer_index:footer_index] = potentialFlow
            footer_index += len(potentialFlow)
        else:
            nNonOrthogonalCorrectors = dictParse.find_element(
                [{'type': 'dictionary', 'key': 'nNonOrthogonalCorrectors'}], parent = potentialFlow)['element']
            if nNonOrthogonalCorrectors is None:
                block_end = dictParse.find_element([{'type': 'block_end'}], parent = potentialFlow, reverse = True)
                block_end['parent'][block_end['index']:block_end['index']] = dictParse.DictParser2(string =
                    'nNonOrthogonalCorrectors\t10;\n').elements

        # SIMPLE, PIMPLE, PISO
        linebreak = dictParse.DictParser2(string = '\n').elements[0]
        for k in ('SIMPLE', 'PIMPLE', 'PISO'):
            block = fvSolution.find_element([{'type': 'block', 'key': k}])['element']
            if block is None:
                block_and_linebreak = dictParse.DictParser2(string =
                    str(k) + '\n' +
                    '{\n' +
                    '}\n' +
                    '\n').elements
                fvSolution.elements[footer_index:footer_index] = block_and_linebreak
                footer_index += len(block_and_linebreak)
                block = block_and_linebreak[0]
            i = dictParse.find_element([{'type': 'block_start'}], parent = block)['index'] + 1
            start = dictParse.find_element([{'type': 'linebreak'}], parent = block, start = i,
                index_not_found = i - 1)['index'] + 1

            if k == 'SIMPLE':
                residualControl = dictParse.find_element([{'type': 'block', 'key': 'residualControl'}], parent = block)
                if residualControl['element'] is None:
                    block['value'][start:start] = dictParse.DictParser2(string =
                        'residualControl\n'
                        '{\n'
                        '".*"\t1.0e-03;\n'
                        '}\n').elements
                else:
                    residualControl['parent'][start:start] = [
                        residualControl['parent'].pop(residualControl['index']), linebreak]

            if k != 'PISO':
                consistent = dictParse.find_element([{'type': 'dictionary', 'key': 'consistent'}], parent = block)
                if consistent['element'] is None:
                    block['value'][start:start] = dictParse.DictParser2(string =
                        'consistent\tyes;\n').elements
                else:
                    consistent['parent'][start:start] = [consistent['parent'].pop(consistent['index']), linebreak]

            nNonOrthogonalCorrectors = dictParse.find_element([
                {'type': 'dictionary', 'key': 'nNonOrthogonalCorrectors'}], parent = block)
            if nNonOrthogonalCorrectors['element'] is None:
                block['value'][start:start] = dictParse.DictParser2(string =
                    'nNonOrthogonalCorrectors\t1;\n').elements
            else:
                nNonOrthogonalCorrectors['parent'][start:start] = [
                    nNonOrthogonalCorrectors['parent'].pop(nNonOrthogonalCorrectors['index']), linebreak]

            if k != 'SIMPLE':
                nCorrectors = dictParse.find_element([{'type': 'dictionary', 'key': 'nCorrectors'}], parent = block)
                if nCorrectors['element'] is None:
                    block['value'][start:start] = dictParse.DictParser2(string =
                        'nCorrectors\t3;\n').elements
                else:
                    nCorrectors['parent'][start:start] = [nCorrectors['parent'].pop(nCorrectors['index']), linebreak]

            momentumPredictor = dictParse.find_element(
                [{'type': 'dictionary', 'key': 'momentumPredictor'}], parent = block)
            if momentumPredictor['element'] is None:
                v = 'yes'
            else:
                v = dictParse.find_element([{'except type': 'whitespace|line_comment|block_comment|linebreak'}],
                    parent = momentumPredictor['element'])['element']['value']
                del block['value'][momentumPredictor['index']]
            block['value'][start:start] = dictParse.DictParser2(string =
                'momentumPredictor\t' + v + ';' +
                ' // yes -> 圧力方程式を解く前に，運動方程式を解いて速度を求める．\n').elements

            dictParse.set_blank_line(block, number_of_blank_lines = 0)

        relaxationFactors = fvSolution.find_element([{'type': 'block', 'key': 'relaxationFactors'}])['element']
        if relaxationFactors is None:
            relaxationFactors = dictParse.DictParser2(string =
                'relaxationFactors\n'
                '{\n'
                '}\n\n').elements
            fvSolution.elements[footer_index:footer_index] = relaxationFactors
            footer_index += len(relaxationFactors)
        start = dictParse.find_element([{'type': 'block_start'}], parent = relaxationFactors)['index'] + 1
        i = dictParse.find_element([{'type': 'linebreak'}], parent = relaxationFactors, start = start)
        if i is not None:
            start = i['index'] + 1

        fields = dictParse.find_element([{'type': 'block', 'key': 'fields'}], parent = relaxationFactors)['element']
        if fields is None:
            relaxationFactors['value'][start:start] = dictParse.DictParser2(string =
                'fields // p = p^{old} + \\alpha (p - p^{old})\n'
                '{'
                '"p|p_rgh"\t1.0;\n'
                'rho\t1.0;\n'
                '}\n').elements
        else:
            fields['value'][:dictParse.find_element(
                [{'type': 'block_start'}], parent = fields)['index']] = dictParse.DictParser2(string =
                    ' // p = p^{old} + \\alpha (p - p^{old})\n').elements

        equations = dictParse.find_element(
            [{'type': 'block', 'key': 'equations'}], parent = relaxationFactors)['element']
        if equations is None:
            relaxationFactors['value'][start:start] = dictParse.DictParser2(string =
                'equations // A_P/\\alpha u_P + \\sum_N A_N u_N = s + (1/\\alpha - 1) A_P u_P^{old}\n'
                '{'
                'U\t1.0;\n'
                '"k|epsilon|omega"\t1.0;\n'
                '}\n'
                ).elements
        else:
            equations['value'][:dictParse.find_element(
                [{'type': 'block_start'}], parent = equations)['index']] = dictParse.DictParser2(string =
                ' // A_P/\\alpha u_P + \\sum_N A_N u_N = s + (1/\\alpha - 1) A_P u_P^{old}\n').elements

        dictParse.set_blank_line(relaxationFactors, number_of_blank_lines = 0)

        string = dictParse.normalize(string = fvSolution.file_string(pretty_print = True))[0]
        if fvSolution.string != string:
#            os.rename(fvSolution_path, fvSolution_path + '_back')
            with open(fvSolution_path, 'w') as f:
                f.write(string)

    if os.path.isdir('system'):
        intoFvSolutionIn('system')
    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
        intoFvSolutionIn(d)

def intoFvSchemes():
    def intoFvSchemesIn(path):
        fvSchemes_path = os.path.join(path, 'fvSchemes')
        if os.path.islink(fvSchemes_path):
            return
        os.chmod(fvSchemes_path, 0o0666)
        dictParse.normalize(file_name = fvSchemes_path)

        fvSchemes = dictParse.DictParser2(file_name = fvSchemes_path)

        footer = fvSchemes.find_separators()[1]
        if footer is None:
            footer_index = len(fvSchemes.elements)
        else:
            footer_index = footer['index']

        # divSchemes, laplacianSchemes, wallDist
        for b, k, v in (
            ('divSchemes', 'div(div(phi,U))', 'Gauss linear'),
            ('laplacianSchemes', 'laplacian(1,p)', 'Gauss linear corrected'),
            ('wallDist', 'method', 'meshWave')):
            block = fvSchemes.find_element([{'type': 'block', 'key': b}])['element']
            if block is None:
                block = dictParse.DictParser2(string =
                    b + '\n' +
                    '{\n' +
                    k + '\t' + v + ';\n' +
                    '}\n' +
                    '\n').elements
                fvSchemes.elements[footer_index:footer_index] = block
                footer_index += len(block)
            else:
                if dictParse.find_element([{'type': 'dictionary', 'key': k}], parent = block)['element'] is None:
                    block_end = dictParse.find_element([{'type': 'block_end'}], parent = block, reverse = True)
                    block_end['parent'][block_end['index']:block_end['index']] = dictParse.DictParser2(string =
                        k + '\t' + v + ';\n').elements

        string = dictParse.normalize(string = fvSchemes.file_string(pretty_print = True))[0]
        if fvSchemes.string != string:
#            os.rename(fvSchemes_path, fvSchemes_path + '_back')
            with open(fvSchemes_path, 'w') as f:
                f.write(string)

    if os.path.isdir('system'):
        intoFvSchemesIn('system')
    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
        intoFvSchemesIn(d)

def intoControlDict():
    controlDict_path = os.path.join('system', 'controlDict')
    os.chmod(controlDict_path, 0o0666)
    dictParse.normalize(file_name = controlDict_path)

    controlDict = dictParse.DictParser2(file_name = controlDict_path)

    footer = controlDict.find_separators()[1]
    if footer is None:
        footer_index = len(controlDict.elements)
    else:
        footer_index = footer['index']

    functions = controlDict.find_element([{'type': 'block', 'key': 'functions'}])
    if functions['element'] is None:
        functions_and_linebreak = dictParse.DictParser2(string =
            'functions\n' +
            '{\n' +
            '}\n' +
            '\n').elements
        controlDict.elements[footer_index:footer_index] = functions_and_linebreak
        functions_index = footer_index
        footer_index += len(functions_and_linebreak)
        functions = functions_and_linebreak[0]
    else:
        functions_index = functions['index']
        functions = functions['element']

    functions_blocks = dictParse.find_all_elements([{'type': 'block'}], parent = functions)
    for block in functions_blocks:
        block = block['element']
        enabled = dictParse.find_element([{'type': 'dictionary', 'key': 'enabled'}], parent = block)
        if enabled['element'] is None:
            v = 'yes'
        else:
            v = dictParse.find_element([{'except type': 'whitespace|line_comment|block_comment|linebreak'}],
                parent = enabled['element'])['element']['value']
            del block['value'][enabled['index']]
        insertion = dictParse.find_element([{'type': 'dictionary', 'key': 'libs'}], parent = block)
        if insertion['element'] is not None:
            insertion = insertion['index'] + 1
        else:
            insertion = dictParse.find_element([{'type': 'dictionary', 'key': 'type'}], parent = block)['index'] + 1
        insertion = dictParse.find_element(
            [{'type': 'linebreak'}], parent = block, start = insertion, index_not_found = insertion - 1)['index'] + 1
        block['value'][insertion:insertion] = dictParse.DictParser2(string =
            'enabled\t' + v + '; // yesで実行\n'
            ).elements
        dictParse.set_blank_line(block, number_of_blank_lines = 0)

    functions_end = dictParse.find_element([{'type': 'block_end'}], parent = functions, reverse = True)['index']
    has_limitNut = has_calcCo = has_printCoMinMax = False
    types = dictParse.find_all_elements([{'type': 'block'}, {'type': 'dictionary', 'key': 'type'}], parent = functions)
    for t in types:
        if (not has_limitNut and
            (dictParse.find_element([{'except type': 'whitespace|line_comment|block_comment|linebreak'}],
                parent = t['element'])['element']['value'] == 'limitFields' and
            dictParse.find_element([{'type': 'dictionary', 'key': 'fields'}, 
                {'except type': 'whitespace|line_comment|block_comment|linebreak'},
                {'except type': 'whitespace|line_comment|block_comment|linebreak|list_start'}],
                parent = t['parent'])['element']['value'] == 'nut' and
            dictParse.find_element([{'type': 'dictionary', 'key': 'limit'},
                {'except type': 'whitespace|line_comment|block_comment|linebreak'}],
                    parent = t['parent'])['element']['value'] == 'max')):
            has_limitNut = True
        elif (not has_calcCo and
            (dictParse.find_element([{'except type': 'whitespace|line_comment|block_comment|linebreak'}],
                parent = t['element'])['element']['value'] == 'CourantNo')):
            has_calcCo = True
        elif (not has_printCoMinMax and
            (dictParse.find_element([{'except type': 'whitespace|line_comment|block_comment|linebreak'}],
                parent = t['element'])['element']['value'] == 'fieldMinMax' and
            dictParse.find_element([{'type': 'dictionary', 'key': 'fields'}, 
                {'except type': 'whitespace|line_comment|block_comment|linebreak'},
                {'except type': 'whitespace|line_comment|block_comment|linebreak|list_start'}],
                parent = t['parent'])['element']['value'] == 'Co')):
            has_printCoMinMax = True

    if not has_limitNut:
        limitNut = dictParse.DictParser2(string =
            '\n'
            'limitNut // nutの最大値を制限する\n'
            '{\n'
            'type\tlimitFields;\n'
            'libs\t(fieldFunctionObjects);\n'
            'enabled\tno; // yesで実行\n'
            'fields\t(nut);\n'
            'limit\tmax; // 渦粘性の場合は上限(max)だけ抑えることが多い\n'
            'max\t0.01;\n'
            '}\n'
            ).elements
        functions['value'][functions_end:functions_end] = limitNut
        functions_end += len(limitNut)
    if not has_calcCo:
        calcCo = dictParse.DictParser2(string =
            '\n'
            'calcCo // クーラン数を計算する（画面に出なくても計算はされる）\n'
            '{\n'
            'type\tCourantNo;\n'
            'libs\t(fieldFunctionObjects);\n'
            'enabled\tno; // yesで実行\n'
            'writeControl\tno;\n'
            '}\n'
            ).elements
        functions['value'][functions_end:functions_end] = calcCo
        functions_end += len(calcCo)
    if not has_printCoMinMax:
        printCoMinMax = dictParse.DictParser2(string =
            '\n'
            'printCoMinMax // クーラン数（"Co"フィールド）の値を画面表示\n'
            '{\n'
            'type\tfieldMinMax;\n'
            'libs\t(fieldFunctionObjects);\n'
            'enabled\tno; // yesで実行\n'
            'fields\t(Co);\n'
            '}\n'
            ).elements
        functions['value'][functions_end:functions_end] = printCoMinMax
        functions_end += len(printCoMinMax)
    dictParse.set_blank_line(functions, number_of_blank_lines = 1)

    runTimeModifiable = controlDict.find_element([{'type': 'dictionary', 'key': 'runTimeModifiable'}])['element']
    if runTimeModifiable is None:
        runTimeModifiable = dictParse.DictParser2(string =
            'runTimeModifiable\tyes;\n' +
            '\n').elements
        controlDict.elements[functions_index:functions_index] = runTimeModifiable
        functions_index += len(runTimeModifiable)
        footer_index += len(runTimeModifiable)
    else:
        i = dictParse.find_element(
            [{'except type': 'whitespace|line_comment|block_comment|linebreak'}], parent = runTimeModifiable)
        i['parent'][i['index']] = dictParse.DictParser2(string = 'yes').elements[0]

    string = dictParse.normalize(string = controlDict.file_string(pretty_print = True))[0]
    if controlDict.string != string:
#        os.rename(controlDict_path, controlDict_path + '_back')
        with open(controlDict_path, 'w') as f:
            f.write(string)

if __name__ == '__main__':
    intoFvSolution()
    intoFvSchemes()
    intoControlDict()
