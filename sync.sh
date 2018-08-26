#!/usr/bin/env sh

VERSION=2.69
SUBPATH="Blender Foundation/Blender/$VERSION"
BASEDIR=$(dirname $(readlink -f "$0"))

. $BASEDIR/sync.config

if [ -z "$BLENDER_APP_BASEDIR" ]; then
    echo "BLENDER_APP_BASEDIR not set"
    echo "Missing $BASEDIR/sys.config?"
    exit 1
fi

if [ -z "$BLENDER_USER_BASEDIR" ]; then
    echo "BLENDER_USER_BASEDIR not set"
    echo "Missing $BASEDIR/sys.config?"
    exit 1
fi

BLENDER_APP_PATH=$BLENDER_APP_BASEDIR/$SUBPATH
BLENDER_USER_PATH=$BLENDER_USER_BASEDIR/$SUBPATH
BLENDER_REPO_PATH=$BASEDIR/Blender/$VERSION

sync()
{
    rsync -a --info=name "$1" "$2" --exclude=__pycache__ --exclude=*.pyc
}

update()
{
    if [ "$1" = "repo" ]; then
        A="$BLENDER_USER_PATH"
        B="$BLENDER_REPO_PATH"
        C="$BLENDER_APP_PATH"
        D="$BLENDER_REPO_PATH"
    fi

    if [ "$1" = "system" ]; then
        A="$BLENDER_REPO_PATH"
        B="$BLENDER_USER_PATH"
        C="$BLENDER_REPO_PATH"
        D="$BLENDER_APP_PATH"
    fi

    cd "$A/config"
    sync *.blend "$B/config/"

    cd "$A/scripts/startup"
    sync *.py "$B/scripts/startup/"

    cd "$A/scripts/modules"
    sync krz "$B/scripts/modules/"
    sync plot.py "$B/scripts/modules/"

    cd "$A/scripts/addons"
    sync krz_*.py "$B/scripts/addons/"

    cd "$C/scripts/addons/io_scene_fbx"
    sync export_fbx.py "$D/scripts/addons/io_scene_fbx/"
    sync __init__.py "$D/scripts/addons/io_scene_fbx/"
}
