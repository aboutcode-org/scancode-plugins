#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/ for support and download.
# ScanCode is a trademark of nexB Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from os.path import abspath
from os.path import dirname
from os.path import join

from plugincode.location_provider import LocationProviderPlugin


class LibarchivePaths(LocationProviderPlugin):

    def get_locations(self):
        curr_dir = dirname(abspath(__file__))
        lib_dir = join(curr_dir, 'lib')
        locations = {
            'extractcode.libarchive.libdir': lib_dir,
            'extractcode.libarchive.dll': join(lib_dir, 'libarchive.dylib'),
        }
        return locations
