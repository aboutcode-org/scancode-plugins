#!/usr/bin/env python3
# Copyright (c) nexB Inc.
# Copyright (c) 2016-2019 Christoph Reiter
#
# Based on MSYS2 web application code.
# download_url: https://raw.githubusercontent.com/msys2/msys2-web/628ec96975ab84b4e13567c8d4bdc25ad1a8f937/main.py

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Utility to keep Windows prebuilt ScanCode toolkit plugins up to date.

This library fetches an msys2 binary package archive and then fetches all its
recursive binary and source packages dependencies. Archives are then extracted.
Finally a configured subset of the files (e.g. dlls, licenses, etc) are installed
in a target directory.

Note that the file formats are essentially the same as ArchLinux.
"""

import argparse
from distutils.dir_util import copy_tree
from itertools import zip_longest
import os
import re
import shutil
import sys
import tarfile
from typing import List, Dict, Tuple, Optional
from urllib.parse import quote

import shared_utils

REQUEST_TIMEOUT = 60

TRACE = False
TRACE_DEEP = False
TRACE_FETCH = False
TRACE_INSTALL = False


class Repository:
    """
    A mingw repository (either 32 or 64 bits) and its collection of packages.
    """

    def __init__(self, name, url, db_url, src_url, vcs_url):
        # mingw64
        self.name = name
        # http://repo.msys2.org/mingw/i686
        self.url = url
        # http://repo.msys2.org/mingw/sources
        self.src_url = src_url
        # http://repo.msys2.org/mingw/x86_64/mingw64.db
        self.db_url = db_url
        # https://github.com/msys2/MINGW-packages
        self.vcs_url = db_url
        # a collection of {binary_package_name: BinaryPackage object}
        self.packages = {}

    def update_packages_index(self, cache_dir):
        """
        Populate BinaryPackage and SourcePackage in this repo.
        Caches the fetched index for the duration of the session.
        """
        if self.packages:
            return self.packages
        print('Loading Repo from %r' % self.db_url)

        binaries = self.packages = {}

        db_loc = shared_utils.fetch_file(
            url=self.db_url,
            dir_location=cache_dir,
            file_name=f'{self.name}.db',
            force=True,
        )

        with open(db_loc, 'rb') as f:
            with tarfile.open(fileobj=f, mode='r:gz') as tar:
                for entry in tar.getmembers():
                    _fqname, _, file_name = entry.name.rpartition('/')
                    if file_name != 'desc':
                        # other names are "files" and we do not need them now
                        continue

                    desc_file = tar.extractfile(entry)
                    if not desc_file:
                        continue

                    with desc_file:
                        desc_text = desc_file.read().decode('utf-8')
                        binary = from_desc(
                            desc_text=desc_text,
                            repo_src_url=self.src_url,
                            base_url=self.url,
                        )
                        if is_newer(binary, binaries):
                            binaries[binary.name] = binary

        for desc_text in OVERRIDES[self.name]:
            binary = from_desc(
                desc_text=desc_text, 
                repo_src_url=self.src_url, 
                base_url=self.url,
            )
            binaries[binary.name] = binary
        return binaries


def is_newer(binary, binaries):
    """
    Return True is the `binary` package is a new package or is newer than other
    package versions in the `binaries` mapping of {name: binary}.
    """
    existing_binary = binaries.get(binary.name)
    if existing_binary:
        if version_is_newer_than(binary.version, existing_binary.version):
            # only keep the latest version
            return True
    else:
        return True


def from_desc(desc_text, repo_src_url, base_url):
    parsed_desc = parse_desc(desc_text)
    if TRACE_DEEP:
        from pprint import pprint
        print('parsed_desc')
        pprint(parsed_desc)

    source = SourcePackage.from_desc(
        desc=parsed_desc,
        repo_src_url=repo_src_url, override=True)

    binary = BinaryPackage.from_desc(
        desc=parsed_desc,
        source_package=source,
        base_url=base_url, override=True)
    return binary


# temporary local data for advanced msys2 builds of patched packages
# that do not exist in the index. These are the text of "desc" as found in the
# index, but recreated manually since this is nt yet in the index
OVERRIDES = {
    'mingw32': [
#         """%FILENAME%
# mingw-w64-i686-file-5.39-1-any.pkg.tar.zst
#
# %NAME%
# mingw-w64-i686-file
#
# %BASE%
# mingw-w64-file
#
# %VERSION%
# 5.39-1
#
# %SHA256SUM%
# b5d2794ed45960520c6d9df2676f571bc8f4a39905649acc465cea40712a29da
#
# %LICENSE%
# BSD
#
# %ARCH%
# any
#
# %DEPENDS%
# mingw-w64-i686-bzip2
# mingw-w64-i686-libsystre
# mingw-w64-i686-xz
# mingw-w64-i686-zlib
# """,

    ],
    'mingw64': [
#         """%FILENAME%
# mingw-w64-x86_64-file-5.39-1-any.pkg.tar.zst
#
# %NAME%
# mingw-w64-x86_64-file
#
# %BASE%
# mingw-w64-file
#
# %VERSION%
# 5.39-1
#
# %SHA256SUM%
# 39fed321c7a61868bc2b728dba576a1d500612aa21d08b9476f474af3a8d18e0
#
# %LICENSE%
# BSD
#
# %ARCH%
# any
#
# %DEPENDS%
# mingw-w64-x86_64-bzip2
# mingw-w64-x86_64-libsystre
# mingw-w64-x86_64-xz
# mingw-w64-x86_64-zlib
# """,
    ]
}

REPOSITORIES = {
    'mingw32': Repository(
        name='mingw32',
        url='http://repo.msys2.org/mingw/i686',
        db_url='http://repo.msys2.org/mingw/i686/mingw32.db',
        src_url='http://repo.msys2.org/mingw/sources',
        vcs_url='https://github.com/msys2/MINGW-packages'),
    'mingw64': Repository(
        name='mingw64',
        url='http://repo.msys2.org/mingw/x86_64',
        db_url='http://repo.msys2.org/mingw/x86_64/mingw64.db',
        src_url='http://repo.msys2.org/mingw/sources',
        vcs_url='https://github.com/msys2/MINGW-packages'),
    'msys32': Repository(
        name='msys32',
        url='http://repo.msys2.org/msys/i686',
        db_url='http://repo.msys2.org/msys/i686/msys.db',
        src_url='http://repo.msys2.org/msys/sources',
        vcs_url='https://github.com/msys2/MSYS2-packages'),
    'msys64': Repository(
        name='msys64',
        url='http://repo.msys2.org/msys/x86_64',
        db_url='http://repo.msys2.org/msys/x86_64/msys.db',
        src_url='http://repo.msys2.org/msys/sources',
        vcs_url='https://github.com/msys2/MSYS2-packages'),
}


class SourcePackage:

    def __init__(self, name, version, repo_src_url, override=False):
        self.name = name
        self.version = version
        # http://repo.msys2.org/mingw/sources/mingw-w64-file-5.37-1.src.tar.gz
        self.download_url = '{repo_src_url}/{name}-{version}.src.tar.gz'.format(
            repo_src_url=repo_src_url,
            name=self.name,
            version=self.version)
        self.override = override

    def __repr__(self) -> str:
        return 'SourcePackage(%s)' % self.download_url

    @property
    def realname(self):
        if self._repo.startswith('mingw'):
            return self.name.split('-', 2)[-1]
        return self.name

    @classmethod
    def from_desc(cls, desc, repo_src_url, override=False):
        """
        Return a new `SourcePackage` object built from a desc `description` mapping.
        """
        name = desc['%NAME%'][0]
        if "%BASE%" not in desc:
            base = name  # "mingw-w64-" + name.split("-", 3)[-1]
        else:
            base = desc["%BASE%"][0]

        version = desc['%VERSION%'][0]
        return cls(name=base, version=version, repo_src_url=repo_src_url, override=override)


def parse_desc(t: str) -> Dict[str, List[str]]:
    """
    Parse a description text and return a mapping of {key: list of string values}.
    For instance:

        %FILENAME%
        mingw-w64-x86_64-gcc-9.3.0-2-any.pkg.tar.xz

        %DEPENDS%
        mingw-w64-x86_64-crt
        mingw-w64-x86_64-headers

    will yield:
        {
        '%FILENAME%': ['mingw-w64-x86_64-gcc-9.3.0-2-any.pkg.tar.xz'],
        '%DEPENDS%': [ 'mingw-w64-x86_64-crt','mingw-w64-x86_64-headers']
        }
    """
    parsed: Dict[str, List[str]] = {}
    cat = None
    values: List[str] = []
    for l in t.splitlines():
        l = l.strip()
        if cat is None:
            cat = l
        elif not l:
            parsed[cat] = values
            cat = None
            values = []
        else:
            values.append(l)
    if cat is not None:
        parsed[cat] = values
    return parsed


class BinaryPackage:

    def __init__(
        self,
        name,
        source_package,
        version,
        depends: List[str],
        filename: str,
        files: List[str],
        makedepends: List[str],
        sha256: str,
        arch: str,
        base_url: str,
        provides: List[str],
        conflicts: List[str],
        replaces: List[str],
        desc: str,
        groups: List[str],
        licenses: List[str],
        optdepends: List[str],
        checkdepends: List[str],
        override=False,
    ) -> None:

        def split_depends(deps: List[str]) -> List[Tuple[str, str]]:
            r = []
            for d in deps:
                parts = re.split('([<>=]+)', d, 1)
                first = parts[0].strip()
                second = ''.join(parts[1:]).strip()
                r.append((first, second))
            return r

        self.depends = split_depends(depends)

        self.checkdepends = split_depends(checkdepends)
        self.filename = filename
        self.makedepends = split_depends(makedepends)
        self.name = name
        self.short_name = name.replace(
            'mingw-w64-x86_64-', '').replace(
            'mingw-w64-i686-', '')

        self.sha256 = sha256
        self.arch = arch
        # http://repo.msys2.org/mingw/x86_64/mingw-w64-x86_64-file-5.37-1-any.pkg.tar.xz
        self.download_url = base_url + '/' + quote(self.filename)
        if TRACE_DEEP:
            print('download_url:', self.download_url)

        self.provides = dict(split_depends(provides))
        self.conflicts = conflicts
        self.replaces = replaces
        self.version = version
        self.source_package = source_package
        self.desc = desc
        self.groups = groups
        self.licenses = licenses
        self.override = override

        def split_opt(deps: List[str]) -> List[Tuple[str, str]]:
            r = []
            for d in deps:
                if ':' in d:
                    a, b = d.split(':', 1)
                    r.append((a.strip(), b.strip()))
                else:
                    r.append((d.strip(), ''))
            return r

        self.optdepends = split_opt(optdepends)

    def __repr__(self) -> str:
        return 'BinaryPackage(%s)' % self.download_url

    @property
    def realprovides(self) -> Dict[str, str]:
        prov = {}
        for key, info in self.provides.items():
            if key.startswith('mingw'):
                key = key.split('-', 3)[-1]
            prov[key] = info
        return prov

    @property
    def realname(self) -> str:
        return self.name.split('-', 3)[-1]

    @classmethod
    def from_desc(cls, desc, source_package, base_url, override=False):
        """
        Return a BinaryPackage built from a desc mapping.
        """
        return cls(
            name=desc['%NAME%'][0],
            source_package=source_package,
            arch=desc['%ARCH%'][0],
            version=desc['%VERSION%'][0],
            filename=desc['%FILENAME%'][0],
            base_url=base_url,

            sha256=desc['%SHA256SUM%'][0],

            desc=desc.get('%DESC%', [''])[0],
            groups=desc.get('%GROUPS%', []),

            licenses=desc.get('%LICENSE%', []),

            files=desc.get('%FILES%', []),

            depends=desc.get('%DEPENDS%', []),

            provides=desc.get('%PROVIDES%', []),
            conflicts=desc.get('%CONFLICTS%', []),
            replaces=desc.get('%REPLACES%', []),
            optdepends=desc.get('%OPTDEPENDS%', []),
            makedepends=desc.get('%MAKEDEPENDS%', []),
            checkdepends=desc.get('%CHECKDEPENDS%', []),
            override=override,
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


def vercmp(v1: str, v2: str) -> int:
    """
    Compare two versions usig the same logic as cmp()
    """

    def cmp(a: int, b: int) -> int:
        return (a > b) - (a < b)

    def split(v: str) -> Tuple[str, str, Optional[str]]:
        if '~' in v:
            e, v = v.split('~', 1)
        else:
            e, v = ('0', v)

        r: Optional[str] = None
        if '-' in v:
            v, r = v.rsplit('-', 1)
        else:
            v, r = (v, None)

        return (e, v, r)

    digit, alpha, other = range(3)

    def get_type(c: str) -> int:
        assert c
        if c.isdigit():
            return digit
        elif c.isalpha():
            return alpha
        else:
            return other

    def parse(v: str) -> List[Tuple[int, Optional[str]]]:
        parts: List[Tuple[int, Optional[str]]] = []
        seps = 0
        current = ''
        for c in v:
            if get_type(c) == other:
                if current:
                    parts.append((seps, current))
                    current = ''
                seps += 1
            else:
                if not current:
                    current += c
                else:
                    if get_type(c) == get_type(current):
                        current += c
                    else:
                        parts.append((seps, current))
                        current = c

        parts.append((seps, current or None))

        return parts

    def rpmvercmp(v1: str, v2: str) -> int:
        for (s1, p1), (s2, p2) in zip_longest(parse(v1), parse(v2),
                                              fillvalue=(None, None)):

            if s1 is not None and s2 is not None:
                ret = cmp(s1, s2)
                if ret != 0:
                    return ret

            if p1 is None and p2 is None:
                return 0

            if p1 is None:
                if get_type(p2) == alpha:
                    return 1
                return -1
            elif p2 is None:
                if get_type(p1) == alpha:
                    return -1
                return 1

            t1 = get_type(p1)
            t2 = get_type(p2)
            if t1 != t2:
                if t1 == digit:
                    return 1
                elif t2 == digit:
                    return -1
            elif t1 == digit:
                ret = cmp(int(p1), int(p2))
                if ret != 0:
                    return ret
            elif t1 == alpha:
                ret = cmp(p1, p2)
                if ret != 0:
                    return ret

        return 0

    e1, v1, r1 = split(v1)
    e2, v2, r2 = split(v2)

    ret = rpmvercmp(e1, e2)
    if ret == 0:
        ret = rpmvercmp(v1, v2)
        if ret == 0 and r1 is not None and r2 is not None:
            ret = rpmvercmp(r1, r2)

    return ret


def version_is_newer_than(v1: str, v2: str) -> bool:
    return vercmp(v1, v2) == 1


def package_name_is_vcs(package_name: str) -> bool:
    return package_name.endswith(
        ("-cvs", "-svn", "-hg", "-darcs", "-bzr", "-git"))


def install_files(extracted_dir, install_dir, package_short_name, copies=None):
    """
    Install libraries and licenses from the extracted_dir
    - lib dir files are installed in install_dir/lib
    - share/licenses dir files are installed in install_dir/licenses
    - share/docs dir files are installed in install_dir/docs
    """
    # map  of src to dst
    # note: the directories MUST end with a /
    copies = dict(copies)

    # also keep .BUILDINF .PKGINFO under the licenses
    copies['.BUILDINFO'] = f'licenses/{package_short_name}/.BUILDINFO'
    copies['.PKGINFO'] = f'licenses/{package_short_name}/.PKGINFO'

    if TRACE: print('Installing with:', copies)

    for src, dst in copies.items():
        isdir = dst.endswith('/')
        src = os.path.join(extracted_dir, src)
        dst = os.path.join(install_dir, dst)
        if os.path.exists(src):
            if TRACE: print('copying:', src, dst)
            if os.path.isdir(src):
                if TRACE_INSTALL:
                    print('Installing:', src, 'to:', dst)
                copy_tree(src, dst)
            else:
                parent = os.path.dirname(dst)
                os.makedirs(parent, exist_ok=True)
                if isdir:
                    os.makedirs(dst, exist_ok=True)
                shutil.copy2(src, dst)
                if TRACE_INSTALL:
                    print('Installing:', src, 'to:', dst)


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


def update_package(name, version=None, repo='mingw64', cache_dir=None,
                  install_dir=None, ignore_deps=(), copies=None, deletes=()):
    """
    Fetch a `package` with `name` and optional `version` from `repo` and save
    its sources and binaries as well as its full dependency tree sources and binaries
    in the `cache_dir` directory, ignoring `ignore_deps` list of dependencies.
    Then delete the list of paths under `install_dir` in `deletes`.
    Then install in `install_dir` using `copies` {from:to} copy operations.
    """
    # Apply presets
    presets = PRESETS.get((name, repo,), {})
    copies = copies or presets.get('copies', {})
    ignore_deps = ignore_deps or presets.get('ignore_deps', [])
    version = version or presets.get('version')
    install_dir = install_dir or presets.get('install_dir')
    deletes = deletes or presets.get('deletes', [])

    print('Updating native code from:', name, version, repo)
    for deletable in deletes:
        deletable = os.path.join(install_dir, deletable)
        if not os.path.exists(deletable):
            continue
        if os.path.isdir(deletable):
            shutil.rmtree(deletable, ignore_errors=False)
        else:
            os.remove(deletable)

    repo = REPOSITORIES[repo]
    binary_packages = repo.update_packages_index(cache_dir=cache_dir)

    root_package = binary_packages[name]

    if version and version != root_package.version:
        raise Exception(f'Incorrect version for {root_package.name}: {root_package.version} vs. {version}')

    if not cache_dir:
        cache_dir = os.path.dirname(__file__)
    os.makedirs(cache_dir, exist_ok=True)

    bin_cache_dir = os.path.join(cache_dir, 'bin')
    os.makedirs(bin_cache_dir, exist_ok=True)

    src_cache_dir = os.path.join(cache_dir, 'src')
    os.makedirs(src_cache_dir, exist_ok=True)

    if not install_dir:
        raise Exception('install_dir is required.')

    if TRACE_FETCH:
        print('Fetching package for: {}'.format(root_package))

    fetched_binary_loc = shared_utils.fetch_file(url=root_package.download_url, dir_location=bin_cache_dir)
    try:
        shared_utils.verify(fetched_binary_loc, root_package.sha256)
    except:
        fetched_binary_loc = shared_utils.fetch_file(url=root_package.download_url, dir_location=bin_cache_dir, force=True)
        shared_utils.verify(fetched_binary_loc, root_package.sha256)
    extracted_dir = shared_utils.extract_in_place(fetched_binary_loc)
    install_files(extracted_dir, install_dir, package_short_name=root_package.short_name, copies=copies)

    extracted_locs = [extracted_dir]

    # also fetch sources
    shared_utils.fetch_file(url=root_package.source_package.download_url, dir_location=src_cache_dir)

    if TRACE_FETCH:
        print('Fetching deps for: {}, ignoring deps: {}'.format(
            root_package.name,
            ', '.join(ignore_deps)))

    for dep in root_package.get_unique_depends(
            binary_packages=binary_packages,
            ignore_deps=ignore_deps):
        if TRACE_FETCH:
            print(f'\n  -> Fetching dependency: {dep}')

        fetched_binary_loc = shared_utils.fetch_file(url=dep.download_url, dir_location=bin_cache_dir, indent=3)
        try:
            shared_utils.verify(fetched_binary_loc, dep.sha256)
        except:
            fetched_binary_loc = shared_utils.fetch_file(url=dep.download_url, dir_location=bin_cache_dir, indent=3, force=True)
            shared_utils.verify(fetched_binary_loc, dep.sha256)
        extracted_dir = shared_utils.extract_in_place(fetched_binary_loc)
        install_files(extracted_dir, install_dir, package_short_name=dep.short_name, copies=copies)

        # also fetch sources
        shared_utils.fetch_file(url=dep.source_package.download_url, dir_location=src_cache_dir, indent=5)

        extracted_locs.append(extracted_dir)

    check_installed_files(install_dir, copies, root_package)

    # finally cleanup after thyself, removing extracted locations
    for loc in extracted_locs:
        shutil.rmtree(loc, False)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--package', type=str,
        help='Package name to fetch')
    parser.add_argument('-v', '--version', type=str, default=None,
        help='Package full version')
    parser.add_argument('--repo', type=str, default='mingw64',
        choices=list(REPOSITORIES),
        help='Repository to use')
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
    parser.add_argument('--build-all', action='store_true',
        help='Build all default packages.')

    args = parser.parse_args()
    name = args.package
    version = args.version
    repo = args.repo
    copies = args.copies or {}
    if copies:
        copies = dict(op.split('=') for op in copies)

    ignore_deps = args.ignore_deps or []
    install_dir = args.install_dir or None
    cache_dir = args.cache_dir or None
    deletes = args.deletes  or []

    if TRACE_DEEP:
        print('name:', name)
        print('version:', version)
        print('install_dir:', copies)
        print('ignore_deps:', ignore_deps)
        print('copies:', copies)
        print('deletes:', deletes)

    if args.build_all:
        cache_dir = cache_dir or 'src-msys2'
        update_package(name='mingw-w64-x86_64-libarchive', repo='mingw64', cache_dir=cache_dir)
        update_package(name='mingw-w64-i686-libarchive', repo='mingw32', cache_dir=cache_dir)
        update_package(name='mingw-w64-x86_64-file', repo='mingw64', cache_dir=cache_dir)
        update_package(name='mingw-w64-i686-file', repo='mingw32', cache_dir=cache_dir)
    else:
        update_package(name=name, version=version, repo=repo, cache_dir=cache_dir,
            install_dir=install_dir, ignore_deps=ignore_deps,
            copies=copies, deletes=deletes)


PRESETS = {
    # latest https://libarchive.org/downloads/libarchive-3.4.2.tar.gz
    ('mingw-w64-x86_64-libarchive', 'mingw64') : {
        'version': '3.4.3-1',
        'ignore_deps': [],
        'deletes': ['licenses', 'lib'],
        'install_dir': 'builtins/extractcode_libarchive-win64/src/extractcode_libarchive',
        'copies': {
            'mingw64/share/licenses/': 'licenses/',
            'mingw64/bin/libarchive-13.dll': 'lib/libarchive.dll',
            'mingw64/include/archive.h': 'licenses/libarchive/libarchive.LICENSE',

            # other libs
            'mingw64/bin/libbz2-1.dll': 'lib/libbz2-1.dll',

            'mingw64/bin/libffi-7.dll': 'lib/libffi-7.dll',

            'mingw64/bin/libtasn1-6.dll': 'lib/libtasn1-6.dll',

            'mingw64/bin/liblz4.dll': 'lib/liblz4.dll',
            'mingw64/include/lz4frame_static.h': 'licenses/lz4/lz4.LICENSE',

            'mingw64/include/mpc.h': 'licenses/mpc/mpc.LICENSE',

            'mingw64/include/mpfr.h': 'licenses/mpfr/mpfr.LICENSE',
            'mingw64/share/doc/mpfr/COPYING.LESSER': 'licenses/mpfr/',
            'mingw64/share/doc/mpfr/AUTHORS': 'licenses/mpfr/',
            'mingw64/share/doc/mpfr/COPYING': 'licenses/mpfr/',
            'mingw64/share/doc/mpfr/COPYING.LESSER': 'licenses/mpfr/',

            'mingw64/bin/libhogweed-6.dll': 'lib/libhogweed-6.dll',
            'mingw64/bin/libnettle-8.dll': 'lib/libnettle-8.dll',
            'mingw64/include/nettle/nettle-meta.h': 'licenses/nettle/nettle.LICENSE',

            # openssl
            'mingw64/bin/libcrypto-1_1-x64.dll': 'lib/libcrypto-1_1-x64.dll',
            'mingw64/bin/libssl-1_1-x64.dll': 'lib/libssl-1_1-x64.dll',

            # p11-kit
            'mingw64/bin/libp11-kit-0.dll': 'lib/libp11-kit-0.dll',
            'mingw64/include/p11-kit-1/p11-kit/p11-kit.h': 'licenses/p11-kit/p11-kit.LICENSE',

            # xz/lzma
            'mingw64/bin/liblzma-5.dll': 'lib/liblzma-5.dll',

            'mingw64/bin/libzstd.dll': 'lib/libzstd.dll',

            # zlib
            'mingw64/bin/zlib1.dll': 'lib/zlib1.dll',

            ######### standard libs
            # expat
            'mingw64/bin/libexpat-1.dll': 'lib/libexpat-1.dll',

            # gcc libs
            'mingw64/bin/libatomic-1.dll': 'lib/libatomic-1.dll',
            'mingw64/bin/libgcc_s_seh-1.dll': 'lib/libgcc_s_seh-1.dll',
            'mingw64/bin/libgomp-1.dll': 'lib/libgomp-1.dll',
            'mingw64/bin/libquadmath-0.dll': 'lib/libquadmath-0.dll',
            'mingw64/bin/libssp-0.dll': 'lib/libssp-0.dll',
            'mingw64/bin/libstdc++-6.dll': 'lib/libstdc++-6.dll',

            # gettext
            'mingw64/bin/libasprintf-0.dll': 'lib/libasprintf-0.dll',
            'mingw64/bin/libgettextlib-0-19-8-1.dll': 'lib/libgettextlib-0-19-8-1.dll',
            'mingw64/bin/libgettextpo-0.dll': 'lib/libgettextpo-0.dll',
            'mingw64/bin/libgettextsrc-0-19-8-1.dll': 'lib/libgettextsrc-0-19-8-1.dll',
            'mingw64/bin/libintl-8.dll': 'lib/libintl-8.dll',

            # gmp
            'mingw64/bin/libgmp-10.dll': 'lib/libgmp-10.dll',
            'mingw64/bin/libgmpxx-4.dll': 'lib/libgmpxx-4.dll',
            'mingw64/include/gmp.h': 'licenses/gmp/gmp.LICENSE',

            # iconv
            'mingw64/bin/libcharset-1.dll': 'lib/libcharset-1.dll',
            'mingw64/bin/libiconv-2.dll': 'lib/libiconv-2.dll',

            # tre and systre
            'mingw64/bin/libsystre-0.dll': 'lib/libsystre-0.dll',
            'mingw64/bin/libtre-5.dll': 'lib/libtre-5.dll',

            # libwinpthread
            'mingw64/bin/libwinpthread-1.dll': 'lib/libwinpthread-1.dll',
        },
    },
    ('mingw-w64-i686-libarchive', 'mingw32') : {
        'version': '3.4.3-1',
        'ignore_deps': [],
        'deletes': ['licenses', 'lib'],
        'install_dir': 'builtins/extractcode_libarchive-win32/src/extractcode_libarchive',
        'copies': {

            'mingw32/share/licenses/': 'licenses/',
            'mingw32/bin/libarchive-13.dll': 'lib/libarchive.dll',
            'mingw32/include/archive.h': 'licenses/libarchive/libarchive.LICENSE',

            # other libs
            'mingw32/bin/libbz2-1.dll': 'lib/libbz2-1.dll',
            'mingw32/bin/liblzma-5.dll': 'lib/liblzma-5.dll',
            'mingw32/bin/zlib1.dll': 'lib/zlib1.dll',

            'mingw32/bin/libzstd.dll': 'lib/libzstd.dll',

            'mingw32/bin/libffi-7.dll': 'lib/libffi-7.dll',

            'mingw32/bin/libtasn1-6.dll': 'lib/libtasn1-6.dll',

            'mingw32/bin/liblz4.dll': 'lib/liblz4.dll',
            'mingw32/include/lz4frame_static.h': 'licenses/lz4/lz4.LICENSE',

            'mingw32/include/mpc.h': 'licenses/mpc.LICENSE',

            'mingw32/include/mpfr.h': 'licenses/mpfr/mpfr.LICENSE',
            'mingw32/share/doc/mpfr/COPYING.LESSER': 'licenses/mpfr/',
            'mingw32/share/doc/mpfr/AUTHORS': 'licenses/mpfr/',
            'mingw32/share/doc/mpfr/COPYING': 'licenses/mpfr/',
            'mingw32/share/doc/mpfr/COPYING.LESSER': 'licenses/mpfr/',

            'mingw32/bin/libhogweed-6.dll': 'lib/libhogweed-6.dll',
            'mingw32/bin/libnettle-8.dll': 'lib/libnettle-8.dll',
            'mingw32/include/nettle/nettle-meta.h': 'licenses/nettle/nettle.LICENSE',

            # openssl
            'mingw32/bin/libcrypto-1_1.dll': 'lib/libcrypto-1_1.dll',
            'mingw32/bin/libssl-1_1.dll': 'lib/libssl-1_1.dll',

            'mingw32/bin/libp11-kit-0.dll': 'lib/libp11-kit-0.dll',
            'mingw32/include/p11-kit-1/p11-kit/p11-kit.h': 'licenses/p11-kit/p11-kit.LICENSE',

            ######### standard libs
            # expat
            'mingw32/bin/libexpat-1.dll': 'lib/libexpat-1.dll',

            # gcc libs
            'mingw32/bin/libatomic-1.dll': 'lib/libatomic-1.dll',
            'mingw32/bin/libgomp-1.dll': 'lib/libgomp-1.dll',
            'mingw32/bin/libquadmath-0.dll': 'lib/libquadmath-0.dll',
            'mingw32/bin/libssp-0.dll': 'lib/libssp-0.dll',
            'mingw32/bin/libstdc++-6.dll': 'lib/libstdc++-6.dll',
            'mingw32/bin/libgcc_s_dw2-1.dll': 'lib/libgcc_s_dw2-1.dll',

            # gettext
            'mingw32/bin/libasprintf-0.dll': 'lib/libasprintf-0.dll',
            'mingw32/bin/libgettextlib-0-19-8-1.dll': 'lib/libgettextlib-0-19-8-1.dll',
            'mingw32/bin/libgettextpo-0.dll': 'lib/libgettextpo-0.dll',
            'mingw32/bin/libgettextsrc-0-19-8-1.dll': 'lib/libgettextsrc-0-19-8-1.dll',
            'mingw32/bin/libintl-8.dll': 'lib/libintl-8.dll',

            # gmp
            'mingw32/bin/libgmp-10.dll': 'lib/libgmp-10.dll',
            'mingw32/bin/libgmpxx-4.dll': 'lib/libgmpxx-4.dll',
            'mingw32/include/gmp.h': 'licenses/gmp/gmp.LICENSE',

            # iconv
            'mingw32/bin/libcharset-1.dll': 'lib/libcharset-1.dll',
            'mingw32/bin/libiconv-2.dll': 'lib/libiconv-2.dll',

            # tre and systre
            'mingw32/bin/libsystre-0.dll': 'lib/libsystre-0.dll',
            'mingw32/bin/libtre-5.dll': 'lib/libtre-5.dll',

            # libwinpthread
            'mingw32/bin/libwinpthread-1.dll': 'lib/libwinpthread-1.dll',
        }
    },

    ('mingw-w64-x86_64-file', 'mingw64') : {
        'version': '5.39-1',
        'ignore_deps': [],
        'install_dir': 'builtins/typecode_libmagic-win64/src/typecode_libmagic',
        'deletes': ['licenses', 'lib', 'data'],
        'copies': {
            'mingw64/share/licenses/': 'licenses/',
            'mingw64/bin/libmagic-1.dll': 'lib/libmagic.dll',
            'mingw64/share/misc/magic.mgc': 'data/magic.mgc',

            'mingw64/bin/libbz2-1.dll': 'lib/libbz2-1.dll',
            'mingw64/bin/liblzma-5.dll': 'lib/liblzma-5.dll',
            'mingw64/bin/zlib1.dll': 'lib/zlib1.dll',

            ######### standard libs
            # expat
            'mingw64/bin/libexpat-1.dll': 'lib/libexpat-1.dll',

            # gcc libs
            'mingw64/bin/libatomic-1.dll': 'lib/libatomic-1.dll',
            'mingw64/bin/libgcc_s_seh-1.dll': 'lib/libgcc_s_seh-1.dll',
            'mingw64/bin/libgomp-1.dll': 'lib/libgomp-1.dll',
            'mingw64/bin/libquadmath-0.dll': 'lib/libquadmath-0.dll',
            'mingw64/bin/libssp-0.dll': 'lib/libssp-0.dll',
            'mingw64/bin/libstdc++-6.dll': 'lib/libstdc++-6.dll',

            # gettext
            'mingw64/bin/libasprintf-0.dll': 'lib/libasprintf-0.dll',
            'mingw64/bin/libgettextlib-0-19-8-1.dll': 'lib/libgettextlib-0-19-8-1.dll',
            'mingw64/bin/libgettextpo-0.dll': 'lib/libgettextpo-0.dll',
            'mingw64/bin/libgettextsrc-0-19-8-1.dll': 'lib/libgettextsrc-0-19-8-1.dll',
            'mingw64/bin/libintl-8.dll': 'lib/libintl-8.dll',

            # gmp
            'mingw64/bin/libgmp-10.dll': 'lib/libgmp-10.dll',
            'mingw64/bin/libgmpxx-4.dll': 'lib/libgmpxx-4.dll',
            'mingw64/include/gmp.h': 'licenses/gmp/gmp.LICENSE',

            # iconv
            'mingw64/bin/libcharset-1.dll': 'lib/libcharset-1.dll',
            'mingw64/bin/libiconv-2.dll': 'lib/libiconv-2.dll',

            # tre and systre
            'mingw64/bin/libsystre-0.dll': 'lib/libsystre-0.dll',
            'mingw64/bin/libtre-5.dll': 'lib/libtre-5.dll',

            # libwinpthread
            'mingw64/bin/libwinpthread-1.dll': 'lib/libwinpthread-1.dll',
        }
    },

    ('mingw-w64-i686-file', 'mingw32') : {
        'version': '5.39-1',
        'ignore_deps': [],
        'install_dir': 'builtins/typecode_libmagic-win32/src/typecode_libmagic',
        'deletes': ['licenses', 'lib', 'data'],
        'copies': {
            'mingw32/share/licenses/': 'licenses/',
            'mingw32/bin/libmagic-1.dll': 'lib/libmagic.dll',
            'mingw32/share/misc/magic.mgc': 'data/magic.mgc',

            'mingw32/bin/libbz2-1.dll': 'lib/libbz2-1.dll',
            'mingw32/bin/liblzma-5.dll': 'lib/liblzma-5.dll',
            'mingw32/bin/zlib1.dll': 'lib/zlib1.dll',

            ######### standard libs
            # expat
            'mingw32/bin/libexpat-1.dll': 'lib/libexpat-1.dll',

            # gcc libs
            'mingw32/bin/libatomic-1.dll': 'lib/libatomic-1.dll',
            'mingw32/bin/libgomp-1.dll': 'lib/libgomp-1.dll',
            'mingw32/bin/libquadmath-0.dll': 'lib/libquadmath-0.dll',
            'mingw32/bin/libssp-0.dll': 'lib/libssp-0.dll',
            'mingw32/bin/libstdc++-6.dll': 'lib/libstdc++-6.dll',
            'mingw32/bin/libgcc_s_dw2-1.dll': 'lib/libgcc_s_dw2-1.dll',

            # gettext
            'mingw32/bin/libasprintf-0.dll': 'lib/libasprintf-0.dll',
            'mingw32/bin/libgettextlib-0-19-8-1.dll': 'lib/libgettextlib-0-19-8-1.dll',
            'mingw32/bin/libgettextpo-0.dll': 'lib/libgettextpo-0.dll',
            'mingw32/bin/libgettextsrc-0-19-8-1.dll': 'lib/libgettextsrc-0-19-8-1.dll',
            'mingw32/bin/libintl-8.dll': 'lib/libintl-8.dll',

            # gmp
            'mingw32/bin/libgmp-10.dll': 'lib/libgmp-10.dll',
            'mingw32/bin/libgmpxx-4.dll': 'lib/libgmpxx-4.dll',
            'mingw32/include/gmp.h': 'licenses/gmp.LICENSE',

            # iconv
            'mingw32/bin/libcharset-1.dll': 'lib/libcharset-1.dll',
            'mingw32/bin/libiconv-2.dll': 'lib/libiconv-2.dll',

            # tre and systre
            'mingw32/bin/libsystre-0.dll': 'lib/libsystre-0.dll',
            'mingw32/bin/libtre-5.dll': 'lib/libtre-5.dll',

            # libwinpthread
            'mingw32/bin/libwinpthread-1.dll': 'lib/libwinpthread-1.dll',
        }
    },

    ('mingw-w64-x86_64-universal-ctags-git', 'mingw64'): {
        'version': 'r7253.7492b90e-1',
        'install_dir': 'binary-analysis/scancode-ctags-win64/src/scancode_ctags',
        'ignore_deps': [],
        'deletes': ['licenses', 'bin', 'lib', ],
        'copies': {
            'mingw64/share/licenses/': 'licenses/',
            'mingw64/bin/ctags.exe': 'bin/ctags.exe',

            'mingw64/bin/libjansson-4.dll': 'bin/libjansson-4.dll',
            'mingw64/bin/liblzma-5.dll': 'bin/liblzma-5.dll',
            'mingw64/bin/libxml2-2.dll': 'bin/libxml2-2.dll',
            'mingw64/bin/libyaml-0-2.dll': 'bin/libyaml-0-2.dll',
            'mingw64/bin/xml2-config': 'bin/xml2-config',
            'mingw64/bin/zlib1.dll': 'bin/zlib1.dll',

            'mingw64/bin/libasprintf-0.dll': 'bin/libasprintf-0.dll',
            'mingw64/bin/libatomic-1.dll': 'bin/libatomic-1.dll',
            'mingw64/bin/libcharset-1.dll': 'bin/libcharset-1.dll',
            'mingw64/bin/libexpat-1.dll': 'bin/libexpat-1.dll',
            'mingw64/bin/libgcc_s_seh-1.dll': 'bin/libgcc_s_seh-1.dll',
            'mingw64/bin/libgettextlib-0-19-8-1.dll': 'bin/libgettextlib-0-19-8-1.dll',
            'mingw64/bin/libgettextpo-0.dll': 'bin/libgettextpo-0.dll',
            'mingw64/bin/libgettextsrc-0-19-8-1.dll': 'bin/libgettextsrc-0-19-8-1.dll',
            'mingw64/bin/libgmp-10.dll': 'bin/libgmp-10.dll',
            'mingw64/bin/libgmpxx-4.dll': 'bin/libgmpxx-4.dll',
            'mingw64/bin/libgomp-1.dll': 'bin/libgomp-1.dll',
            'mingw64/bin/libiconv-2.dll': 'bin/libiconv-2.dll',
            'mingw64/bin/libintl-8.dll': 'bin/libintl-8.dll',
            'mingw64/bin/libquadmath-0.dll': 'bin/libquadmath-0.dll',
            'mingw64/bin/libssp-0.dll': 'bin/libssp-0.dll',
            'mingw64/bin/libstdc++-6.dll': 'bin/libstdc++-6.dll',
            'mingw64/bin/libwinpthread-1.dll': 'bin/libwinpthread-1.dll',

        },
    },
    ('mingw-w64-i686-universal-ctags-git', 'mingw32'): {
        'version': 'r7253.7492b90e-1',
        'install_dir': 'binary-analysis/scancode-ctags-win32/src/scancode_ctags',
        'ignore_deps': [],
        'deletes': ['licenses', 'bin', 'lib', ],
        'copies': {
            'mingw32/share/licenses/': 'licenses/',
            'mingw32/bin/ctags.exe': 'bin/ctags.exe',

            'mingw32/bin/libjansson-4.dll': 'bin/libjansson-4.dll',
            'mingw32/bin/liblzma-5.dll': 'bin/liblzma-5.dll',
            'mingw32/bin/libxml2-2.dll': 'bin/libxml2-2.dll',
            'mingw32/bin/libyaml-0-2.dll': 'bin/libyaml-0-2.dll',
            'mingw32/bin/xml2-config': 'bin/xml2-config',
            'mingw32/bin/zlib1.dll': 'bin/zlib1.dll',

            'mingw32/bin/libasprintf-0.dll': 'bin/libasprintf-0.dll',
            'mingw32/bin/libatomic-1.dll': 'bin/libatomic-1.dll',
            'mingw32/bin/libcharset-1.dll': 'bin/libcharset-1.dll',
            'mingw32/bin/libexpat-1.dll': 'bin/libexpat-1.dll',
            'mingw32/bin/libgcc_s_seh-1.dll': 'bin/libgcc_s_seh-1.dll',
            'mingw32/bin/libgettextlib-0-19-8-1.dll': 'bin/libgettextlib-0-19-8-1.dll',
            'mingw32/bin/libgettextpo-0.dll': 'bin/libgettextpo-0.dll',
            'mingw32/bin/libgettextsrc-0-19-8-1.dll': 'bin/libgettextsrc-0-19-8-1.dll',
            'mingw32/bin/libgmp-10.dll': 'bin/libgmp-10.dll',
            'mingw32/bin/libgmpxx-4.dll': 'bin/libgmpxx-4.dll',
            'mingw32/bin/libgomp-1.dll': 'bin/libgomp-1.dll',
            'mingw32/bin/libiconv-2.dll': 'bin/libiconv-2.dll',
            'mingw32/bin/libintl-8.dll': 'bin/libintl-8.dll',
            'mingw32/bin/libquadmath-0.dll': 'bin/libquadmath-0.dll',
            'mingw32/bin/libssp-0.dll': 'bin/libssp-0.dll',
            'mingw32/bin/libstdc++-6.dll': 'bin/libstdc++-6.dll',
            'mingw32/bin/libwinpthread-1.dll': 'bin/libwinpthread-1.dll',
        },
    },
    ('mingw-w64-cross-binutils', 'msys64'): {
        'version': '2.34-1',
        'install_dir': 'binary-analysis/scancode-readelf-win64/src/scancode_readelf',
        'ignore_deps': [],
        'deletes': ['licenses', 'lib', 'bin', 'doc'],
        'copies': {
#            'usr/share/licenses': 'licenses',
        },
    },

    ('mingw-w64-cross-binutils', 'msys32'): {
        'version': '2.34-1',
        'ignore_deps': [],
        'install_dir': 'binary-analysis/scancode-readelf-win32/src/scancode_readelf',
        'deletes': ['licenses', 'lib', 'bin', 'doc'],
        'copies': {
#            'usr/share/licenses': 'licenses',
        },
    },
}

if __name__ == '__main__':
    sys.exit(main(sys.argv))
