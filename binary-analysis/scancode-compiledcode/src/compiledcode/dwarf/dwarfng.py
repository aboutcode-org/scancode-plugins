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

from elftools.common.py3compat import bytes2str
from elftools.dwarf.descriptions import set_global_machine_arch
from elftools.elf.elffile import ELFFile

from typecode import contenttype


def get_dwarf_cu_and_die_paths(location):
    """
    Yield tuple of (path type, path) extracted from DWARFs in the ELF file at
    ``location``. Path type is either "primary" for CU paths or "secondary" for
    indirect references to DIE paths.
    """
    if not os.path.exists(location):
        return

    T = contenttype.get_type(location)
    if (not T.is_elf) or T.is_stripped_elf:
        return

    with open(location, 'rb') as inp:
        elffile = ELFFile(inp)
        if not elffile.has_dwarf_info():
            return

        dwarfinfo = elffile.get_dwarf_info()

        # warning this is a global meaning that the library may not be thread safe
        set_global_machine_arch(elffile.get_machine_arch())

        seen = set()

        for cu in dwarfinfo.iter_CUs():

            # The first Debug Informnation Entry in a CU has the paths.
            top_die = cu.get_top_DIE()
            path = top_die.get_full_path()
            if path not in seen:
                yield 'primary', path
                seen.add(path)

            lineprogram = dwarfinfo.line_program_for_CU(cu)

            try:
                cu_filename = bytes2str(lineprogram['file_entry'][0].name)
                if len(lineprogram['include_directory']) > 0:
                    # add directory if possible
                    dir_index = lineprogram['file_entry'][0].dir_index
                    if dir_index > 0:
                        pdir = lineprogram['include_directory'][dir_index - 1]
                        cu_filename = f'{bytes2str(pdir)}/{cu_filename}'
                    if cu_filename not in seen and not any(x.endswith(f'/{cu_filename}') for x in seen):
                        yield 'secondary-lp1', cu_filename
                        seen.add(cu_filename)
                else:
                    if cu_filename not in seen and not any(x.endswith(f'/{cu_filename}') for x in seen):
                        yield 'secondary-lp2', cu_filename
                        seen.add(cu_filename)
            except IndexError:
                pass

            # also yield other dies
            for die in cu.iter_DIEs():
                if not die:
                    continue

                decl_file_attrib = die.attributes.get("DW_AT_decl_file")
                if not decl_file_attrib or not decl_file_attrib.value:
                    continue
                die_lineprogram = die.dwarfinfo.line_program_for_CU(die.cu)
                file_entry = die_lineprogram.header.file_entry[decl_file_attrib.value - 1]
                fname = bytes2str(file_entry.name)
                try:
                    file_dir = bytes2str(die_lineprogram['include_directory'][file_entry.dir_index - 1])
                except:
                    continue

                path = f'{file_dir}/{fname}'
                if path not in seen:
                    yield 'secondary-decl1', path
                    seen.add(path)

                comp_dir_attr = die.attributes.get('DW_AT_comp_dir', None)
                comp_dir = bytes2str(comp_dir_attr.value) if comp_dir_attr else ''
                fname_attr = die.attributes.get('DW_AT_name', None)
                fname = bytes2str(fname_attr.value) if fname_attr else ''
                if comp_dir:
                    path = f'{comp_dir}/{fname}'
                    if path not in seen:
                        yield 'secondary-decl2', path
                        seen.add(path)
