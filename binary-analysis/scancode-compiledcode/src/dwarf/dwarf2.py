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
Functions to extract information from binary Elf files DWARF debug data from
the standard nm command output.
"""

import logging
import re
from collections import namedtuple

from commoncode import command
from commoncode.text import toascii
from plugincode.location_provider import get_location
from typecode import contenttype

SCANCODE_BINUTILS_NM_EXE = 'scancode.nm.exe'

logger = logging.getLogger(__name__)

################################################################
# NM PARSING
################################################################
# 0804871c<space>T<space>_init<tab>/usr/src//glibc-2.6.1/cc-nptl/csu/crti.S:15

LINE_WITH_SOURCE_PATH = re.compile(
    r'^'
    # the line starts with 8 or 16 hex chars
    r'([0-9a-fA-F]{8}|[0-9a-fA-F]{16})'
    r'\s'
    # type of lines/symbol
    r'(?P<type>[a-zA-Z])'
    r'\s'
    # symbol name
    r'(?P<symbol>.*)'
    # tab
    r'\t'
    # full path to source file
    r'(?P<path>.*)'
    r':'
    r'(?P<linenum>\d*)'
    r'$'
).match

POSSIBLE_SOURCE_PATH = re.compile(
    r'^'
    # the line starts with 8 or 16 hex chars
    r'([0-9a-fA-F]{8}|[0-9a-fA-F]{16})'
    r'\s'
    # type of lines/symbol
    r'(?P<type>[a-zA-Z])'
    r'\s'
    # symbol name which is a path possibly
    r'(?P<path>.*\.(c|cc|cpp|cxx|h|hh|hpp|hxx|i|m|y|s)?)'
    r'$', re.IGNORECASE
).match


def call_nm(elffile):
    """
    Call nm and returns the returncode, and the filepaths containing the
    stdout and stderr.
    """
    logger.debug('Executing nm command on %(elffile)r' % locals())

    nm_command = get_location(SCANCODE_BINUTILS_NM_EXE)
    return command.execute(
        cmd_loc=nm_command,
        args=['-al', elffile],
        to_files=True,
    )


Entry = namedtuple('Entry', ['type', 'symbol', 'path', 'linenum'])


def parse(location):
    """
    Yield Entry tuples from parsing the `nm` output file at `location`.
    """
    # do not report duplicate symbols
    seen = set()

    # We loop through each line passing control to a handler as needed
    with open(location, 'rb') as lines:
        for line in lines:
            line = line.strip()
            line = toascii(line)
            if not line:
                continue

            withpath = LINE_WITH_SOURCE_PATH(line)
            if withpath:
                logger.debug('Processing path line     : %(line)r' % locals())
                symbol_type = withpath.group('type')
                symbol = withpath.group('symbol')
                debug_path = withpath.group('path')
                lineno = withpath.group('linenum')
                entry = Entry(symbol_type, symbol, debug_path, lineno)
                if entry not in seen:
                    yield entry
                    seen.add(entry)
                continue

            possible_path = POSSIBLE_SOURCE_PATH(line)
            if possible_path:
                logger.debug('Processing path-like line: %(line)r' % locals())
                symbol_type = possible_path.group('type')
                symbol = ''
                debug_path = possible_path.group('path')
                lineno = ''
                entry = Entry(symbol_type, symbol, debug_path, lineno)
                if entry not in seen:
                    yield entry
                    seen.add(entry)

# TODO: demangle symbols


def get_dwarfs(location):
    """
    Yield tuples with debug information extracted from the DWARF
    debug symbols. Return also the symbol type, the symbol value itself and
    the line number in the source code at where the symbol is used or defined.

    Yields this tuple:
        (symbol_type, symbol, path_to_source, symbol_source_line)
    """

    T = contenttype.get_type(location)
    if T.is_elf:
        rc, out, err = call_nm(location)
        if rc != 0:
            raise Exception(repr(open(err).read()))
        for res in parse(out):
            yield res
