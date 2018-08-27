#!/usr/bin/env sh

VERSION=2.69
BASEDIR=$(dirname $(readlink -f "$0"))

if [ ! -f "$BASEDIR/sync.config" ]; then
    echo "$BASEDIR/sync.config does not exist; see sync.config.example"
    exit 1
fi

. $BASEDIR/sync.config

if [ -z "$BLENDER_USER_PATH" ]; then
    echo "BLENDER_USER_PATH not set in $BASEDIR/sys.config"
    exit 1
fi

BLENDER_REPO_PATH="$BASEDIR/Blender"

update()
{
    if [ "$1" = "repo" ]; then
        A="$BLENDER_USER_PATH/$VERSION"
        B="$BLENDER_REPO_PATH/$VERSION"
    fi

    if [ "$1" = "system" ]; then
        A="$BLENDER_REPO_PATH/$VERSION"
        B="$BLENDER_USER_PATH/$VERSION"

        if [ ! -d "$B" ]; then
            mkdir -p $B
        fi

        cd "$B/scripts/addons"
        rm -fv krz_*.py
        rm -rf __pycache__

        cd "$B/scripts/startup"
        rm -fv log.py space_view3d_mod.py textutils.py
    fi

    cd "$A/config"
    rsync -a --info=name *.blend "$B/config/"

    cd "$A/scripts/modules"
    rsync -a --info=name --exclude=__pycache__ --exclude=*.pyc cc "$B/scripts/modules/"
    rsync -a --info=name --exclude=__pycache__ --exclude=*.pyc krz "$B/scripts/modules/"
    rsync -a --info=name plot.py "$B/scripts/modules/"

    cd "$A/scripts/addons"
    rsync -a --info=name cc_*.py "$B/scripts/addons/"
}

if [ "$1" = "system" ]; then
    update system
fi

if [ "$1" = "repo" ]; then
    update repo
fi

if [ "$1" = "config" ]; then
    cd "$BLENDER_USER_PATH/$VERSION/config"
    rsync -a --info=name *.blend "$BLENDER_REPO_PATH/$VERSION/config/"
fi
