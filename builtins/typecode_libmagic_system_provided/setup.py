#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from glob import glob
from os.path import basename
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


desc = '''A ScanCode path provider plugin to provide a system package provided libmagic binary and database.'''

setup(
    name='typecode_libmagic_system_provided',
    version='5.39.210531',
    license=(
        'apache-2.0 AND bsd-simplified-darwin AND (bsd-simplified AND public-domain AND '
        'bsd-new AND isc AND (bsd-new OR gpl-1.0-plus) AND bsd-original)'
    ),
    description=desc,
    long_description=desc,
    author='nexB',
    author_email='info@aboutcode.org',
    url='https://github.com/nexB/scancode-plugins',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
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
