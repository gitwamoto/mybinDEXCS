#!/bin/bash
# makeMakeConvinient.sh
# by Yukiharu Iwamoto
# 2026/4/22 12:55:46 PM

#RSYNC_OPTION='--delete'
#RSYNC_OPTION='--delete --dry-run'

cd "$(dirname "$0")"

rsync -av $RSYNC_OPTION ../texteditwx/texteditwx.py binDEXCS（解析フォルダを端末で開いてから）
rsync -av $RSYNC_OPTION ../matplotlibwx makeConvenient/resources --exclude='backup_matplotlibwx.txt' --exclude='.git*'
rsync -av $RSYNC_OPTION binDEXCS（解析フォルダを端末で開いてから） makeConvenient/resources --exclude='*.pyc' --exclude='__init__.py' --exclude='__pycache__'
rsync -av $RSYNC_OPTION copybinDEXCS.sh makeConvenient/resources
rsync -av $RSYNC_OPTION importDXF.py makeConvenient/resources
rsync -av $RSYNC_OPTION FCMacro/exportStl.FCMacro makeConvenient/resources
rsync -av $RSYNC_OPTION FCMacro/makeCfMeshSetting.FCMacro makeConvenient/resources
rsync -av $RSYNC_OPTION FCMacro/makeSnappyHexMeshSetting.FCMacro makeConvenient/resources
rsync -av $RSYNC_OPTION FCMacro/sHM.png makeConvenient/resources

cd -
