#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 格子点数と領域の大きさを調べる.py
# by Yukiharu Iwamoto
# 2024/5/28 12:01:56 PM

import os
from utilities import misc

if __name__ == '__main__':
    misc.showDirForPresentAnalysis(__file__)

    n, box = misc.bounding_box_of_calculation_range(os.path.join('constant', 'polyMesh', 'points'))
    print('folder\tn_points\tx_min\tx_max\ty_min\ty_max\tz_min\tz_max')
    print('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(
        os.path.basename(os.getcwd()), n, box[0][0], box[0][1], box[1][0], box[1][1], box[2][0], box[2][1]))
