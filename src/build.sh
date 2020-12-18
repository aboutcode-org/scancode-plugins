#!/bin/bash
#
# Copyright (c) nexB Inc. http://www.nexb.com/ - All rights reserved.
#
# mini build script for patchelf

# Current directory where this script lives
build_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pushd $build_dir

root_dir=$(dirname $build_dir)

for pe_local_dir in $build_dir/patchelf-*
    do
    if [[ -d "$pe_local_dir" ]]; then
        echo "about to rm -rf $pe_local_dir"
    fi
done

tar -xf patchelf*.tar.gz

patchelf_dir=$build_dir/$(ls patchelf-*/ -d)

pushd $patchelf_dir

./bootstrap.sh
./configure --prefix=$root_dir/tmp --exec-prefix=$root_dir/tmp
make
make install

popd
popd