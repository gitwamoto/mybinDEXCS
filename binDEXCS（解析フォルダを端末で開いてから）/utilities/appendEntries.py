#!/usr/bin/env python
# -*- coding: utf-8 -*-
# appendEntries.py
# by Yukiharu Iwamoto
# 2026/5/14 10:49:02 AM

import os
import sys
import glob
import re
# このファイルの中の関数を呼び出すプログラムから，このファイルを含むフォルダが見えるようにする．
if os.path.dirname(__file__) not in sys.path:
    sys.path.append(os.path.dirname(__file__))
import dictParse

def intoFvSolution():
    def intoFvSolutionIn(path):
        fvSolution_path = os.path.join(path, 'fvSolution')
        if os.path.islink(fvSolution_path):
            return
        os.chmod(fvSolution_path, 0o0666)
        dictParse.normalize(file_name = fvSolution_path)

        fvSolution = dictParse.DictParser(file_name = fvSolution_path)

        solvers = fvSolution.find_element([{'type': 'block', 'key': 'solvers'}])['element']
        if solvers is not None:
            information_date = '2026/3/9' # 情報の日付
            solvers_start = solvers.find_element([{'type': 'block_start'}])['index'] + 1
            i = solvers.find_element([{'type': 'block_comment'}], start = solvers_start)
            if i['element'] is not None and '数値的に安定だと思われる設定' in i['element']['value']:
                s = re.search(r'数値的に安定だと思われる設定\s*[(（]\s*([0-9/]+)\s*現在\s*[)）]', i['element']['value'])
                if s is None or s.group(1) != information_date:
                    del i['parent'][i['index']]
                    i['element'] = None
            if i['element'] is None or '数値的に安定だと思われる設定' not in i['element']['value']:
                solvers['value'][solvers_start:solvers_start] = dictParse.DictParser(string =
                '\n'
                '/*\n'
                f'\t数値的に安定だと思われる設定({information_date}現在)\n'
                '\t残差は\n'
                '\t「方程式の右辺 - 方程式の左辺」の絶対値の全格子点に対する総和/「方程式の右辺」の絶対値の全格子点に対する総和\n'
                '\tのこと\n'
                '\t"p|p_rgh"\n'
                '\t{\n'
                '\t\tsolver\tGAMG;\n'
                '\t\tsmoother\tDIC;\n'
                '\t\ttolerance\t1.0e-06; // 残差がこれより小さくなったら繰り返し計算をやめる\n'
                '\t\trelTol\t0.001; // 残差が「relTol*繰り返し計算1回目の残差」より小さくなったら繰り返し計算をやめる\n'
                '\t}\n'
                '\t"U|k|epsilon|omega"\n'
                '\t{\n'
                '\t\tsolver\tPBiCGStab;\n'
                '\t\tpreconditioner\tDILU;\n'
                '\t\ttolerance\t1.0e-06; // 残差がこれより小さくなったら繰り返し計算をやめる\n'
                '\t\trelTol\t0.001; // 残差が「relTol*繰り返し計算1回目の残差」より小さくなったら繰り返し計算をやめる\n'
                '\t}\n'
                '\t*/\n')['value']

            # solvers/Phi
            params = '|'.join([i['element']['key'].strip('"')
                for i in solvers.find_all_elements([{'type': 'block'}])])
            if re.search(params, 'Phi') is None:
                p = re.search(params, 'p')
                if p is None:
                    p = re.search(params, 'p_rgh')
                if p is not None:
                    block_end = solvers.find_element([{'type': 'block_end'}], reverse = True)
                    block_end['parent'][block_end['index']:block_end['index']] = dictParse.DictParser(string =
                        '\n'
                        'Phi\n'
                        '{\n'
                        f'\t${p.groups()};\n'
                        '}\n')['value']

            solvers.set_blank_line(number_of_blank_lines = 1)

        tail_index = fvSolution.find_element([{'except type': 'whitespace|linebreak|separator'}],
            reverse = True, index_not_found = len(fvSolution['value']) - 1)['index'] + 1

        # potentialFlow
        potentialFlow = fvSolution.find_element([{'type': 'block', 'key': 'potentialFlow'}])['element']
        if potentialFlow is None:
            linebreak_and_potentialFlow = dictParse.DictParser(string =
                '\n'
                '\n'
                'potentialFlow\n'
                '{\n'
                '\tnNonOrthogonalCorrectors\t10;\n'
                '}')['value']
            fvSolution['value'][tail_index:tail_index] = linebreak_and_potentialFlow
            tail_index += len(linebreak_and_potentialFlow)
        else:
            nNonOrthogonalCorrectors = potentialFlow.find_element(
                [{'type': 'dictionary', 'key': 'nNonOrthogonalCorrectors'}])['element']
            if nNonOrthogonalCorrectors is None:
                block_end = potentialFlow.find_element([{'type': 'block_end'}], reverse = True)
                block_end['parent'][block_end['index']:block_end['index']] = dictParse.DictParser(string =
                    'nNonOrthogonalCorrectors\t10;\n')['value']

        # SIMPLE, PIMPLE, PISO
        linebreak = dictParse.DictParser(string = '\n')['value'][0]
        for k in ('SIMPLE', 'PIMPLE', 'PISO'):
            block = fvSolution.find_element([{'type': 'block', 'key': k}])['element']
            if block is None:
                linebreak_and_block = dictParse.DictParser(string =
                    '\n'
                    '\n'
                    f'{k}\n'
                    '{\n'
                    '}')['value']
                fvSolution['value'][tail_index:tail_index] = linebreak_and_block
                tail_index += len(linebreak_and_block)
                block = linebreak_and_block[-1]
            i = block.find_element([{'type': 'block_start'}])['index'] + 1
            block_start = block.find_element(
                [{'type': 'linebreak'}], start = i, index_not_found = i - 1)['index'] + 1

            if k == 'SIMPLE':
                residualControl = block.find_element([{'type': 'block', 'key': 'residualControl'}])
                if residualControl['element'] is None:
                    block['value'][block_start:block_start] = dictParse.DictParser(string =
                        'residualControl\n'
                        '{\n'
                        '\t".*"\t1.0e-03;\n'
                        '}\n')['value']
                else:
                    residualControl['parent'][block_start:block_start] = [
                        residualControl['parent'].pop(residualControl['index']), linebreak]

            if k != 'PISO':
                consistent = block.find_element([{'type': 'dictionary', 'key': 'consistent'}])
                if consistent['element'] is None:
                    block['value'][block_start:block_start] = dictParse.DictParser(string =
                        'consistent\tyes;\n')['value']
                else:
                    consistent['parent'][block_start:block_start] = [
                        consistent['parent'].pop(consistent['index']), linebreak]

            nNonOrthogonalCorrectors = block.find_element([
                {'type': 'dictionary', 'key': 'nNonOrthogonalCorrectors'}])
            if nNonOrthogonalCorrectors['element'] is None:
                block['value'][block_start:block_start] = dictParse.DictParser(string =
                    'nNonOrthogonalCorrectors\t1;\n')['value']
            else:
                nNonOrthogonalCorrectors['parent'][block_start:block_start] = [
                    nNonOrthogonalCorrectors['parent'].pop(nNonOrthogonalCorrectors['index']), linebreak]

            if k != 'SIMPLE':
                nCorrectors = block.find_element([{'type': 'dictionary', 'key': 'nCorrectors'}])
                if nCorrectors['element'] is None:
                    block['value'][block_start:block_start] = dictParse.DictParser(string =
                        'nCorrectors\t3;\n')['value']
                else:
                    nCorrectors['parent'][block_start:block_start] = [
                        nCorrectors['parent'].pop(nCorrectors['index']), linebreak]

            momentumPredictor = block.find_element([{'type': 'dictionary', 'key': 'momentumPredictor'}])
            if momentumPredictor['element'] is None:
                v = 'yes'
            else:
                v = momentumPredictor['element'].find_element([{'except type': 'ignorable'}])['element']['value']
                del block['value'][momentumPredictor['index']]
            block['value'][block_start:block_start] = dictParse.DictParser(string =
                f'momentumPredictor\t{v};'
                ' // yes -> 圧力方程式を解く前に，運動方程式を解いて速度を求める．\n')['value']

            block.set_blank_line(number_of_blank_lines = 0)

        relaxationFactors = fvSolution.find_element([{'type': 'block', 'key': 'relaxationFactors'}])['element']
        if relaxationFactors is None:
            linebreak_and_relaxationFactors = dictParse.DictParser(string =
                '\n'
                '\n'
                'relaxationFactors\n'
                '{\n'
                '}')['value']
            fvSolution['value'][tail_index:tail_index] = linebreak_and_relaxationFactors
            tail_index += len(linebreak_and_relaxationFactors)
            relaxationFactors = linebreak_and_relaxationFactors[-1]
        relaxationFactors_start = relaxationFactors.find_element([{'type': 'block_start'}])['index'] + 1

        fields = relaxationFactors.find_element([{'type': 'block', 'key': 'fields'}])['element']
        if fields is None:
            relaxationFactors['value'][
                relaxationFactors_start:relaxationFactors_start] = dictParse.DictParser(string =
                '\n'
                '\tfields // p = p^{old} + \\alpha (p - p^{old})\n'
                '\t{\n'
                '\t\t"p|p_rgh"\t1.0;\n'
                '\t\trho\t1.0;\n'
                '\t}')['value']
        else:
            fields['value'][:fields.find_element([{'type': 'block_start'}])['index']
                ] = dictParse.DictParser(string = ' // p = p^{old} + \\alpha (p - p^{old})\n')['value']

        equations = relaxationFactors.find_element([{'type': 'block', 'key': 'equations'}])['element']
        if equations is None:
            relaxationFactors['value'][
                relaxationFactors_start:relaxationFactors_start] = dictParse.DictParser(string =
                '\n'
                '\tequations // A_P/\\alpha u_P + \\sum_N A_N u_N = s + (1/\\alpha - 1) A_P u_P^{old}\n'
                '\t{\n'
                '\t\tU\t1.0;\n'
                '\t\t"k|epsilon|omega"\t1.0;\n'
                '\t}')['value']
        else:
            equations['value'][:equations.find_element(
                [{'type': 'block_start'}])['index']] = dictParse.DictParser(string =
                    ' // A_P/\\alpha u_P + \\sum_N A_N u_N = s + (1/\\alpha - 1) A_P u_P^{old}\n')['value']

        relaxationFactors.set_blank_line(number_of_blank_lines = 0)

        string = dictParse.normalize(string = fvSolution.file_string())[0]
        if fvSolution.string != string:
#            os.rename(fvSolution_path, f'{fvSolution_path}_bak')
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

        fvSchemes = dictParse.DictParser(file_name = fvSchemes_path)

        # divSchemes, laplacianSchemes, wallDist
        for b, k, v in (
            ('divSchemes', 'div(div(phi,U))', 'Gauss linear'),
            ('laplacianSchemes', 'laplacian(1,p)', 'Gauss linear corrected'),
            ('wallDist', 'method', 'meshWave')):
            block = fvSchemes.find_element([{'type': 'block', 'key': b}])['element']
            if block is None:
                linebreak_and_block = dictParse.DictParser(string =
                    '\n'
                    '\n'
                    f'{b}\n'
                    '{\n'
                    f'\t{k}\t{v};\n'
                    '}')['value']
                tail_index = fvSchemes.find_element([{'except type': 'whitespace|linebreak|separator'}],
                    reverse = True, index_not_found = len(fvSchemes['value']) - 1)['index'] + 1
                fvSchemes['value'][tail_index:tail_index] = linebreak_and_block
#                tail_index += len(linebreak_and_block)
            else:
                if block.find_element([{'type': 'dictionary', 'key': k}])['element'] is None:
                    block_end = block.find_element([{'type': 'block_end'}], reverse = True)
                    block_end['parent'][block_end['index']:block_end['index']
                        ] = dictParse.DictParser(string =f'{k}\t{v};\n')['value']

        string = dictParse.normalize(string = fvSchemes.file_string())[0]
        if fvSchemes.string != string:
#            os.rename(fvSchemes_path, f'{fvSchemes_path}_bak')
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

    controlDict = dictParse.DictParser(file_name = controlDict_path)

    startFrom = controlDict.find_element([{'type': 'dictionary', 'key': 'startFrom'},
        {'except type': 'ignorable'}])['element']
    if startFrom != 'latestTime':
        startFrom['patent'][startFrom['index']:startFrom['index'] + 1] = dictParse.DictParser(string =
            'latestTime')['value']
        print(f'!!! {controlDict_path}ファイルのstartFromをlatestTimeに書き換えました．')

    deltaT_index = controlDict.find_element([{'type': 'dictionary', 'key': 'deltaT'}])['index']
    i = controlDict.find_element(
        [{'type': 'block_comment'}], start = deltaT_index - 1, reverse = True)['element']
    if i is None or 'simpleFoam' not in i['value']:
        controlDict['value'][deltaT_index:deltaT_index] = dictParse.DictParser(string =
            '/*\n'
            'simpleFoamnの場合，deltaTは使っていないのでいくらでも良い．\n'
            '計算の安定性はsystem/fvSolutionの中のrelaxationFactorsで制御する．\n'
            '*/\n')['value']

    tail_index = controlDict.find_element([{'except type': 'whitespace|linebreak|separator'}],
        reverse = True, index_not_found = len(controlDict['value']) - 1)['index'] + 1

    functions = controlDict.find_element([{'type': 'block', 'key': 'functions'}])
    if functions['element'] is None:
        linebreak_and_functions = dictParse.DictParser(string =
            '\n'
            '\n'
            'functions\n'
            '{\n'
            '}')['value']
        controlDict['value'][tail_index:tail_index] = linebreak_and_functions
        functions_index = tail_index
        tail_index += len(linebreak_and_functions)
        functions = linebreak_and_functions[-1]
    else:
        functions_index = functions['index']
        functions = functions['element']

    for block in functions.find_all_elements([{'type': 'block'}]):
        block = block['element']
        enabled = block.find_element([{'type': 'dictionary', 'key': 'enabled'}])
        if enabled['element'] is None:
            v = 'yes'
        else:
            v = enabled['element'].find_element([{'except type': 'ignorable'}])['element']['value']
            del block['value'][enabled['index']]
        insertion = block.find_element([{'type': 'dictionary', 'key': 'libs'}])
        if insertion['element'] is not None:
            insertion = insertion['index'] + 1
        else:
            insertion = block.find_element([{'type': 'dictionary', 'key': 'type'}])['index'] + 1
        insertion = block.find_element(
            [{'type': 'linebreak'}], start = insertion, index_not_found = insertion - 1)['index'] + 1
        block['value'][insertion:insertion] = dictParse.DictParser(string =
            f'enabled\t{v}; // yesで実行\n')['value']
        block.set_blank_line(number_of_blank_lines = 0)

    functions_end = functions.find_element([{'type': 'block_end'}], reverse = True)['index']
    has_limitNut = False
# Geminiによると，simpleFoamでは時間ステップが使われていないため，クーラン数を表示する必要はないらしい．
#    has_calcCo = has_printCoMinMax = False
    types = functions.find_all_elements([{'type': 'block'}, {'type': 'dictionary', 'key': 'type'}])
    for t in types:
        if (not has_limitNut and
            (t['element'].find_element([{'except type': 'ignorable'}]
                )['element']['value'] == 'limitFields' and
            t['parent'].find_element([{'type': 'dictionary', 'key': 'fields'}, 
                {'except type': 'ignorable'}, {'except type': 'ignorable|list_start'}]
                )['element']['value'] == 'nut' and
            t['parent'].find_element([{'type': 'dictionary', 'key': 'limit'},
                {'except type': 'ignorable'}])['element']['value'] == 'max')):
            has_limitNut = True
#        elif (not has_calcCo and
#            (t['element'].find_element([{'except type': 'ignorable'}])['element']['value'] == 'CourantNo')):
#            has_calcCo = True
#        elif (not has_printCoMinMax and
#            (t['element'].find_element([{'except type': 'ignorable'}])['element']['value'] == 'fieldMinMax' and
#            t['parent'].find_element([{'type': 'dictionary', 'key': 'fields'}, 
#                {'except type': 'ignorable'}, {'except type': 'ignorable|list_start'}]
#                )['element']['value'] == 'Co')):
#            has_printCoMinMax = True

    if not has_limitNut:
        limitNut = dictParse.DictParser(string =
            '\n'
            '\tlimitNut // nutの最大値を制限する\n'
            '\t{\n'
            '\t\ttype\tlimitFields;\n'
            '\t\tlibs\t(fieldFunctionObjects);\n'
            '\t\tenabled\tno; // yesで実行\n'
            '\t\tfields\t(nut);\n'
            '\t\tlimit\tmax; // 渦粘性の場合は上限(max)だけ抑えることが多い\n'
            '\t\tmax\t0.01;\n'
            '\t}\n')['value']
        functions['value'][functions_end:functions_end] = limitNut
        functions_end += len(limitNut)
#    if not has_calcCo:
#        calcCo = dictParse.DictParser(string =
#            '\n'
#            '\tcalcCo // クーラン数を計算する（画面に出なくても計算はされる）\n'
#            '\t{\n'
#            '\t\ttype\tCourantNo;\n'
#            '\t\tlibs\t(fieldFunctionObjects);\n'
#            '\t\tenabled\tno; // yesで実行\n'
#            '\t}\n')['value']
#        functions['value'][functions_end:functions_end] = calcCo
#        functions_end += len(calcCo)
#    if not has_printCoMinMax:
#        printCoMinMax = dictParse.DictParser(string =
#            '\n'
#            '\tprintCoMinMax // クーラン数（"Co"フィールド）の値を画面表示\n'
#            '\t{\n'
#            '\t\ttype\tfieldMinMax;\n'
#            '\t\tlibs\t(fieldFunctionObjects);\n'
#            '\t\tenabled\tno; // yesで実行\n'
#            '\t\tfields\t(Co);\n'
#            '\t}\n')['value']
#        functions['value'][functions_end:functions_end] = printCoMinMax
#        functions_end += len(printCoMinMax)
    functions.set_blank_line(number_of_blank_lines = 1)

    runTimeModifiable = controlDict.find_element(
        [{'type': 'dictionary', 'key': 'runTimeModifiable'}])['element']
    if runTimeModifiable is None:
        linebreak_and_runTimeModifiable = dictParse.DictParser(string =
            '\n'
            'runTimeModifiable\tyes;\n')['value']
        controlDict['value'][functions_index:functions_index] = linebreak_and_runTimeModifiable
        functions_index += len(linebreak_and_runTimeModifiable)
        tail_index += len(linebreak_and_runTimeModifiable)
    else:
        i = runTimeModifiable.find_element([{'except type': 'ignorable'}])
        i['parent'][i['index']] = dictParse.DictParser(string = 'yes')['value'][0]

    string = dictParse.normalize(string = controlDict.file_string())[0]
    if controlDict.string != string:
#        os.rename(controlDict_path, f'{controlDict_path}_bak')
        with open(controlDict_path, 'w') as f:
            f.write(string)

if __name__ == '__main__':
    intoFvSolution()
    intoFvSchemes()
    intoControlDict()
