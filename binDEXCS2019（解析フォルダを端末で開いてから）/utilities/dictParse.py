#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dictParse.py
# by Yukiharu Iwamoto
# 2022/11/25 8:20:28 PM

import sys
import os
import re
if sys.version_info.major > 2:
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
        with open(file_name, 'w') as self.f:
            self.f.write(str(x))

    def writeFile(self, file_name, x = None, indent = '', last_char = '\n'):
        self.indent = indent
        self.last_char = last_char
        if x is None:
            x = self.contents
        with open(file_name, 'w') as self.f:
            self.writeContents(x, self.f)

    def writeContents(self, x, f):
        if type(x) is DictParserList:
            if x.type == DictParserList.BLOCK:
                self.writeContents(x[:2], f)
                self.writeContents('{', f)
                self.indent += '\t'
                self.writeContents(x[2], f)
                self.indent = self.indent[:-1]
                self.writeContents('}', f)
            elif x.type == DictParserList.DICT:
                self.writeContents(x[0], f)
                if ((x[1] == '' or x[1][0] not in ' \t\r\n') and
                    (x[1] != '' or len(x[2]) > 0 or x[3] != '')):
                    f.write('\t')
                    self.last_char = '\t'
                self.writeContents(x[1:], f)
                self.writeContents(';', f)
            elif x.type == DictParserList.LISTP:
                if x[0] != '':
                    self.writeContents(x[0], f)
                    f.write(x[1] + '(')
                    self.last_char = '('
                else:
                    self.writeContents('(', f)
                self.indent += '\t'
                self.writeContents(x[2], f)
                self.indent = self.indent[:-1]
                self.writeContents(')', f)
            elif x.type == DictParserList.LISTB:
                self.writeContents('[', f)
                self.indent += '\t'
                self.writeContents(x[:], f)
                self.indent = self.indent[:-1]
                self.writeContents(']', f)
            elif x.type in (DictParserList.INCLUDE, DictParserList.INCLUDE_ETC, DictParserList.CALC):
                self.writeContents('#include' if x.type == DictParserList.INCLUDE else
                    ('#includeEtc' if x.type == DictParserList.INCLUDE_ETC else '#calc'), f)
                self.writeContents(x[:], f)
        elif type(x) is list:
            for y in x:
                self.writeContents(y, f)
        elif x != '':
            if self.last_char in '\r\n':
                if x.strip() != '':
                    f.write(self.indent)
            elif self.last_char not in ' \t[{(' and x[0] not in ' \t\r\n]}):;,':
                x = ' ' + x
            if re.match('([ \\r\\n]*)/\*', x):
                x = re.sub('([\\r\\n]+)(?!$)', '\\1' + self.indent, x)
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
            if re.match('([ \\r\\n]*)/\*', x):
                x = re.sub('([\\r\\n]+)(?!$)', '\\1' + self.indent, x)
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

if __name__ == '__main__':
    file_name = sys.argv[1]
    base_name = os.path.basename(file_name)
    dp = DictParser(file_name = file_name)
    root, ext = os.path.splitext(base_name)
    dp.writeFileAsItIs(os.path.join(os.path.dirname(file_name), root + 'r' + ext))
    dp.writeFile(os.path.join(os.path.dirname(file_name), root + 'p' + ext))
#    index = dp.getIndexOfItem(['solvers', 'Phi'])
#    print('index = ' + str(index))
#    if index is not None:
#        print('item = ' + str(dp.getItemAtIndex(index[:-1])))
