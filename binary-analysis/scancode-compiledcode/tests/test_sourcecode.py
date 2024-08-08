# -*- coding: utf-8 -*-
#
# Copyright (c) nexB Inc. and others. All rights reserved.
# ScanCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/aboutcode-org/scancode-plugins for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

import os

from scancode.cli_test_utils import check_json_scan
from scancode.cli_test_utils import run_scan_click

from commoncode.testcase import FileBasedTesting


class TestCodeCommentLinesScan(FileBasedTesting):

    test_data_dir = os.path.join(os.path.dirname(__file__), 'data')

    def test_codecommentlines(self):
        test_dir = self.get_test_loc('sourcecode/input')
        result_file = self.get_temp_file('json')
        args = ['--codecommentlines', test_dir, '--json', result_file]
        run_scan_click(args)
        test_loc = self.get_test_loc('sourcecode/expected.json')
        check_json_scan(test_loc, result_file, regen=False)
