#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dictParse.py
# by Yukiharu Iwamoto
# 2026/2/28 8:15:54 PM

import sys
import os
import re

if sys.version_info.major > 2: # DictParser
    import io

class DictParserList(list):
    BLOCK = 1
    #                                       0      1                2
    # DictParserList(DictParserList.BLOCK, [title, '/* comment */', [...]])
    #  type  0      1                2
    # [block|title, '/* comment */', [...]]
    # -> title /* comment */ {...}
    DICT = 2
    #                                      0    1                 2      3
    # DictParserList(DictParserList.DICT, [key, '/* comment1 */', [...], '/* comment2 */'])
    #  type 0    1                 2      3
    # [dict|key, '/* comment1 */', [...], '/* comment2 */']
    # -> key /* comment1 */ ... /* comment2 */ ;
    LISTP = 3
    #                                       0                1                2
    # DictParserList(DictParserList.LISTP, [number_of_items, '/* comment */', [...]])
    #  type  0                1                2
    # [listp|number_of_items, '/* comment */', [...]]
    # -> number_of_items /* comment */ (...)
    LISTB = 4
    #                                       0
    # DictParserList(DictParserList.LISTB, [...])
    #  type  0
    # [listb|...]
    # -> [...]
    INCLUDE = 5
    #                                         0                1
    # DictParserList(DictParserList.INCLUDE, ['/* comment */', '"file_name"'])
    #  type     0                1
    # [#include|'/* comment */', '"file_name"']
    # -> #include /* comment */ "file_name"
    INCLUDE_ETC = 6
    #                                             0                1
    # DictParserList(DictParserList.INCLUDE_ETC, ['/* comment */', '"file_name"'])
    #  type        0                1
    # [#includeEtc|'/* comment */', '"file_name"']
    # -> #includeEtc /* comment */ "file_name"
    CALC = 7
    #                                      0                1
    # DictParserList(DictParserList.CALC, ['/* comment */', '"equation"'])
    #  type  0                1
    # [#calc|'/* comment */', '"equation"']
    # -> #calc /* comment */ "equation"

    @classmethod
    def isType(cls, x, type_):
        if isinstance(type_, list):
            type_ = tuple(type_)
        elif not isinstance(type_, tuple):
            type_ = (type_,)
        return True if type(x) is cls and x.type in type_ else False

    def __init__(self, type_, items = []):
        super(DictParserList, self).__init__()
        if isinstance(items, tuple):
            items = list(items)
        elif not isinstance(items, list):
            items = [items]
        self.type = type_
        self.extend(items)
        if self.type in (DictParserList.BLOCK, DictParserList.DICT, DictParserList.LISTP):
            if isinstance(self[2], tuple):
                self[2] = list(self[2])
            elif not isinstance(self[2], list):
                self[2] = [self[2]]

    def key(self):
        if self.type in (DictParserList.BLOCK, DictParserList.DICT):
            return self[0]
        elif self.type == DictParserList.INCLUDE:
            return '#include'
        elif self.type == DictParserList.INCLUDE_ETC:
            return '#includeEtc'
        elif self.type == DictParserList.CALC:
            return '#calc'
        else:
            return None

    def setKey(self, key):
        if self.type in (DictParserList.BLOCK, DictParserList.DICT):
            self[0] = key

    def valueIndex(self):
        if self.type in (DictParserList.BLOCK, DictParserList.DICT, DictParserList.LISTP):
            return 2
        elif self.type == DictParserList.LISTB:
            return None
        else:
            return 1

    def value(self):
        return self[self.valueIndex()] if self.valueIndex is not None else self[:]

    def setValue(self, value):
        if self.type in (DictParserList.BLOCK, DictParserList.DICT,
            DictParserList.LISTP, DictParserList.LISTB):
            if isinstance(value, tuple):
                value = list(value)
            elif not isinstance(value, list):
                value = [value]
            i = self.valueIndex()
            if i is not None:
                self[i] = value
            else:
                self[:] = value
        else:
            self[self.valueIndex()] = value

    def __str__(self):
        if self.type == DictParserList.BLOCK:
            s = '[block|'
        elif self.type == DictParserList.DICT:
            s = '[dict|'
        elif self.type == DictParserList.LISTP:
            s = '[listp|'
        elif self.type == DictParserList.LISTB:
            s = '[listb|'
        elif self.type == DictParserList.INCLUDE:
            s = '[#include|'
        elif self.type == DictParserList.INCLUDE_ETC:
            s = '[#includeEtc|'
        elif self.type == DictParserList.CALC:
            s = '[#calc|'
        if len(self) > 0:
            s += repr(self[0])
            for x in self[1:]:
                s += ', ' + repr(x)
        return s + ']'

    def __repr__(self):
        return self.__str__()

class DictParser:
    def __init__(self, file_name = None, string = None):
        try:
            self.n_line = 0 # 行番号
            self.index = 0 # 列番号
            if file_name is not None:
                with open(file_name, 'r') as self.f:
                    self.line = self.f.readline()
                    self.contents = self.structureExpression()
            else:
                self.f = string.splitlines(True)
                self.line = self.f[self.n_line] if self.n_line < len(self.f) else ''
                self.contents = self.structureExpression()
        except ValueError as e:
            if type(self.f) is (file if sys.version_info.major <= 2 else io.TextIOWrapper):
                print('File "{}", line {}'.format(file_name, self.n_line + 1))
            else:
                print('String, line {}'.format(self.n_line + 1))
            print(self.line.rstrip())
            print(' '*(self.index - 1) + '^')
            print('Error: {}'.format(e.message))
            sys.exit(1)
        except:
            print(sys.exc_info())
            sys.exit(1)

    def structureExpression(self, terminator = ''):
        x = []
        stack = []
        while True:
            if len(stack) == 0:
                x.append(self.returnCommentExpression(ignore = ';'))
            if self.token in terminator or self.token == '':
                x.extend(stack)
                if len(x) > 0 and x[0] == '':
                    del x[0]
                if len(x) > 0 and x[-1] == '':
                    del x[-1]
                return x
            elif self.token == '{':
                if len(stack) == 0:
                    stack.extend(['', ''])
                elif len(stack) == 1:
                    stack.append('')
#                if len(stack) < 2:
#                    raise ValueError('No title in block.')
                x.extend(stack[:-2])
                x.append(DictParserList(DictParserList.BLOCK,
                    [stack[-2], stack[-1], self.structureExpression(terminator = '}')]))
                del stack[:]
                if self.token != '}':
                    raise ValueError('Unterminated block.')
            elif self.token == ';':
                if len(stack) >= 4:
                    x.append(DictParserList(DictParserList.DICT,
                        [stack[0], stack[1], stack[2:-1], stack[-1]]))
                elif len(stack) == 2:
                    x.append(DictParserList(DictParserList.DICT,
                        [stack[0], stack[1], [], '']))
                else:
                    raise ValueError('Invalid structure in dictionary.')
                del stack[:]
            elif self.token == '(':
                if len(stack) >= 2 and type(stack[-2]) is str and stack[-2].isdigit():
                    if (type(stack[-1]) != str or
                        stack[-1] != '' and stack[-1][0] not in '\r\n/'):
                        raise ValueError('Invalid structure in list.')
                    stack.append(DictParserList(DictParserList.LISTP,
                        [stack[-2], stack[-1], self.structureExpression(terminator = ')')]))
                    del stack[-3:-1]
                else:
                    stack.append(DictParserList(DictParserList.LISTP,
                        ['', '', self.structureExpression(terminator = ')')]))
                if self.token != ')':
                    raise ValueError('Unterminated list.')
                stack.append(self.returnCommentExpression()) # should be called when len(stack) > 0
            elif self.token == '[':
                stack.append(DictParserList(DictParserList.LISTB, self.structureExpression(terminator = ']')))
                if self.token != ']':
                    raise ValueError('Unterminated list.')
                stack.append(self.returnCommentExpression()) # should be called when len(stack) > 0
            elif self.token in ('#include', '#includeEtc'):
                x.extend(stack)
                del stack[:]
                y = DictParserList(DictParserList.INCLUDE if self.token == '#include'
                    else DictParserList.INCLUDE_ETC, [self.returnCommentExpression()])
                if self.token in '{}()[];':
                    raise ValueError('Invalid structure in "' + self.token + '" directive.')
                if self.token[0] != '"':
                    self.token = '"' + self.token # correction
                if self.token[-1] != '"':
                    self.token += '"' # correction
                y.append(self.token)
                x.append(y)
            elif self.token == '#calc':
                y = DictParserList(DictParserList.CALC, [self.returnCommentExpression()])
                if self.token in '{}()[];':
                    raise ValueError('Invalid structure in "#calc" directive.')
                if self.token[0] != '"':
                    self.token = '"' + self.token # correction
                if self.token[-1] != '"':
                    self.token += '"' # correction
                y.append(self.token)
                stack.append(y)
                stack.append(self.returnCommentExpression()) # should be called when len(stack) > 0
            else:
                stack.append(self.token)
                stack.append(self.returnCommentExpression())

    def returnCommentExpression(self, ignore = ''):
        x = ''
        self.token = self.nextToken()
        while True:
            if self.token == '':
                return x
            elif self.token in ignore:
                pass
            elif self.token[0] in '\r\n':
                x += self.token
            elif self.token[0] == '/':
                if x != '' and x[-1] not in '\n\t':
                    x += ' '
                x += self.token
            else:
                return x
            self.token = self.nextToken()

    def nextToken(self):
        while True:
            token = self.nextChar()
            if token == '': # EOF
                return token
            elif token not in ' \t':
                break
        if token in '{}()[];\r\n':
            return token
        elif token == '/':
            token += self.nextChar()
            if token == '/*': # block comment
                while True:
                    c = self.nextChar()
                    if c == '': # EOF
                        return token + '*/' # correction
                    if token[-1] not in '\r\n' or c not in ' \t':
                        token += c
                    if token[-2:] == '*/':
                        return token
            elif token == '//': # inline comment
                while True:
                    c = self.nextChar()
                    token += c
                    if c in '\r\n': # includes c == ''
                        return token
            else:
                raise ValueError('Invalid token "{}".'.format(token))
        elif token == '"': # string
            while True:
                c = self.nextChar()
                if c == '': # EOF
                    return token + '"' # correction
                token += c
                if token[-2:-1] != '\\' and c == '"':
                    return token
        else:
            while True:
                c = self.nextChar()
                if c in ' \t': # includes c == ''
                    return token
                elif c in '{}()[];\r\n/"':
                    if not token.isdigit() and c == '(': 
                        token += c # function
                        while True:
                            c = self.nextChar()
                            if c in ' \t': # includes c == ''
                                break
                            elif c in ';\r\n':
                                self.index -= 1
                                break
                            token += c
                        if not token.endswith(')'):
                            token += ')' # correction
                    elif token == '#' and c == '{': 
                        token += c # coded block
                        while True:
                            c = self.nextChar()
                            if c == '': # EOF
                                token += '#}' # correction
                                break
                            token += c
                            if token[-2:] == '#}':
                                break
                    else:
                        self.index -= 1
                    return token
                token += c

    def nextChar(self):
        while True:
            if self.line == '': # EOF
                return self.line
            elif self.index >= len(self.line):
                self.n_line += 1
                if type(self.f) is (file if sys.version_info.major <= 2 else io.TextIOWrapper):
                    self.line = self.f.readline()
                else:
                    self.line = self.f[self.n_line] if self.n_line < len(self.f) else ''
                self.index = 0
            else:
                c = self.line[self.index]
                self.index += 1
                return c

    def writeFileAsItIs(self, file_name, x = None):
        if x is None:
            x = self.contents
        with open(file_name, 'w') as f:
            f.write(str(x))

    def writeFile(self, file_name, x = None, indent = '', last_char = '\n'):
        if x is None:
            x = self.contents
        with open(file_name, 'w') as f:
            self.writeContents(x, f, indent, last_char)

    def writeContents(self, x, f, indent = '', last_char = '\n'):
        self.indent = indent
        self.last_char = last_char
        self.writeContent(x, f)

    def writeContent(self, x, f):
        if type(x) is DictParserList:
            if x.type == DictParserList.BLOCK:
                self.writeContent(x[:2], f)
                self.writeContent('{', f)
                self.indent += '\t'
                self.writeContent(x[2], f)
                self.indent = self.indent[:-1]
                self.writeContent('}', f)
            elif x.type == DictParserList.DICT:
                self.writeContent(x[0], f)
                if ((x[1] == '' or x[1][0] not in ' \t\r\n') and
                    (x[1] != '' or len(x[2]) > 0 or x[3] != '')):
                    f.write('\t')
                    self.last_char = '\t'
                self.writeContent(x[1:], f)
                self.writeContent(';', f)
            elif x.type == DictParserList.LISTP:
                if x[0] != '':
                    self.writeContent(x[0], f)
                    f.write(x[1] + '(')
                    self.last_char = '('
                else:
                    self.writeContent('(', f)
                self.indent += '\t'
                self.writeContent(x[2], f)
                self.indent = self.indent[:-1]
                self.writeContent(')', f)
            elif x.type == DictParserList.LISTB:
                self.writeContent('[', f)
                self.indent += '\t'
                self.writeContent(x[:], f)
                self.indent = self.indent[:-1]
                self.writeContent(']', f)
            elif x.type in (DictParserList.INCLUDE, DictParserList.INCLUDE_ETC, DictParserList.CALC):
                self.writeContent('#include' if x.type == DictParserList.INCLUDE else
                    ('#includeEtc' if x.type == DictParserList.INCLUDE_ETC else '#calc'), f)
                self.writeContent(x[:], f)
        elif type(x) is list:
            for y in x:
                self.writeContent(y, f)
        elif x != '':
            if self.last_char in '\r\n':
                if x.strip() != '':
                    f.write(self.indent)
            elif self.last_char not in ' \t[{(' and x[0] not in ' \t\r\n]}):;,':
                x = ' ' + x
            if re.match(r'([ \r\n]*)/\*', x):
                x = re.sub(r'([\r\n]+)(?!$)', r'\1' + self.indent, x)
            f.write(x)
            self.last_char = x[-1]

    def toString(self, x = None, indent = '', last_char = '\n'):
        if x is None:
            x = self.contents
        self.indent = indent
        self.last_char = last_char
        return self.contentsToString(x)

    def contentsToString(self, x):
        s = ''
        if type(x) is DictParserList:
            if x.type == DictParserList.BLOCK:
                s += self.contentsToString(x[:2])
                s += self.contentsToString('{')
                self.indent += '\t'
                s += self.contentsToString(x[2])
                self.indent = self.indent[:-1]
                s += self.contentsToString('}')
            elif x.type == DictParserList.DICT:
                s += self.contentsToString(x[0])
                if ((x[1] == '' or x[1][0] not in ' \t\r\n') and
                    (x[1] != '' or len(x[2]) > 0 or x[3] != '')):
                    s += '\t'
                    self.last_char = '\t'
                s += self.contentsToString(x[1:])
                s += self.contentsToString(';')
            elif x.type == DictParserList.LISTP:
                if x[0] != '':
                    s += self.contentsToString(x[0])
                    s += x[1] + '('
                    self.last_char = '('
                else:
                    s += self.contentsToString('(')
                self.indent += '\t'
                s += self.contentsToString(x[2])
                self.indent = self.indent[:-1]
                s += self.contentsToString(')')
            elif x.type == DictParserList.LISTB:
                s += self.contentsToString('[')
                self.indent += '\t'
                s += self.contentsToString(x[:])
                self.indent = self.indent[:-1]
                s += self.contentsToString(']')
            elif x.type in (DictParserList.INCLUDE, DictParserList.INCLUDE_ETC, DictParserList.CALC):
                s += self.contentsToString('#include' if x.type == DictParserList.INCLUDE else
                    ('#includeEtc' if x.type == DictParserList.INCLUDE_ETC else '#calc'))
                s += self.contentsToString(x[:])
        elif type(x) is list:
            for y in x:
                s += self.contentsToString(y)
        elif x != '':
            if self.last_char == '\r' or self.last_char == '\n':
                if x.strip() != '':
                    s += self.indent
            elif self.last_char not in ' \t[{(' and x[0] not in ' \t\r\n]}):;,':
                x = ' ' + x
            if re.match(r'([ \r\n]*)/\*', x):
                x = re.sub(r'([\r\n]+)(?!$)', r'\1' + self.indent, x)
            s += x
            self.last_char = x[-1]
        return s

    def getDPLForKey(self, key_list): # zero length is also possible
        index_list = self.getIndexOfItem(key_list)
        if index_list is None:
            return index_list
        return self.getItemAtIndex(index_list[:-1])

    def getValueForKey(self, key_list): # zero length is also possible
        x = self.getDPLForKey(key_list)
        return x.value() if x is not None else x

    def setValueForKey(self, key_list, value):
        x = self.getDPLForKey(key_list)
        if x is not None:
            x.setValue(value)

    def deleteDictWithKey(self, key_list):
        index_list = self.getIndexOfItem(key_list)
        if index_list is None:
            return
        del self.getItemAtIndex(index_list[:-2])[index_list[-2]]

    def getItemAtIndex(self, index_list):
        if isinstance(index_list, tuple):
            index_list = list(index_list)
        elif not isinstance(index_list, list):
            index_list = [index_list]
        if len(index_list) > 0 and index_list[0] is None:
            return None
        x = self.contents
        for i in index_list:
            x = x[i]
        return x

    def getIndexOfItem(self, word_list, x = None):
        if isinstance(word_list, tuple):
            word_list = list(word_list)
        elif not isinstance(word_list, list):
            word_list = [word_list]
        if x is None:
            x = self.contents
        if len(x) == 0 or len(word_list) == 0:
            return None # returns index list, e.g. [0, 9, 4] or None
        if type(x) is DictParserList:
            if x.type in (DictParserList.BLOCK, DictParserList.DICT):
                if x[0] == word_list[0]:
                    if len(word_list) == 1:
                        return [0]
                    else:
                        j = self.getIndexOfItem(word_list[1:], x[2])
                        if j is not None:
                            j.insert(0, 2)
                            return j
            elif x.type == DictParserList.LISTP:
                j = self.getIndexOfItem(word_list, x[2])
                if j is not None:
                    j.insert(0, 2)
                    return j
            elif x.type == DictParserList.LISTB:
                j = self.getIndexOfItem(word_list, x[0])
                if j is not None:
                    j.insert(0, 0)
                    return j
            elif x.type in (DictParserList.INCLUDE, DictParserList.INCLUDE_ETC, DictParserList.CALC):
                k = ('#include' if x.type == DictParserList.INCLUDE else
                    ('#includeEtc' if x.type == DictParserList.INCLUDE_ETC else '#calc'))
                if k == word_list[0]:
                    if len(word_list) == 1:
                        return []
                    elif len(word_list) == 2 and x[1] == word_list[1]:
                        return [1]
        else:
            for i, y in enumerate(x):
                if type(y) is DictParserList or type(y) is list:
                    j = self.getIndexOfItem(word_list, y)
                    if j is not None:
                        j.insert(0, i)
                        return j
                elif y == word_list[0] and len(word_list) == 1:
                    return [i]
        return None

    def searchString(self, regexp, x = None):
        if type(regexp) != str:
            regexp = str(regexp)
        if x is None:
            x = self.contents
        p = re.compile(regexp)
        for i, y in enumerate(x):
            if type(y) is DictParserList or type(y) is list:
                j = self.searchString(regexp, y)
                if j is not None:
                    j.insert(0, i)
                    return j
            elif p.search(y) is not None:
                return [i]
        return None # returns index list, e.g. [0, 9, 4] or None

# ------------------------------------------------------------------------------

def normalize(file_name = None, string = None, overwrite_file = True):
    if file_name is not None:
        with open(file_name, 'r') as f:
            string = f.read()
    if sys.version_info.major <= 2:
        normalized_string = re.sub(u'[ \\t]+(?=\\r?\\n|$)', '', # 末尾の空白を削除
            re.sub(u'(?<=[;{}()\\[\\]][ \\t])[ \\t]+(?=\\S)', '', # セミコロン，かっこの後ろの余計なスペースを削除
            re.sub(u'[！-～]', lambda m: unichr(ord(m.group(0)) - 0xFEE0), # 全角英数字・記号を半角に変換
            string.decode('UTF-8').replace(u'　', u' '), # 全角スペースを半角に
            flags = re.U))).encode('UTF-8')
        pass
    else:
        normalized_string = re.sub(r'[ \t]+(?=\r?\n|$)', '', # 末尾の空白を削除
            re.sub(r'(?<=[;{}()\[\]][ \t])[ \t]+(?=\S)', '', # セミコロン，かっこの後ろの余計なスペースを削除
            re.sub('[！-～]', lambda m: chr(ord(m.group(0)) - 0xFEE0), # 全角英数字・記号を半角に変換
            string.replace('　', ' '), # 全角スペースを半角に
            flags = re.U)))
    changed = normalized_string != string
    if file_name is not None and overwrite_file and changed:
        with open(file_name, 'w') as f:
            f.write(normalized_string)
    return normalized_string, changed

def find_element(path_list, parent, reverse = False):
    # path_list = [{'type': 'block', 'key': 'FoamFile'}, {'type': 'dictionary', 'key': 'version'}, ...]
    #   {'type': 'block_start|block_end'} -> 'type' is 'block_start' or 'block_end'
    #   {'except type': 'whitespace|semicolon'} -> 'type' is neither 'whitespace' nor 'semicolon'
    if not isinstance(parent, list):
        parent = parent['value']
    if isinstance(path_list, dict):
        path_list = [path_list]
    elif len(path_list) == 0:
        return None
    # next(..., None) とすることで、見つからない場合にエラーにならず None を返します
    c = next(({'index': i, 'element': parent[i]} for i in
        (range(len(parent) -1 , -1, -1) if reverse else range(len(parent)))
        if all(parent[i].get(k[7:]) not in v.split('|') if k.startswith('except ') else parent[i].get(k) in v.split('|')
        for k, v in path_list[0].items())), None)
    if c is None:
        return None
    elif len(path_list) == 1:
        return {'parent': parent, 'index': c['index'], 'element': c['element']}
    else:
        return find_element(path_list[1:], c['element'], reverse)

def find_all_elements(path_list, parent, reverse = False):
    # path_list = [{'type': 'block', 'key': 'FoamFile'}, {'type': 'dictionary', 'key': 'version'}, ...]
    #   {'type': 'block_start|block_end'} -> 'type' is 'block_start' or 'block_end'
    #   {'except type': 'whitespace|semicolon'} -> 'type' is neither 'whitespace' nor 'semicolon'
    if not isinstance(parent, list):
        parent = parent['value']
    if isinstance(path_list, dict):
        path_list = [path_list]
    elif len(path_list) == 0:
        return []
    c = [{'index': i, 'element': parent[i]} for i in
        (range(len(parent) -1 , -1, -1) if reverse else range(len(parent)))
        if all(parent[i].get(k[7:]) not in v.split('|') if k.startswith('except ') else parent[i].get(k) in v.split('|')
        for k, v in path_list[0].items())]
    if len(c) == 0 or len(path_list) == 1:
        return [{'parent': parent, 'index': i['index'], 'element': i['element']} for i in c]
    else:
        elements = []
        for i in c:
            elements += find_all_elements(path_list[1:], i['element'], reverse)
            return elements

def set_blank_line(parent, number_of_blank_lines = 1):
    if isinstance(parent, list):
        start = 0
        end = len(parent)
    else:
        if parent['type'] in ('block', 'list', 'dimension'):
            start = find_element([{'type': parent['type'] + '_start'}], parent['value'])['index'] + 1
            end = find_element([{'type': parent['type'] + '_end'}], parent['value'], reverse = True)['index'] - 1
            parent = parent['value']
            if parent[start]['type'] == 'linebreak':
                while start + 1 < len(parent) and parent[start + 1]['type'] in ('linebreak', 'whitespace'):
                    del parent[start + 1]
                    end -= 1
                start += 1
            if parent[end]['type'] == 'linebreak':
                while end - 1 > 0 and parent[end - 1]['type'] in ('linebreak', 'whitespace'):
                    del parent[end - 1]
                    end -= 1
        else:
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
            while j < end and parent[j]['type'] in ('linebreak', 'whitespace'):
                j += 1
            parent[i:j] = number_of_blank_lines*[linebreak]
            end += i - j + number_of_blank_lines
            i += number_of_blank_lines
        else:
            i += 1

def structure_string(parent, indent_level = 0):
    if not isinstance(parent, list):
        parent = parent['value']
    l = len(str(len(parent) - 1))
    s = '[\n'
    indent = '    '*(indent_level + 1)
    for n, i in enumerate(parent):
        if i['type'] in ('dictionary', 'block'):
            s += (str(n).zfill(l) + ': ' + indent + "{'type': '" + i['type'] + "', " +
                ("'key': '" + i['key'] + "', " if 'key' in i else "") + 
                "'value': " + structure_string(i['value'], indent_level + 1) + "},\n")
        elif i['type'] == 'list':
            s += (str(n).zfill(l) + ': ' + indent + "{'type': 'list', " +
                ("'length': {}, ".format(i['length']) if 'length' in i else "") +
                "'value': " + structure_string(i['value'], indent_level + 1) + "},\n")
        else:
            s += str(n).zfill(l) + ': ' + indent + str(i) + ',\n'
    return s + '    '*indent_level + ']'

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
            start = find_element([{'type': i['type'] + '_start'}], i['value'])['index'] + 1
            end = find_element([{'type': i['type'] + '_end'}], i['value'], reverse = True)['index'] - 1
            s += (i.get('key', '') + i.get('length', '') +
                file_string(i['value'][:start], indent_level, pretty_print, commentless) +
                file_string(i['value'][start: end], indent_level + 1, pretty_print, commentless) +
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
        r'(?P<string>"([^"\\]|\\.)*")' '|'
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
        self.elements = self.elements_list(index = 0, terminator = None)[0]

    def elements_list(self, index, terminator = None, essentials_required = 0):
        # terminator = 'block_end' | 'list_end' | 'dimension_end' | 'reached'
        debug = False
        def raise_error(message, last_index):
            raise Exception('Error in parser' +
                ('' if self.file_name is None else ' (File: ' + os.path.basename(self.file_name) + ')') +
                ': ' + message + ' | ' + self.string[max(last_index - 20, 0): last_index])
        # word -> Essential words, such as word, string.
        # IIII -> Nonessential words, such as whitespace, comments, linebreak, which doesn't always exist.
        # JJJJ -> Nonessential words, such as whitespace, comments, which doesn't always exist.
        # -------------------------------------------------------
        #  type          |  pattern
        # -------------------------------------------------------
        #                | key     | value
        #                |---------------------------------------
        #  directive     | #SSSS   | IIII SSSS JJJJ
        #                | #SSSS   | IIII
        #  dictionary    | SSSS    | IIII SSSS ... ; JJJJ
        #                | SSSS    | IIII          ; JJJJ
        #  block         | SSSS    | IIII { IIII SSSS ... } JJJJ
        #                |         |      { IIII SSSS ... } JJJJ
        # -------------------------------------------------------
        #                | length  | value
        #                |---------------------------------------
        #  list          | integer | IIII ( IIII SSSS ... ) JJJJ
        #                |         |      ( IIII SSSS ... ) JJJJ
        # -------------------------------------------------------
        #                |           value
        #                |---------------------------------------
        #  dimension     |           [ IIII SSSS ... ] JJJJ
        #  line_comment  |           //...
        #  block_comment |           /* ... */
        #  code          |           #{ ... #}
        #  string        |           " ... "
        #  word          |           word
        #  float         |           float string
        #  integer       |           integer string
        #  semicolon     |           ;
        #  whitespace    |           white space
        #  linebreak     |           line break
        #  separator     |           // * * ... * * //
        #                |           // *** ... *** //
        # -------------------------------------------------------
        if debug:
            print('elements_list from {}, terminator = {}, essentials_required = {}'.format(
                index, terminator, essentials_required))
        l = []
        terminator_reached = True if terminator == 'reached' else False
        essentials = 0
        while index < len(self.string):
            s = self.PATTERN.search(self.string, pos = index)
            if debug:
                print('  [{}, {}) '.format(s.start(), s.end()) + s.lastgroup + ' "' +
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
                    print('    -> {}'.format(l[-1]))
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
                    print('    -> {}'.format(l[-1]))
            elif s.lastgroup in ('block_start', 'list_start'):
                type_string = s.lastgroup[:-6]
                v, index = self.elements_list(index = s.end(), terminator = type_string + '_end')
                if len(l) > 0:
                    for i in range(len(l) - 1, -1, -1):
                        if l[i]['type'] not in ('line_comment', 'block_comment', 'whitespace', 'linebreak'):
                            if type_string == 'block' and l[i]['type'] in ('word', 'string'):
                                l[i:] = [{'type': type_string, 'key': l[i]['value'],
                                    'value': l[i + 1:] + [{'type': s.lastgroup, 'value': s.group()}] + v}]
                            elif type_string == 'list' and l[i]['type'] == 'integer':
                                l[i:] = [{'type': type_string, 'length': int(l[i]['value']),
                                    'value': l[i + 1:] + [{'type': s.lastgroup, 'value': s.group()}] + v}]
                            else:
                                l.append({'type': type_string, 'value': [{'type': s.lastgroup, 'value': s.group()}] + v})
                            break
                else:
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
                if s.lastgroup == 'line_comment' and re.match(r'^// (?:\* ?)+//$', s.group()):
                    l.append({'type': 'separator', 'value': s.group()})
                else:
                    l.append({'type': s.lastgroup, 'value': s.group()})
                index = s.end()
            if s.lastgroup not in ('line_comment', 'block_comment', 'whitespace', 'linebreak'):
                essentials += 1
                if essentials == essentials_required:
                    terminator_reached = True
            if s.lastgroup == terminator:
                terminator_reached = True
        if not terminator_reached and terminator is not None:
            raise_error('Missing "' + self.CLOSING_SYMBOL[terminator] + '".', len(self.string))
        if debug:
            print('    return {}'.format(l))
        return l, index

    def find_separators(self):
        separators = self.find_all_elements([{'type': 'separator'}])
        if len(separators) == 0:
            return [None, None] # header, footer
        for i in separators[-1]['parent'][separators[-1]['index'] + 1:]:
            if i['type'] not in ('line_comment', 'block_comment', 'whitespace', 'linebreak'):
                return [separators[0], None] # header, footer
        return [None if len(separators) == 1 else separators[0], separators[-1]] # header, footer

    def find_element(self, path_list, reverse = False):
        return find_element(path_list, self.elements, reverse)

    def find_all_elements(self, path_list, reverse = False):
        return find_all_elements(path_list, self.elements, reverse)

    def set_blank_line(self, number_of_blank_lines = 1):
        set_blank_line(self.elements, number_of_blank_lines)

    def structure_string(self, indent_level = 0):
        return structure_string(self.elements, indent_level)

    def file_string(self, indent_level = 0, pretty_print = True, commentless = False):
        return file_string(self.elements, indent_level, pretty_print, commentless)

if __name__ == '__main__':
#    file_name = sys.argv[1]
#    base_name = os.path.basename(file_name)
#    dp = DictParser(file_name = file_name)
#    root, ext = os.path.splitext(base_name)
#    dp.writeFileAsItIs(os.path.join(os.path.dirname(file_name), root + 'r' + ext))
#    dp.writeFile(os.path.join(os.path.dirname(file_name), root + 'p' + ext))
#    index = dp.getIndexOfItem(['solvers', 'Phi'])
#    print('index = ' + str(index))
#    if index is not None:
#        print('item = ' + str(dp.getItemAtIndex(index[:-1])))

# ------------------------------------------------------------------------------

    normalize(file_name = sys.argv[1])
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
#            {'type': 'whitespace|semicolon|linebreak'}])])
#    print(dp.find_element([{'type': 'block', 'key': 'solvers'}, {'type': 'block'}]))
#    print([i['element']['key'] for i in dp.find_all_elements([{'type': 'block', 'key': 'solvers'}, {'type': 'block'}, {'type': 'dictionary'}])])
#    for i, e in enumerate(dp.find_element([{'type': 'block', 'key': 'solvers'}])[1]['value']):
#        print(i, e)
#    separators = dp.find_separators()
#    print([(s['index'], s['element']) for s in separators])
