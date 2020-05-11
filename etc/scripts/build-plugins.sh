#!/bin/bash
#
# Copyright (c) nexB Inc. http://www.nexb.com/ - All rights reserved.
#

# This script builds wheels for all the plugins

set -e

# un-comment to trace execution
set -x


here="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
mkdir -p $here/dist

for root in builtins misc binary-analysis
  do
    for i in `ls $root`
      do 
        pushd $root/$i
        rm -rf dist build
        python setup.py release
        cp dist/* $here/dist
        popd
      done
  done
