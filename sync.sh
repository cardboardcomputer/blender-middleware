#!/usr/bin/env sh

# Usage:
#
# Make a sync.config file in this dir and define a BLENDER_USER_PATH
# shell variable that points to your system's blender user scripts
# folder (see sync.config.example.)
#
#   ./sync.sh system - Copy files over to the user scripts folder
#   ./sync.sh repo   - Copy files back to the repository
#   ./sync.sh config - Copy only config files back to the repo *
#   ./sync.sh system noconfig   - Exclude config files *
#   ./sync.sh repo noconfig     - Exclude config files *
#
# Config files are `startup.blend` and `userprefs.blend`

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

BLENDER_REPO_PATH="$BASEDIR/Blender/$VERSION"

update()
{
    if [ "$1" = "repo" ]; then
        A="$BLENDER_USER_PATH"
        B="$BLENDER_REPO_PATH"
    fi

    if [ "$1" = "system" ]; then
        A="$BLENDER_REPO_PATH"
        B="$BLENDER_USER_PATH"

        if [ ! -d "$B" ]; then
            mkdir -p $B
        fi

        cd "$B/scripts/addons"
        rm -fv krz_*.py
        rm -rf __pycache__

        cd "$B/scripts/startup"
        rm -fv log.py space_view3d_mod.py textutils.py
    fi

    if [ ! "$2" = "noconfig" ]; then
        cd "$A/config"
        rsync -a --info=name *.blend "$B/config/"
    fi

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
    cd "$BLENDER_USER_PATH/config"
    rsync -a --info=name *.blend "$BLENDER_REPO_PATH/config/"
fi
