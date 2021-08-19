
# -*- coding: utf-8 -*-
#
# Copyright (c) nexB Inc. and others. All rights reserved.
# ScanCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/scancode-plugins for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

import re
import logging

from cluecode import finder

LOG = logging.getLogger(__name__)

# TODO: beef up.
# add detailed annotation for each of the common MODULE_XXX macros
# add support for checking the GPL symbols GPLONLY and so on
# add support for finding the init_module and module_init functions defs
# add separate support for finding all linux includes
LKM_REGEXES = [
    # ('lkm-header-include', 'include[^\n]*<linux\/kernel\.h>'),
    ('lkm-header-include', 'include[^\n]*<linux\/module\.h>'),
    ('lkm-make-flag', '\-DMODULE'),
    ('lkm-make-flag', '\_\_KERNEL\_\_'),
    ('lkm-license', 'MODULE_LICENSE.*\("(.*)"\);'),
    ('lkm-symbol', 'EXPORT_SYMBOL.*\("(.*)"\);'),
    ('lkm-symbol-gpl', 'EXPORT_SYMBOL_GPL.*\("(.*)"\);'),
]


def lkm_patterns():
    return [(key, re.compile(regex),) for key, regex in LKM_REGEXES]


def find_lkms(location):
    """
    Yield possible LKM-related clues found in file at location.
    """
    matches = finder.find(location, lkm_patterns())
    matches = finder.apply_filters(matches, finder.unique_filter)
    for key, lkm_clue, _line, _lineno in matches:
        yield key, lkm_clue
