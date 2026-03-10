#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dakuten.py
# by Yukiharu Iwamoto
# 2022/6/22 2:03:43 PM

import os
import glob
import sys
import chardet
import codecs

def decode_if_necessary(s):
    return s.decode('CP932' if sys.platform == 'win32' else 'UTF-8') if sys.version_info.major <= 2 else s

def divide_dakuten(ustr):
    if sys.version_info.major <= 2 and type(ustr) is str:
        ustr = ustr.decode('UTF-8')
    dict3099 = {
        u'が': u'か', u'ぎ': u'き', u'ぐ': u'く', u'げ': u'け', u'ご': u'こ',
        u'ざ': u'さ', u'じ': u'し', u'ず': u'す', u'ぜ': u'せ', u'ぞ': u'そ',
        u'だ': u'た', u'ぢ': u'ち', u'づ': u'つ', u'で': u'て', u'ど': u'と',
        u'ば': u'は', u'び': u'ひ', u'ぶ': u'ふ', u'べ': u'へ', u'ぼ': u'ほ',
        u'ガ': u'カ', u'ギ': u'キ', u'グ': u'ク', u'ゲ': u'ケ', u'ゴ': u'コ',
        u'ザ': u'サ', u'ジ': u'シ', u'ズ': u'ス', u'ゼ': u'セ', u'ゾ': u'ソ',
        u'ダ': u'タ', u'ヂ': u'チ', u'ヅ': u'ツ', u'デ': u'テ', u'ド': u'ト',
        u'バ': u'ハ', u'ビ': u'ヒ', u'ブ': u'フ', u'ベ': u'ヘ', u'ボ': u'ホ'
    }
    dict309a = {
        u'ぱ': u'は', u'ぴ': u'ひ', u'ぷ': u'ふ', u'ぺ': u'へ', u'ぽ': u'ほ',
        u'パ': u'ハ', u'ピ': u'ヒ', u'プ': u'フ', u'ペ': u'ヘ', u'ポ': u'ホ'
    }
    s = u''
    for i in ustr:
        if i in dict3099:
            s += dict3099[i] + u'\u3099'
        elif i in dict309a:
            s += dict309a[i] + u'\u309a'
        else:
            s += i
    return s # unicode

def divide_dakuten_in(path):
    if sys.version_info.major <= 2 and type(path) is str:
        path = path.decode('UTF-8')
    r = divide_dakuten(path)
    if path != r:
        os.rename(path, r)
        print(path + u' -> ' + r)
        path = r
    if os.path.isdir(path):
        for i in glob.iglob(os.path.join(path, u'*')):
            divide_dakuten_in(i)

def join_dakuten(ustr):
    if sys.version_info.major <= 2 and type(ustr) is str:
        ustr = ustr.decode('UTF-8')
    dict3099 = {
        u'か': u'が', u'き': u'ぎ', u'く': u'ぐ', u'け': u'げ', u'こ': u'ご',
        u'さ': u'ざ', u'し': u'じ', u'す': u'ず', u'せ': u'ぜ', u'そ': u'ぞ',
        u'た': u'だ', u'ち': u'ぢ', u'つ': u'づ', u'て': u'で', u'と': u'ど',
        u'は': u'ば', u'ひ': u'び', u'ふ': u'ぶ', u'へ': u'べ', u'ほ': u'ぼ',
        u'カ': u'ガ', u'キ': u'ギ', u'ク': u'グ', u'ケ': u'ゲ', u'コ': u'ゴ',
        u'サ': u'ザ', u'シ': u'ジ', u'ス': u'ズ', u'セ': u'ゼ', u'ソ': u'ゾ',
        u'タ': u'ダ', u'チ': u'ヂ', u'ツ': u'ヅ', u'テ': u'デ', u'ト': u'ド',
        u'ハ': u'バ', u'ヒ': u'ビ', u'フ': u'ブ', u'ヘ': u'ベ', u'ホ': u'ボ'
    }
    dict309a = {
        u'は': u'ぱ', u'ひ': u'ぴ', u'ふ': u'ぷ', u'へ': u'ぺ', u'ほ': u'ぽ',
        u'ハ': u'パ', u'ヒ': u'ピ', u'フ': u'プ', u'ヘ': u'ペ', u'ホ': u'ポ'
    }
    s = u''
    for i in ustr:
        try:
            if i == u'\u3099':
                s = s[:-1] + dict3099[s[-1]]
            elif i == u'\u309a':
                s = s[:-1] + dict309a[s[-1]]
            else:
                s += i
        except:
            s += i
    return s # unicode

def join_dakuten_in(path):
    if sys.version_info.major <= 2 and type(path) is str:
        path = path.decode('UTF-8')
    r = join_dakuten(path)
    if path != r:
        os.rename(path, r)
        print(path + u' -> ' + r)
        path = r
    if os.path.isdir(path):
        for i in glob.iglob(os.path.join(path, u'*')):
            join_dakuten_in(i)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('Usage: %s {-d[ivide] | -j[oin]} {[<path>] | -s[tring] <string> | -f[ile] <path>} ' % os.path.basename(sys.argv[0]))
        quit()

# For test
#    with codecs.open('a.txt', 'w', encoding = 'UTF-8') as f:
#        f.write(u'た' + u'\u3099')

    i = 1
    operation = ''
    path = u''
    while i < len(sys.argv):
        if sys.argv[i].startswith('-d'):
            operation += 'divide'
        elif sys.argv[i].startswith('-j'):
            operation += 'join'
        elif sys.argv[i].startswith('-s'):
            operation += 'string'
            i += 1
            path = decode_if_necessary(sys.argv[i])
        elif sys.argv[i].startswith('-f'):
            operation += 'file'
            i += 1
            path = decode_if_necessary(sys.argv[i])
        else:
            path = decode_if_necessary(sys.argv[i])
        i += 1

    if 'string' in operation:
        r = divide_dakuten(path) if 'divide' in operation else join_dakuten(path)
        if path != r:
            print(path + u' -> ' + r)
        else:
            print('Not changed.')
    elif 'file' in operation:
        with open(path, 'r') as f:
            s = f.read()
        if s == '':
            print('Not changed.')
        else:
            encoding = chardet.detect(s)['encoding']
            s = s.decode(encoding)
            r = divide_dakuten(s) if 'divide' in operation else join_dakuten(s)
            if s != r:
                with codecs.open(path, 'w', encoding = encoding) as f:
                    f.write(r)
                print('Changed.')
            else:
                print('Not changed.')
    else:
        if path == u'':
            path = os.getcwd()
        if 'divide' in operation:
            divide_dakuten_in(path)
        else:
            join_dakuten_in(path)
