#!/usr/bin/env bash
#
# Copyright (c) nexB Inc. http://www.nexb.com/ - All rights reserved.
#

set -e
cd lib-src/
rm -rf file-5.39/
tar -xf file-5.39.tar.gz 
cd file-5.39/
./configure 
make
cp src/.libs/libmagic.so.1.0.0  ../../src/typecode_libmagic/lib/libmagic.so
cp magic/magic.mgc ../../src/typecode_libmagic/data/
