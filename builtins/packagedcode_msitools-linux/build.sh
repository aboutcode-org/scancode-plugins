#!/usr/bin/env bash
#
# Copyright (c) nexB Inc. http://www.nexb.com/ - All rights reserved.
#

set -e

base_name=msitools-0.101
bats_base_name=bats-core-ce5ca2802fabe5dc38393240cd40e20f8928d3b0

cd lib-src/

rm -rf $base_name
tar -xf $base_name.tar.gz

rm -rf $bats_base_name
unzip $bats_base_name.zip

mv $bats_base_name bats-core
mv bats-core $base_name/subprojects/

cd $base_name/

echo Build msitools
meson build
ninja -C build
strip build/tools/msibuild build/tools/msiextract build/tools/msiinfo
cp build/tools/msibuild build/tools/msidiff build/tools/msidump build/tools/msiextract build/tools/msiinfo ../../src/packagedcode_msitools/bin/
cd ..
echo Done building msitools

rm -rf $base_name/
