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

from compiledcode.sourcecode import kernel
from compiledcode.sourcecode.metrics import file_lines_count


@scan_impl
class CodeCommentLinesScanner(ScanPlugin):
    """
    Scan the number of lines of code and lines of the comments.
    """
    resource_attributes = dict(
        codelines=attr.ib(default=attr.Factory(int), repr=False),
        commentlines=attr.ib(default=attr.Factory(int), repr=False),

    )

    options = [
        PluggableCommandLineOption(('--codecommentlines',),
            is_flag=True, default=False,
            help='Count the number of lines of code and comments.',
            help_group=SCAN_GROUP,
            sort_order=100),
    ]

    def is_enabled(self, codecommentlines, **kwargs):
        return codecommentlines

    def get_scanner(self, **kwargs):
        return get_codecommentlines


def get_codecommentlines(location, **kwargs):
    """
    Return the cumulative number of lines of code in the whole directory tree
    at `location`. Use 0 if `location` is not a source file.
    """
    codelines, commentlines = file_lines_count(location)
    return dict(
        codelines=codelines,
        commentlines=commentlines
    )
