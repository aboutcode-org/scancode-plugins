#!/usr/bin/env bash
#
# Copyright (c) nexB Inc. http://www.nexb.com/ - All rights reserved.
#

set -e

base_name=rpm-rpm-4.16.1.3
so_version=9.1.3


cd lib-src/

rm -rf $base_name
tar -xf $base_name.tar.gz

cd $base_name/


# This is to ensure we support ndb, bdb-ro and sqlite formats.
echo Configure RPM 
./autogen.sh \
  --enable-static \
  --enable-shared=no \
  --disable-openmp \
  --enable-bdb=no \
  --enable-bdb-ro=yes \
  --enable-ndb \
  --enable-sqlite=yes \
  --enable-zstd=yes \
  --disable-plugins \
  --without-lua  \
  --with-crypto=libgcrypt \
  --disable-rpath

echo Build RPM
make
strip rpm
cp rpm  ../../src/rpm_inspector_rpm/bin/
cd ..
echo Done building RPM

rm -rf $base_name/

