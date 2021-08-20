# -*- coding: utf-8 -*-
#
# Copyright (c) nexB Inc. and others. All rights reserved.
# ScanCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/scancode-plugins for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

from collections import namedtuple
from functools import partial
from itertools import chain
import re

import attr

from commoncode.cliutils import PluggableCommandLineOption
from commoncode.cliutils import SCAN_GROUP
from plugincode.scan import ScanPlugin
from plugincode.scan import scan_impl
from textcode import analysis
from typecode import contenttype


@scan_impl
class GWTScanner(ScanPlugin):
    """
    Parse GWT (Google Web Toolkit) ".symbolMap" files to extract compilation/debug
    symbols. Used to infer the relationship between the compiled JavaScript and
    the original Java Source code.
    """
    resource_attributes = dict(
        gwt=attr.ib(default=attr.Factory(list), repr=False),
    )

    options = [
        PluggableCommandLineOption(('--gwt',),
                          is_flag=True, default=False,
                          help='Parse GWT (Google Web Toolkit) ".symbolMap" files to extract compilation/debug symbols. Used to infer the relationship between the compiled JavaScript and the original Java Source code.',
                          help_group=SCAN_GROUP,
                          sort_order=100),
    ]

    def is_enabled(self, gwt, **kwargs):
        return gwt

    def get_scanner(self, **kwargs):
        return gwt_scan


# maps actual header names to our field names
gwt_headers = (
    'jsName',
    'jsniIdent',
    'className',
    'memberName',
    'sourceUri',
    'sourceLine',
)

GwtSymbol = namedtuple('GwtSymbol', gwt_headers)


def is_symbol_map(location):
    return location.lower().endswith('.symbolmap')


def gwt_scan(location, **kwargs):
    """
    return symbols extracted for a .symbolmap location. Symbol maps
    are produced by GWT compilation.
    See:
    http://code.google.com/p/google-web-toolkit/wiki/WebModeExceptions#Resymbolization_/_Deobfuscation
    "Symbol maps can be generated at compile time using the -extra GWT
    compiler argument, e.g. -extra war/WEB-INF/classes/"
    These files are like a CSV location with # python like comment lines.
    See as a good base to understand the format:
    http://code.google.com/p/speedtracer/source/browse/trunk/src/client/ui/src/com/google/speedtracer/client/GwtSymbolMapParser.java?r=84
    Another format is compressed: this is not handled here yet:
    http://code.google.com/p/speedtracer/source/browse/trunk/src/client/ui/src/com/google/speedtracer/client/CompactGwtSymbolMapParser.java?spec=svn84&r=84
    See also for general JS map parsing: https://github.com/pombredanne/python-sourcemap-1/blob/master/smap.py
    """
    results = []
    if is_symbol_map(location):
        with open(location, 'rU') as symap_file:
            for line in symap_file:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('#'):
                    # header line
                    if any(x in line for x in gwt_headers):
                        pass
                    else:
                        # ignore other comment lines
                        pass
                    continue

                gwts = GwtSymbol(*line.split(','))
                # remove possible jar:file: prefix
                clean_path = gwts.sourceUri.replace('jar:file:', '')
                # remove possible c: or drive name from windows paths. they
                # are useless
                clean_path = '/'.join([x for x in clean_path.split('/')
                                             if ':' not in x])
                results.append(dict(jsName=gwts.jsName,
                                    jsniIdent=gwts.jsniIdent,
                                    className=gwts.className,
                                    memberName=gwts.memberName, clean_path=clean_path, sourceLine=gwts.sourceLine))
    return dict(gwt=results)
