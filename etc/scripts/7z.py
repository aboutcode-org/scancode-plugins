#!/usr/bin/env python3
# Copyright (c) 2020 nexB Inc.
# Copyright (c) 2016-2019 Christoph Reiter
#

"""
Utility to keep Windows prebuilt ScanCode toolkit plugins for 7zip on Windows up to date.
"""

import argparse
from distutils.dir_util import copy_tree
import os
import shutil
import subprocess
import sys

import shared_utils

REQUEST_TIMEOUT = 60


TRACE = False
TRACE_DEEP = False


def extract_7zip(location, target_dir):
    """
    Extract a 7z archive at `location` in the `target_dir` directory.
    """
    out = subprocess.check_output(['7z', 'x', location], cwd=target_dir)
    if not b'Everything is Ok' in out:
        raise Exception(out)


def install_files(extracted_dir, install_dir, copies):
    """
    Install libraries and licenses from the extracted_dir
    - lib dir files are installed in install_dir/lib
    - share/licenses dir files are installed in install_dir/licenses
    - share/docs dir files are installed in install_dir/docs
    """
    copies = dict(copies)

    if TRACE: print('Installing with:', copies)

    for src, dst in copies.items():
        isdir = dst.endswith('/')
        src = os.path.join(extracted_dir, src)
        dst = os.path.join(install_dir, dst)
        if os.path.exists(src):
            if TRACE: print('copying:', src, dst)
            if os.path.isdir(src):
                copy_tree(src, dst)
            else:
                parent = os.path.dirname(dst)
                os.makedirs(parent, exist_ok=True)
                if isdir:
                    os.makedirs(dst, exist_ok=True)
                shutil.copy2(src, dst)

def extract_in_place(location):
    """
    Extract an archive at `location` in a directory created side-by-side with
    the archive.
    Return the directory where the files are extracted
    """
    target_dir = location.replace('.exe', '')
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir, exist_ok=True)
    extract_7zip(location, target_dir)
    return target_dir


def fetch_package(name, cache_dir):
    """
    Fetch and install a 7z package with `name` using `cache_dir` directory for cache.
    """
    # Apply presets
    presets = PACKAGES[name]

    bin_url = presets['bin_url']
    bin_sha256 = presets['bin_sha256']

    src_url = presets['src_url']
    src_sha256 = presets['src_sha256']

    copies = presets['copies']
    install_dir = presets['install_dir']

    cache_dir = os.path.abspath(cache_dir)
    install_dir = os.path.abspath(install_dir)

    os.makedirs(cache_dir, exist_ok=True)
    bin_cache_dir = os.path.join(cache_dir, 'bin')
    os.makedirs(bin_cache_dir, exist_ok=True)
    src_cache_dir = os.path.join(cache_dir, 'src')
    os.makedirs(src_cache_dir, exist_ok=True)

    print('Fetching package: {}'.format(bin_url))

    fetched_binary_loc = shared_utils.fetch_file(url=bin_url, dir_location=bin_cache_dir)
    shared_utils.verify(fetched_binary_loc, bin_sha256)

    extracted_dir = extract_in_place(fetched_binary_loc)
    install_files(extracted_dir, install_dir, copies)

    # also fetch sources
    fetched_src_loc = shared_utils.fetch_file(url=src_url, dir_location=src_cache_dir)
    shared_utils.verify(fetched_src_loc, src_sha256)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--package', type=str,
        help='Package name to fetch')
    parser.add_argument('--cache-dir', type=str,
        help='Target directory where archives are fetched')
    parser.add_argument('--build-all', action='store_true',
        help='Build all default packages.')

    args = parser.parse_args()
    name = args.package

    cache_dir = args.cache_dir or None

    if TRACE_DEEP:
        print('name:', name)

    if args.build_all:
        cache_dir = cache_dir or 'src-7zip'
        fetch_package(name='7zip-64', cache_dir=cache_dir)
        fetch_package(name='7zip-32', cache_dir=cache_dir)
    else:
        fetch_package(name=name, cache_dir=cache_dir)


PACKAGES = {
    '7zip-64': {
        'bin_url': 'https://master.dl.sourceforge.net/project/sevenzip/7-Zip/16.04/7z1604-x64.exe',
        'bin_sha256': '9bb4dc4fab2a2a45c15723c259dc2f7313c89a5ac55ab7c3f76bba26edc8bcaa',

        'src_url': 'https://master.dl.sourceforge.net/project/sevenzip/7-Zip/16.04/7z1604-src.7z',
        'src_sha256': '4f46b057b8b020e5c1146ca08faae0437a8d176388ffcb16ccbdecaebd9e10d0',

        'install_dir': 'builtins/extractcode_7z-win64/src/extractcode_7z',
        'copies': {
            '7z.exe': 'bin/',
            '7z.dll': 'bin/',
            'License.txt': 'licenses/',
            'readme.txt': 'licenses/',
            'History.txt': 'licenses/',
        },
    },
    '7zip-32': {
        'bin_url': 'https://master.dl.sourceforge.net/project/sevenzip/7-Zip/16.04/7z1604.exe',
        'bin_sha256': 'dbb2b11dea9f4432291e2cbefe14ebe05e021940e983a37e113600eee55daa95',

        'src_url': 'https://master.dl.sourceforge.net/project/sevenzip/7-Zip/16.04/7z1604-src.7z',
        'src_sha256': '4f46b057b8b020e5c1146ca08faae0437a8d176388ffcb16ccbdecaebd9e10d0',

        'install_dir': 'builtins/extractcode_7z-win32/src/extractcode_7z',
        'copies': {
            '7z.exe': 'bin/',
            '7z.dll': 'bin/',
            'License.txt': 'licenses/',
            'readme.txt': 'licenses/',
            'History.txt': 'licenses/',
        },
    },
}


if __name__ == '__main__':
    sys.exit(main(sys.argv))
