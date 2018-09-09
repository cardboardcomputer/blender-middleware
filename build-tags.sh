#!/usr/bin/env sh

cd $(dirname $(readlink -f "$0"))

find Blender/2.69/scripts -name '*.py' \
     -exec ctags -e --verbose=yes \
     --exclude=*/__pycache__/* \
     {} +
