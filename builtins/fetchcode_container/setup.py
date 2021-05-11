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
    "A ScanCode path provider plugin to provide a prebuilt native skopeo"
    "binary built from sources that are bundled in the repo and sdist."
)


def run_native_build():
    exitcode, output = subprocess.getstatusoutput(["./build.sh"])
    print(output)
    if exitcode:
        raise LibError("Unable to build native")


class BuildNative(distutils_build):

    def run(self):
        self.execute(run_native_build, (), msg="Building native code")
        distutils_build.run(self)


class DevelopNative(setuptools_develop):

    def run(self):
        self.execute(run_rpm_build, (), msg="Building native code")
        setuptools_develop.run(self)


setup(
    name="fetchcode-container",
    version="1.2.3.210511",
    license=" apache-2.0 AND other-permissive",
    description=desc,
    long_description=desc,
    author="nexB",
    author_email="info@aboutcode.org",
    url="https://github.com/nexB/scancode-plugins",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Utilities",
    ],
    keywords=[
        "open source", "docker", "scancode", "container", "fetchcode", "skopeo",
    ],
    install_requires=[
        "plugincode",
    ],
    entry_points={
        "scancode_location_provider": [
            "fetchcode_container= fetchcode_container:SkopeoPaths",
        ],
    },
    cmdclass={"build": BuildNative, "develop": DevelopNative}
)
