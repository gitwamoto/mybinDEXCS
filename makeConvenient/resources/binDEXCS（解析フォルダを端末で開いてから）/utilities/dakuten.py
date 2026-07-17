#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dakuten.py
# by Yukiharu Iwamoto
# 2026/5/12 9:53:09 PM

import os
import glob
import sys
import chardet
import codecs


def decode_if_necessary(s):
    return (
        s.decode("CP932" if sys.platform == "win32" else "UTF-8")
        if sys.version_info.major <= 2
        else s
    )


def divide_dakuten(ustr):
    if sys.version_info.major <= 2 and type(ustr) is str:
        ustr = ustr.decode("UTF-8")
    dict3099 = {
        "が": "か",
        "ぎ": "き",
        "ぐ": "く",
        "げ": "け",
        "ご": "こ",
        "ざ": "さ",
        "じ": "し",
        "ず": "す",
        "ぜ": "せ",
        "ぞ": "そ",
        "だ": "た",
        "ぢ": "ち",
        "づ": "つ",
        "で": "て",
        "ど": "と",
        "ば": "は",
        "び": "ひ",
        "ぶ": "ふ",
        "べ": "へ",
        "ぼ": "ほ",
        "ガ": "カ",
        "ギ": "キ",
        "グ": "ク",
        "ゲ": "ケ",
        "ゴ": "コ",
        "ザ": "サ",
        "ジ": "シ",
        "ズ": "ス",
        "ゼ": "セ",
        "ゾ": "ソ",
        "ダ": "タ",
        "ヂ": "チ",
        "ヅ": "ツ",
        "デ": "テ",
        "ド": "ト",
        "バ": "ハ",
        "ビ": "ヒ",
        "ブ": "フ",
        "ベ": "ヘ",
        "ボ": "ホ",
    }
    dict309a = {
        "ぱ": "は",
        "ぴ": "ひ",
        "ぷ": "ふ",
        "ぺ": "へ",
        "ぽ": "ほ",
        "パ": "ハ",
        "ピ": "ヒ",
        "プ": "フ",
        "ペ": "ヘ",
        "ポ": "ホ",
    }
    s = ""
    for i in ustr:
        if i in dict3099:
            s += dict3099[i] + "\u3099"
        elif i in dict309a:
            s += dict309a[i] + "\u309a"
        else:
            s += i
    return s  # unicode


def divide_dakuten_in(path):
    if sys.version_info.major <= 2 and type(path) is str:
        path = path.decode("UTF-8")
    r = divide_dakuten(path)
    if path != r:
        os.rename(path, r)
        print(path + " -> " + r)
        path = r
    if os.path.isdir(path):
        for i in glob.iglob(os.path.join(path, "*")):
            divide_dakuten_in(i)


def join_dakuten(ustr):
    if sys.version_info.major <= 2 and type(ustr) is str:
        ustr = ustr.decode("UTF-8")
    dict3099 = {
        "か": "が",
        "き": "ぎ",
        "く": "ぐ",
        "け": "げ",
        "こ": "ご",
        "さ": "ざ",
        "し": "じ",
        "す": "ず",
        "せ": "ぜ",
        "そ": "ぞ",
        "た": "だ",
        "ち": "ぢ",
        "つ": "づ",
        "て": "で",
        "と": "ど",
        "は": "ば",
        "ひ": "び",
        "ふ": "ぶ",
        "へ": "べ",
        "ほ": "ぼ",
        "カ": "ガ",
        "キ": "ギ",
        "ク": "グ",
        "ケ": "ゲ",
        "コ": "ゴ",
        "サ": "ザ",
        "シ": "ジ",
        "ス": "ズ",
        "セ": "ゼ",
        "ソ": "ゾ",
        "タ": "ダ",
        "チ": "ヂ",
        "ツ": "ヅ",
        "テ": "デ",
        "ト": "ド",
        "ハ": "バ",
        "ヒ": "ビ",
        "フ": "ブ",
        "ヘ": "ベ",
        "ホ": "ボ",
    }
    dict309a = {
        "は": "ぱ",
        "ひ": "ぴ",
        "ふ": "ぷ",
        "へ": "ぺ",
        "ほ": "ぽ",
        "ハ": "パ",
        "ヒ": "ピ",
        "フ": "プ",
        "ヘ": "ペ",
        "ホ": "ポ",
    }
    s = ""
    for i in ustr:
        try:
            if i == "\u3099":
                s = s[:-1] + dict3099[s[-1]]
            elif i == "\u309a":
                s = s[:-1] + dict309a[s[-1]]
            else:
                s += i
        except:
            s += i
    return s  # unicode


def join_dakuten_in(path):
    if sys.version_info.major <= 2 and type(path) is str:
        path = path.decode("UTF-8")
    r = join_dakuten(path)
    if path != r:
        os.rename(path, r)
        print(path + " -> " + r)
        path = r
    if os.path.isdir(path):
        for i in glob.iglob(os.path.join(path, "*")):
            join_dakuten_in(i)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(
            f"Usage: {os.path.basename(sys.argv[0])} "
            "{-j[oin] | -d[ivide]} {<folder_path> | <file_path> | -s[tring] <string>}"
        )
        quit()

    # For test
    #    with codecs.open('a.txt', 'w', encoding = 'UTF-8') as f:
    #        f.write(u'た' + u'\u3099')

    i = 1
    operation = path = None
    while i < len(sys.argv):
        if sys.argv[i].startswith("-d"):
            operation = "divide"
        elif sys.argv[i].startswith("-j"):
            operation = "join"
        elif sys.argv[i].startswith("-s"):
            operation = "string"
            i += 1
            path = decode_if_necessary(sys.argv[i])
        else:
            path = decode_if_necessary(sys.argv[i])
        i += 1

    if "string" in operation:
        r = divide_dakuten(path) if "divide" in operation else join_dakuten(path)
        if path != r:
            print(path + " -> " + r)
        else:
            print("Not changed.")
    elif os.path.isfile(path):
        with open(path, "rb") as f:
            s = f.read()
        if s == "":
            print("Not changed.")
        else:
            encoding = chardet.detect(s)["encoding"]
            s = s.decode(encoding)
            r = divide_dakuten(s) if "divide" in operation else join_dakuten(s)
            if s != r:
                with codecs.open(path, "w", encoding=encoding) as f:
                    f.write(r)
                print("Changed.")
            else:
                print("Not changed.")
    else:
        if "divide" in operation:
            divide_dakuten_in(path)
        else:
            join_dakuten_in(path)
