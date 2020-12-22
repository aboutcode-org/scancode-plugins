#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

from glob import glob
from os.path import basename
from os.path import join
from os.path import splitext
import sys

from setuptools import find_packages
from setuptools import setup

desc = '''A ScanCode path provider plugin to provide a prebuilt native sevenzip binary.'''

sys_platform = str(sys.platform).lower()
if sys_platform.startswith('linux'):
    os = 'linux'
elif 'win32' in sys_platform:
    os = 'win'
elif 'darwin' in sys_platform:
    os = 'macosx'
else:
    raise Exception(f'Unsupported OS/platform {sys_platform}')

#
src_dir = f'extractcode_7z-{os}'
#
#
setup(
    name='extractcode_7z',
    version='16.5',
    license='lgpl-2.1 and unrar and brian-gladman-3-clause',
    description=desc,
    long_description=desc,
    author='nexB',
    author_email='info@aboutcode.org',
    url='https://github.com/nexB/scancode-plugins',
    packages=find_packages(src_dir),
    package_dir={'': src_dir},
    py_modules=[splitext(basename(path))[0] for path in glob(f'{src_dir}/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
    ],
    keywords=[
        'open source', 'extractcode', 'libarchive'
    ],
    entry_points={
        'scancode_location_provider': [
            'extractcode_7zip = extractcode_7z:SevenzipPaths',
        ],
    },
)
