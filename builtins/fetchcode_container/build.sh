#!/usr/bin/env bash
#
# Copyright (c) nexB Inc. http://www.nexb.com/ - All rights reserved.
#

set -e

base_name=skopeo-1.2.3

cd lib-src/

rm -rf $base_name
tar -xf $base_name.tar.gz

cd $base_name/


echo Build skopeo
make bin/skopeo
strip bin/skopeo
cp bin/skopeo default-policy.json ../../src/fetchcode_container/bin/
cd ..
echo Done building skopeo

rm -rf $base_name/

