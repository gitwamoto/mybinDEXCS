#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setFuncsInCD.py
# by Yukiharu Iwamoto
# 2026/3/10 2:05:49 PM

import os
import sys
import subprocess
import re
# このファイルの中の関数を呼び出すプログラムから，このファイルを含むフォルダが見えるようにする．
if os.path.dirname(__file__) not in sys.path:
    sys.path.append(os.path.dirname(__file__))
import dictParse

def setAllEnabled(enabled = True, path = os.curdir):
    controlDict_path = os.path.join(path, 'system', 'controlDict')
    controlDict = dictParse.DictParser2(file_name = controlDict_path)

    functions = controlDict.find_element([{'type': 'block', 'key': 'functions'}])['element']
    if functions is None:
        return
    yesno = 'yes' if enabled else 'no'
    for function in dictParse.find_all_elements([{'type': 'block'}], parent = functions):
        function = function['element']
        e = dictParse.find_element([{'type': 'dictionary', 'key': 'enabled'}], parent = function)['element']
        if e is None:
            t = dictParse.find_element([{'type': 'dictionary', 'key': 'type'}], parent = function)
            if t['element'] is None:
                print(f'エラー: ファイル {controlDict_path} のfunctionsで，typeがない項目があります．')
                sys.exit(1)
            i = dictParse.find_element([{'type': 'dictionary', 'except key': 'libs'}], parent = function,
                start = t['index'] + 1, index_not_found = t['index'])['index'] + 1
            function['value'][i:i] = dictParse.DictParser2(string = '\n'
                f'enabled\t{yesno}; yesで実行\n').elements
        else:
            e['value'][dictParse.find_element([{'type': 'word'}], parent = e)['index']] = yesno

    string = dictParse.normalize(string = controlDict.file_string(pretty_print = True))[0]
    if enabled:
        re.sub(r'\b(//([/ \t]*)+(?=#includeFunc)'
    if controlDict.string != string:
#        os.rename(controlDict_path, controlDict_path + '_bak')
        with open(controlDict_path, 'w') as f:
            f.write(string)



    for enabled in dictParse.find_all_elements([{'type': 'block'}, {'type': 'dictionary', 'key': 'enabled'}],
        parent = functions['element']):
        i = dictParse.element([{'type': 'word'}])
        enabled['element'][i['index']] = 'yes' if enabled else 'no'
    if x is not None:
        for n, y in enumerate(x):
            if DictParserList.isType(y, DictParserList.BLOCK):
                i = controlDict.getIndexOfItem([y.key(), 'enabled'], y)
                vy = y.value()
                if (i is not None and DictParserList.isType(vy[i[1]], DictParserList.DICT)):
                    vy[i[1]].setValue(v)
                else:
                    z = DictParserList(DictParserList.DICT, ['enabled', '', v, '/* yesで実行 */'])
                    if len(vy) == 0:
                        vy.extend(['\n', z, '\n'])
                    if len(vy) > 0 and type(vy[-1]) is str:
                        vy[-1:] = ['\n', z, '\n' + vy[-1].lstrip()]
                    else:
                        vy.extend(['\n\n', z,' \n'])
            elif not enabled and DictParserList.isType(y, DictParserList.DICT) and y.key() == '#includeFunc':
                y.setKey('// ' + y.key())
            elif enabled and type(y) is str and y.find('#includeFunc'):
                x[n] = re.sub(r'//\s*(#includeFunc\s+)', r'\t\1', y)
    s = controlDict.toString()
    if s != s_old:
        with open(controlDict_path, 'w') as f:
            f.write(s)

def setEnabledForType(type_ = '', enabled = True, path = os.curdir):
    controlDict_path = os.path.join(path, 'system', 'controlDict')
    controlDict = dictParse.DictParser2(file_name = controlDict_path)
    v = ['yes' if enabled else 'no']
    x = controlDict.getValueForKey(['functions'])
    if x is not None:
        for n, y in enumerate(x):
            if DictParserList.isType(y, DictParserList.BLOCK):
                i = controlDict.getIndexOfItem([y.key(), 'type'], y)
                vy = y.value()
                if (i is None or
                   not DictParserList.isType(vy[i[1]], DictParserList.DICT) or
                   vy[i[1]].value()[0] != type_):
                   continue
                i = controlDict.getIndexOfItem([y.key(), 'enabled'], y)
                if (i is not None
                    and DictParserList.isType(vy[i[1]], DictParserList.DICT)):
                    vy[i[1]].setValue(v)
                else:
                    z = DictParserList(DictParserList.DICT, ['enabled', '', v,
                        '/* yesで実行 */'])
                    if len(vy) == 0:
                        vy.extend(['\n', z, '\n'])
                    if len(vy) > 0 and type(vy[-1]) is str:
                        vy[-1:] = ['\n', z, '\n' + vy[-1].lstrip()]
                    else:
                        vy.extend(['\n\n', z,' \n'])
            elif (not enabled and DictParserList.isType(y, DictParserList.DICT) and y.key() == '#includeFunc'
                and y.value()[0].startswith(type_ + '(')):
                y.setKey('// ' + y.key())
            elif enabled and type(y) is str and y.find('#includeFunc'):
                x[n] = re.sub(r'//\s*(#includeFunc\s+(?:/\*.+\*/\s*)?' + type_ + r'\()', r'\t\1', y)
    s = controlDict.toString()
    if s != s_old:
        with open(controlDict_path, 'w') as f:
            f.write(s)

if __name__ == '__main__':
    path = os.curdir if len(sys.argv) == 1 else sys.argv[1]
#    setAllEnabled(False, path)
    setEnabledForType('patchAverage', True, path)
