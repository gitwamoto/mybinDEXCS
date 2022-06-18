#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ofpolymesh.py
# by Yukiharu Iwamoto
# 2021/6/30 12:23:52 PM

import sys
import os
import numpy as np
from struct import pack

class boundary2D(object):
    def __init__(self, name, type, i0, i1, j0, j1):
        if i0 != i1 and j0 != j1:
            print('Relationship i0 = i1 or j0 = j1 should be satisfied.')
            sys.exit(1)
        self.i0 = i0
        self.i1 = i1
        self.j0 = j0
        self.j1 = j1
        self.nFaces = self.startFace = 0
        self.name = '' if name is None else name
        self.type = '' if type is None else type

class structure2D(object):
    def __init__(self, imax, jmax, x, y, ascii = True, parent_dir_path = None, comment = None, depth = 1.0, right_handed = True):
        self.imax = imax
        self.jmax = jmax
        self.ca = 1 if right_handed else 0
        self.cb = 0 if right_handed else 1
        self.nCells = (imax - 1)*(jmax - 1)
        self.x = x if type(x) is np.ndarray else np.array(x)
        self.y = y if type(y) is np.ndarray else np.array(y)
        self.depth = depth
        self.ascii = ascii
        self.parent_dir_path = '' if parent_dir_path is None else parent_dir_path
        self.comment = '' if comment is None else comment.replace('\n', '\n// ')
        self.pidx = np.empty((imax, jmax), dtype = 'u4')
        self.fiidx = np.empty((imax,     jmax - 1, 5), dtype = 'u4')
        self.fjidx = np.empty((imax - 1, jmax,     5), dtype = 'u4')
        self.fkidx = np.empty((imax - 1, jmax - 1, 5), dtype = 'u4')
        self.boundary = []

    def set_boundary(self, name, type, i0 = None, i1 = None, j0 = None, j1 = None):
        if i1 == None:
            if i0 == None:
                i0 = 0
                i1 = self.imax
            else:
                i1 = i0
        if j1 == None:
            if j0 == None:
                j0 = 0
                j1 = self.jmax
            else:
                j1 = j0
        self.boundary.append(boundary2D(name, type, i0, i1, j0, j1))
        return self

    def make_indices(self):
        # points
        self.nPoints = 0
        for j in range(self.jmax):
            for i in range(self.imax):
                if i > 0 and self.x[i, j] == self.x[i - 1, j] and self.y[i, j] == self.y[i - 1, j]:
                    self.pidx[i, j] = self.pidx[i - 1, j]
                elif j > 0 and self.x[i, j] == self.x[i, j - 1] and self.y[i, j] == self.y[i, j - 1]:
                    self.pidx[i, j] = self.pidx[i, j - 1]
                else:
                    self.pidx[i, j] = self.nPoints
                    self.nPoints += 1
        # internal faces
        self.nInternalFaces = self.nFacePoints = 0
        for i in range(1, self.imax - 1):
            for j in range(self.jmax - 1):
                if self.pidx[i, j + 1] != self.pidx[i, j]:
                    self.fiidx[i, j, 0] = 4
                    self.nFacePoints += 4
                    self.fiidx[i, j, 1] = self.pidx[i, j]
                    self.fiidx[i, j, 2] = self.pidx[i, j + self.ca] + self.cb*self.nPoints
                    self.fiidx[i, j, 3] = self.pidx[i, j + 1] + self.nPoints
                    self.fiidx[i, j, 4] = self.pidx[i, j + self.cb] + self.ca*self.nPoints
                    self.nInternalFaces += 1
                else:
                    self.fiidx[i, j, 0] = 0
        for j in range(1, self.jmax - 1):
            for i in range(self.imax - 1):
                if self.pidx[i + 1, j] != self.pidx[i, j]:
                    self.fjidx[i, j, 0] = 4
                    self.nFacePoints += 4
                    self.fjidx[i, j, 1] = self.pidx[i, j]
                    self.fjidx[i, j, 2] = self.pidx[i + self.cb, j] + self.ca*self.nPoints
                    self.fjidx[i, j, 3] = self.pidx[i + 1, j] + self.nPoints
                    self.fjidx[i, j, 4] = self.pidx[i + self.ca, j] + self.cb*self.nPoints
                    self.nInternalFaces += 1
                else:
                    self.fjidx[i, j, 0] = 0
        self.nFaces = self.nInternalFaces
        # boundary faces
        for b in self.boundary:
            b.startFace = self.nFaces
            if b.i0 == b.i1:
                ca, cb = (self.ca, self.cb) if b.i0 > 0 else (self.cb, self.ca)
                for j in range(b.j0, b.j1 - 1):
                    if self.pidx[b.i0, j + 1] != self.pidx[b.i0, j]:
                        self.fiidx[b.i0, j, 0] = 4
                        self.nFacePoints += 4
                        self.fiidx[b.i0, j, 1] = self.pidx[b.i0, j]
                        self.fiidx[b.i0, j, 2] = self.pidx[b.i0, j + ca] + cb*self.nPoints
                        self.fiidx[b.i0, j, 3] = self.pidx[b.i0, j + 1] + self.nPoints
                        self.fiidx[b.i0, j, 4] = self.pidx[b.i0, j + cb] + ca*self.nPoints
                        b.nFaces += 1
                        self.nFaces += 1
                    else:
                        self.fiidx[b.i0, j, 0] = 0
            else: # b.j0 == b.j1
                ca, cb = (self.ca, self.cb) if b.j0 > 0 else (self.cb, self.ca)
                for i in range(b.i0, b.i1 - 1):
                    if self.pidx[i + 1, b.j0] != self.pidx[i, b.j0]:
                        self.fjidx[i, b.j0, 0] = 4
                        self.nFacePoints += 4
                        self.fjidx[i, b.j0, 1] = self.pidx[i, b.j0]
                        self.fjidx[i, b.j0, 2] = self.pidx[i + cb, b.j0] + ca*self.nPoints
                        self.fjidx[i, b.j0, 3] = self.pidx[i + 1, b.j0] + self.nPoints
                        self.fjidx[i, b.j0, 4] = self.pidx[i + ca, b.j0] + cb*self.nPoints
                        b.nFaces += 1
                        self.nFaces += 1
                    else:
                        self.fjidx[i, b.j0, 0] = 0
        i = 0
        while i < len(self.boundary):
            j = i + 1
            while j < len(self.boundary) and self.boundary[j].name == '':
                self.boundary[i].nFaces += self.boundary[j].nFaces
                del self.boundary[j]
            i += 1
        # back
        self.front_startFace = self.nFaces
        self.front_nFaces = 0
        for j in range(self.jmax - 1):
            for i in range(self.imax - 1):
                n = 1
                if self.pidx[i + self.cb, j + self.ca] != self.pidx[i, j]:
                    n += 1
                    self.fkidx[i, j, n] = pidx[i + self.cb, j + self.ca]
                if self.pidx[i + 1, j + 1] != self.pidx[i + self.cb, j + self.ca]:
                    n += 1
                    self.fkidx[i, j, n] = self.pidx[i + 1, j + 1]
                if (self.pidx[i + self.ca, j + self.cb] != self.pidx[i + 1, j + 1] and
                    self.pidx[i + self.ca, j + self.cb] != self.pidx[i, j]):
                    n += 1
                    self.fkidx[i, j, n] = self.pidx[i + self.ca, j + self.cb]
                if n > 2:
                    self.fkidx[i, j, 0] = n
                    self.nFacePoints += 2*n
                    self.fkidx[i, j, 1] = self.pidx[i, j]
                    self.front_nFaces += 1
                else:
                    self.fkidx[i, j, 0] = 0
        self.nFaces += 2*self.front_nFaces
        self.nPoints *= 2
        return self

    def cindex(self, i, j):
        return (self.imax - 1)*j + i

    def make_files(self):
        if self.parent_dir_path != '':
            os.mkdir(self.parent_dir_path)
            os.chmod(self.parent_dir_path, 0o0777)
            self.parent_dir_path = os.path.join(self.parent_dir_path, 'polyMesh')
        else:
            self.parent_dir_path = os.path.join(os.curdir, 'polyMesh')
        os.mkdir(self.parent_dir_path)
        os.chmod(self.parent_dir_path, 0o0777)

        if self.ascii:
            with open(os.path.join(self.parent_dir_path, 'points'), 'w') as fp:
                fp.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tvectorField;\n' +
                    '\tlocation\t"constant/polyMesh";\n\tobject\tpoints;\n}\n')
                fp.write('{}\n(\n'.format(self.nPoints))
                n = 0
                for j in range(self.jmax):
                    for i in range(self.imax):
                        if self.pidx[i, j] == n:
                            fp.write('(%#.*e %#.*e 0)\n' %
                                (sys.float_info.dig, self.x[i, j], sys.float_info.dig, self.y[i, j]))
                            n += 1
                n = 0
                for j in range(self.jmax):
                    for i in range(self.imax):
                        if self.pidx[i, j] == n:
                            fp.write('(%#.*e %#.*e %#.*e)\n', (sys.float_info.dig, self.x[i, j],
                                sys.float_info.dig, self.y[i, j], sys.float_info.dig, self.depth))
                            n += 1
                fp.write(')\n')

            with open(os.path.join(self.parent_dir_path, 'faces'), 'w') as ff:
                ff.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tfaceList;\n' +
                    '\tlocation\t"constant/polyMesh";\n\tobject\tfaces;\n}\n')
                ff.write('{}\n(\n'.format(self.nFaces))
                with open(os.path.join(self.parent_dir_path, 'owner'), 'w') as fo:
                    fo.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tlabelList;\n' +
                        '\tnote"nPoints: %d nCells: %d nFaces: %d nInternalFaces: %d"\n' +
                        '\tlocation\t"constant/polyMesh";\n\tobject\towner;\n}\n' %
                        (self.nPoints, self.nCells, self.nFaces, self.nInternalFaces))
                    fo.write('{}\n(\n'.format(self.nFaces))
                    with open(os.path.join(self.parent_dir_path, 'neighbour'), 'w') as fn:
                        fn.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tlabelList;\n' +
                            '\tnote"nPoints: %d nCells: %d nFaces: %d nInternalFaces: %d"\n' +
                            '\tlocation\t"constant/polyMesh";\n\tobject\tneighbour;\n}\n' %
                            (self.nPoints, self.nCells, self.nFaces, self.nInternalFaces))
                        fn.write('{}\n(\n'.format(self.nInternalFaces))
                        # internal faces
                        for i in range(1, self.imax - 1):
                            for j in range(self.jmax - 1):
                                if self.fiidx[i, j, 0] > 0:
                                    ff.write('{}({}'.format(self.fiidx[i, j, 0], self.fiidx[i, j, 1]))
                                    for n in range(2, self.fiidx[i, j, 0] + 1):
                                        ff.write(' {}'.format(self.fiidx[i, j, n]))
                                    ff.write(')\n')
                                    fo.write('{}\n'.format(self.cindex(i - 1, j)))
                                    fn.write('{}\n'.format(self.cindex(i, j)))
                        for j in range(1, self.jmax - 1):
                            for i in range(self.imax - 1):
                                if self.fjidx[i, j, 0] > 0:
                                    ff.write('{}({}'.format(self.fjidx[i, j, 0], self.fjidx[i, j, 1]))
                                    for n in range(2, self.fjidx[i, j, 0] + 1):
                                        ff.write(' {}'.format(self.fjidx[i, j, n]))
                                    ff.write(')\n')
                                    fo.write('{}\n'.format(self.cindex(i, j - 1)))
                                    fn.write('{}\n'.format(self.cindex(i, j)))
                        fn.write(')\n')
                    # boundary faces
                    for b in self.boundary:
                        if b.i0 == b.i1:
                            for j in range(b.j0, b.j1 - 1):
                                if self.fiidx[b.i0, j, 0]:
                                    ff.write('{}({}'.format(self.fiidx[b.i0, j, 0], self.fiidx[b.i0, j, 1]))
                                    for n in range(2, self.fiidx[b.i0, j, 0] + 1):
                                        ff.write(' {}'.format(self.fiidx[b.i0, j, n]))
                                    ff.write(')\n')
                                    fo.write('{}\n'.format(self.cindex(b.i0 - 1 if b.i0 > 0 else 0, j)))
                        else: # b.j0 == b.j1
                            for i in range(b.i0, b.i1 - 1):
                                if self.fjidx[i, b.j0, 0] > 0:
                                    ff.write('{}({}'.format(self.fjidx[i, b.j0, 0], self.fjidx[i, b.j0, 1]))
                                    for n in range(2, self.fjidx[i, b.j0, 0] + 1):
                                        ff.write(' {}'.format(self.fjidx[i, b.j0, n]))
                                    ff.write(')\n')
                                    fo.write('{}\n'.format(self.cindex(i, b.j0 - 1 if b.j0 > 0 else 0)))
                    # front
                    for j in range(self.jmax - 1):
                        for i in range(self.imax - 1):
                            if self.fkidx[i, j, 0] > 0:
                                ff.write('{}({}'.format(self.fkidx[i, j, 0], self.fkidx[i, j, 1] + self.nPoints/2))
                                for n in range(self.fkidx[i, j, 0], 1, -1):
                                    ff.write(' {}'.format(self.fkidx[i, j, n] + self.nPoints/2))
                                ff.write(')\n')
                                fo.write('{}\n'.format(self.cindex(i, j)))
                    # back
                    for j in range(self.jmax - 1):
                        for i in range(self.imax - 1):
                            if self.fkidx[i, j, 0] > 0:
                                ff.write('{}({}'.format(self.fkidx[i, j, 0], self.fkidx[i, j, 1]))
                                for n in range(2, self.fkidx[i, j, 0] + 1):
                                    ff.write(' {}'.format(self.fkidx[i, j, n]))
                                ff.write(')\n')
                                fo.write('{}\n'.format(self.cindex(i, j)))
                    fo.write(')\n')
                ff.write(')\n')
        else: # not self.ascii
            with open(os.path.join(self.parent_dir_path, 'points'), 'wb') as fp:
                fp.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tbinary;\n\tclass\tvectorField;\n' +
                    '\tlocation\t"constant/polyMesh";\n\tobject\tpoints;\n}\n')
                fp.write('{}\n('.format(self.nPoints))
                n = 0
                for j in range(self.jmax):
                    for i in range(self.imax):
                        if pidx[i, j] == n:
                            fp.write(pack('<ddd', self.x[i, j], self.y[i, j], 0.0))
                            n += 1
                n = 0
                for j in range(self.jmax):
                    for i in range(self.imax):
                        if pidx[i, j] == n:
                            fp.write(pack('<ddd', self.x[i, j], self.y[i, j], self.depth))
                            n += 1
                fp.write(')\n')

            with open(os.path.join(self.parent_dir_path, 'faces'), 'wb') as ff:
                ff.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tbinary;\n\tclass\tfaceCompactList;\n' +
                    '\tlocation\t"constant/polyMesh";\n\tobject\tfaces;\n}\n')
                ff.write('{}\n('.format(self.nFaces + 1))
                n = 0
                ff.write(pack('<I', n))
                # internal faces
                for i in range(1, self.imax - 1):
                    for j in range(self.jmax - 1):
                        if self.fiidx[i, j, 0] > 0:
                            n += self.fiidx[i, j, 0]
                            ff.write(pack('<I', n))
                for j in range(1, self.jmax - 1):
                    for i in range(self.imax - 1):
                        if self.fjidx[i, j, 0] > 0:
                            n += self.fjidx[i, j, 0]
                            ff.write(pack('<I', n))
                # boundary faces
                for b in self.boundary:
                    if b.i0 == b.i1:
                        for j in range(b.j0, b.j1 - 1):
                            if self.fiidx[b.i0, j, 0] > 0:
                                n += self.fiidx[b.i0, j, 0]
                                ff.write(pack('<I', n))
                    else: # b.j0 == b.j1
                        for i in range(b.i0, b.i1 - 1):
                            if self.fjidx[i, b.j0, 0] > 0:
                                n += self.fjidx[i, b.j0, 0]
                                ff.write(pack('<I', n))
                # front
                for j in range(self.jmax - 1):
                    for i in range(self.imax - 1):
                        if self.fkidx[i, j, 0] > 0:
                            n += self.fkidx[i, j, 0]
                            ff.write(pack('<I', n))
                # back
                for j in range(self.jmax - 1):
                    for i in range(self.imax - 1):
                        if self.fkidx[i, j, 0] > 0:
                            n += self.fkidx[i, j, 0]
                            ff.write(pack('<I', n))
                ff.write(')\n{}\n('.format(self.nFacePoints))

                with open(os.path.join(self.parent_dir_path, 'owner'), 'wb') as fo:
                    fo.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tbinary;\n\tclass\tlabelList;\n' +
                        '\tnote"nPoints: %d nCells: %d nFaces: %d nInternalFaces: %d"\n' +
                        '\tlocation\t"constant/polyMesh";\n\tobject\towner;\n}\n' %
                        (self.nPoints, self.nCells, self.nFaces, self.nInternalFaces))
                    fo.write('{}\n('.format(self.nFaces))
                    with open(os.path.join(self.parent_dir_path, 'neighbour'), 'wb') as fn:
                        fn.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tbinary;\n\tclass\tlabelList;\n' +
                            '\tnote"nPoints: %d nCells: %d nFaces: %d nInternalFaces: %d"\n' +
                            '\tlocation\t"constant/polyMesh";\n\tobject\tneighbour;\n}\n' %
                            (self.nPoints, self.nCells, self.nFaces, self.nInternalFaces))
                        fn.write('{}\n('.format(self.nInternalFaces))
                        # internal faces
                        for i in range(1, self.imax - 1):
                            for j in range(self.jmax - 1):
                                if self.fiidx[i, j, 0] > 0:
                                    self.fiidx[i, j, 1:1 + self.fiidx[i, j, 0]].astype('<I').tofile(ff)
                                    fo.write(pack('<I', self.cindex(i - 1, j)))
                                    fn.write(pack('<I', self.cindex(i, j)))
                        for j in range(1, self.jmax - 1):
                            for i in range(self.imax - 1):
                                if self.fjidx[i, j, 0] > 0:
                                    self.fjidx[i, j, 1:1 + self.fjidx[i, j, 0]].astype('<I').tofile(ff)
                                    fo.write(pack('<I', self.cindex(i, j - 1)))
                                    fn.write(pack('<I', self.cindex(i, j)))
                        fn.write(')\n')
                    # boundary faces
                    for b in self.boundary:
                        if b.i0 == b.i1:
                            for j in range(b.j0, b.j1 - 1):
                                if self.fiidx[b.i0, j, 0] > 0:
                                    self.fiidx[b.i0, j, 1:1 + self.fiidx[b.i0, j, 0]].astype('<I').tofile(ff)
                                    fo.write(pack('<I', self.cindex(b.i0 - 1 if b.i0 > 0 else 0, j)))
                        else: # b.j0 == b.j1
                            for i in range(b.i0, b.i1 - 1):
                                if self.fjidx[i, b.j0, 0] > 0:
                                    self.fjidx[i, b.j0, 1:1 + self.fjidx[i, b.j0, 0]].astype('<I').tofile(ff)
                                    fo.write(pack('<I', self.cindex(i, b.j0 - 1 if b.j0 > 0 else 0)))
                    # front
                    for j in range(self.jmax - 1):
                        for i in range(self.imax - 1):
                            if self.fkidx[i, j, 0] > 0:
                                ff.write(pack('<I', self.fkidx[i, j, 1] + self.nPoints/2))
                                self.fkidx[i, j, self.fkidx[i, j, 0]:1:-1].astype('<I').tofile(ff)
                                fo.write(pack('<I', self.cindex(i, j)))
                    # back
                    for j in range(self.jmax - 1):
                        for i in range(self.imax - 1):
                            if self.fkidx[i, j, 0] > 0:
                                self.fkidx[i, j, 1:1 + self.fkidx[i, j, 0]].astype('<I').tofile(ff)
                                fo.write(pack('<I', self.cindex(i, j)))
                    fo.write(')\n')
                ff.write(')\n')

        with open(os.path.join(self.parent_dir_path, 'boundary'), 'w') as fb:
            fb.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\t%s;\n\tclass\tpolyBoundaryMesh;\n' +
                '\tlocation\t"constant/polyMesh";\n\tobject\tboundary;\n}\n' %
                ('ascii' if self.ascii else 'binary'))
            if self.comment != '':
                fb.write('// {}\n\n'.format(self.comment))
            fb.write('{}\n(\n'.format(len(self.boundary) + 2))
            for b in self.boundary:
                fb.write('\t%s\n\t{\n\t\ttype\t%s;\n\t\tnFaces\t%d;\n\t\tstartFace\t%d;\n\t}\n' %
                    (b.name, b.type, b.nFaces, b.startFace))
            fb.write('\tfront\n\t{\n\t\ttype\tempty;\n\t\tnFaces\t%d;\n\t\tstartFace\t%d;\n\t}\n' %
                (self.front_nFaces, self.front_startFace))
            fb.write('\tback\n\t{\n\t\ttype\tempty;\n\t\tnFaces\t%d;\n\t\tstartFace\t%d;\n\t}\n' %
                (self.front_nFaces, self.front_startFace + self.front_nFaces))
            fb.write(')\n')

        return self

class boundary3D(object):
    def __init__(self, name, type, i0, i1, j0, j1, k0, k1):
        if i0 != i1 and j0 != j1 and k0 != k1:
            print('Relationship i0 = i1 or j0 = j1 or k0 = k1 should be satisfied.')
            sys.exit(1)
        self.i0 = i0
        self.i1 = i1
        self.j0 = j0
        self.j1 = j1
        self.k0 = k0
        self.k1 = k1
        self.nFaces = self.startFace = 0
        self.name = '' if name is None else name
        self.type = '' if type is None else type

class structured3D(object):
    def __init__(self, imax, jmax, kmax, x, y, z, ascii = True, parent_dir_path = None, comment = None, right_handed = True):
        self.imax = imax
        self.jmax = jmax
        self.kmax = kmax
        self.ca = 1 if right_handed else 0
        self.cb = 0 if right_handed else 1
        self.nCells = (imax - 1)*(jmax - 1)*(kmax - 1)
        self.x = x if type(x) is np.ndarray else np.array(x)
        self.y = y if type(y) is np.ndarray else np.array(y)
        self.z = z if type(z) is np.ndarray else np.array(z)
        self.ascii = ascii
        self.parent_dir_path = '' if parent_dir_path is None else parent_dir_path
        self.comment = '' if comment is None else comment.replace('\n', '\n// ')
        self.pidx = np.empty((imax, jmax, kmax), dtype = 'u4')
        self.fiidx = np.empty((imax,     jmax - 1, kmax - 1, 5), dtype = 'u4')
        self.fjidx = np.empty((imax - 1, jmax,     kmax - 1, 5), dtype = 'u4')
        self.fkidx = np.empty((imax - 1, jmax - 1, kmax,     5), dtype = 'u4')
        self.boundary = []

    def set_boundary(self, name, type, i0 = None, i1 = None, j0 = None, j1 = None, k0 = None, k1 = None):
        if i1 == None:
            if i0 == None:
                i0 = 0
                i1 = self.imax
            else:
                i1 = i0
        if j1 == None:
            if j0 == None:
                j0 = 0
                j1 = self.jmax
            else:
                j1 = j0
        if k1 == None:
            if k0 == None:
                k0 = 0
                k1 = self.kmax
            else:
                k1 = k0
        self.boundary.push_back(boundary3D(name, type, i0, i1, j0, j1, k0, k1))
        return self

    def make_indices(self):
        # points
        self.nPoints = 0
        for k in range(self.kmax):
            for j in range(self.jmax):
                for i in range(self.imax):
                    if (i > 0 and self.x[i, j, k] == self.x[i - 1, j, k] and
                        self.y[i, j, k] == self.y[i - 1, j, k] and self.z[i, j, k] == self.z[i - 1, j, k]):
                        self.pidx[i, j, k] = self.pidx[i - 1, j, k]
                    elif (j > 0 and self.x[i, j, k] == self.x[i, j - 1, k] and
                        self.y[i, j, k] == self.y[i, j - 1, k] and self.z[i, j, k] == self.z[i, j - 1, k]):
                        self.pidx[i, j, k] = self.pidx[i, j - 1, k]
                    elif (k > 0 and self.x[i, j, k] == self.x[i, j, k - 1] and
                        self.y[i, j, k] == self.y[i, j, k - 1] and self.z[i, j, k] == self.z[i, j, k - 1]):
                        self.pidx[i, j, k] = self.pidx[i, j, k - 1]
                    else:
                        self.pidx[i, j, k] = self.nPoints
                        self.nPoints += 1
        # internal faces
        self.nInternalFaces = self.nFacePoints = 0
        for i in range(1, self.imax - 1):
            for k in range(self.kmax - 1):
                for j in range(self.jmax - 1):
                    n = 1
                    if self.pidx[i, j + self.ca, k + self.cb] != self.pidx[i, j, k]:
                        n += 1
                        self.fiidx[i, j, k, n] = self.pidx[i, j + self.ca, k + self.cb]
                    if self.pidx[i, j + 1, k + 1] != self.pidx[i, j + self.ca, k + self.cb]:
                        n += 1
                        self.fiidx[i, j, k, n] = self.pidx[i, j + 1, k + 1]
                    if (self.pidx[i, j + self.cb, k + self.ca] != self.pidx[i, j + 1, k + 1] and
                        self.pidx[i, j + self.cb, k + self.ca] != self.pidx[i, j, k]):
                        n += 1
                        self.fiidx[i, j, k, n] = self.pidx[i, j + self.cb, k + self.ca]
                    if n > 2:
                        self.fiidx[i, j, k, 0] = n
                        self.nFacePoints += n
                        self.fiidx[i, j, k, 1] = self.pidx[i, j, k]
                        self.nInternalFaces += 1
                    else:
                        self.fiidx[i, j, k, 0] = 0
        for j in range(1, self.jmax - 1):
            for i in range(self.imax - 1):
                for k in range(self.kmax - 1):
                    n = 1
                    if self.pidx[i + self.cb, j, k + self.ca] != self.pidx[i, j, k]:
                        n += 1
                        self.fjidx[i, j, k, n] = self.pidx[i + self.cb, j, k + self.ca]
                    if self.pidx[i + 1, j, k + 1] != self.pidx[i + self.cb, j, k + self.ca]:
                        n += 1
                        self.fjidx[i, j, k, n] = self.pidx[i + 1, j, k + 1]
                    if (self.pidx[i + self.ca, j, k + self.cb] != self.pidx[i + 1, j, k + 1] and
                        self.pidx[i + self.ca, j, k + self.cb] != self.pidx[i, j, k]):
                        n += 1
                        self.fjidx[i, j, k, n] = self.pidx[i + self.ca, j, k + self.cb]
                    if n > 2:
                        self.fjidx[i, j, k, 0] = n
                        self.nFacePoints += n
                        self.fjidx[i, j, k, 1] = self.pidx[i, j, k]
                        self.nInternalFaces += 1
                    else:
                        self.fjidx[i, j, k, 0] = 0
        for k in range(1, self.kmax - 1):
            for j in range(self.jmax - 1):
                for i in range(self.imax - 1):
                    n = 1
                    if self.pidx[i + self.ca, j + self.cb, k] != self.pidx[i, j, k]:
                        n += 1
                        self.fkidx[i, j, k, n] = self.pidx[i + self.ca, j + self.cb, k]
                    if self.pidx[i + 1, j + 1, k] != self.pidx[i + self.ca, j + self.cb, k]:
                        n += 1
                        self.fkidx[i, j, k, n] = self.pidx[i + 1, j + 1, k]
                    if (self.pidx[i + self.cb, j + self.ca, k] != self.pidx[i + 1, j + 1, k] and
                        self.pidx[i + self.cb, j + self.ca, k] != self.pidx[i, j, k]):
                        n += 1
                        self.fkidx[i, j, k, n] = self.pidx[i + self.cb, j + self.ca, k]
                    if n > 2:
                        self.fkidx[i, j, k, 0] = n
                        self.nFacePoints += n
                        self.fkidx[i, j, k, 1] = self.pidx[i, j, k]
                        self.nInternalFaces += 1
                    else:
                        self.fkidx[i, j, k, 0] = 0
        self.nFaces = self.nInternalFaces
        # boundary faces
        for b in self.boundary:
            b.startFace = self.nFaces;
            if b.i0 == b.i1:
                ca, cb = (self.ca, self.cb) if b.i0 > 0 else (self.cb, self.ca)
                for k in range(b.k0, b.k1 - 1):
                    for j in range(b.j0, b.j1 - 1):
                        n = 1
                        if self.pidx[b.i0, j + ca, k + cb] != self.pidx[b.i0, j, k]:
                            n += 1
                            self.fiidx[b.i0, j, k, n] = self.pidx[b.i0, j + ca, k + cb]
                        if self.pidx[b.i0, j + 1, k + 1] != self.pidx[b.i0, j + ca, k + cb]:
                            n += 1
                            self.fiidx[b.i0, j, k, n] = self.pidx[b.i0, j + 1, k + 1]
                        if (self.pidx[b.i0, j + cb, k + ca] != self.pidx[b.i0, j + 1, k + 1] and
                            self.pidx[b.i0, j + cb, k + ca] != self.pidx[b.i0, j, k]):
                            n += 1
                            self.fiidx[b.i0, j, k, n] = self.pidx[b.i0, j + cb, k + ca]
                        if n > 2:
                            self.fiidx[b.i0, j, k, 0] = n
                            self.nFacePoints += n
                            self.fiidx[b.i0, j, k, 1] = self.pidx[b.i0, j, k]
                            b.self.nFaces += 1
                            self.nFaces += 1
                        else:
                            self.fiidx[b.i0, j, k, 0] = 0
            elif b.j0 == b.j1:
                ca, cb = (self.ca, self.cb) if b.j0 > 0 else (self.cb, self.ca)
                for i in range(b.i0, b.i1):
                    for k in range(b.k0, b.k1 - 1):
                        n = 1
                        if self.pidx[i + cb, b.j0, k + ca] != self.pidx[i, b.j0, k]:
                            n += 1
                            self.fjidx[i, b.j0, k, n] = self.pidx[i + cb, b.j0, k + ca]
                        if self.pidx[i + 1, b.j0, k + 1] != self.pidx[i + cb, b.j0, k + ca]:
                            n += 1
                            self.fjidx[i, b.j0, k, n] = self.pidx[i + 1, b.j0, k + 1]
                        if (self.pidx[i + ca, b.j0, k + cb] != self.pidx[i + 1, b.j0, k + 1] and
                            self.pidx[i + ca, b.j0, k + cb] != self.pidx[i, b.j0, k]):
                            n += 1
                            self.fjidx[i, b.j0, k, n] = self.pidx[i + ca, b.j0, k + cb]
                        if n > 2:
                            self.fjidx[i, b.j0, k, 0] = n
                            self.nFacePoints += n
                            self.fjidx[i, b.j0, k, 1] = self.pidx[i, b.j0, k]
                            b.self.nFaces += 1
                            self.nFaces += 1
                        else:
                            self.fjidx[i, b.j0, k, 0] = 0
            else: # b.k0 == b.k1
                ca, cb = (self.ca, self.cb) if b.k0 > 0 else (self.cb, self.ca)
                for j in range(b.j0, b.j1 - 1):
                    for i in range(b.i0, b.i1 - 1):
                        n = 1
                        if self.pidx[i + ca, j + cb, b.k0] != self.pidx[i, j, b.k0]:
                            n += 1
                            self.fkidx[i, j, b.k0, n] = self.pidx[i + ca, j + cb, b.k0]
                        if self.pidx[i + 1, j + 1, b.k0] != self.pidx[i + ca, j + cb, b.k0]:
                            n += 1
                            self.fkidx[i, j, b.k0, n] = self.pidx[i + 1, j + 1, b.k0]
                        if (self.pidx[i + cb, j + ca, b.k0] != self.pidx[i + 1, j + 1, b.k0] and
                            self.pidx[i + cb, j + ca, b.k0] != self.pidx[i, j, b.k0]):
                            n += 1
                            self.fkidx[i, j, b.k0, n] = self.pidx[i + cb, j + ca, b.k0]
                        if n > 2:
                            self.fkidx[i, j, b.k0, 0] = n
                            self.nFacePoints += n
                            self.fkidx[i, j, b.k0, 1] = self.pidx[i, j, b.k0]
                            b.self.nFaces += 1
                            self.nFaces += 1
                        else:
                            self.fkidx[i, j, b.k0, 0] = 0
        i = 0
        while i < len(self.boundary):
            j = i + 1
            while j < len(self.boundary) and self.boundary[j].name == '':
                self.boundary[i].nFaces += self.boundary[j].nFaces
                del self.boundary[j]
            i += 1
        return self

    def cindex(self, i, j, k):
        return (self.imax - 1)*((self.jmax - 1)*k + j) + i

    def make_files(self):
        if self.parent_dir_path != '':
            os.mkdir(self.parent_dir_path)
            os.chmod(self.parent_dir_path, 0o0777)
            self.parent_dir_path = os.path.join(self.parent_dir_path, 'polyMesh')
        else:
            self.parent_dir_path = os.path.join(os.curdir, 'polyMesh')
        os.mkdir(self.parent_dir_path)
        os.chmod(self.parent_dir_path, 0o0777)

        if self.ascii:
            with open(os.path.join(self.parent_dir_path, 'points'), 'w') as fp:
                fp.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tvectorField;\n' +
                    '\tlocation\t"constant/polyMesh";\n\tobject\tpoints;\n}\n')
                fp.write('{}\n(\n'.format(self.nPoints))
                n = 0
                for k in range(self.kmax):
                    for j in range(self.jmax):
                        for i in range(self.imax):
                            if self.pidx[i, j, k] == n:
                                fp.write('(%#.*e %#.*e %#.*e)\n' % (sys.float_info.dig,  self.x[i, j, k],
                                    sys.float_info.dig, self.y[i, j, k], sys.float_info.dig, self.z[i, j, k]))
                                n += 1
                fp.write(')\n')

            with open(os.path.join(self.parent_dir_path, 'faces'), 'w') as ff:
                ff.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tfaceList;\n' +
                    '\tlocation\t"constant/polyMesh";\n\tobject\tfaces;\n}\n')
                ff.write('{}\n(\n'.format(self.nFaces))
                with open(os.path.join(self.parent_dir_path, 'owner'), 'w') as fo:
                    fo.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tlabelList;\n' +
                        '\tnote"nPoints: %d nCells: %d nFaces: %d nInternalFaces: %d"\n' +
                        '\tlocation\t"constant/polyMesh";\n\tobject\towner;\n}\n' %
                        (self.nPoints, self.nCells, self.nFaces, self.nInternalFaces))
                    fo.write('{}\n(\n'.format(self.nFaces))
                    with open(os.path.join(self.parent_dir_path, 'neighbour'), 'w') as fn:
                        fn.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tascii;\n\tclass\tlabelList;\n' +
                            '\tnote"nPoints: %d nCells: %d nFaces: %d nInternalFaces: %d"\n' +
                            '\tlocation\t"constant/polyMesh";\n\tobject\tneighbour;\n}\n' %
                            (self.nPoints, self.nCells, self.nFaces, self.nInternalFaces))
                        fn.write('{}\n(\n'.format(self.nInternalFaces))
                        # internal faces
                        for i in range(1, imax - 1):
                            for k in range(self.kmax - 1):
                                for j in range(self.jmax - 1):
                                    if self.fiidx[i, j, k, 0] > 0:
                                        ff.write('{}({}'.format(self.fiidx[i, j, k, 0], self.fiidx[i, j, k, 1]))
                                        for n in range(2, self.fiidx[i, j, k, 0] + 1):
                                            ff.write(' {}'.format(self.fiidx[i, j, k, n]))
                                        ff.write(')\n')
                                        fo.write('{}\n'.format(self.cindex(i - 1, j, k)))
                                        fn.write('{}\n'.format(self.cindex(i, j, k)))
                        for j in range(1, jmax - 1):
                            for i in range(imax - 1):
                                for k in range(kmax - 1):
                                    if self.fjidx[i, j, k, 0] > 0:
                                        ff.write('{}({}'.format(self.fjidx[i, j, k, 0], self.fjidx[i, j, k, 1]))
                                        for n in range(2, self.fjidx[i, j, k, 0] + 1):
                                            ff.write(' {}'.format(self.fjidx[i, j, k, n]))
                                        ff.write(')\n')
                                        fo.write('{}\n'.format(self.cindex(i, j - 1, k)))
                                        fn.write('{}\n'.format(self.cindex(i, j, k)))
                        for k in range(1, kmax - 1):
                            for j in range(jmax - 1):
                                for i in range(imax - 1):
                                    if self.fkidx[i, j, k, 0] > 0:
                                        ff.write('{}({}'.format(self.fkidx[i, j, k, 0], self.fkidx[i, j, k, 1]))
                                        for n in range(2, self.fkidx[i, j, k, 0] + 1):
                                            ff.write(' {}'.format(self.fkidx[i, j, k, n]))
                                        ff.write(')\n')
                                        fo.write('{}\n'.format(self.cindex(i, j, k - 1)))
                                        fn.write('{}\n'.format(self.cindex(i, j, k)))
                        fn.write(')\n')
                    # boundary faces
                    for b in self.boundary:
                        if b.i0 == b.i1:
                            for k in range(b.k0, b.k1 - 1):
                                for j in range(b.j0, b.j1 - 1):
                                    if self.fiidx[b.i0, j, k, 0] > 0:
                                        ff.write('{}({}'.format(self.fiidx[b.i0, j, k, 0], self.fiidx[b.i0, j, k, 1]))
                                        for n in range(2, self.fiidx[b.i0, j, k, 0] + 1):
                                            ff.write(' {}'.format(self.fiidx[b.i0, j, k, n]))
                                        ff.write(')\n')
                                        fo.write('{}\n'.format(self.cindex(b.i0 - 1 if b.i0 > 0 else 0, j, k)))
                        elif b.j0 == b.j1:
                            for i in range(b.i0, b.i1 - 1):
                                for k in range(b.k0, b.k1 - 1):
                                    if self.fjidx[i, b.j0, k, 0] > 0:
                                        ff.write('{}({}'.format(self.fjidx[i, b.j0, k, 0], self.fjidx[i, b.j0, k, 1]))
                                        for n in range(2, self.fjidx[i, b.j0, k, 0] + 1):
                                            ff.write(' {}'.format(self.fjidx[i, b.j0, k, n]))
                                        ff.write(')\n')
                                        fo.write('{}\n'.format(self.cindex(i, b.j0 - 1 if b.j0 > 0 else 0, k)))
                        else: # b.k0 == b.k1
                            for j in range(b.j0, b.j1 - 1):
                                for i in range(b.i0, b.i1 - 1):
                                    if self.fkidx[i, j, b.k0, 0] > 0:
                                        ff.write('{}({}'.format(self.fkidx[i, j, b.k0, 0], self.fkidx[i, j, b.k0, 1]))
                                        for n in range(2, self.fkidx[i, j, b.k0, 0] + 1):
                                            ff.write(' {}'.format(self.fkidx[i, j, b.k0, n]))
                                        ff.write(')\n')
                                        fo.write('{}\n'.format(self.cindex(i, j, b.k0 - 1 if b.k0 > 0 else 0)))
                    fo.write(')\n')
                ff.write(')\n')
        else: # not self.ascii
            with open(os.path.join(self.parent_dir_path, 'points'), 'wb') as fp:
                fp.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tbinary;\n\tclass\tvectorField;\n' +
                    '\tlocation\t"constant/polyMesh";\n\tobject\tpoints;\n}\n')
                fp.write('{}\n('.format(self.nPoints))
                n = 0
                for k in range(kmax):
                    for j in range(jmax):
                        for i in range(imax):
                            if pidx[i, j, k] == n:
                                fp.write(pack('<ddd', self.x[i, j, k], self.y[i, j, k], self.z[i, j, k]))
                                n += 1
                fp.write(')\n')

            with open(os.path.join(self.parent_dir_path, 'faces'), 'wb') as ff:
                ff.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tbinary;\n\tclass\tfaceCompactList;\n' +
                    '\tlocation\t"constant/polyMesh";\n\tobject\tfaces;\n}\n')
                ff.write('{}\n('.format(self.nFaces + 1))
                n = 0
                ff.write(pack('<I', n))
                # internal faces
                for i in range(1, imax - 1):
                    for k in range(kmax - 1):
                        for j in range(jmax - 1):
                            if self.fiidx[i, j, k, 0] > 0:
                                n += self.fiidx[i, j, k, 0]
                                ff.write(pack('<I', n))
                for j in range(1, jmax - 1):
                    for i in range(imax - 1):
                        for k in range(kmax - 1):
                            if self.fjidx[i, j, k, 0] > 0:
                                n += self.fjidx[i, j, k, 0]
                                ff.write(pack('<I', n))
                for k in range(1, kmax - 1):
                    for j in range(jmax - 1):
                        for i in range(imax - 1):
                            if self.fkidx[i, j, k, 0] > 0:
                                n += self.fkidx[i, j, k, 0]
                                ff.write(pack('<I', n))
                # boundary faces
                for b in self.boundary:
                    if b.i0 == b.i1:
                        for k in range(b.k0, b.k1 - 1):
                            for j in range(b.j0, b.j1 - 1):
                                if self.fiidx[b.i0, j, k, 0] > 0:
                                    n += self.fiidx[b.i0, j, k, 0]
                                    ff.write(pack('<I', n))
                    elif b.j0 == b.j1:
                        for i in range(b.i0, b.i1 - 1):
                            for k in range(b.k0, b.k1 - 1):
                                if self.fjidx[i, b.j0, k, 0] > 0:
                                    n += self.fjidx[i, b.j0, k, 0]
                                    ff.write(pack('<I', n))
                    else: # b.k0 == b.k1
                        for j in range(b.j0, b.j1 - 1):
                            for i in range(b.i0, b.i1 - 1):
                                if self.fkidx[i, j, b.k0, 0] > 0:
                                    n += self.fkidx[i, j, b.k0, 0]
                                    ff.write(pack('<I', n))
                ff.write(')\n{}\n('.format(self.nFacePoints))

                with open(os.path.join(self.parent_dir_path, 'owner'), 'wb') as fo:
                    fo.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tbinary;\n\tclass\tlabelList;\n' +
                        '\tnote"nPoints: %d nCells: %d nFaces: %d nInternalFaces: %d"\n' +
                        '\tlocation\t"constant/polyMesh";\n\tobject\towner;\n}\n' %
                        (self.nPoints, self.nCells, self.nFaces, self.nInternalFaces))
                    fo.write('{}\n('.format(self.nFaces))
                    with open(os.path.join(self.parent_dir_path, 'neighbour'), 'wb') as fn:
                        fn.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\tbinary;\n\tclass\tlabelList;\n' +
                            '\tnote"nPoints: %d nCells: %d nFaces: %d nInternalFaces: %d"\n' +
                            '\tlocation\t"constant/polyMesh";\n\tobject\tneighbour;\n}\n' %
                            (self.nPoints, self.nCells, self.nFaces, self.nInternalFaces))
                        fn.write('{}\n('.format(self.nInternalFaces))
                        # internal faces
                        for i in range(1, imax - 1):
                            for k in range(kmax - 1):
                                for j in range(jmax - 1):
                                    if self.fiidx[i, j, k, 0] > 0:
                                        self.fiidx[i, j, k, 1:1 + self.fiidx[i, j, k, 0]].astype('<I').tofile(ff)
                                        fo.write(pack('<I', self.cindex(i - 1, j, k)))
                                        fn.write(pack('<I', self.cindex(i, j, k)))
                        for j in range(1, jmax - 1):
                            for i in range(imax - 1):
                                for k in range(kmax - 1):
                                    if self.fjidx[i, j, k, 0] > 0:
                                        self.fjidx[i, j, k, 1:1 + self.fjidx[i, j, k, 0]].astype('<I').tofile(ff)
                                        fo.write(pack('<I', self.cindex(i, j - 1, k)))
                                        fn.write(pack('<I', self.cindex(i, j, k)))
                        for k in range(1, kmax - 1):
                            for j in range(jmax - 1):
                                for i in range(imax - 1):
                                    if self.fkidx[i, j, k, 0] > 0:
                                        self.fkidx[i, j, k, 1:1 + self.fkidx[i, j, k, 0]].astype('<I').tofile(ff)
                                        fo.write(pack('<I', self.cindex(i, j, k - 1)))
                                        fn.write(pack('<I', self.cindex(i, j, k)))
                        fn.write(')\n')
                    # boundary faces
                    for b in self.boundary:
                        if b.i0 == b.i1:
                            for k in range(b.k0, b.k1 - 1):
                                for j in range(b.j0, b.j1 - 1):
                                    if self.fiidx[b.i0, j, k, 0] > 0:
                                        self.fiidx[b.i0, j, k, 1:1 + self.fiidx[b.i0, j, k, 0]].astype('<I').tofile(ff)
                                        fo.write(pack('<I', self.cindex(b.i0 - 1 if b.i0 > 0 else 0, j, k)))
                        elif b.j0 == b.j1:
                            for i in range(b.i0, b.i1 - 1):
                                for k in range(b.k0, b.k1 - 1):
                                    if self.fjidx[i, b.j0, k, 0] > 0:
                                        self.fjidx[i, b.j0, k, 1:1 + self.fjidx[i, b.j0, k, 0]].astype('<I').tofile(ff)
                                        fo.write(pack('<I', self.cindex(i, b.j0 - 1 if b.j0 > 0 else 0, k)))
                        else: # b.k0 == b.k1
                            for j in range(b.j0, b.j1 - 1):
                                for i in range(b.i0, b.i1 - 1):
                                    if self.fkidx[i, j, b.k0, 0] > 0:
                                        self.fkidx[i, j, b.k0, 1:1 + self.fkidx[i, j, b.k0, 0]].astype('<I').tofile(ff)
                                        fo.write(pack('<I', self.cindex(i, j, b.k0 - 1 if b.k0 > 0 else 0)))
                    fo.write(')\n')
                ff.write(')\n')

        with open(os.path.join(self.parent_dir_path, 'boundary'), 'w') as fb:
            fb.write('FoamFile\n{\n\tversion\t2.0;\n\tformat\t%s;\n\tclass\tpolyBoundaryMesh;\n' +
                '\tlocation\t"constant/polyMesh";\n\tobject\tboundary;\n}\n' +
                ('ascii' if self.ascii else 'binary'))
            if self.comment != '':
                fb.write('// {}\n\n'.format(self.comment))
            fb.write('{}\n(\n'.format(len(self.boundary)))
            for b in self.boundary:
                fb.write('\t{}\n\t{\n\t\ttype\t{};\n\t\tnFaces\t{};\n\t\tstartFace\t{};\n\t}\n'.format(
                    b.name, b.type, b.nFaces, b.startFace))
            fb.write(')\n')

        return self
