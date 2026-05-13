#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 格子点数と領域の大きさを調べる.py
# by Yukiharu Iwamoto
# 2026/5/12 10:01:11 PM

import os
from utilities import misc

if __name__ == '__main__':
    misc.showDirForPresentAnalysis(__file__)

    n, box = misc.bounding_box_of_calculation_range(os.path.join('constant', 'polyMesh', 'points'))
    print('folder\tn_points\tx_min\tx_max\ty_min\ty_max\tz_min\tz_max')
    print(f'{os.path.basename(os.getcwd())}\t{n}\t'
        f'{box[0][0]}\t{box[0][1]}\t{box[1][0]}\t{box[1][1]}\t{box[2][0]}\t{box[2][1]}')
