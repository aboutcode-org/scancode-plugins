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


sys_platform = str(sys.platform).lower()
if sys_platform.startswith('linux'):
    os = 'linux'
elif 'win32' in sys_platform:
    os = 'win64'
elif 'darwin' in sys_platform:
    os = 'macosx'
else:
    raise Exception(f'Unsupported OS/platform {sys_platform}')

src_dir = f'typecode_libmagic-{os}'

desc = '''A ScanCode path provider plugin to provide a prebuilt native libmagic binary and database.'''

setup(
    name='typecode_libmagic',
    version='5.39.1.1',
    license='bsd-simplified',
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
        'open source', 'typecode', 'libmagic'
    ],
    entry_points={
        'scancode_location_provider': [
            'typecode_libmagic = typecode_libmagic:LibmagicPaths',
        ],
    },
)
