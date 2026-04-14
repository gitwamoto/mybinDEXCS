#!/bin/bash
# makeMakeConvinient.sh
# by Yukiharu Iwamoto
# 2026/4/14 3:45:35 PM

#RSYNC_OPTION='--delete'
#RSYNC_OPTION='--delete --dry-run'

cd "$(dirname "$0")"

rsync -av $RSYNC_OPTION ../texteditwx/texteditwx.py binDEXCS（解析フォルダを端末で開いてから）
rsync -av $RSYNC_OPTION ../matplotlibwx makeConvenient/resources --exclude=backup_matplotlibwx.txt
rsync -av $RSYNC_OPTION binDEXCS（解析フォルダを端末で開いてから） makeConvenient/resources
rsync -av $RSYNC_OPTION copybinDEXCS.sh makeConvenient/resources
rsync -av $RSYNC_OPTION importDXF.py makeConvenient/resources
rsync -av $RSYNC_OPTION FCMacro/exportStl.FCMacro makeConvenient/resources
rsync -av $RSYNC_OPTION FCMacro/makeCfMeshSetting.FCMacro makeConvenient/resources
rsync -av $RSYNC_OPTION FCMacro/makeSnappyHexMeshSetting.FCMacro makeConvenient/resources
rsync -av $RSYNC_OPTION FCMacro/sHM.png makeConvenient/resources

cd -
