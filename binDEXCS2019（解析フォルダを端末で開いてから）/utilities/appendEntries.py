#!/usr/bin/env python
# -*- coding: utf-8 -*-
# appendEntries.py
# by Yukiharu Iwamoto
# 2026/2/28 11:06:55 PM

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
        solvers = fvSolution.find_element([{'type': 'block', 'key': 'solvers'}])
        if solvers is not None:
            solvers = solvers['element']
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
        potentialFlow = fvSolution.find_element([{'type': 'block', 'key': 'potentialFlow'}])
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
            potentialFlow = potentialFlow['element']
            nNonOrthogonalCorrectors = dictParse.find_element(
                [{'type': 'dictionary', 'key': 'nNonOrthogonalCorrectors'}], parent = potentialFlow)
            if nNonOrthogonalCorrectors is None:
                block_end = dictParse.find_element([{'type': 'block_end'}], parent = potentialFlow, reverse = True)
                block_end['parent'][block_end['index']:block_end['index']] = dictParse.DictParser2(string =
                    'nNonOrthogonalCorrectors\t10;\n').elements

        # SIMPLE, PIMPLE, PISO
        linebreak = dictParse.DictParser2(string = '\n').elements[0]
        for k in ('SIMPLE', 'PIMPLE', 'PISO'):
            block = fvSolution.find_element([{'type': 'block', 'key': k}])
            if block is None:
                block_and_linebreak = dictParse.DictParser2(string =
                    str(k) + '\n' +
                    '{\n' +
                    '}\n' +
                    '\n').elements
                fvSolution.elements[footer_index:footer_index] = block_and_linebreak
                footer_index += len(block_and_linebreak)
                block = block_and_linebreak[0]
            else:
                block = block['element']
            start = dictParse.find_element([{'type': 'block_start'}], parent = block)['index'] + 1
            i = dictParse.find_element([{'type': 'linebreak'}], parent = block[start:])
            if i is not None:
                start += i['index'] + 1

            if k == 'SIMPLE':
                residualControl = dictParse.find_element([{'type': 'block', 'key': 'residualControl'}],
                    parent = block)
                if residualControl is None:
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
                if consistent is None:
                    block['value'][start:start] = dictParse.DictParser2(string =
                        'consistent\tyes;\n').elements
                else:
                    consistent['parent'][start:start] = [consistent['parent'].pop(consistent['index']), linebreak]

            nNonOrthogonalCorrectors = dictParse.find_element([
                {'type': 'dictionary', 'key': 'nNonOrthogonalCorrectors'}], parent = block)
            if nNonOrthogonalCorrectors is None:
                block['value'][start:start] = dictParse.DictParser2(string =
                    'nNonOrthogonalCorrectors\t1;\n').elements
            else:
                nNonOrthogonalCorrectors['parent'][start:start] = [
                    nNonOrthogonalCorrectors['parent'].pop(nNonOrthogonalCorrectors['index']), linebreak]

            if k != 'SIMPLE':
                nCorrectors = dictParse.find_element([{'type': 'dictionary', 'key': 'nCorrectors'}], parent = block)
                if nCorrectors is None:
                    block['value'][start:start] = dictParse.DictParser2(string =
                        'nCorrectors\t3;\n').elements
                else:
                    nCorrectors['parent'][start:start] = [nCorrectors['parent'].pop(nCorrectors['index']), linebreak]

            momentumPredictor = dictParse.find_element([{'type': 'dictionary', 'key': 'momentumPredictor'}],
                parent = block)
            if momentumPredictor is None:
                v = 'yes'
            else:
                v = dictParse.find_element([{'except type': 'whitespace|line_comment|block_comment|linebreak'}],
                    parent = momentumPredictor['element'])['element']['value']
                del block['value'][momentumPredictor['index']]
            block['value'][start:start] = dictParse.DictParser2(string =
                'momentumPredictor\t' + v + ';' +
                ' // yes -> 圧力方程式を解く前に，運動方程式を解いて速度を求める．\n').elements

            dictParse.set_blank_line(block, number_of_blank_lines = 0)

        relaxationFactors = fvSolution.find_element([{'type': 'block', 'key': 'relaxationFactors'}])
        if relaxationFactors is None:
            relaxationFactors = dictParse.DictParser2(string =
                'relaxationFactors\n'
                '{\n'
                '}\n\n').elements
            fvSolution.elements[footer_index:footer_index] = relaxationFactors
            footer_index += len(relaxationFactors)
        else:
            relaxationFactors = relaxationFactors['element']
        start = dictParse.find_element([{'type': 'block_start'}], parent = relaxationFactors)['index'] + 1
        i = dictParse.find_element([{'type': 'linebreak'}], parent = relaxationFactors[start:])
        if i is not None:
            start += i['index'] + 1

        fields = dictParse.find_element([{'type': 'block', 'key': 'fields'}], parent = relaxationFactors)
        if fields is None:
            relaxationFactors['value'][start:start] = dictParse.DictParser2(string =
                'fields // p = p^{old} + \\alpha (p - p^{old})\n'
                '{'
                '"p|p_rgh"\t1.0;\n'
                'rho\t1.0;\n'
                '}\n').elements
        else:
            fields['element']['value'][:dictParse.find_element([{'type': 'block_start'}],
                parent = fields['element'])['index']] = dictParse.DictParser2(string =
                    ' // p = p^{old} + \\alpha (p - p^{old})\n').elements

        equations = dictParse.find_element([{'type': 'block', 'key': 'equations'}], parent = relaxationFactors)
        if equations is None:
            relaxationFactors['value'][start:start] = dictParse.DictParser2(string =
                'equations // A_P/\\alpha u_P + \\sum_N A_N u_N = s + (1/\\alpha - 1) A_P u_P^{old}\n'
                '{'
                'U\t1.0;\n'
                '"k|epsilon|omega"\t1.0;\n'
                '}\n'
                ).elements
        else:
            equations['element']['value'][:dictParse.find_element([{'type': 'block_start'}],
                parent = equations['element'])['index']] = dictParse.DictParser2(string =
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
            block = fvSchemes.find_element([{'type': 'block', 'key': b}])
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
                block = block['element']
                d = dictParse.find_element(
                    [{'type': 'dictionary', 'key': k}], parent = block)
                if d is None:
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
    controlDict_path = os.path.join(path, 'controlDict')
    if os.path.islink(controlDict_path):
        return
    os.chmod(controlDict_path, 0o0666)
    dictParse.normalize(file_name = controlDict_path)

    controlDict = dictParse.DictParser2(file_name = controlDict_path)

    footer = controlDict.find_separators()[1]
    if footer is None:
        footer_index = len(controlDict.elements)
    else:
        footer_index = footer['index']

    functions = controlDict.find_element([{'type': 'dictionary', 'key': 'functions'}])
    if functions is None:
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

    functions_blocks = dictParse.find_all_elements([{'type': 'block'}], parent = functions)])
    if functions_blocks is not None:
        for block in functions_blocks:
            enabled = dictParse.find_element([{'type': 'dictionary', 'key': 'enabled'}], parent = block['elements'])
            if enabled is not None:
                v = 'yes'
            else:
                v = dictParse.find_element([{'except type': 'whitespace|line_comment|block_comment|linebreak'}],
                    parent = enabled['element'])['element']['value']
                del functions_blocks['value'][enabled['index']]
            insertion = dictParse.find_element([{'type': 'dictionary', 'key': 'libs'}], parent = block)
            if insertion is not None:
                insertion = insertion['index'] + 1
            else:
                insertion = dictParse.find_element(
                    [{'type': 'dictionary', 'key': 'type'}], parent = block)['index'] + 1
            i = dictParse.find_element([{'type': 'linebreak'}], parent = block[insertion:])
            if i is not None:
                insertion += i['index'] + 1
            block['value'][insertion:insertion] = dictParse.DictParser2(string =
                'enabled\t' + v + '; // yesで実行\n'
                ).elements
            dictParse.set_blank_line(block, number_of_blank_lines = 0)

#    end = dictParse.find_element([{'type': 'block_end'}], parent = functions, reverse = True)['index']
    has_limitNut = has_calcCo = has_printCoMinMax = False
    types = dictParse.find_all_elements([{'type': 'block'}, {'type': 'dictionaty', 'key': 'type'}],
        parent = functions)
    if types is not None:
        for t in types:
            if (dictParse.find_element([{'except type': 'whitespace|line_comment|block_comment|linebreak'}],
                    parent = t['element'])['element']['value'] == 'limitFields' and
                dictParse.find_element([{'except type': 'whitespace|line_comment|block_comment|linebreak|list_start'}],
                    parent = dictParse.find_element([{'type': 'dictionary', 'key': 'fields'}],
                        parent = t['parent'])['element'])['element']['value'] == 'nut' and
                dictParse.find_element([{'except type': 'whitespace|line_comment|block_comment|linebreak'}],
                    parent = dictParse.find_element([{'type': 'dictionary', 'key': 'limit'}],
                        parent = t['parent'])['element'])['element']['value'] == 'max'):
                has_limitNut = True

#	limitNut // nutの最大値を制限する
#	{
#		type	limitFields;
#		libs	(fieldFunctionObjects);
#		enabled	no; // yesで実行
#		fields	(nut);
#		limit	max; // 渦粘性の場合は上限(max)だけ抑えることが多い
#		max	#calc "1000.0*$_nu";
#	}
#    calcCo // クーラン数を計算する（画面に出なくても計算はされる）
#    {
#        type            CourantNo;
#        libs            (fieldFunctionObjects);
#        enabled	no; // yesで実行
#        writeControl    none;
#    }
#    printCoMinMax // クーラン数（"Co"フィールド）の値を画面表示
#    {
#        type            fieldMinMax;
#        libs            (fieldFunctionObjects);
#        enabled	no; // yesで実行
#        fields           (Co);
#    }

    x = dp.getValueForKey(['functions'])
    if x is not None:
        for y in x:
            if (DictParserList.isType(y, DictParserList.BLOCK) and
                dp.getIndexOfItem([y.key(), 'enabled'], y) is None):
                a = DictParser(string = '\nenabled\tno /* yesで実行 */;\n').contents # list
                z = y.value()
                if len(z) == 0:
                    z.extend(a)
                elif type(z[-1]) is str:
                    z[-1:] = a + [z[-1].lstrip()]
                else:
                    z.extend(a)

    runTimeModifiable = controlDict.find_element([{'type': 'dictionary', 'key': 'runTimeModifiable'}])
    if runTimeModifiable is None:
        runTimeModifiable = dictParse.DictParser2(string =
            'runTimeModifiable\tyes;\n' +
            '\n').elements
        controlDict.elements[functions_index:functions_index] = runTimeModifiable
        functions_index += len(runTimeModifiable)
        footer_index += len(runTimeModifiable)
    else:
        i = dictParse.find_element([{'except type': 'whitespace|line_comment|block_comment|linebreak'}],
            parent = runTimeModifiable['element'])
        i['parent'][i['index']] = dictParse.DictParser2(string = 'yes').elements[0]

    string = dictParse.normalize(string = controlDict.file_string(pretty_print = True))[0]
    if controlDict.string != string:
#        os.rename(controlDict_path, controlDict_path + '_back')
        with open(controlDict_path, 'w') as f:
            f.write(string)

if __name__ == '__main__':
    intoFvSolution()
    intoFvSchemes()
#    intoControlDict()
