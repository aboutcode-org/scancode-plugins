# -*- coding: utf-8 -*-
#
# Copyright (c) nexB Inc. and others. All rights reserved.
# ScanCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/scancode-plugins for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

import os

from functools import partial
from itertools import chain

import attr

from commoncode import fileutils
from commoncode.cliutils import PluggableCommandLineOption
from commoncode.cliutils import SCAN_GROUP
from plugincode.scan import ScanPlugin
from plugincode.scan import scan_impl
from typecode import contenttype

from compiledcode.dwarf import dwarf
from compiledcode.dwarf import dwarf2
from compiledcode.dwarf import dwarfng


@scan_impl
class DwarfScanner(ScanPlugin):
    """
    Scan a dwarf infos for URLs.
    """
    resource_attributes = dict(
        dwarf_source_path=attr.ib(default=attr.Factory(list), repr=False)
    )

    options = [
        PluggableCommandLineOption(('--dwarf',),
            is_flag=True, default=False,
            help='Collect source code path from compilation units found in '
                 'ELF DWARFs.',
            help_group=SCAN_GROUP,
            sort_order=100
        ),
    ]

    def is_enabled(self, dwarf, **kwargs):
        return dwarf

    def get_scanner(self, **kwargs):
        return get_dwarfs


def get_dwarfs(location, **kwargs):
    """
    Return a mapping with original_source_files and included_source_files or None.
    """
    return dict(
#         dwarf_source_path=list(dwarf_source_path(location))
        dwarf_source_path=list(dwarf_source_path_ng(location))
    )


def dwarf_source_path_ng(location, **kwargs):
    """
    Collect unique paths to compiled source code found in Elf binaries DWARF
    sections for D2D.
    """
    return dwarfng.get_dwarf_cu_and_die_paths(location)


def dwarf_source_path(location):
    """
    Collect unique paths to compiled source code found in Elf binaries DWARF
    sections for D2D.
    """
    if not os.path.exists(location):
        return
    T = contenttype.get_type(location)
    if not (T.is_elf or T.is_stripped_elf):
        return
    seen_paths = set()
    path_file_names = set()
    bare_file_names = set()
    for dpath in chain(get_dwarf1(location), get_dwarf2(location)):
        if dpath in seen_paths:
            continue
        fn = fileutils.file_name(dpath)
        if fn == dpath:
            bare_file_names.add(fn)
            continue
        else:
            path_file_names.add(fn)
        seen_paths.add(dpath)
        yield dpath
    # only yield filename that do not exist as full paths
    for bfn in sorted(bare_file_names):
        if bfn not in path_file_names and bfn not in seen_paths:
            yield bfn
            seen_paths.add(bfn)


def get_dwarf1(location):
    """
    Using Dwarfdump
    """
    d = dwarf.Dwarf(location)
    if d:
        # Show the error in the scan result ahead to make it easy to be catched
        for e in d.parse_errors:
            yield e

        # Note: we return all paths at once, when we should probably return the
        # std and original path as separate annotations
        for p in d.original_source_files + d.included_source_files:
            yield p


def get_dwarf2(location):
    """
    Using NM
    """
    for _, _, path_to_source, _ in dwarf2.get_dwarfs(location):
        if path_to_source:
            yield path_to_source
