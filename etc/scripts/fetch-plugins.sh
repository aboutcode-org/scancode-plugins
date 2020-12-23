#!/bin/bash
#
# Copyright (c) nexB Inc. http://www.nexb.com/ - All rights reserved.
#

# This script fetches the latest binaries and sources for plugins in this repository

set -e

# un-comment to trace execution
# set -x


mkdir -p src-homebrew
mkdir -p src-msys2
mkdir -p src-7z
python etc/scripts/msys2.py
python etc/scripts/homebrew.py
python etc/scripts/7z.py

# https://github.com/nexB/thirdparty-packages/releases/tag/scancode-native
