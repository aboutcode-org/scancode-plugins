#!/usr/bin/env python
# -*- encoding: utf-8 -*-

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
    'A ScanCode path provider plugin to provide a prebuilt native rpm '
    'binary built with many rpmdb formats support. rpm binaries are is built '
    'from sources that are bundled in the repo and sdist.'
)


def run_rpm_build():
    exitcode, output = subprocess.getstatusoutput(['./build.sh'])
    print(output)
    if exitcode:
        raise LibError("Unable to build rpm")


class BuildRPM(distutils_build):

    def run(self):
        self.execute(run_rpm_build, (), msg="Building rpm")
        distutils_build.run(self)


class DevelopRPM(setuptools_develop):

    def run(self):
        self.execute(run_rpm_build, (), msg="Building rpm")
        setuptools_develop.run(self)


setup(
    name='rpm-inspector-rpm',
    version='4.16.1.3.210330.1',
    license=' apache-2.0 AND (gpl-2.0 AND lgpl-2.0)',
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
        'open source', 'packagedcode', 'scancode', 'rpm', 'rpmdb',
    ],
    install_requires=[
        'plugincode',
    ],
    entry_points={
        'scancode_location_provider': [
            'rpm_inspector_rpm = rpm_inspector_rpm:RpmPaths',
        ],
    },
    cmdclass={'build': BuildRPM, 'develop': DevelopRPM}
)
