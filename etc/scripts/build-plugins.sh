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
        python setup.py release
        if [[ "$plugin" == extractcode_libarchive-linux ]]
        then
            # fix the wheel .so rpaths and copy to the top level dist
            LD_LIBRARY_PATH=$(pwd)/src/extractcode_libarchive/lib \
                auditwheel repair \
                --lib-sdir /lib \
                --plat manylinux2014_x86_64 \
                --wheel-dir $dist \
                dist/$(ls -1 dist) 
        elif [[ "$plugin" == typecode_libmagic-linux ]]
        then
            # fix the wheel .so rpaths and copy to the top level dist
            LD_LIBRARY_PATH=$(pwd)/src/typecode_libmagic/lib \
                auditwheel repair \
                --lib-sdir /lib \
                --plat manylinux2014_x86_64 \
                --wheel-dir $dist \
                dist/$(ls -1 dist) 
        else
            cp dist/* $dist
        fi
        popd
      done
  done
