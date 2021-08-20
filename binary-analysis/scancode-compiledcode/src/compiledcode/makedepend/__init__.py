
# -*- coding: utf-8 -*-
#
# Copyright (c) nexB Inc. and others. All rights reserved.
# ScanCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/scancode-plugins for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

from itertools import chain
from functools import partial

import attr

from commoncode import fileutils
from commoncode.cliutils import PluggableCommandLineOption
from commoncode.cliutils import SCAN_GROUP
from plugincode.scan import ScanPlugin
from plugincode.scan import scan_impl
from typecode import contenttype


@scan_impl
class MakeDependScanner(ScanPlugin):
    """
    Parse generated make depend files to find sources corresponding binaries.
    """
    resource_attributes = dict(
        makedepend=attr.ib(default=attr.Factory(dict), repr=False),
    )

    options = [
        PluggableCommandLineOption(('--makedepend',),
                          is_flag=True, default=False,
                          help='Parse generated make depend files to find sources corresponding binaries.',
                          help_group=SCAN_GROUP,
                          sort_order=100),
    ]

    def is_enabled(self, makedepend, **kwargs):
        return makedepend

    def get_scanner(self, **kwargs):
        return makedepend_scan


def is_make_depend(location):
    return location.endswith('.d')


def makedepend_scan(location, **kwargs):
    """
    Return path of the .o location and the list of the source location paths
    that were built in the .o given the location of the .d location generated
    by makedepend
    """
    obj_path = ''
    src_paths = []
    if is_make_depend(location):
        file_name = fileutils.resource_name(fileutils.as_posixpath(location))

        with open(location, 'rU') as dfile:
            for line in dfile:
                line = line.strip()

                if not line or line == "\\":
                    continue

                if ":" in line and obj_path:
                    break

                if ":" in line:
                    left, right = line.split(":")
                    left = left.strip()
                    # Assuming there is no space in the filename and that
                    # several files may exist on the left side, space
                    # separated FIXME: we should use a proper makefile parser
                    if " " in left:
                        left_files = []
                        for f in left.split():
                            if (f not in left_files
                                and f != file_name
                                and not f.endswith(file_name)
                                and not f.endswith('.d')):
                                left_files.append(f)

                        lenf = len(left_files)

                        if lenf >= 1:
                            obj_path = left_files[0]
                    else:
                        obj_path = left

                    right = right.strip()
                    right = right.rstrip("\\")
                    right = right.strip()

                    if right:
                        for r in right.split():
                            src_paths.append(r)

                else:
                    line = line.strip()
                    line = line.rstrip("\\")
                    line = line.strip()
                    if line and not line.endswith('.d'):
                        # FIXME: we assume no spaces in filenames: use a make
                        # parser
                        for p in line.split():
                            src_paths.append(p)
    if obj_path and src_paths:
        makedepend_result = dict()
        makedepend_result[obj_path] = src_paths
        return dict(makedepend=makedepend_result)

