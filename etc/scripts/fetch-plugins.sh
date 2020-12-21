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
mkdir -p src-7zip
python etc/scripts/msys2.py  --cache-dir src-msys2 --build-all
python etc/scripts/homebrew.py  --cache-dir src-homebrew --build-all
python etc/scripts/7z.py  --cache-dir src-7zip
