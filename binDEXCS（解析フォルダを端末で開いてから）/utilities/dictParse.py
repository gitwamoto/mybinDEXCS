#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dictParse.py
# by Yukiharu Iwamoto
# 2026/5/1 3:32:28 PM

import sys
import os
import re

def normalize(file_name = None, string = None, overwrite_file = True):
    if file_name is not None:
        with open(file_name, 'r') as f:
            string = f.read()
    if sys.version_info.major <= 2:
        normalized_string = re.sub(u'[ \\t]+(?=\\r?\\n|$)', '', # 末尾の空白を削除
            re.sub(u'(?<=[;{}()\\[\\]][ \\t])[ \\t]+(?=\\S)', '', # セミコロン，かっこの後ろの余計なスペースを削除
            re.sub(u'(?<＝[\\u3040-\\u309F\\u30A0-\\u30FF\\u4E00-\\u9FFF])[,.]',
                lambda m: unichr(ord(m.group(0)) + 0xFEE0), # 全角ひらがな，カタカナ，漢字以外に続く「．」と「，」を半角に
            re.sub('[！-～]', lambda m: unichr(ord(m.group(0)) - 0xFEE0), # 英数字・記号を半角に変換
            string.decode('UTF-8').replace(u'　', u' '), # 全角スペースを半角に
            flags = re.UNICODE)))).encode('UTF-8')
        pass
    else:
        normalized_string = re.sub(r'[ \t]+(?=\r?\n|$)', '', # 末尾の空白を削除
            re.sub(r'(?<=[;{}()\[\]][ \t])[ \t]+(?=\S)', '', # セミコロン，かっこの後ろの余計なスペースを削除
            re.sub(r'(?<=[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF])[,.]',
                lambda m: chr(ord(m.group(0)) + 0xFEE0), # 全角ひらがな，カタカナ，漢字に続く「.」と「,」を全角に
            re.sub('[！-～]', lambda m: chr(ord(m.group(0)) - 0xFEE0), # 英数字・記号を半角に変換
            string.replace('　', ' ') # 全角スペースを半角に
            ))))
    changed = normalized_string != string
    if file_name is not None and overwrite_file and changed:
        with open(file_name, 'w') as f:
            f.write(normalized_string)
    return normalized_string, changed

def re_sub_except_comments(pattern, repl, string):
    pat = re.compile(
        r'(?P<line_comment>//.*)' '|'
        r'(?P<block_comment>/\*[\s\S]*?\*/)' '|' # [\s\S]*?の?がないと\*/も[\s\S]*が取り込んでしまう
        r'(?P<string>"(?:[^"\\]|\\.)*")' # 文字列内にコメントと同じ表現がある時は文字列とみなして欲しい
    )
    pat_sub = re.compile(pattern)
    index = substring_start = 0
    replaced_string = ''
    while index < len(string):
        s = pat.search(string, pos = index)
        if s is None:
            replaced_string += pat_sub.sub(repl, string[substring_start:])
            break
        if s.lastgroup == 'string':
            index = s.end()
            continue
        if substring_start != s.start():
            replaced_string += pat_sub.sub(repl, string[substring_start:s.start()])
        replaced_string += s.group()
        index = substring_start = s.end()
    return replaced_string

def re_sub_in_comments(pattern, repl, string):
    pat = re.compile(
        r'(?P<line_comment>//.*)' '|'
        r'(?P<block_comment>/\*[\s\S]*?\*/)' '|' # [\s\S]*?の?がないと\*/も[\s\S]*が取り込んでしまう
        r'(?P<string>"(?:[^"\\]|\\.)*")' # 文字列内にコメントと同じ表現がある時は文字列とみなして欲しい
    )
    pat_sub = re.compile(pattern)
    index = substring_start = 0
    replaced_string = ''
    while index < len(string):
        s = pat.search(string, pos = index)
        if s is None:
            replaced_string += string[substring_start:]
            break
        if s.lastgroup == 'string':
            index = s.end()
            continue
        if substring_start != s.start():
            replaced_string += string[substring_start:s.start()]
        replaced_string += pat_sub.sub(repl, s.group())
        index = substring_start = s.end()
    return replaced_string

def re_findall_except_comments(pattern, string):
    pat = re.compile(
        r'(?P<line_comment>//.*)' '|'
        r'(?P<block_comment>/\*[\s\S]*?\*/)' '|' # [\s\S]*?の?がないと\*/も[\s\S]*が取り込んでしまう
        r'(?P<string>"(?:[^"\\]|\\.)*")' # 文字列内にコメントと同じ表現がある時は文字列とみなして欲しい
    )
    pat_findall = re.compile(pattern)
    index = substring_start = 0
    result = []
    while index < len(string):
        s = pat.search(string, pos = index)
        if s is None:
            result.extend(pat_findall.findall(string, pos = substring_start))
            break
        if s.lastgroup == 'string':
            index = s.end()
            continue
        if substring_start != s.start():
            result.extend(pat_findall.findall(string, pos = substring_start, endpos = s.start()))
        index = substring_start = s.end()
    return result

def re_findall_in_comments(pattern, string):
    pat = re.compile(
        r'(?P<line_comment>//.*)' '|'
        r'(?P<block_comment>/\*[\s\S]*?\*/)' '|' # [\s\S]*?の?がないと\*/も[\s\S]*が取り込んでしまう
        r'(?P<string>"(?:[^"\\]|\\.)*")' # 文字列内にコメントと同じ表現がある時は文字列とみなして欲しい
    )
    pat_findall = re.compile(pattern)
    index = 0
    result = []
    while index < len(string):
        s = pat.search(string, pos = index)
        if s is None:
            break
        if s.lastgroup != 'string':
            result.extend(pat_findall.findall(s.group()))
        index = s.end()
    return result

def find_element(path_list, parent, start = None, end = None, reverse = False, index_not_found = None):
    # path_list = [{'type': 'block', 'key': 'FoamFile'}, {'type': 'dictionary', 'key': 'version'}, ...]
    #   {'type': 'block_start|block_end'} -> 'type' is 'block_start' or 'block_end'
    #   {'except type': 'whitespace|semicolon'} -> 'type' is neither 'whitespace' nor 'semicolon'
    assert (start is None and end is None) or len(path_list) == 1
    if not isinstance(parent, list):
        parent = parent['value']
    if isinstance(path_list, dict):
        path_list = [path_list]
    elif len(path_list) == 0:
        return None
    p = {k: v.replace('ignorable', 'whitespace|linebreak|line_comment|block_comment').split('|')
        for k, v in path_list[0].items()}
    # next(..., None) とすることで、見つからない場合にエラーにならず None を返します
    # k.startswith('except ') = False -> (parent[i].get(k.replace('except ', '')) in p[k]) = True のものを抽出したい
    # k.startswith('except ') = True  -> (parent[i].get(k.replace('except ', '')) in p[k]) = Falseのものを抽出したい
    c = next(({'index': i, 'element': parent[i]} for i in range(
        (len(parent) - 1 if reverse else 0) if start is None else start,
        (-1 if reverse else len(parent)) if end is None else end,
        -1 if reverse else 1)
        if all((parent[i].get(k.replace('except ', '')) in p[k]) != k.startswith('except ')
            for k, v in p.items())), None)
    if c is None:
        return {'parent': None, 'index': index_not_found, 'element': None}
    elif len(path_list) == 1:
        return {'parent': parent, 'index': c['index'], 'element': c['element']}
    else:
        return find_element(path_list[1:], parent = c['element'], start = start, end = end, reverse = reverse,
            index_not_found = index_not_found)

def find_all_elements(path_list, parent):
    # path_list = [{'type': 'block', 'key': 'FoamFile'}, {'type': 'dictionary', 'key': 'version'}, ...]
    #   {'type': 'block_start|block_end'} -> 'type' is 'block_start' or 'block_end'
    #   {'except type': 'whitespace|semicolon'} -> 'type' is neither 'whitespace' nor 'semicolon'
    if not isinstance(parent, list):
        parent = parent['value']
    if isinstance(path_list, dict):
        path_list = [path_list]
    elif len(path_list) == 0:
        return []
    p = {k: v.replace('ignorable', 'whitespace|linebreak|line_comment|block_comment').split('|')
        for k, v in path_list[0].items()}
    # k.startswith('except ') = False -> (parent[i].get(k.replace('except ', '')) in p[k]) = True のものを抽出したい
    # k.startswith('except ') = True  -> (parent[i].get(k.replace('except ', '')) in p[k]) = Falseのものを抽出したい
    c = [{'index': i, 'element': parent[i]} for i in range(len(parent))
        if all((parent[i].get(k.replace('except ', '')) in p[k]) != k.startswith('except ')
            for k, v in path_list[0].items())]
    if len(c) == 0 or len(path_list) == 1:
        return [{'parent': parent, 'index': i['index'], 'element': i['element']} for i in c]
    else:
        elements = []
        for i in c:
            elements += find_all_elements(path_list[1:], i['element'])
        return elements

def set_blank_line(parent, number_of_blank_lines = 1):
    if isinstance(parent, list):
        if find_element([{'type': 'linebreak'}], parent)['element'] is None:
            return
        start = 0
        end = len(parent)
    else:
        if parent['type'] in ('block', 'list', 'dimension'):
            start = find_element([{'type': parent['type'] + '_start'}], parent = parent['value'])['index'] + 1
            end = find_element([{'type': parent['type'] + '_end'}], parent = parent['value'], reverse = True)['index']
            parent = parent['value']
            i = find_element([{'type': 'linebreak'}], parent = parent, start = start, end = end)
            if i['element'] is None:
                return
            start = i['index'] + 1
            i = find_element([{'except type': 'whitespace|linebreak'}], parent = parent, start = start, end = end)
            if i['element'] is not None:
                i = i['index']
                del parent[start:i]
                end += start - i
            if start != end:
                end = find_element([{'type': 'linebreak'}], parent = parent, start = end - 1, end = start - 1,
                    reverse = True)['index']
                i = find_element([{'except type': 'whitespace|linebreak'}], parent = parent, start = end - 1,
                    end = start - 1, reverse = True)
                if i['element'] is not None:
                    i = i['index'] + 1
                    del parent[i:end]
                    end = i
        else:
            if find_element([{'type': 'linebreak'}], parent['value'])['element'] is None:
                return
            parent = parent['value']
            start = 0
            end = len(parent)
    i = start
    while i < end:
        if (parent[i]['type'] == 'linebreak' and
            i > start and parent[i - 1]['type'] not in ('line_comment', 'block_comment')):
            linebreak = parent[i]
            if parent[i - 1]['type'] != 'linebreak':
                i += 1
            j = i
            while j < end and parent[j]['type'] in ('whitespace', 'linebreak'):
                j += 1
            parent[i:j] = number_of_blank_lines*[linebreak]
            end += i - j + number_of_blank_lines
            i += number_of_blank_lines
        else:
            i += 1

def structure_string(parent, parent_header = '', indent_level = 0):
    if not isinstance(parent, list):
        parent = parent['value']
    l = len(str(len(parent) - 1))
    h = ' '*l
    s = '[\n'
    indent = '  '*indent_level
    for n, i in enumerate(parent):
        s += f'{str(n).zfill(l)}: {indent}'
        if i['type'] in ('dictionary', 'block'):
            s += (f"{{'type': '{i['type']}', "  +
                (f"'key': '{i['key']}', " if 'key' in i else "") + 
                f"'value': {structure_string(i['value'], h, indent_level + 1)}}},\n")
        elif i['type'] == 'list':
            s += ("{'type': 'list', " +
                (f"'length': {i['length']}, " if 'length' in i else "") +
                f"'value': {structure_string(i['value'], h, indent_level + 1)}}},\n")
        else:
            s += f'{i},\n'
    return s + (parent_header + '  ' + '  '*(indent_level - 1) if indent_level > 0 else '') + ']'

def file_string(parent, indent_level = 0, pretty_print = True, commentless = False):
    if not isinstance(parent, list):
        parent = parent['value']
    s = ''
    indent = '\t'*indent_level
    linebreak = False
    for i in parent:
        if pretty_print and linebreak: # 改行直後
            if (i['type'] == 'whitespace' or
                commentless and i['type'] in ('line_comment', 'block_comment')):
                continue
            elif i['type'] != 'linebreak':
                s += indent
        if i['type'] in ('block', 'list', 'dimension'):
            start = find_element([{'type': i['type'] + '_start'}], parent = i['value'])['index'] + 1
            end = find_element([{'type': i['type'] + '_end'}], parent = i['value'], reverse = True)['index']
            j = find_element([{'except type': 'whitespace'}], parent = i['value'], start = end - 1, end = start - 1,
                reverse = True)
            if j['element'] is not None:
                end = j['index'] if j['element']['type'] == 'linebreak' else len(i['value'])
                s += (i.get('key', '') + i.get('length', '') +
                    file_string(i['value'][:start], indent_level, pretty_print, commentless) +
                    file_string(i['value'][start:end], indent_level + 1, pretty_print, commentless) +
                    file_string(i['value'][end:], indent_level, pretty_print, commentless))
        else:
            if commentless and i['type'] == 'block_comment':
                if not s.endswith(' '):
                    s += ' '
            elif not commentless or i['type'] != 'line_comment':
                if isinstance(i['value'], list):
                    s += (i.get('key', '') + i.get('length', '') +
                        file_string(i['value'], indent_level, pretty_print, commentless))
                else:
                    s += i['value']
        linebreak = (i['type'] == 'linebreak')
    return s

class DictParser2:
    PATTERN = re.compile(
        # .      -> 改行（\n）以外の任意の1文字
        # [\s\S] -> 全ての文字
        r'(?P<line_comment>//.*)' '|'
        r'(?P<block_comment>/\*[\s\S]*?\*/)' '|' # [\s\S]*?の?がないと\*/も[\s\S]*が取り込んでしまう
        r'(?P<code>#\{[\s\S]*?#\})' '|' # block_startよりも前！
        r'(?P<string>"(?:[^"\\]|\\.)*")' '|'
        r'(?P<directive>#[^{}][a-zA-Z]*)' '|'
        r'(?P<word>(?:[a-zA-Z_$](?:[a-zA-Z0-9_.:,*]|/(?![/*]))*(?:\([^\s\n;]*\))?)+)' '|'
        # /(?![/*])で行コメントやブロックコメントの始まりを排除
        # (?:\[^\s\n;]*\))?でfvSchemesのdiv((nuEff*dev(T(grad(U)))))なども捕獲
        r'(?P<float>[-+]?\d*(?:\.\d*(?:[eE][-+]?\d+)?|[eE][-+]?\d+))' '|' # integerよりも先！
        r'(?P<integer>[-+]?\d+)' '|' # floatよりも後！
        r'(?P<block_start>\{)' '|' # codeよりも後！
        r'(?P<block_end>\})' '|'
        r'(?P<list_start>\()' '|'
        r'(?P<list_end>\))' '|'
        r'(?P<dimension_start>\[)' '|'
        r'(?P<dimension_end>\])' '|'
        r'(?P<semicolon>;)' '|'
        r'(?P<whitespace>(?:[ \t]|\\\r?\n)+)' '|' # linebreakよりも前！
        r'(?P<linebreak>\r?\n)' '|' # whitespaceより後！
        r'(?P<equal>=)' '|'
        r'(?P<unknown>.)'
    )
    CLOSING_SYMBOL = {'block_end': '}', 'list_end': ')', 'dimension_end': ']'}

    def __init__(self, file_name = None, string = None):
        self.file_name = file_name
        if file_name is not None:
            with open(file_name, 'r') as f:
                self.string = f.read()
        else:
            self.string = string
        self.elements = self.elements_list()[0]

    def elements_list(self, index = 0, terminator = None, essentials_required = 0):
        # terminator = 'block_end' | 'list_end' | 'dimension_end' | 'reached'
        debug = False
        def raise_error(message, last_index):
            raise Exception('Error in parser' +
                ('' if self.file_name is None else ' (File: ' + os.path.basename(self.file_name) + ')') +
                ': ' + message + ' | ' + self.string[max(last_index - 20, 0): last_index])
        # ssss -> Python string.
        # @@@@ -> Essential words, such as word, string.
        # _scn -> Nonessential words, such as whitespace, comments, linebreak, which doesn't always exist.
        # _sc_ -> Nonessential words, such as whitespace, comments, which doesn't always exist.
        # -------------------------------------------------------
        #  type          |  pattern
        # -------------------------------------------------------
        #                | key     | value
        #                |---------------------------------------
        #  directive     | #ssss   | _scn @@@@ _sc_
        #                | #ssss   | _sc_
        #  dictionary    | ssss    | _scn @@@@ ... ; _sc_
        #                | ssss    | _scn          ; _sc_
        #  block         | ssss    | _scn { _scn @@@@ ... } _sc_
        #                |         |      { _scn @@@@ ... } _sc_
        # -------------------------------------------------------
        #                | length  | value
        #                |---------------------------------------
        #  list          | integer | _scn ( _scn @@@@ ... ) _sc_
        #                |         |      ( _scn @@@@ ... ) _sc_
        # -------------------------------------------------------
        #                |           value
        #                |---------------------------------------
        #  dimension     |           [ _scn @@@@ ... ] _sc_
        #  line_comment  |           //...
        #  block_comment |           /* ... */
        #  code          |           #{ ... #}
        #  string        |           " ... "
        #  word          |           word
        #  float         |           float string
        #  integer       |           integer string
        #  semicolon     |           ;
        #  equal         |           =
        #  whitespace    |           white space
        #  linebreak     |           line break
        #  separator     |           // * * ... * * //
        #                |           // *** ... *** //
        # -------------------------------------------------------
        if debug:
            print(f'elements_list from {index}, terminator = {terminator}, '
                f'essentials_required = {essentials_required}')
        l = []
        terminator_reached = True if terminator == 'reached' else False
        essentials = 0
        while index < len(self.string):
            s = self.PATTERN.search(self.string, pos = index)
            if debug:
                print(f'  [{s.start()}, {s.end()}) {s.lastgroup} "' +
                    s.group().replace('\r', r'\r').replace('\n', r'\n').replace('\t', r'\t') + '"')
            if terminator_reached and s.lastgroup not in ('whitespace', 'line_comment', 'block_comment'):
                if debug:
                    print('    return {}'.format(l))
                return l, s.start()
            if s.lastgroup == 'directive':
                if s.group() in ('#else', '#endif', '#merge', '#overwrite', '#protect', '#warn'):
                    v, index = self.elements_list(index = s.end(), terminator = 'reached')
                else:
                    v, index = self.elements_list(index = s.end(), essentials_required = 1)
                l.append({'type': s.lastgroup, 'key': s.group(), 'value': v})
                if debug:
                    print(f'    -> {l[-1]}')
            elif s.lastgroup == 'semicolon':
                dictionary = False
                for i in range(len(l)):
                    if l[i]['type'] in ('word', 'string'):
                        v, index = self.elements_list(index = s.end(), terminator = 'reached')
                        l[i:] = [{'type': 'dictionary', 'key': l[i]['value'],
                            'value': l[i + 1:] + [{'type': s.lastgroup, 'value': s.group()}] + v}]
                        dictionary = True
                        break
                if not dictionary: # meaningless semicolon
                    l.append({'type': s.lastgroup, 'value': s.group()})
                    index = s.end()
                if debug:
                    print(f'    -> {l[-1]}')
            elif s.lastgroup in ('block_start', 'list_start'):
                type_string = s.lastgroup[:-6]
                v, index = self.elements_list(index = s.end(), terminator = type_string + '_end')
                has_header = False
                for i in range(len(l) - 1, -1, -1):
                    if l[i]['type'] in ('whitespace', 'linebreak', 'line_comment', 'block_comment'):
                        continue
                    if type_string == 'block' and l[i]['type'] in ('word', 'string'):
                        l[i:] = [{'type': type_string, 'key': l[i]['value'],
                            'value': l[i + 1:] + [{'type': s.lastgroup, 'value': s.group()}] + v}]
                        has_header = True
                        break
                    if type_string == 'list' and l[i]['type'] == 'integer':
                        l[i:] = [{'type': type_string, 'length': int(l[i]['value']),
                            'value': l[i + 1:] + [{'type': s.lastgroup, 'value': s.group()}] + v}]
                        has_header = True
                        break
                if not has_header:
                    l.append({'type': type_string, 'value': [{'type': s.lastgroup, 'value': s.group()}] + v})
            elif s.lastgroup == 'dimension_start':
                v, index = self.elements_list(index = s.end(), terminator = 'dimension_end')
                l.append({'type': 'dimension', 'value': [{'type': s.lastgroup, 'value': s.group()}] + v})
            elif s.lastgroup in ('block_end', 'list_end', 'dimension_end'):
                if s.lastgroup != terminator:
                    raise_error('Inappropriate closing bracket, "' + self.CLOSING_SYMBOL[terminator] + '" is required.', s.end())
                l.append({'type': s.lastgroup, 'value': s.group()})
                index = s.end()
            elif s.lastgroup == 'unknown':
                raise_error('Unknown token "' + s.group() + '".', s.end())
            else:
                if s.lastgroup == 'line_comment' and re.match(r'// (?:\* ?)+//$', s.group()):
                    l.append({'type': 'separator', 'value': s.group()})
                else:
                    l.append({'type': s.lastgroup, 'value': s.group()})
                index = s.end()
            if s.lastgroup not in ('whitespace', 'linebreak', 'line_comment', 'block_comment'):
                essentials += 1
                if essentials == essentials_required:
                    terminator_reached = True
            if s.lastgroup == terminator:
                terminator_reached = True
        if not terminator_reached and terminator is not None:
            raise_error('Missing "' + self.CLOSING_SYMBOL[terminator] + '".', len(self.string))
        if debug:
            print(f'    return {l}')
        return l, index

    def find_separators(self, header_index_not_found = None, footer_index_not_found = None):
        separators = self.find_all_elements([{'type': 'separator'}])
        if len(separators) == 0:
            return [{'parent': None, 'index': header_index_not_found, 'element': None},
                {'parent': None, 'index': footer_index_not_found, 'element': None}] # header, footer
        if self.find_element([{'except type': 'ignorable'}],
            start = separators[-1]['index'] + 1)['element'] is not None:
            return [separators[0],
                {'parent': None, 'index': footer_index_not_found, 'element': None}] # header, footer
        return [{'parent': None, 'index': header_index_not_found, 'element': None}
            if len(separators) == 1 else separators[0], separators[-1]] # header, footer

    def find_element(self, path_list, start = None, end = None, reverse = False, index_not_found = None):
        return find_element(path_list, parent = self.elements, start = start, end = end, reverse = reverse,
            index_not_found = index_not_found)

    def find_all_elements(self, path_list):
        return find_all_elements(path_list, self.elements)

    def set_blank_line(self, number_of_blank_lines = 1):
        set_blank_line(self.elements, number_of_blank_lines)

    def structure_string(self, indent_level = 0):
        return structure_string(self.elements, indent_level)

    def file_string(self, indent_level = 0, pretty_print = True, commentless = False):
        return file_string(self.elements, indent_level, pretty_print, commentless)

if __name__ == '__main__':
#    normalize(file_name = sys.argv[1])
#    try:
#        dp = DictParser2(file_name = sys.argv[1])
#    except:
#        print(sys.exc_info())
#    print(dp.structure_string())
#    print(dp.file_string(pretty_print = True, commentless = False))
#    print(dp.structure_string())
#    set_blank_line(dp.find_element([{'type': 'block', 'key': 'functions'}])['element'], 3)
#    print(dp.file_string(pretty_print = True, commentless = False))
#    print([i['index']
#        for i in dp.find_all_elements([{'type': 'block', 'key': 'gradSchemes'}, {'type': 'dictionary'},
#            {'type': 'whitespace|linebreak|semicolon'}])])
#    print(dp.find_element([{'type': 'block', 'key': 'solvers'}, {'type': 'block'}]))
#    print([i['element']['key'] for i in dp.find_all_elements([{'type': 'block', 'key': 'solvers'}, {'type': 'block'}, {'type': 'dictionary'}])])
#    for i, e in enumerate(dp.find_element([{'type': 'block', 'key': 'solvers'}])[1]['value']):
#        print(i, e)
#    separators = dp.find_separators()
#    print([(s['index'], s['element']) for s in separators])
#    print(structure_string(DictParser2(string =
#        '#includeFunc surfaceFieldValue(name=inletFlux, patch=inlet, field=phi)'
#        #f'surfaceFile\t"{stl_2D_file_name}";\n'
#        ).elements))
#    dp2 = DictParser2(string =
#'''castellatedMeshControls
#{
#	features
#	(
#		{
#			file	"probe.extendedFeatureEdgeMesh";
#			level	1;
#		}
#	);
#}''')
#    print(dp2.structure_string())
#    print(dp2.find_element(
#                [{'type': 'block', 'key': 'castellatedMeshControls'},
#                {'type': 'dictionary', 'key': 'features'}, {'type': 'list'}, {'type': 'block'},
#                {'type': 'dictionary', 'key': 'level'}, {'type': 'integer'}])['element']['value'])
    dp2 = DictParser2(string = 'refine_left\n'
        '{\n'
		'\ttype	box;\n'
        '}; // (optional)\n')
    print(f'\t{file_string(dp2.elements, indent_level = 1)}')
