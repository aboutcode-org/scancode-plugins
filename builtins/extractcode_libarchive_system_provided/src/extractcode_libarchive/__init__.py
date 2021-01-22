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

from os import path
import platform

from plugincode.location_provider import LocationProviderPlugin


class LibarchivePaths(LocationProviderPlugin):
    def get_locations(self):
        """
        Return a mapping of {location key: location} providing the installation
        locations of the libarchive shared library as installed on various Linux
        distros or on FreeBSD.
        """
        system_arch = platform.machine()
        mainstream_system = platform.system().lower()
        if mainstream_system == 'linux':
            distribution = platform.linux_distribution()[0].lower()
            debian_based_distro = ['ubuntu', 'mint', 'debian']
            rpm_based_distro = ['fedora', 'redhat']

            if distribution in debian_based_distro:
                lib_dir = '/usr/lib/'+system_arch+'-linux-gnu'

            elif distribution in rpm_based_distro:
                lib_dir = '/usr/lib64'

            else:
                raise Exception('Unsupported system: {}'.format(distribution))

        elif mainstream_system == 'freebsd':
            if path.isdir('/usr/local/'):
                lib_dir = '/usr/local/lib'
            else:
                lib_dir = '/usr/lib'

        locations = {
            'extractcode.libarchive.libdir': lib_dir,
            'extractcode.libarchive.dll': path.join(lib_dir, 'libarchive.so'),
        }
        return locations
