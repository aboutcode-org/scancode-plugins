#!/usr/bin/env bash
#
# Copyright (c) nexB Inc. http://www.nexb.com/ - All rights reserved.
#

set -e
base_name=rpm-rpm-4.16.1.2-release
cd lib-src/

rm -rf $base_name
tar -xf $base_name.tar.gz

cd $base_name/


# This is to ensure we support ndb, bdb-ro and sqlite formats.
./autogen.sh \
  --enable-static \
  --disable-openmp \
  --enable-bdb=no \
  --enable-bdb-ro=yes \
  --enable-ndb \
  --enable-sqlite=yes \
  --disable-plugins \
  --without-lua  \
  --with-crypto=openssl


make
echo Done building RPM
cp .libs/rpm  ../../src/rpm_inspector_rpm/bin/
cp .libs/rpmdb  ../../src/rpm_inspector_rpm/bin/
cp lib/.libs/librpm.so.9.1.2  ../../src/rpm_inspector_rpm/bin/librpm.so.9
cp rpmio/.libs/librpmio.so.9.1.2  ../../src/rpm_inspector_rpm/bin/librpmio.so.9
strip  ../../src/rpm_inspector_rpm/bin/*
cd ..

#rm -rf $base_name/