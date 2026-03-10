#!/usr/bin/env python
# -*- coding: utf-8 -*-
# rmObjects.py
# by Yukiharu Iwamoto
# 2026/2/13 2:25:21 PM

import os
import glob
import re
import shutil
import sys
import filecmp
import folderTime

def removeInessentials():
    dir_name = os.path.dirname(__file__)
    for path in (os.curdir, dir_name, os.path.normpath(os.path.join(dir_name, os.pardir))):
        for curDir, dirs, files in os.walk(path):
            for name in files:
                if re.match('\._.+|[._]+DS_Store', name):
                    os.remove(os.path.join(curDir, name))
    try:
        if os.path.isdir('dynamicCode'):
            shutil.rmtree('dynamicCode')
    except:
        pass
    for d in glob.iglob('*.analyzed/'):
        shutil.rmtree(d)

def removeLogPlotPngs():
    for i in ('residualsInitial.png', 'residualsFinal.png', 'continuityErrors.png',
        'residuals0.png', 'residuals.png', 'continuity_errors.png'):
        if os.path.isfile(i):
            os.remove(i)

def removePyFoamPlots():
    pat = re.compile(r'(linear|cont|bound|courant|deltaT|custom[0-9][0-9][0-9][0-9])\.png$')
    for i in glob.glob('*.png'):
        if os.path.isfile(i) and pat.match(i):
            os.remove(i)

def removeProcessorDirs(option = '', path = os.curdir):
    noZero, noLatest = 'noZero' in option, 'noLatest' in option
    pat = re.compile(r'(?:\./)?processor([0-9]+)/$')
    if not noLatest and not noZero:
        for p in glob.iglob(os.path.join(path, 'processor[0-9]*/')):
            if pat.match(p):
                shutil.rmtree(p)
    else:
        latest_time = folderTime.latestTime(path)
        if latest_time is None:
            return
        latest_time = float(latest_time)
        if noLatest and latest_time == 0.0:
            noZero = False
        pdirs = []
        for p in glob.iglob(os.path.join(path, 'processor[0-9]*/')):
            s = pat.match(p)
            if s is not None:
                pdirs.append(int(s.group(1)))
        pdirs.sort()
        if noZero:
            if noLatest:
                s = '0秒と{}秒'.format(latest_time)
            else:
                s = '0秒'
        else:
            s = '{}秒'.format(latest_time)
        for p in pdirs:
            p = os.path.join(path, 'processor' + str(p))
            print('{}から{}以外の結果を消去中...'.format(p, s))
            for t in glob.iglob(os.path.join(p, '*' + os.sep)):
                try:
                    ft = float(os.path.basename(os.path.dirname(t)))
                    if (ft < latest_time if noLatest else True) and (ft > 0.0 if noZero else True):
                        shutil.rmtree(t)
                except:
                    pass

def removeResultDirsWoZeroAndLatest(path = os.curdir):
    latest_time = folderTime.latestTime(path)
    if latest_time is None:
        return
    latest_time = float(latest_time)
    for t in glob.iglob(os.path.join(path, '*' + os.sep)):
        try:
            ft = float(os.path.basename(os.path.dirname(t)))
            if ft != 0.0 and ft < latest_time:
                shutil.rmtree(t)
        except:
            pass

def removeResultDirsWithTimeGreaterThan(time, path = os.curdir):
    time = float(time)
    for t in glob.iglob(os.path.join(path, '*' + os.sep)):
        try:
            if float(os.path.basename(os.path.dirname(t))) > time:
                shutil.rmtree(t)
        except:
            pass

def removeDirsAndFilesWithName(dirs = None, files = None, path = os.curdir):
    dirs = [t for t in (dirs if isinstance(dirs, (tuple, list)) else (dirs,)) if t is not None]
    files = [t for t in (files if isinstance(files, (tuple, list)) else (files,)) if t is not None]
    for obj in os.listdir(path):
        pathobj = os.path.join(path, obj)
        if os.path.isdir(pathobj):
            for p in dirs:
                r = re.search(p, obj)
                if r is not None and len(r.group()) == len(obj):
                    try:
                        shutil.rmtree(pathobj)
                    except:
                        pass
        elif os.path.isfile(pathobj):
            for p in files:
                r = re.search(p, obj)
                if r is not None and len(r.group()) == len(obj):
                    try:
                        os.remove(pathobj)
                    except:
                        pass

def removeDirsAndFilesWithNameRecursively(dirs = None, files = None, path = os.curdir):
    dirs = [t for t in (dirs if isinstance(dirs, (tuple, list)) else (dirs,)) if t is not None]
    files = [t for t in (files if isinstance(files, (tuple, list)) else (files,)) if t is not None]
    for dirpath, dirnames, filenames in os.walk(path):
        for obj in dirnames:
            for p in dirs:
                r = re.search(p, obj)
                if r is not None and len(r.group()) == len(obj):
                    try:
                        shutil.rmtree(os.path.join(dirpath, obj))
                    except:
                        pass
        for obj in filenames:
            for p in files:
                r = re.search(p, obj)
                if r is not None and len(r.group()) == len(obj):
                    try:
                        os.remove(os.path.join(dirpath, obj))
                    except:
                        pass

def remove0_bakRecursively(path = os.curdir):
    for dirpath, dirnames, filenames in os.walk(path):
        if '0_bak' not in dirnames or '0' not in dirnames:
            continue
        d0_bak = os.path.join(dirpath, '0_bak')
        d0 = os.path.join(dirpath, '0')
        dcmp = filecmp.dircmp(d0_bak, d0)
        if len(dcmp.left_only) == 0 and len(dcmp.right_only) == 0 and len(dcmp.diff_files) == 0:
            shutil.rmtree(d0_bak)

if __name__ == '__main__':
    path = os.curdir if len(sys.argv) == 1 else sys.argv[1]
    removeProcessorDirs('noLatest', path)
#    removeResultDirsWithTimeGreaterThan(path)
#    removeInessentials(path)
#    removeResultDirsWoZeroAndLatest(path)
#    remove0_bakRecursively(path)
#    if len(sys.argv) > 1:
#        dirs = []
#        files = []
#        path = os.curdir
#        i = 1
#        while i < len(sys.argv):
#            if sys.argv[i] == '-d':
#                i += 1
#                dirs.extend(sys.argv[i].split(','))
#            elif sys.argv[i] == '-f':
#                i += 1
#                files.extend(sys.argv[i].split(','))
#            else:
#                path = sys.argv[i]
#            i += 1
#    removeDirsAndFilesWithNameRecursively(dirs, files, path)
