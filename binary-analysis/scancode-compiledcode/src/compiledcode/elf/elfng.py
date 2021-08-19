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

from elftools.elf.elffile import ELFFile
from elftools.elf.dynamic import DynamicSection
from typecode import contenttype

"""
Functions and objects to extract information from binary Elf files using pyelftools.
Based on code by:
Eli Bendersky (eliben@gmail.com): "This code is in the public domain"

For a good introduction on readelf and ELF see:
    http://www.linuxforums.org/misc/understanding_elf_using_readelf_and_objdump.html
"""


def get_elf_needed_library(location):
    """
    Return a list of needed_libraries
    """
    if not os.path.exists(location):
        return

    T = contenttype.get_type(location)
    if not T.is_elf:
        return
    with open(location, 'rb') as f:
        elffile = ELFFile(f)
        for section in elffile.iter_sections():
            if not isinstance(section, DynamicSection):
                continue
            for tag in section.iter_tags():
                if tag.entry.d_tag == 'DT_NEEDED':
                    yield tag.needed
