#!/bin/bash
#
# Copyright (c) nexB Inc. http://www.nexb.com/ - All rights reserved.
#

# This script builds wheels for all the plugins

set -e

# un-comment to trace execution
set -x


here="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
dist=$here/../../dist
mkdir -p $dist

for root in builtins misc binary-analysis
  do
    for plugin in `ls $root`
      do 
        pushd $root/$plugin
        rm -rf dist build
        # build and copy up
        python setup.py release
        mv dist/* $dist
        rm -rf build
        popd
      done
  done
