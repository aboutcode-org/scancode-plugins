#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from glob import glob
from os.path import basename
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup

desc = '''A ScanCode scan plugin to get lkmclue, dwarf, gwt, cpp includes, code/comments lines generated code and elf info.'''

setup(
    name='compiledcode',
    version='2.1.0',
    license='Apache-2.0',
    description=desc,
    long_description=desc,
    author='nexB',
    author_email='info@aboutcode.org',
    url='https://github.com/nexB/scancode-plugins/binary-analysis/scancode-compiledcode',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list:
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
    keywords=[
        'open source', 'scancode', 'dwarf', 'lkmclue', 'elf', 'cpp includes', 'gwt',
    ],
    install_requires=[
        'commoncode',
        'plugincode',
        'typecode',
        'attrs',
        'pyelftools',
    ],

    extra_requires={
        'full': [
            'scancode-toolkit',
        ],
        'binary': [
            'scancode-ctags',
            'scancode-dwarfdump',
            'scancode-readelf',
        ],
        'testing': [
            'pytest',
        ]
    },
    entry_points={
        'scancode_scan': [
            'scancode-lkmclue = compiledcode.lkmclue:LKMClueScanner',
            'scancode-elf = compiledcode.elf:ELFScanner',
            'scancode-cppincludes = compiledcode.cppincludes:CPPIncludesScanner',
            'scancode-dwarf = compiledcode.dwarf:DwarfScanner',
            'scancode-gwt = compiledcode.gwt:GWTScanner',
            'scancode-makedepend = compiledcode.makedepend:MakeDependScanner',
            'scancode-javaclass = compiledcode.javaclass:JavaClassScanner',
            'scancode-codecommentlines = compiledcode.sourcecode:CodeCommentLinesScanner',
        ],
    }
)
