#!/usr/bin/env python3

# Copyright (c) nexB Inc.
# SPDX-License-Identifier: Apache-2.0
#

"""
Utility to keep prebuilt ScanCode toolkit plugins for XPDF up to date.
"""

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
        if not os.path.exists(src):
            raise Exception(f'File not found: {src}')
        if TRACE: print('copying:', src, dst)
        if os.path.isdir(src):
            copy_tree(src, dst)
        else:
            parent = os.path.dirname(dst)
            os.makedirs(parent, exist_ok=True)
            if isdir:
                os.makedirs(dst, exist_ok=True)
            shutil.copy2(src, dst)


def fetch_and_install_package(osarch, cache_dir='src-xpdf'):
    """
    Fetch and install an XPDF package with `osarch` using `cache_dir` directory for cache.
    """
    # Apply presets
    presets = PACKAGES[osarch]

    bin_url = presets['bin_url']
    bin_sha256 = presets['bin_sha256']

    src_url = presets['src_url']
    src_sha256 = presets['src_sha256']

    copies = presets['copies']

    base_dir = presets['base_dir']
    base_dir = os.path.abspath(base_dir)

    install_dir = presets['install_dir']
    install_dir = os.path.join(base_dir, install_dir)
    os.makedirs(install_dir, exist_ok=True)

    cache_dir = os.path.abspath(cache_dir)
    os.makedirs(cache_dir, exist_ok=True)

    print('Fetching package: {}'.format(bin_url))

    fetched_binary_loc = shared_utils.fetch_file(url=bin_url, dir_location=cache_dir)
    shared_utils.verify(fetched_binary_loc, bin_sha256)

    about_resource = os.path.basename(fetched_binary_loc)
    about_dir = os.path.dirname(fetched_binary_loc)
    shared_utils.create_about_file(
        about_resource=about_resource,
        type='generic',
        name=presets['name'],
        version=presets['version'],
        download_url=src_url,
        target_directory=about_dir,
    )

    extracted_dir = shared_utils.extract_in_place(fetched_binary_loc)
    install_files(extracted_dir, install_dir, copies)

    # fetch sources
    fetched_src_loc = shared_utils.fetch_file(url=src_url, dir_location=cache_dir)
    shared_utils.verify(fetched_src_loc, src_sha256)

    about_resource = os.path.basename(fetched_src_loc)
    about_dir = os.path.dirname(fetched_src_loc)
    shared_utils.create_about_file(
        about_resource=about_resource,
        type='generic',
        name=presets['name'],
        version=presets['version'],
        download_url=src_url,
        target_directory=about_dir,
    )

    shutil.rmtree(extracted_dir, ignore_errors=False)


def main():
    fetch_and_install_package(osarch='linux')
    fetch_and_install_package(osarch='macos')
    fetch_and_install_package(osarch='windows')


PACKAGES = {
    'linux': {
        'name': 'pdf2text',
        'version': '4.03',

        'bin_url': 'https://dl.xpdfreader.com/xpdf-tools-linux-4.03.tar.gz',
        'bin_sha256': 'c2d25ecb9c5385e0f60063a62b28daa2a7dc4a980ae40bf3f216f00b2ab7e98e',

        'src_url': 'https://dl.xpdfreader.com/xpdf-4.03.tar.gz',
        'src_sha256': '0fe4274374c330feaadcebb7bd7700cb91203e153b26aa95952f02bf130be846',

        'base_dir': 'builtins/textcode_pdf2text-linux',
        'install_dir': 'src/textcode_pdf2text',
        'copies': {
            'xpdf-tools-linux-4.03/bin64/pdftotext': 'bin/',
            'xpdf-tools-linux-4.03/doc/pdftotext.1': 'licenses/',
            'xpdf-tools-linux-4.03/ANNOUNCE': 'licenses/',
            'xpdf-tools-linux-4.03/CHANGES': 'licenses/',
            'xpdf-tools-linux-4.03/COPYING': 'licenses/',
            'xpdf-tools-linux-4.03/COPYING3': 'licenses/',
            'xpdf-tools-linux-4.03/INSTALL': 'licenses/',
            'xpdf-tools-linux-4.03/README': 'licenses/',
        },
    },

    'macos': {
        'name': 'pdf2text',
        'version': '4.03',

        'bin_url': 'https://dl.xpdfreader.com/xpdf-tools-mac-4.03.tar.gz',
        'bin_sha256': '1045f614bcac94c1baa6c2939e7aed26e020167c26dff59c1a1abfd0f1ba480a',

        'src_url': 'https://dl.xpdfreader.com/xpdf-4.03.tar.gz',
        'src_sha256': '0fe4274374c330feaadcebb7bd7700cb91203e153b26aa95952f02bf130be846',

        'base_dir': 'builtins/textcode_pdf2text-macosx',
        'install_dir': 'src/textcode_pdf2text',
        'copies': {
            'xpdf-tools-mac-4.03/bin64/pdftotext': 'bin/',
            'xpdf-tools-mac-4.03/doc/pdftotext.1': 'licenses/',
            'xpdf-tools-mac-4.03/ANNOUNCE': 'licenses/',
            'xpdf-tools-mac-4.03/CHANGES': 'licenses/',
            'xpdf-tools-mac-4.03/COPYING': 'licenses/',
            'xpdf-tools-mac-4.03/COPYING3': 'licenses/',
            'xpdf-tools-mac-4.03/INSTALL': 'licenses/',
            'xpdf-tools-mac-4.03/README': 'licenses/',
        },
    },

    'windows': {
        'name': 'pdf2text',
        'version': '4.03',

        'bin_url': 'https://dl.xpdfreader.com/xpdf-tools-win-4.03.zip',
        'bin_sha256': 'b74023968740402ca1b40cd47dc5b120814fe95e755f9676340ca9c3ae2b2175',

        'src_url': 'https://dl.xpdfreader.com/xpdf-4.03.tar.gz',
        'src_sha256': '0fe4274374c330feaadcebb7bd7700cb91203e153b26aa95952f02bf130be846',

        'base_dir': 'builtins/textcode_pdf2text-win64',
        'install_dir': 'src/textcode_pdf2text',
        'copies': {
            'xpdf-tools-win-4.03/bin64/pdftotext.exe': 'bin/',
            'xpdf-tools-win-4.03/doc/pdftotext.txt': 'licenses/',
            'xpdf-tools-win-4.03/ANNOUNCE': 'licenses/',
            'xpdf-tools-win-4.03/CHANGES': 'licenses/',
            'xpdf-tools-win-4.03/COPYING': 'licenses/',
            'xpdf-tools-win-4.03/COPYING3': 'licenses/',
            'xpdf-tools-win-4.03/INSTALL': 'licenses/',
            'xpdf-tools-win-4.03/README': 'licenses/',
        },
    },

}

if __name__ == '__main__':
    sys.exit(main())
