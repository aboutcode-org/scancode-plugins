#
# Copyright (c) nexB Inc. and others. All rights reserved.
# ScanCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/scancode-toolkit for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
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
