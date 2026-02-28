#!/usr/bin/env python
# -*- coding: utf-8 -*-
# appendEntries.py
# by Yukiharu Iwamoto
# 2026/2/28 12:30:48 AM

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

#def intoFvSolution():
#    def intoFvSolutionIn(path):
#        fvSolution = os.path.join(path, 'fvSolution')
#        if os.path.islink(fvSolution):
#            return
#        os.chmod(fvSolution, 0o0666)
#        dp = DictParser(fvSolution)
#        s_old = dp.toString()
#
#        x = dp.getValueForKey(['solvers'])
#        if x is not None:
#            params = []
#            for y in x:
#                if DictParserList.isType(y, DictParserList.BLOCK):
#                    params.append(y.key())
#            if 'Phi' not in params and ('p' in params or 'p_rgh' in params):
#                a = (
#                    '\n' +
#                    '\tPhi\n' +
#                    '\t{\n' +
#                    '\t\t' + ('$p' if 'p' in params else '$p_rgh') + ';\n' +
#                    '\t}\n'
#                )
#                if len(x) == 0:
#                    x.append(a)
#                elif type(x[-1]) is str:
#                    b = x[-1].rstrip()
#                    if len(x) == 1 and b == '':
#                        x[0] = a
#                    else:
#                        x[-1:] = [b + '\n', a]
#                else:
#                    x.extend(['\n', a])
#
#        x = dp.getValueForKey(['potentialFlow'])
#        i = None
#        if x is not None:
#            i = dp.getIndexOfItem(['nNonOrthogonalCorrectors'], x)
#            if i is not None:
#                i = i[0]
#                if not DictParserList.isType(x[i], DictParserList.DICT):
#                    i = None
#        if i is None:
#            a = '\n\tnNonOrthogonalCorrectors\t10;\n'
#            if x is None:
#                a = 'potentialFlow\n{' + a + '}\n'
#                x = dp.contents
#            if len(x) == 0:
#                x.append(a)
#            elif type(x[-1]) is str:
#                b = x[-1].rstrip()
#                if len(x) == 1 and b == '':
#                    x[0] = a
#                else:
#                    x[-1:] = [b if a[0] == '\n' else b + '\n', a]
#            elif a[0] == '\n':
#                x.append(a)
#            else:
#                x.extend(['\n\n', a])
#
#        c = '/* yesだと圧力方程式を解く前に，運動方程式からなる連立方程式を解いて速度を求める． */'
#        for t in ('SIMPLE', 'PIMPLE', 'PISO'):
#            x = dp.getValueForKey([t])
#            if x is not None:
#                i = dp.getIndexOfItem(['momentumPredictor'], x)
#                if i is not None and DictParserList.isType(x[i[0]], DictParserList.DICT):
#                    x[i[0]][-1] = c
#                else:
#                    dictFormat.insertEntryIntoBlockTop(
#                        entry = DictParser(
#                            string = 'momentumPredictor\tyes ' + c + ';\n'
#                        ).contents, block = x)
#                if t != 'SIMPLE' and dp.getIndexOfItem(['nCorrectors'], x) is None:
#                    dictFormat.insertEntryIntoBlockBottom(
#                        entry = DictParser(
#                            string = 'nCorrectors\t3;\n'
#                        ).contents, block = x)
#                if dp.getIndexOfItem(['nNonOrthogonalCorrectors'], x) is None:
#                    dictFormat.insertEntryIntoBlockBottom(
#                        entry = DictParser(
#                            string = 'nNonOrthogonalCorrectors\t1;\n'
#                        ).contents, block = x)
#                if t == 'SIMPLE' and dp.getIndexOfItem(['residualControl'], x) is None:
#                    dictFormat.insertEntryIntoBlockBottom(
#                        entry = DictParser(
#                            string = 'residualControl\n{\n\t".*"\t1.0e-03;\n}\n'
#                        ).contents, block = x)
#            else:
#                dictFormat.insertEntryIntoTopLayerBottom(
#                    entry = DictParser(
#                        string = '\n' + t + '\n{\nmomentumPredictor\tyes ' + c +
#                        ('' if t == 'SIMPLE' else ';\nnCorrectors\t3') + ';\n}\n'
#                    ).contents, contents = dp.contents)
#
#        cfields = '// p = p^{old} + \\alpha (p - p^{old})\n'
#        cequations = '// A_P/\\alpha u_P + \\sum_N A_N u_N = s + (1/\\alpha - 1) A_P u_P^{old}\n'
#        x = dp.getValueForKey(['relaxationFactors'])
#        if x is not None:
#            i = dp.getIndexOfItem(['fields'], x)
#            if i is not None and DictParserList.isType(x[i[0]], DictParserList.BLOCK):
#                x[i[0]][1] = cfields
#            else:
#                dictFormat.insertEntryIntoBlockBottom(
#                    entry = DictParser(string = 'fields ' + cfields +
#                        '{\n"p|p_rgh"\t1;\nrho\t1;\n}\n'
#                    ).contents, block = x)
#            i = dp.getIndexOfItem(['equations'], x)
#            if i is not None and DictParserList.isType(x[i[0]], DictParserList.BLOCK):
#                x[i[0]][1] = cequations
#            else:
#                dictFormat.insertEntryIntoBlockBottom(
#                    entry = DictParser(string = 'equations ' + cequations +
#                        '{\nU\t1;\n"k|epsilon|omega|R"\t1;\n}\n'
#                    ).contents, block = x)
#        else:
#            dictFormat.insertEntryIntoTopLayerBottom(
#                entry = DictParser(string = '\nrelaxationFactors\n{\nfields ' + cfields +
#                    '{\n"p|p_rgh"\t1;\nrho\t1;\n}\nequations' + cequations +
#                    '{\nU\t1;\n"k|epsilon|omega|R"\t1;\n}\n}\n'
#                ).contents, contents = dp.contents)
#
#        dp = dictFormat.moveLineToBottom(dp)
#        s = dp.toString()
#        if s != s_old:
#            with open(fvSolution, 'w') as f:
#                f.write(s)
#
#    if os.path.isdir('system'):
#        intoFvSolutionIn('system')
#    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
#        intoFvSolutionIn(d)

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
            if 'Phi' not in params and ('p_rgh' in params or 'p' in params):
                i = dictParse.find_element([{'type': 'block_end'}], parent = solvers, reverse = True)
                i['parent'][i['index']:i['index']] = dictParse.DictParser2(string =
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
                i = dictParse.find_element([{'type': 'block_end'}], parent = potentialFlow, reverse = True)
                i['parent'][i['index']:i['index']] = dictParse.DictParser2(string =
                    'nNonOrthogonalCorrectors\t10;\n'
                    ).elements

        # SIMPLE, PIMPLE, PISO
        linebreak = dictParse.DictParser2(string = '\n').elements[0]
        for k in ('SIMPLE', 'PIMPLE', 'PISO'):
            block = fvSolution.find_element([{'type': 'block', 'key': k}])
            if block is None:
                block_and_linebreak = dictParse.DictParser2(string =
                    str(k) + '\n' +
                    '{\n' +
                    '}\n\n').elements
                fvSolution.elements[footer_index:footer_index] = block_and_linebreak
                footer_index += len(block_and_linebreak)
                block = block_and_linebreak[0]
            else:
                block = block['element']
            start = dictParse.find_element([{'type': 'block_start'}], parent = block)['index'] + 1
            if block['value'][start]['type'] == 'linebreak':
                start += 1

            if k == 'SIMPLE':
                i = dictParse.find_element([{'type': 'block', 'key': 'residualControl'}], parent = block)
                if i is None:
                    block['value'][start:start] = dictParse.DictParser2(string =
                        'residualControl\n'
                        '{\n'
                        '".*"\t1.0e-03;\n'
                        '}\n'
                        ).elements
                else:
                    i['parent'][start:start] = [i['parent'].pop(i['index']), linebreak]

            if k != 'PISO':
                i = dictParse.find_element([{'type': 'dictionary', 'key': 'consistent'}], parent = block)
                if i is None:
                    block['value'][start:start] = dictParse.DictParser2(string =
                        'consistent\tyes;\n'
                        ).elements
                else:
                    i['parent'][start:start] = [i['parent'].pop(i['index']), linebreak]

            i = dictParse.find_element([{'type': 'dictionary', 'key': 'nNonOrthogonalCorrectors'}], parent = block)
            if i is None:
                block['value'][start:start] = dictParse.DictParser2(string =
                    'nNonOrthogonalCorrectors\t1;\n'
                    ).elements
            else:
                i['parent'][start:start] = [i['parent'].pop(i['index']), linebreak]

            if k != 'SIMPLE':
                i = dictParse.find_element([{'type': 'dictionary', 'key': 'nCorrectors'}], parent = block)
                if i is None:
                    block['value'][start:start] = dictParse.DictParser2(string =
                        'nCorrectors\t3;\n'
                        ).elements
                else:
                    i['parent'][start:start] = [i['parent'].pop(i['index']), linebreak]

            i = dictParse.find_element([{'type': 'dictionary', 'key': 'momentumPredictor'}], parent = block)
            if i is None:
                v = 'yes'
            else:
                v = dictParse.find_element([{'except type': 'line_comment|block_comment|whitespace|linebreak'}],
                    parent = i['element'])['element']['value']
                del block['value'][i['index']]
            block['value'][start:start] = dictParse.DictParser2(string =
                'momentumPredictor\t' + v + ';' +
                ' // yes -> 圧力方程式を解く前に，運動方程式を解いて速度を求める．\n'
                ).elements

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
        if relaxationFactors['value'][start]['type'] == 'linebreak':
            start += 1

        i = dictParse.find_element([{'type': 'block', 'key': 'fields'}], parent = relaxationFactors)
        if i is None:
            relaxationFactors['value'][start:start] = dictParse.DictParser2(string =
                'fields // p = p^{old} + \\alpha (p - p^{old})\n'
                '{'
                '"p|p_rgh"\t1.0;\n'
                'rho\t1.0;\n'
                '}\n'
                ).elements
        else:
            i['element']['value'][:dictParse.find_element([{'type': 'block_start'}],
                parent = i['element'])['index']] = dictParse.DictParser2(string =
                ' // p = p^{old} + \\alpha (p - p^{old})\n'
                ).elements

        i = dictParse.find_element([{'type': 'block', 'key': 'equations'}], parent = relaxationFactors)
        if i is None:
            relaxationFactors['value'][start:start] = dictParse.DictParser2(string =
                'equations // A_P/\\alpha u_P + \\sum_N A_N u_N = s + (1/\\alpha - 1) A_P u_P^{old}\n'
                '{'
                'U\t1.0;\n'
                '"k|epsilon|omega"\t1.0;\n'
                '}\n'
                ).elements
        else:
            i['element']['value'][:dictParse.find_element([{'type': 'block_start'}],
                parent = i['element'])['index']] = dictParse.DictParser2(string =
                ' // A_P/\\alpha u_P + \\sum_N A_N u_N = s + (1/\\alpha - 1) A_P u_P^{old}\n'
                ).elements

        dictParse.set_blank_line(relaxationFactors, number_of_blank_lines = 0)

        string = dictParse.normalize(string = fvSolution.file_string(pretty_print = True))[0]
        if fvSolution.string != string:
            os.rename(fvSolution_path, fvSolution_path + '_back')
            with open(fvSolution_path, 'w') as f:
                f.write(string)

    if os.path.isdir('system'):
        intoFvSolutionIn('system')
    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
        intoFvSolutionIn(d)

def intoFvSchemes():
    def intoFvSchemesIn(path):
        fvSchemes = os.path.join(path, 'fvSchemes')
        if os.path.islink(fvSchemes):
            return
        os.chmod(fvSchemes, 0o0666)
        dp = DictParser(fvSchemes)
        s_old = dp.toString()

        for t, k, v in (
                ('divSchemes', 'div(div(phi,U))', 'Gauss linear'),
                ('laplacianSchemes', 'laplacian(1,p)', 'Gauss linear corrected'),
                ('wallDist', 'method', 'meshWave'),
            ):
            x = dp.getValueForKey([t])
            i = None
            if x is not None:
                i = dp.getIndexOfItem([k], x)
                if i is not None:
                    i = i[0]
                    if not DictParserList.isType(x[i], DictParserList.DICT):
                        i = None
            if i is None:
                a = '\n\t' + k + '\t' + v + ';\n'
                if x is None:
                    a = t + '\n{' + a + '}\n'
                    x = dp.contents
                if len(x) == 0:
                    x.append(a)
                elif type(x[-1]) is str:
                    b = x[-1].rstrip()
                    if len(x) == 1 and b == '':
                        x[0] = a
                    else:
                        x[-1:] = [b if a[0] == '\n' else b + '\n', a]
                elif a[0] == '\n':
                    x.append(a)
                else:
                    x.extend(['\n\n', a])

        dp = dictFormat.moveLineToBottom(dp)
        s = dp.toString()
        if s != s_old:
            with open(fvSchemes, 'w') as f:
                f.write(s)

    if os.path.isdir('system'):
        intoFvSchemesIn('system')
    for d in glob.iglob(os.path.join('system', '*' + os.sep)):
        intoFvSchemesIn(d)

def intoControlDict():
    controlDict = os.path.join('system', 'controlDict')
    os.chmod(controlDict, 0o0666)
    dp = DictParser(controlDict)
    s_old = dp.toString()

    x = dp.getDPLForKey(['runTimeModifiable'])
    if x is not None:
        x.setValue(['yes'])
    else:
        a = DictParser(string = 'runTimeModifiable\tyes;\n').contents # list
        if len(dp.contents) == 0:
            dp.contents.extend(a)
        elif type(dp.contents[-1]) is str:
            b = dp.contents[-1].rstrip()
            if len(dp.contents) == 1 and b == '':
                dp.contents[:] = a
            else:
                dp.contents[-1:] = [b + '\n\n'] + a
        else:
            dp.contents.extend(['\n\n'] + a)

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

    dp = dictFormat.moveLineToBottom(dp)
    s = dp.toString()
    if s != s_old:
        with open(controlDict, 'w') as f:
            f.write(s)

if __name__ == '__main__':
    intoFvSolution()
#    intoFvSchemes()
#    intoControlDict()
