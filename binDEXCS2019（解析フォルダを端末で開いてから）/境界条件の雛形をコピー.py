#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 境界条件の雛形をコピー.py
# by Yukiharu Iwamoto
# 2025/3/18 9:08:08 AM

import os
import sys
import signal
import pyperclip
import tty
import termios

src = 'https://develop.openfoam.com/Development/openfoam/tree/maintenance-v2106/src/'

# fixedValueFvPatchFieldのデフォルトはvalueが必要
# zeroGradientFvPatchFieldのデフォルトはvalueが不要
# mixedFvPatchFieldのデフォルトはvalueが不要

boundary_conditions = (
    ('calculated',
    '他の変数から計算可能であることを表す．\n壁面でない境界におけるnutの境界条件としてよく使われる．',
    'value $internalField; // 実際には使わないけど必要',
    src + 'finiteVolume/fields/fvPatchFields/basic/calculated'),
    ('compressible::alphatWallFunction',
    'alphat = mut/Prt（mut: 乱流粘性係数）から壁面乱流温度拡散率を計算する．',
    'Prt 0.85; // 乱流プラントル数\nvalue $internalField; // 実際には使わないけど必要',
    src + 'TurbulenceModels/compressible/turbulentFluidThermoModels/derivedFvPatchFields/wallFunctions/alphatWallFunctions/alphatWallFunction'),
    ('compressible::turbulentTemperatureCoupledBaffleMixed',
    '境界の両側で熱流束が一致するように温度Tを決める．\n' +
    '-kappa*(T_boundary - T)/delta =\n  -kappa_nbr*(T_nbr - T_boundary)/delta_nbr',
    'Tnbr T; // 隣接する場の名前．普通はT．\n' +
    'kappaMethod fluidThermo; // 境界内側の熱伝導率を指定\n// 流体側の境界ならfluidThermo，個体側の境界ならsolidThermo\n' +
    'value $internalField; // 実際には使わないけど必要',
    src + 'TurbulenceModels/compressible/turbulentFluidThermoModels/derivedFvPatchFields/turbulentTemperatureCoupledBaffleMixed'),
    ('compressible::turbulentTemperatureRadCoupledMixed',
    '熱ふく射も含めて，境界の両側で熱流束が一致するように温度Tを決める．\n' +
    '-kappa*(T_boundary - T)/delta + qr =\n  -kappa_nbr*(T_nbr - T_boundary)/delta_nbr - qr_nbr +\n' +
    '  (delta*rho*Cp + delta_nbr*rho_nbr*Cp_nbr)*\n  (T_boundary - T_old)/dt',
    'kappaMethod fluidThermo; // 境界内側の熱伝導率を指定\n// 流体側の境界ならfluidThermo，個体側の境界ならsolidThermo\n' +
    'thermalInertia false; // 境界付近の温度の時間的変化を考慮に入れるか\n' +
    '// falseだとdt = ∞（定常）またはCp = 0に相当する．',
    src + 'TurbulenceModels/compressible/turbulentFluidThermoModels/derivedFvPatchFields/turbulentTemperatureRadCoupledMixed'),
    ('cyclic',
    '周期境界\nconstant/polyMesh/boundaryで\nneighbourPatchを指定しないといけない．\n' +
    'http://penguinitis.g1.xrea.com/study/OpenFOAM/cyclic/cyclic.html',
    '',
    src + 'finiteVolume/fields/fvPatchFields/constraint/cyclic'),
    ('empty',
    '1次元または2次元解析の時に，計算しない方向に垂直な面であることを示す．',
    '',
    src + 'finiteVolume/fields/fvPatchFields/constraint/empty'),
    ('epsilonWallFunction',
    'epsilonの壁面境界条件',
    'value $internalField; // 実際には使わないけど必要',
    src + 'TurbulenceModels/turbulenceModels/derivedFvPatchFields/wallFunctions/epsilonWallFunctions/epsilonWallFunction'),
    ('externalWallHeatFluxTemperature',
    '壁面からの熱伝達',
    'mode flux;\n// flux→熱流束q | power→熱量Q | coefficient→熱伝達率h = q/(T - Ta)\n' +
    'q uniform 100; // fluxの時に使用\n// Q 100; // powerの時に使用\n' +
    '// h 10; // coefficientの時に使用\n// Ta 500; // 外部温度, coefficientの時に使用\n' +
    'kappaMethod fluidThermo; // 境界内側の熱伝導率を指定\n// 流体側の境界ならfluidThermo，個体側の境界ならsolidThermo\n' +
    'value $internalField; // 実際には使わないけど必要',
    src + 'TurbulenceModels/compressible/turbulentFluidThermoModels/derivedFvPatchFields/externalWallHeatFluxTemperature'),
    ('fixedFluxPressure',
    '速度境界条件を満足するようにp_rghを設定',
    '',
    src + 'finiteVolume/fields/fvPatchFields/derived/fixedFluxPressure'),
    ('fixedGradient',
    'こう配をgradientで決めた値にする．',
    'gradient uniform 1.2; // ベクトルの場合は(1.2 3.4 5.6)のように書く．',
    src + 'finiteVolume/fields/fvPatchFields/basic/fixedGradient'),
    ('fixedValue',
    'valueで決めた値に固定',
    'value uniform 1.2; // ベクトルの場合は(1.2 3.4 5.6)のように書く．',
    src + 'finiteVolume/fields/fvPatchFields/basic/fixedValue'),
    ('flowRateInletVelocity',
    '体積流量または質量流量で流入速度を設定し，\n境界に平行な方向の速度は0にする．',
    'volumetricFlowRate 0.1; // 体積流量, massFlowRateとは併用できない．\n' +
    '// massFlowRate 0.1; // 質量流量, volumetricFlowRateとは併用できない．\n' +
    '// rhoInlet 1; // 密度, massFlowRateの場合に必要\n' +
    'extrapolateProfile false;\n// true→内側と相似な速度分布で流入 | false→一様流入\n' +
    'value $internalField; // 実際には使わないけど必要',
    src + 'finiteVolume/fields/fvPatchFields/derived/flowRateInletVelocity'),
    ('freestreamPressure',
    'pに対する自由流入出条件．freestreamVelocityと併用する．\n' +
    '境界垂直方向と流速方向が完全に同じ向きで\n' +
    '流入する時はzeroGradienに規定し，\n' +
    '流出する時はfreestreamValueにする．\n' +
    '完全に同じでないときは，これらの間を連続的に変化させたものを使う．',
    'freestreamValue uniform 1.0e+05;',
    src + 'finiteVolume/fields/fvPatchFields/derived/freestreamPressure'),
    ('freestreamVelocity',
    'Uに対する自由流入出条件．freestreamPressureと併用する．\n' +
    '境界垂直方向と流速方向が完全に同じ向きで\n' +
    '流入する時はfreestreamValueに規定し，\n' +
    '流出する時はzeroGradientにする．\n' +
    '完全に同じでないときは，これらの間を連続的に変化させたものを使う．',
    'freestreamValue uniform (100 0 0);',
    src + 'finiteVolume/fields/fvPatchFields/derived/freestreamVelocity'),
    ('greyDiffusiveRadiationViewFactor',
    '形態係数を利用してふく射による熱流速を決定する．\n' +
    '壁面は灰色体（ふく射率にはconstant/radiationPropertiesの中にある\nemissivityを利用？）とする．',
    'qro uniform 0; // 外部から入るふく射による熱流束',
    src + 'thermophysicalModels/radiation/derivedFvPatchFields/greyDiffusiveViewFactor'),
    ('inletOutlet',
    '計算領域内に流入する場合→inletValueで決めた値に設定\n計算領域外に流出する場合→zeroGradient',
    'inletValue uniform 0; // ベクトルの場合は(1.2 3.4 5.6)のように書く．',
    src + 'finiteVolume/fields/fvPatchFields/derived/inletOutlet'),
    ('kqRWallFunction',
    '高レイノルズ数型乱流モデルにおけるk, q, Rの壁面境界条件\nzeroGrdientのラッパー',
    'value $internalField; // 実際には使わないけど必要',
    src + 'TurbulenceModels/turbulenceModels/derivedFvPatchFields/wallFunctions/kqRWallFunctions/kqRWallFunction'),
    ('movingWallVelocity',
    'Uに使用\n移動壁面の場合のnoSlip条件，壁面が移動しなければnoSlipと同じ',
    'value uniform (0 0 0); // 初期速度',
    src + 'finiteVolume/fields/fvPatchFields/derived/movingWallVelocity'),
    ('nutkRoughWallFunction',
    '荒い壁面に対するnutの境界条件\n' +
    'nutkWallFunctionで使っている式に，\n壁面荒さ（凹凸の高さ）Ks，定数Csによる補正を加えている．\n' +
    'https://dergipark.org.tr/en/download/article-file/202910',
    'Ks uniform 0; // 単位はm，0だと滑面\nCs uniform 0.5; // 0.5 - 1.0，大きいほど荒さの影響大\n' +
    'value $internalField; // 実際には使わないけど必要',
    src + 'TurbulenceModels/turbulenceModels/derivedFvPatchFields/wallFunctions/nutWallFunctions/nutkRoughWallFunction'),
    ('nutkWallFunction',
    '壁面に対するnutの境界条件，標準的\n' +
    'yPlus = C_mu^0.25*sqrt(k)*y/nuから格子中心のyPlusを求め，\n対数則領域内に格子中心があるかどうかを判断する．\n' +
    'ある場合，対数速度分布から得られる壁面せん断応力\ntau_w = mu*kappa*yPlus/log(E*yPlus)*(u/y)\n' +
    'になるように乱流粘性係数を設定する．\nhttps://www.slideshare.net/fumiyanozaki96/openfoam-36426892',
    'value $internalField; // 実際には使わないけど必要',
    src + 'TurbulenceModels/turbulenceModels/derivedFvPatchFields/wallFunctions/nutWallFunctions/nutkWallFunction'),
    ('nutUWallFunction',
    '壁面に対するnutの境界条件\n' +
    '格子中心での速度u，壁からの距離y，対数速度分布から得られる関係\n' +
    'yPlus*log(E*yPlus) = kappa*u*y/nuから格子中心のyPlusを求め，\n対数則領域内に格子中心があるかどうかを判断する．\n' +
    'ある場合，対数速度分布から得られる壁面せん断応力\ntau_w = mu*kappa*yPlus/log(E*yPlus)*(u/y)\n' +
    'になるように乱流粘性係数を設定する．\nhttps://www.slideshare.net/fumiyanozaki96/openfoam-36426892',
    'value $internalField; // 実際には使わないけど必要',
    src + 'TurbulenceModels/turbulenceModels/derivedFvPatchFields/wallFunctions/nutWallFunctions/nutUWallFunction'),
    ('noSlip',
    'U = (0 0 0)に規定',
    '',
    src + 'finiteVolume/fields/fvPatchFields/derived/noSlip'),
    ('omegaWallFunction',
    '壁面に対するomegaの境界条件',
    'value $internalField; // 実際には使わないけど必要',
    src + 'TurbulenceModels/turbulenceModels/derivedFvPatchFields/wallFunctions/omegaWallFunctions/omegaWallFunction'),
    ('outletInlet',
    '計算領域外に流出する場合→outletValueで決めた値に設定\n計算領域内に流入する場合→zeroGradient',
    'outletValue uniform 0; // ベクトルの場合は(1.2 3.4 5.6)のように書く．',
    src + 'finiteVolume/fields/fvPatchFields/derived/outletInlet'),
    ('outletPhaseMeanVelocity',
    'alphaで示す相の平均流出流速がUmeanになるように規定する．\n' +
    '典型的な例としては，曳航水槽による船周りの流れシミュレーションで，\n入口と出口の水位が同じになるようにする場合に使う．',
    'alpha alpha.water;\nUmean 1.2;',
    src + 'finiteVolume/fields/fvPatchFields/derived/outletPhaseMeanVelocity'),
    ('pressureInletOutletVelocity',
    'Uに使用\n計算領域内に流入する場合→垂直方向成分はこう配が0，\n接線方向成分はtangentialVelocityのうちの接線方向成分のみ\n' +
    '計算領域外に流出する場合→全成分でこう配が0',
    'tangentialVelocity uniform (0 0 0);\nvalue $internalField; // 実際には使わないけど必要',
    src + 'finiteVolume/fields/fvPatchFields/derived/pressureInletOutletVelocity'),
    ('prghPressure',
    'p_rghに使用\n設定したいpの値からp_rghを計算して設定する．\n対応するパッチのpにはcalculatedを使う．',
    'rho rhok; // 計算で用いる密度の変数名，rhoまたはrhok\n// pの次元がPaの場合→rho，m^2/s^2にの場合→rhok\n' +
    'p uniform 0; // 設定したいpの値',
    src + 'finiteVolume/fields/fvPatchFields/derived/prghPressure'),
    ('rotatingWallVelocity',
    '速度を回転物体表面の速度と一致させる',
    'origin (0 0 0); // 回転中心\n' +
    'axis (0 0 1); // 回転軸\n' +
    'omega (0 0 1); // 右ねじが進む向きを正とした角速度 [rps]',
    src + 'finiteVolume/fields/fvPatchFields/derived/rotatingWallVelocity'),
    ('slip',
    '非粘性流れの壁面境界条件',
    '',
    src + 'finiteVolume/fields/fvPatchFields/derived/slip'),
    ('surfaceNormalFixedValue',
    '境界に垂直な方向の速度を外向きを正として設定し，平行方向の速度は0にする．',
    'refValue uniform -10; // 垂直方向速度',
    src + 'finiteVolume/fields/fvPatchFields/derived/surfaceNormalFixedValue'),
    ('symmetry',
    '対称境界，境界が曲がっていても使える',
    '',
    src + 'finiteVolume/fields/fvPatchFields/constraint/symmetry'),
    ('symmetryPlane',
    '対称境界，完全な平面にしか使えない',
    '',
    src + 'finiteVolume/fields/fvPatchFields/constraint/symmetryPlane'),
    ('totalPressure',
    'pまたはp_rghに使用\np0で決めた値が全圧（p_rghの場合は全圧 + rho*g*z）になるように設定',
    'p0 uniform 0;',
    src + 'finiteVolume/fields/fvPatchFields/derived/totalPressure'),
    ('turbulentIntensityKineticEnergyInlet',
    '計算領域内に流入する場合→k = 1.5*(intensity*局所速度)^2に規定\n計算領域外に流出する場合→zeroGradient',
    'intensity 0.05;\nvalue $internalField; // 実際には使わないけど必要',
    src + 'finiteVolume/fields/fvPatchFields/derived/turbulentIntensityKineticEnergyInlet'),
    ('turbulentMixingLengthDissipationRateInlet',
    '計算領域内に流入する場合→epsilon = C_mu^0.75*k^1.5/混合距離, C_mu = 0.09に規定\n計算領域外に流出する場合→zeroGradient',
    'mixingLength 0.001; // 混合距離，ふつうは0.07*管内径ぐらいの大きさ\nvalue $internalField; // 実際には使わないけど必要',
    src + 'TurbulenceModels/turbulenceModels/RAS/derivedFvPatchFields/turbulentMixingLengthDissipationRateInlet'),
    ('turbulentMixingLengthFrequencyInlet',
    '計算領域内に流入する場合→omega = k^0.5/(C_mu^0.25*混合距離), C_mu = 0.09に規定\n計算領域外に流出する場合→zeroGradient',
    'mixingLength 0.001; // 混合距離，ふつうは0.07*管内径ぐらいの大きさ\nvalue $internalField; // 実際には使わないけど必要',
    src + 'TurbulenceModels/turbulenceModels/RAS/derivedFvPatchFields/turbulentMixingLengthFrequencyInlet'),
    ('variableHeightFlowRate',
    'alphaに使用\n' +
    'alpha < lowerBoundの時→alpha = lowerBound，\n' +
    'lowerBound < alpha < upperBoundの時→zeroGradient，\n' +
    'upperBound < alpha の時→alpha = upperBound',
    'lowerBound 0.0;\nupperBound 1.0;',
    src + 'finiteVolume/fields/fvPatchFields/derived/variableHeightFlowRate'),
    ('zeroGradient',
    'こう配が0，境界での値 = セル中心での値にする．',
    '',
    src + 'finiteVolume/fields/fvPatchFields/basic/zeroGradient'),
)

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def common_prefix(a, b):
    p = ''
    for i, j in zip(a.lower(), b.lower()):
        if i != j:
            break
        p += i
    return p

def select_boundary_condition():
    type_name = ''
    while True:
        print('\033[1;1H\033[0J')
        print('\033[7m境界条件の雛形をクリップボードにコピーします．\033[m\n')
        n = 0
        s = ''
        p = None
        for bc in boundary_conditions:
            if not bc[0].lower().startswith(type_name.lower()):
                continue
            n += 1
            j = bc[1].find('\n')
            if j == -1:
                j = len(bc[1])
            s += '%s: %s\n' % (bc[0], bc[1][:j])
            p = bc[0] if p is None else common_prefix(p, bc[0])
            selection = bc
        if n == 0:
            print('候補がありません．')
        elif n == 1:
            print('\033[4;5m%s' % s[:-1])
            print('--> %sの雛形をクリップボードにコピーしたければ，Enterを押して下さい．\033[m' % selection[0])
        else:
            print(s[:-1])
        print('\n上に挙げる境界条件の中からtypeの最初の数文字を入力して，候補を絞って下さい．(Enterのみ: 終了, Tab: %sまで書き込む) > %s' % (p, type_name))
        c = getch()
        oc = ord(c)
        if oc == 13: # enter
            if n == 1:
                return selection
            elif type_name == '':
                return None
        elif oc == 127: # delete
            type_name = type_name[:-1]
        elif oc == 9: # tab
            type_name = p
        elif oc == 3: # control + c
            quit()
        else:
            type_name += c

def template_string(bc, indent = '', include_src_url = False):
    s = indent + '{\n' + indent + '\ttype ' + bc[0] + ';\n'
    if bc[1] != '':
        s += indent + '\t// ' + bc[1].replace('\n', '\n' + indent + '\t// ') + '\n'
    if bc[2] != '':
        s += indent + '\t' + bc[2].replace('\n', '\n' + indent + '\t') + '\n'
    if include_src_url and bc[3] != '':
        s += indent + '\t// ' + bc[3] + '\n'
    s += indent + '}\n'
    return s

def write_boundary_conditions(include_src_url = False):
    key = ''
    s = ''
    for bc in boundary_conditions:
        if bc[0][0].upper() != key:
            key = bc[0][0].upper()
            s += '// %sで始まるもの\n' % key
        s += template_string(bc, indent = '', include_src_url = include_src_url)
    with open('境界条件あれこれ.txt', 'w') as f:
        f.write(s)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        write_boundary_conditions(include_src_url = False if len(sys.argv) == 2 else True)
    else:
        signal.signal(signal.SIGINT, signal.SIG_DFL) # Ctrl+Cで終了
        print('\033]2;%s\007' % os.path.basename(__file__))
        print('\033[2J')
        while True:
            selection = select_boundary_condition()
            if selection is None:
                break
            else:
                pyperclip.copy(template_string(selection, '\t'))
                print('コピーしました．変数のファイルにペーストして，適切に書き換えて下さい．')
