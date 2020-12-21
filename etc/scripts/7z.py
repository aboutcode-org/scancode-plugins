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
import sys

import shared_utils

REQUEST_TIMEOUT = 60

TRACE = False
TRACE_DEEP = False


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


    base_dir = presets['base_dir']
    base_dir = os.path.abspath(base_dir)

    source_plugins_dir = presets['source_plugins_dir']
    source_plugins_dir = os.path.abspath(source_plugins_dir)

    base_dir_name = os.path.basename(base_dir)
    saved_sources_dir = os.path.join(source_plugins_dir, base_dir_name)
    if os.path.exists(saved_sources_dir):
        shutil.rmtree(saved_sources_dir, ignore_errors=False)

    install_dir = presets['install_dir']
    install_dir = os.path.join(base_dir, install_dir)
    os.makedirs(install_dir, exist_ok=True)

    thirdparty_dir = presets['thirdparty_dir']
    thirdparty_dir = os.path.join(base_dir, thirdparty_dir)
    os.makedirs(thirdparty_dir, exist_ok=True)

    cache_dir = os.path.abspath(cache_dir)
    os.makedirs(cache_dir, exist_ok=True)

    bin_cache_dir = os.path.join(cache_dir, 'bin')
    os.makedirs(bin_cache_dir, exist_ok=True)

    src_cache_dir = os.path.join(cache_dir, 'src')
    os.makedirs(src_cache_dir, exist_ok=True)

    print('Fetching package: {}'.format(bin_url))

    fetched_binary_loc = shared_utils.fetch_file(url=bin_url, dir_location=bin_cache_dir)
    shared_utils.verify(fetched_binary_loc, bin_sha256)

    extracted_dir = shared_utils.extract_in_place(fetched_binary_loc)
    install_files(extracted_dir, install_dir, copies)

    # fetch sources
    fetched_src_loc = shared_utils.fetch_file(url=src_url, dir_location=src_cache_dir)
    shared_utils.verify(fetched_src_loc, src_sha256)

    # save also in the plugin thirdparty with an ABOUT file
    shutil.copy2(fetched_src_loc, thirdparty_dir)
    about_resource =os.path.basename(fetched_src_loc)
    shared_utils.create_about_file(
        about_resource=about_resource,
        name=presets['name'],
        version=presets['version'],
        download_url=src_url,
        target_directory=thirdparty_dir,
    )

    # finally make a copy of the  plugins with their sources on our "sdist"
    copy_tree(base_dir, saved_sources_dir)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache-dir', type=str,
        help='Target directory where archives are fetched')

    args = parser.parse_args()
    cache_dir = args.cache_dir or None

    cache_dir = cache_dir or 'src-7zip'
    fetch_package(name='7zip-64', cache_dir=cache_dir)



PACKAGES = {
    '7zip-64': {
        'name': '7zip',
        'version': '16.04',
        'bin_url': 'https://master.dl.sourceforge.net/project/sevenzip/7-Zip/16.04/7z1604-x64.exe',
        'bin_sha256': '9bb4dc4fab2a2a45c15723c259dc2f7313c89a5ac55ab7c3f76bba26edc8bcaa',

        'src_url': 'https://master.dl.sourceforge.net/project/sevenzip/7-Zip/16.04/7z1604-src.7z',
        'src_sha256': '4f46b057b8b020e5c1146ca08faae0437a8d176388ffcb16ccbdecaebd9e10d0',

        'base_dir': 'builtins/extractcode_7z-win64',
        'install_dir': 'src/extractcode_7z',
        'thirdparty_dir': 'thirdparty',

        'source_plugins_dir': 'builtins/extractcode_7z-sources',

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
