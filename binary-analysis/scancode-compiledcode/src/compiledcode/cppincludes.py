# -*- coding: utf-8 -*-
#
# Copyright (c) nexB Inc. and others. All rights reserved.
# ScanCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/scancode-toolkit for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

import re

import attr

from commoncode.cliutils import SCAN_GROUP
from commoncode.cliutils import PluggableCommandLineOption
from plugincode.scan import ScanPlugin
from plugincode.scan import scan_impl
from textcode import analysis
from typecode import contenttype


@scan_impl
class CPPIncludesScanner(ScanPlugin):
    """
    Collect the #includes statements in a C/C++ file.
    """
    resource_attributes = dict(
        cpp_includes=attr.ib(default=attr.Factory(list), repr=False),
    )

    options = [
        PluggableCommandLineOption(('--cpp-includes',),
            is_flag=True, default=False,
            help='Collect the #includes statements in a C/C++ file.',
            help_group=SCAN_GROUP,
            sort_order=100),
    ]

    def is_enabled(self, cpp_includes, **kwargs):
        return cpp_includes

    def get_scanner(self, **kwargs):
        return cpp_includes


def cpp_includes_re():
    return re.compile(
        '(?:[\t ]*#[\t ]*'
        '(?:include|import)'
        '[\t ]+)'
        '''(["'<][a-zA-Z0-9_\-/\. ]*)'''
        '''(?:["'>"])'''
    )


def cpp_includes(location, **kwargs):
    """Collect the #includes statements in a C/C++ file."""
    T = contenttype.get_type(location)
    if not T.is_c_source:
        return
    results = []
    for line in analysis.unicode_text_lines(location):
        for inc in cpp_includes_re().findall(line):
            results.append(inc)
    return dict(cpp_includes=results)
