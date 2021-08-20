# -*- coding: utf-8 -*-
#
# Copyright (c) nexB Inc. and others. All rights reserved.
# ScanCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/scancode-plugins for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

from functools import partial
from itertools import chain

import attr

from commoncode import fileutils
from commoncode.cliutils import PluggableCommandLineOption
from commoncode.cliutils import SCAN_GROUP
from plugincode.scan import ScanPlugin
from plugincode.scan import scan_impl
from typecode import contenttype

from compiledcode.elf.elf import Elf
from compiledcode.elf import elfng


@scan_impl
class ELFScanner(ScanPlugin):
    """
    Collect the names of shared objects/libraries needed by an Elf binary file.
    """
    resource_attributes = dict(
        elf_needed_library=attr.ib(default=attr.Factory(list), repr=False),
    )

    options = [
        PluggableCommandLineOption(('--elf',),
            is_flag=True, default=False,
            help='Collect dependent libraries names needed by an Elf file.',
            help_group=SCAN_GROUP,
            sort_order=100),
    ]

    def is_enabled(self, elf, **kwargs):
        return elf

    def get_scanner(self, **kwargs):
        return get_elf_needed_library_ng


def get_elf_needed_library_ng(location, **kwargs):
    """
    Return a list of needed_libraries
    """
    results = [enl for enl in  elfng.get_elf_needed_library(location)]
    return dict(elf_needed_library=results)


def get_elf_needed_library(location, **kwargs):
    """
    Return a list of needed_libraries
    """

    T = contenttype.get_type(location)
    if not T.is_elf:
        return
    elfie = Elf(location)
    results = []
    for needed_library in  elfie.needed_libraries:
        results.append(needed_library)
    return dict(elf_needed_library=results)
