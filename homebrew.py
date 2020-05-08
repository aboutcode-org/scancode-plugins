#!/usr/bin/env python3
# Copyright (c) 2020 nexB Inc.

"""
Utility to keep linux and macOS prebuilt ScanCode toolkit plugins up to date.
"""

import argparse
from distutils.dir_util import copy_tree
import hashlib
import os
import shutil
import sys
import tarfile

import requests


REQUEST_TIMEOUT = 60


TRACE = False
TRACE_DEEP = False

# homebrew uses version names and not numbers.
# See https://en.wikipedia.org/wiki/MacOS_version_history#Releases
MACOS_VERSIONS = {
    '10.6': 'snow_leopard',
    '10.7': 'lion',
    '10.8': 'mountain_lion',
    '10.9': 'mavericks',
    '10.10': 'yosemite',
    '10.11': 'el_capitan',
    '10.12': 'sierra',
    '10.13': 'high_sierra',
    '10.14': 'mojave',
    '10.15': 'catalina',
}


DARWIN_VERSIONS = {
    '10.6': '10',
    '10.7': '11',
    '10.8': '12',
    '10.9': '13',
    '10.10': '14',
    '10.11': '15',
    '10.12': '16',
    '10.13': '17',
    '10.14': '18',
    '10.15': '19',
}


"""
https://github.com/Homebrew/formulae.brew.sh/blob/b578ad73a21ce8078e68c28d2a8a94afc0f31654/_config.yml#L43
homebrew-core
linuxbrew-core
homebrew-cask
"""

class Repository:
    """
    A repository (either 32 or 64 bits) and its collection of packages.
    """

    def __init__(self, name, db_url, formula_base_url):
        self.name = name
        self.db_url = db_url
        self.formula_base_url = formula_base_url
        # a collection of {binary_package_name: BinaryPackage object}
        self.packages = {}

    def fetch_packages_index(self, cache_dir):
        """
        Populate BinaryPackage and SourcePackage in this repo.
        Caches the data for the duration of the session.
        """
        if self.packages:
            return self.packages
        print('Loading Repo from %r' % self.db_url)
        packages = self.packages = {}
        index_loc = os.path.join(cache_dir, f'formula-{self.name}.json')
        req = requests.get(self.db_url, timeout=REQUEST_TIMEOUT)
        with open(index_loc, 'wb') as o:
            o.write(req.content)
        items = req.json()

        for item in items:
            try:
                binary = BinaryPackage.from_index(item, repo=self)
                packages[binary.name] = binary
            except:
                if TRACE_DEEP:
                    print('Skipping incomplete package: {name}'.format(**item))
        return packages


OSARCHES = [
    'catalina', 'mojave', 'high_sierra', 'sierra', 'el_capitan',
    'mavericks', 'yosemite',
    'x86_64_linux'
]


REPOSITORIES = {
    'x86_64_linux': Repository(
        name='linuxbrew',
        db_url='https://formulae.brew.sh/api/formula-linux.json',
        formula_base_url='https://raw.githubusercontent.com/Homebrew/linuxbrew-core/master/Formula/{}.rb'),
    # after polling mac users, high_sierra is the oldest version we support for now
    'high_sierra': Repository(
        name='homebrew',
        db_url='https://formulae.brew.sh/api/formula.json',
        formula_base_url='https://raw.githubusercontent.com/Homebrew/homebrew-core/master/Formula/{}.rb'),

#     'mojave': Repository(
#         name='homebrew',
#         db_url='https://formulae.brew.sh/api/formula.json',
#         formula_base_url='https://raw.githubusercontent.com/Homebrew/homebrew-core/master/Formula/{}.rb'),
#     'catalina': Repository(
#         name='homebrew',
#         db_url='https://formulae.brew.sh/api/formula.json',
#         formula_base_url='https://raw.githubusercontent.com/Homebrew/homebrew-core/master/Formula/{}.rb'),
}



class Download:
    """
    Represent a source, patch or binary download.
    """
    def __init__(self, url, file_name=None, sha256=None):
        self.url = url.strip('/')
        if not file_name:
            _, _, file_name = self.url.rpartition('/')
        self.file_name = file_name
        self.sha256 = sha256
        self.fetched_location = None

    @classmethod
    def from_index(cls, url, tag=None, revision=None, sha256=None, **kwargs):
        """
        The index contains these three fields for a URL:
            "url": "https://github.com/coccinelle/coccinelle.git",
            "tag": "1.0.8",
            "revision": "d678c34afc0cfb479ad34f2225c57b1b8d3ebeae"
        """
        url = url.strip('/')
        if not tag and not revision:
            _, _, file_name = url.rpartition('/')
            return cls(url=url, file_name=file_name,)
        # a github URL
        assert url.startswith('https://github.com'), f'Invalid {url}'
        if not tag and not revision:
            return
        if url.endswith('.git'):
            url, _, _ = url.rpartition('.git')
        # prefer revision over tag
        commitish = revision or tag
        download_url = f'{url}/archive/{commitish}.tar.gz'
        _, _, repo_name = url.rpartition('/')
        file_name = f'{repo_name}-{commitish}.tar.gz'
        return cls(url=download_url, file_name=file_name,)

    def verify(self):
        if not self.fetched_location or not self.sha256:
            print(f'Cannot verify download: {self}')
        with open (self.fetched_location, 'rb') as f:
            fsha256 = hashlib.sha256(f.read()).hexdigest()
            assert fsha256 == self.sha256

    def fetch(self, dir_location, force=False, verify=False):
        """
        Fetch this downloa` and save it in `dir_location`.
        Return the `location` where the file is saved.
        If `force` is False, do not refetch if already fetched.
        """
        self.fetched_location = fetch_file(
            url=self.url, dir_location=dir_location, file_name=self.file_name, force=force)
        return self.fetched_location


class BinaryPackage:

    def __init__(self, name, version, revision, download_urls,
                 formula_download_url, source_download_urls, depends):

        self.name = name
        self.version = version
        self.revision = revision
        # mapping of {osarch: Download}
        self.download_urls = download_urls
        # direct fetch of the ruby code of a formula
        self.formula_download_url = formula_download_url
        # list of Download: archive, patches, etc
        self.source_download_urls = source_download_urls
        self.depends = depends
        self.fullversion = self.version
        if self.revision:
            self.fullversion += '_' + self.revision
        self.fqname = f'{self.name}@{self.fullversion}'

    def __repr__(self) -> str:
        return f'BinaryPackage({self.fqname})'

    def add_formula_source_download_urls(self, location):
        """
        Add source_download_urls found in the Ruby formula file at `location`.
        These would typically be patches.
        """
        known_urls = set(d.url for d in self.source_download_urls)
        for url in get_formula_urls(location):
            if url not in known_urls:
                dnl = Download(url)
                if not dnl:
                    # this can happen for bare github URL when we have no tag or commit
                    continue
                self.source_download_urls.append(dnl)

    @classmethod
    def from_index(cls, item, repo):
        """
        Return a BinaryPackage built from an index entry.
            {
                "name": "clamav",
                "versions": {
                  "stable": "0.102.2",
            ...
                },
                "urls": {
                  "stable": {
                    "url": "https://www.clamav.net/downloads/production/clamav-0.102.2.tar.gz",
                    "tag": null,
                    "revision": null
                  }
                },
                "revision": 0,
                "bottle": {
                  "stable": {
                    "rebuild": 0,
            ...
                    "files": {
                      "catalina": {
                        "url": "https://homebrew.bintray.com/bottles/clamav-0.102.2.catalina.bottle.tar.gz",
                        "sha256": "544f511ddd1c68b88a93f017617c968a4e5d34fc6a010af15e047a76c5b16a9f"
                      },
                      "mojave": {
                        "url": "https://homebrew.bintray.com/bottles/clamav-0.102.2.mojave.bottle.tar.gz",
                        "sha256": "a92959f8a348642739db5e023e4302809c8272da1bea75336635267e449aacdf"
                      },
                    }
                  }
                },
            ....
                "dependencies": [
                  "json-c",
                  "openssl@1.1",
                  "pcre",
                  "yara"
                ],
            ....

        """
        name = item['name']
        version = item['versions']['stable']
        revision = item['revision']
        if revision == 0:
            revision = ''
        revision = str(revision)

        formula_download_url = Download(url=repo.formula_base_url.format(name))
        source_url = item['urls']['stable']
        source_download_urls = [Download.from_index(**source_url)]

        download_urls = {}
        for osarch, durl in item['bottle']['stable']['files'].items():
            if repo.name not in durl['url']:
                # in linuxbrew, we have incorrect URLS for homebrew packages
                continue
            download_urls[osarch] = Download.from_index(**durl)

        depends = []
        for dep in item['dependencies']:
            dname, _, dversion = dep.partition('@')
            depends.append((dname, dversion,))

        return BinaryPackage(
            name=name,
            version=version,
            revision=revision,
            download_urls=download_urls,
            formula_download_url=formula_download_url,
            source_download_urls=source_download_urls,
            depends=depends,
    )

    def get_all_depends(self, binary_packages, ignore_deps=()):
        """
        Yield all the recursive deps of this package given a packages mapping
        of {name: package}
        """
        for dep_name, _dep_req in self.depends:
            if ignore_deps and dep_name in ignore_deps:
                continue

            try:
                depp = binary_packages[dep_name]
            except KeyError:
                depp = binary_packages[dep_name + '-git']

            yield depp

            for subdep in depp.get_all_depends(binary_packages, ignore_deps):
                yield subdep

    def get_unique_depends(self, binary_packages, ignore_deps=()):
        """
        Return a list of unique package deps of this package given a
        packages mapping of {name: package}
        """
        unique = {}
        for dep in self.get_all_depends(binary_packages, ignore_deps):
            if dep.name not in unique:
                unique[dep.name] = dep
        return list(unique.values())


def get_formula_urls(location):
    """
    Yield URLs extracted from the Ruby formula file at location.
    """
    with open(location) as formula:
        for line in formula:
            line = line .strip()
            if line.startswith('url '):
                _, _, url = line.partition('url ')
                yield url.strip(' "')


def fetch_file(url, dir_location, file_name=None, force=False):
    """
    Fetch the file at `url` and save it in `dir_location`.
    Return the `location` where the file is saved.
    If `force` is False, do not refetch if already fetched.
    """
    print('  Fetching %r' % url)
    if not file_name:
        _, _, file_name = url.rpartition('/')
    location = os.path.join(dir_location, file_name)
    if force or not os.path.exists(location):
        with open(location, 'wb') as o:
            o.write(requests.get(url, timeout=REQUEST_TIMEOUT).content)
    return location


def extract_tar(location, target_dir):
    """
    Extract a tar archive at `location` in the `target_dir` directory.
    """

    with open(location, 'rb') as input_tar:
        with tarfile.open(fileobj=input_tar) as tar:
            tar.extractall(target_dir)


def install_files(extracted_dir, install_dir, package_name, package_fullversion, copies=None):
    """
    Install libraries and licenses from the extracted_dir
    - lib dir files are installed in install_dir/lib
    - share/licenses dir files are installed in install_dir/licenses
    - share/docs dir files are installed in install_dir/docs
    """
    # map of src to dst
    default_copies = {
        # base
        'lib': 'lib',
        'bin': 'bin',

        # doc and licenses
        'share': 'licenses',
    }

    copies = copies or default_copies

    if TRACE: print('    Installing with:', copies)

    for src, dst in copies.items():
        isdir = dst.endswith('/')
        src = os.path.join(extracted_dir, src)
        dst = os.path.join(install_dir, dst)
        if os.path.exists(src):
            if TRACE: print('      copying:', src, dst)
            if os.path.isdir(src):
                copy_tree(src, dst)
            else:
                parent = os.path.dirname(dst)
                os.makedirs(parent, exist_ok=True)
                if isdir:
                    os.makedirs(dst, exist_ok=True)
                shutil.copy2(src, dst)


def check_installed_files(install_dir, copies, package):
    """
    Verifies that all the `copies` operations for Package `package` took place with
    all files present in `install_dir`
    """
    missing = []
    for src, dst in copies.items():
        src_isdir = src.endswith('/')
        dst_isdir = dst.endswith('/')
        dst_loc = os.path.join(install_dir, dst)

        if dst_isdir and not src_isdir:
            # file to dir
            filename = os.path.basename(src)
            dst_loc = os.path.join(dst_loc, filename)
            if not os.path.exists(dst_loc):
                missing.append(dst_loc)
            continue
        if dst_isdir and src_isdir:
            # dir to dir
            if not os.path.exists(dst_loc):
                missing.append(dst_loc)
            else:
                if not os.listdir(dst_loc):
                    missing.append(dst_loc)
            continue
        if not dst_isdir:
            # file to file
            if not os.path.exists(dst_loc):
                missing.append(dst_loc)
            continue

        if src_isdir and not dst_isdir:
            # dir to file: illegal
            raise Exception(f'Illegal copy from: {src} to {dst}.')
            continue

    if missing:
        missing = '\n'.join(missing)
        raise Exception(f'These files were not installed for {package}:\n{missing}')


def extract_in_place(location):
    """
    Extract a tar archive at `location` in a directory created side-by-side with
    the archive.
    Return the directory where the files are extracted
    """
    target_dir = location.replace('.tar.xz', '').replace('.tar.gz', '')
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir, exist_ok=True)
    extract_tar(location, target_dir)
    return target_dir


def fetch_package(name, osarch, fullversion=None, cache_dir=None,
                  install_dir=None, ignore_deps=(), copies=None, deletes=()):
    """
    Fetch a `package` with `name` for `osarch` and optional `fullversion` and
    save its sources and binaries as well as its full dependency tree sources
    and binaries in the `cache_dir` directory, ignoring `ignore_deps` list of
    dependencies. Then delete the list of paths under `install_dir` in
    `deletes`. Then install in `install_dir` using `copies` {from:to} copy
    operations.
    """
    # Apply presets
    presets = PRESETS.get((name, osarch,), {})
    copies = copies or presets.get('copies', {})
    ignore_deps = ignore_deps or presets.get('ignore_deps', [])
    fullversion = fullversion or presets.get('fullversion')
    install_dir = install_dir or presets.get('install_dir')
    deletes = deletes or presets.get('deletes', [])

    for deletable in deletes:
        deletable = os.path.join(install_dir, deletable)
        if not os.path.exists(deletable):
            continue
        if os.path.isdir(deletable):
            shutil.rmtree(deletable, ignore_errors=False)
        else:
            os.remove(deletable)

    repository = REPOSITORIES[osarch]
    binary_packages = repository.fetch_packages_index(cache_dir=cache_dir)

    root_package = binary_packages[name]

    if fullversion and fullversion != root_package.fullversion:
        raise Exception(f'Incorrect version for {root_package.name}: {root_package.fullversion} vs. {fullversion}')

    if not cache_dir:
        cache_dir = os.path.dirname(__file__)
    os.makedirs(cache_dir, exist_ok=True)

    bin_cache_dir = os.path.join(cache_dir, 'bin')
    os.makedirs(bin_cache_dir, exist_ok=True)

    src_cache_dir = os.path.join(cache_dir, 'src')
    os.makedirs(src_cache_dir, exist_ok=True)

    if not install_dir:
        raise Exception('install_dir is required.')

    process_package(
        package=root_package, osarch=osarch,
        install_dir=install_dir, copies=copies,
        bin_cache_dir=bin_cache_dir, src_cache_dir=src_cache_dir)

    print('Fetching deps for: {}, ignoring deps: {}'.format(
        root_package.name,
        ', '.join(ignore_deps)))

    for dependency in root_package.get_unique_depends(
            binary_packages=binary_packages,
            ignore_deps=ignore_deps):

        process_package(
            package=dependency, osarch=osarch,
            install_dir=install_dir, copies=copies,
            bin_cache_dir=bin_cache_dir, src_cache_dir=src_cache_dir)

    check_installed_files(install_dir, copies, root_package)


def process_package(package, osarch, install_dir, copies, bin_cache_dir, src_cache_dir):
    """
    Fetch sources and binaries and install files for package.
    """
    print('Fetching package for: {}'.format(package))

    # fetch the binary for the requested osarch
    package_bin = package.download_urls[osarch]
    fetched_binary_loc = package_bin.fetch(dir_location=bin_cache_dir)
    extracted_dir = extract_in_place(location=fetched_binary_loc)

    # fetch the upstream formula and collect extra sources/patches:
    # formula_loc = package.formula_download_url.fetch(dir_location=src_cache_dir)

    # collect the actual formula(s) used for the build (which may be older than upstream)
    brew_dir = os.path.join(extracted_dir, package.name, package.fullversion, '.brew')
    for brew_formula in os.listdir(brew_dir):
        brew_formula_loc = os.path.join(brew_dir, brew_formula)
        shutil.copy2(brew_formula_loc, src_cache_dir)
        package.add_formula_source_download_urls(brew_formula_loc)

    # fetch all sources
    for src_download in package.source_download_urls:
        src_download.fetch(dir_location=src_cache_dir)

    # install the binary
    install_files(
        extracted_dir=extracted_dir, install_dir=install_dir,
        package_name=package.name,
        package_fullversion=package.fullversion,
        copies=copies)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--package', type=str,
        help='Package name to fetch')
    parser.add_argument('-v', '--fullversion', type=str, default=None,
        help='Package fullversion ')
    parser.add_argument('--osarch', type=str,
        choices=OSARCHES,
        help='OS/Arch to use for the selected package ')
    parser.add_argument('--cache-dir', type=str,
        help='Target directory where archives are fetched')
    parser.add_argument('--install-dir', type=str,
        help='Install directory where archive files are copied')
    parser.add_argument('--ignore-deps', type=str, action='append',
        help='Ignore a dependent package with this name. Repeat for more ignores.')
    parser.add_argument('--copies', type=str, action='append',
        help='Copy this extra file or directory from the binary package to the '
             'install directory (such as in foo=bar/data). Repeat for more copies.')
    parser.add_argument('--deletes', type=str, action='append',
        help='Delete this path before installing. Repeat for more paths.')

    args = parser.parse_args()
    name = args.package
    fullversion = args.fullversion
    osarch = args.osarch
    copies = args.copies or {}
    if copies:
        copies = dict(op.split('=') for op in copies)

    ignore_deps = args.ignore_deps or []
    install_dir = args.install_dir or None
    cache_dir = args.cache_dir or None
    deletes = args.deletes  or []

    if TRACE_DEEP:
        print('name:', name)
        print('fullversion:', fullversion)
        print('install_dir:', copies)
        print('ignore_deps:', ignore_deps)
        print('copies:', copies)
        print('deletes:', deletes)

    if args.build_all:
        fetch_package(name='libarchive', osarch='x86_64_linux', cache_dir='homebrew-cache')
        fetch_package(name='p7zip', osarch='x86_64_linux', cache_dir='homebrew-cache')
        fetch_package(name='libmagic', osarch='x86_64_linux', cache_dir='homebrew-cache')
        fetch_package(name='libarchive', osarch='high_sierra', cache_dir='homebrew-cache')
        fetch_package(name='p7zip', osarch='high_sierra', cache_dir='homebrew-cache')
        fetch_package(name='libmagic', osarch='high_sierra', cache_dir='homebrew-cache')

    else:

        fetch_package(name=name, fullversion=fullversion, osarch=osarch, cache_dir=cache_dir,
            install_dir=install_dir, ignore_deps=ignore_deps,
            copies=copies, deletes=deletes)


PRESETS = {
    # latest https://libarchive.org/downloads/libarchive-3.4.2.tar.gz
    ('libarchive', 'x86_64_linux'): {
        'fullversion': '3.4.2_1',
        'ignore_deps': [],
        'deletes': ['licenses', 'lib'],
        'install_dir': 'plugins-builtin/extractcode_libarchive-manylinux1_x86_64/src/extractcode_libarchive',
        'copies': {
            'libarchive/3.4.2_1/lib/libarchive.so': 'lib/',
            'libarchive/3.4.2_1/INSTALL_RECEIPT.json': 'licenses/libarchive/',
            'libarchive/3.4.2_1/COPYING': 'licenses/libarchive/',
            'libarchive/3.4.2_1/README.md': 'licenses/libarchive/',

            'libb2/0.98.1/lib/libb2.so.1': 'lib/',
            'libb2/0.98.1/INSTALL_RECEIPT.json': 'licenses/libb2/',
            'libb2/0.98.1/COPYING': 'licenses/libb2/',

            'libbsd/0.10.0/lib/libbsd.so.0': 'lib/',
            'libbsd/0.10.0/INSTALL_RECEIPT.json': 'licenses/libbsd/',
            'libbsd/0.10.0/COPYING': 'licenses/libbsd/',
            'libbsd/0.10.0/README': 'licenses/libbsd/',
            'libbsd/0.10.0/ChangeLog': 'licenses/libbsd/',

            'bzip2/1.0.8/lib/libbz2.so.1': 'lib/',
            'bzip2/1.0.8/INSTALL_RECEIPT.json': 'licenses/bzip2/',
            'bzip2/1.0.8/LICENSE': 'licenses/bzip2/',
            'bzip2/1.0.8/README': 'licenses/bzip2/',
            'bzip2/1.0.8/CHANGES': 'licenses/bzip2/',

            'expat/2.2.9/lib/libexpat.so.1': 'lib/',
            'expat/2.2.9/INSTALL_RECEIPT.json': 'licenses/expat/',
            'expat/2.2.9/COPYING': 'licenses/expat/',
            'expat/2.2.9/README.md': 'licenses/expat/',
            'expat/2.2.9/AUTHORS': 'licenses/expat/',
            'expat/2.2.9/Changes': 'licenses/expat/',
            'expat/2.2.9/share/doc/expat/changelog': 'licenses/expat/',

            'lz4/1.9.2/lib/liblz4.so.1': 'lib/',
            'lz4/1.9.2/INSTALL_RECEIPT.json': 'licenses/lz4/',
            'lz4/1.9.2/LICENSE': 'licenses/lz4/',
            'lz4/1.9.2/README.md': 'licenses/lz4/',
            'lz4/1.9.2/include/lz4frame_static.h': 'licenses/lz4/lz4.LICENSE',

            'xz/5.2.5/lib/liblzma.so.5': 'lib/',
            'xz/5.2.5/INSTALL_RECEIPT.json': 'licenses/xz/',
            'xz/5.2.5/COPYING': 'licenses/xz/',
            'xz/5.2.5/README': 'licenses/xz/',
            'xz/5.2.5/AUTHORS': 'licenses/xz/',
            'xz/5.2.5/share/doc/xz/THANKS': 'licenses/xz/',
            'xz/5.2.5/ChangeLog': 'licenses/xz/',

            'zlib/1.2.11/lib/libz.so.1': 'lib/',
            'zlib/1.2.11/INSTALL_RECEIPT.json': 'licenses/zlib/',
            'zlib/1.2.11/README': 'licenses/zlib/',
            'zlib/1.2.11/ChangeLog': 'licenses/zlib/',

            'zstd/1.4.4/lib/libzstd.so.1': 'lib/',
            'zstd/1.4.4/INSTALL_RECEIPT.json': 'licenses/zstd/',
            'zstd/1.4.4/COPYING': 'licenses/zstd/',
            'zstd/1.4.4/README.md': 'licenses/zstd/',
            'zstd/1.4.4/LICENSE': 'licenses/zstd/',
            'zstd/1.4.4/CHANGELOG': 'licenses/zstd/',
        }
    },

    ('libarchive', 'high_sierra'): {
        'fullversion': '3.4.2_1',
        'ignore_deps': [],
        'deletes': ['licenses', 'lib'],
        'install_dir': 'plugins-builtin/extractcode_libarchive-macosx_10_9_intel/src/extractcode_libarchive',
        'copies': {
            'libarchive/3.4.2_1/lib/libarchive.13.dylib': 'lib/libarchive.dylib',
            'libarchive/3.4.2_1/INSTALL_RECEIPT.json': 'licenses/libarchive/',
            'libarchive/3.4.2_1/COPYING': 'licenses/libarchive/',
            'libarchive/3.4.2_1/README.md': 'licenses/libarchive/',

            'libb2/0.98.1/lib/libb2.1.dylib': 'lib/',
            'libb2/0.98.1/INSTALL_RECEIPT.json': 'licenses/libb2/',
            'libb2/0.98.1/COPYING': 'licenses/libb2/',

            'lz4/1.9.2/lib/liblz4.1.dylib': 'lib/',
            'lz4/1.9.2/INSTALL_RECEIPT.json': 'licenses/lz4/',
            'lz4/1.9.2/LICENSE': 'licenses/lz4/',
            'lz4/1.9.2/README.md': 'licenses/lz4/',
            'lz4/1.9.2/include/lz4frame_static.h': 'licenses/lz4/lz4.LICENSE',

            'xz/5.2.5/lib/liblzma.5.dylib': 'lib/',
            'xz/5.2.5/INSTALL_RECEIPT.json': 'licenses/xz/',
            'xz/5.2.5/COPYING': 'licenses/xz/',
            'xz/5.2.5/README': 'licenses/xz/',
            'xz/5.2.5/AUTHORS': 'licenses/xz/',
            'xz/5.2.5/share/doc/xz/THANKS': 'licenses/xz/',
            'xz/5.2.5/ChangeLog': 'licenses/xz/',

            'zstd/1.4.4/lib/libzstd.1.dylib': 'lib/',
            'zstd/1.4.4/INSTALL_RECEIPT.json': 'licenses/zstd/',
            'zstd/1.4.4/COPYING': 'licenses/zstd/',
            'zstd/1.4.4/README.md': 'licenses/zstd/',
            'zstd/1.4.4/LICENSE': 'licenses/zstd/',
            'zstd/1.4.4/CHANGELOG': 'licenses/zstd/',
        }
    },


    ('p7zip', 'x86_64_linux'): {
        'fullversion': '16.02_2',
        'install_dir': 'plugins-builtin/extractcode_7z-manylinux1_x86_64/src/extractcode_7z',
        'ignore_deps': [],
        'deletes': ['licenses', 'lib', 'bin', 'doc'],
        'copies': {
            'p7zip/16.02_2/lib/p7zip/7z': 'bin/',
            'p7zip/16.02_2/lib/p7zip/7z.so': 'bin/',

            'p7zip/16.02_2/INSTALL_RECEIPT.json': 'licenses/p7zip/',
            'p7zip/16.02_2/share/doc/p7zip/README': 'licenses/p7zip/',
            'p7zip/16.02_2/share/doc/p7zip/DOC/License.txt': 'licenses/p7zip/',
            'p7zip/16.02_2/share/doc/p7zip/DOC/copying.txt': 'licenses/p7zip/',
            'p7zip/16.02_2/share/doc/p7zip/DOC/unRarLicense.txt': 'licenses/p7zip/',
            'p7zip/16.02_2/share/doc/p7zip/DOC/readme.txt': 'licenses/p7zip/',
            'p7zip/16.02_2/share/doc/p7zip/DOC/src-history.txt': 'licenses/p7zip/',
            'p7zip/16.02_2/share/doc/p7zip/ChangeLog': 'licenses/p7zip/',
        },
    },


    ('p7zip', 'high_sierra'): {
        'fullversion': '16.02_2',
        'install_dir': 'plugins-builtin/extractcode_7z-macosx_10_9_intel/src/extractcode_7z',
        'ignore_deps': [],
        'deletes': ['licenses', 'lib', 'bin', 'doc'],
        'copies': {
            'p7zip/16.02_2/lib/p7zip/7z': 'bin/',
            'p7zip/16.02_2/lib/p7zip/7z.so': 'bin/',

            'p7zip/16.02_2/INSTALL_RECEIPT.json': 'licenses/p7zip/',
            'p7zip/16.02_2/share/doc/p7zip/README': 'licenses/p7zip/',
            'p7zip/16.02_2/share/doc/p7zip/DOC/License.txt': 'licenses/p7zip/',
            'p7zip/16.02_2/share/doc/p7zip/DOC/copying.txt': 'licenses/p7zip/',
            'p7zip/16.02_2/share/doc/p7zip/DOC/unRarLicense.txt': 'licenses/p7zip/',
            'p7zip/16.02_2/share/doc/p7zip/DOC/readme.txt': 'licenses/p7zip/',
            'p7zip/16.02_2/share/doc/p7zip/DOC/src-history.txt': 'licenses/p7zip/',
            'p7zip/16.02_2/share/doc/p7zip/ChangeLog': 'licenses/p7zip/',
        },
    },

    ('libmagic', 'x86_64_linux'): {
        'fullversion': '5.38',
        'install_dir': 'plugins-builtin/typecode_libmagic-manylinux1_x86_64/src/typecode_libmagic',
        'ignore_deps': [],
        'deletes': ['licenses', 'lib', 'bin', 'doc'],
        'copies': {
            'libmagic/5.38/lib/libmagic.so': 'lib/',
            'libmagic/5.38/share/misc/magic.mgc': 'data/',
            'libmagic/5.38/INSTALL_RECEIPT.json': 'licenses/libmagic/',
            'libmagic/5.38/COPYING': 'licenses/libmagic/',
            'libmagic/5.38/README': 'licenses/libmagic/',
            'libmagic/5.38/AUTHORS': 'licenses/libmagic/',
            'libmagic/5.38/ChangeLog': 'licenses/libmagic/',

            'zlib/1.2.11/lib/libz.so.1': 'lib/',
            'zlib/1.2.11/INSTALL_RECEIPT.json': 'licenses/zlib/',
            'zlib/1.2.11/README': 'licenses/zlib/',
            'zlib/1.2.11/ChangeLog': 'licenses/zlib/',
        },
    },
    ('libmagic', 'high_sierra'): {
        'fullversion': '5.38',
        'install_dir': 'plugins-builtin/typecode_libmagic-macosx_10_9_intel/src/typecode_libmagic',
        'ignore_deps': [],
        'deletes': ['licenses', 'lib', 'bin', 'doc'],
        'copies': {
            'libmagic/5.38/lib/libmagic.1.dylib': 'lib/libmagic.dylib',
            'libmagic/5.38/share/misc/magic.mgc': 'data/',
            'libmagic/5.38/INSTALL_RECEIPT.json': 'licenses/libmagic/',
            'libmagic/5.38/COPYING': 'licenses/libmagic/',
            'libmagic/5.38/README': 'licenses/libmagic/',
            'libmagic/5.38/AUTHORS': 'licenses/libmagic/',
            'libmagic/5.38/ChangeLog': 'licenses/libmagic/',
        },
    },

}


if __name__ == '__main__':
    sys.exit(main(sys.argv))
