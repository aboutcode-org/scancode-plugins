# -*- coding: utf-8 -*-
#
# Copyright (c) nexB Inc. and others. All rights reserved.
# ScanCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/scancode-plugins for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

"""
Functions to extract information from binary Elf files DWARF debug data using
pyelftools.
Based on code by:
Eli Bendersky (eliben@gmail.com): "This code is in the public domain"
"""
import os

from elftools.elf.elffile import ELFFile
from typecode import contenttype


def get_compilation_units_fullpath(location):
    """
    Yield DWARF CU full paths (aka. path_to_source)
    """
    if not os.path.exists(location):
        return

    T = contenttype.get_type(location)
    if (not T.is_elf) or T.is_stripped_elf:
        return

    with open(location, 'rb') as f:
        elffile = ELFFile(f)

        if not elffile.has_dwarf_info():
            return

        dwarfinfo = elffile.get_dwarf_info()
        # iterate all compilation units
        for cu in dwarfinfo.iter_CUs():
            # The first Debug Informnation Entry in a CU has the paths.
            top_die = cu.get_top_DIE()
            yield top_die.get_full_path()
            # alos yield other dies
            # for die in cu.iter_DIEs():
            #     if not die:
            #         continue
            #     fp = die.get_full_path()
            #     if fp:
            #         yield fp
