#!/bin/bash
#
# Copyright (c) nexB Inc. http://www.nexb.com/ - All rights reserved.
#

# This script uses bumpversion to update the minor version of all plugins

set -e

# un-comment to trace execution
set -x

for root in builtins
  do
    for i in `ls $root`
      do 
        pushd $root/$i
        echo "Bumping $i"
        bumpversion patch
        popd
      done
  done
