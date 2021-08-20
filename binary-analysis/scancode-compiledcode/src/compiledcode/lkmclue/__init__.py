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


@scan_impl
class LKMClueScanner(ScanPlugin):
    """
    Scan lkm-clue information from the resource.
    """
    resource_attributes = dict(
        lkm_clue=attr.ib(default=attr.Factory(dict), repr=False),
    )

    options = [
        PluggableCommandLineOption(('--lkmclue',),
            is_flag=True, default=False,
            help='Collect LKM module clues and type indicating a possible Linux Kernel Module. (formerly lkm_hint and lkm_line).',
            help_group=SCAN_GROUP,
            sort_order=100),
    ]

    def is_enabled(self, lkmclue, **kwargs):
        return lkmclue

    def get_scanner(self, **kwargs):
        return get_lkm_clues


def get_lkm_clues(location, **kwargs):
    """
    Return a mapping content
        key: lkm_clue_type and
        value: list of lkm_clue
    """
    clues = dict()
    for type, clue in kernel.find_lkms(location):
        if not type or not clue:
            continue
        if clues.get(type):
            clues[type] = clues.get(type).append(clue)
        else:
            clues[type] = [clue]
    return dict(
        lkm_clue=clues,
    )
