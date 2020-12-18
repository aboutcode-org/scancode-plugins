#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

from glob import glob
from os.path import basename
from os.path import join
from os.path import splitext
import subprocess

from setuptools import find_packages
from setuptools import setup

from distutils.errors import LibError
from distutils.command.build import build as distutils_build
from setuptools.command.develop import develop as setuptools_develop

desc = (
    'A ScanCode path provider plugin to provide a prebuilt native libmagic '
    'binary and database. libmagic is built from sources that are bundled '
    'in the repo and sdist'
)


def run_libmagic_build():
    exitcode, output = subprocess.getstatusoutput(['./build.sh'])
    print(output)
    if exitcode:
        raise LibError("Unable to build libmagic")


class BuildLibMagic(distutils_build):

    def run(self):
        self.execute(run_libmagic_build, (), msg="Building libmagic")
        distutils_build.run(self)


class DevelopLibMagic(setuptools_develop):

    def run(self):
        self.execute(run_libmagic_build, (), msg="Building libmagic")
        setuptools_develop.run(self)


setup(
    name='typecode_libmagic_from_sources',
    version='5.39.1.1',
    license=(
        'bsd-simplified-darwin AND bsd-simplified AND public-domain AND '
        'bsd-new AND isc AND (bsd-new OR gpl-1.0-plus) AND bsd-original'
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
        'Programming Language :: Python',
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
    cmdclass={'build': BuildLibMagic, 'develop': DevelopLibMagic}
)
