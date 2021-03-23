#
# Copyright (c) nexB Inc. and others. All rights reserved.
# ScanCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/scancode-toolkit for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#


import platform
from os import path

from plugincode.location_provider import LocationProviderPlugin


class SevenzipPaths(LocationProviderPlugin):

    def get_locations(self):
        """
        Return a mapping of {location key: location} providing the installation
        locations of the 7zip exe and shared libraries as installed on various
        Linux distros or on FreeBSD.
        """
        mainstream_system = platform.system().lower()
        if mainstream_system == 'linux':
            distribution = platform.linux_distribution()[0].lower()
            debian_based_distro = ['ubuntu', 'mint', 'debian']
            rpm_based_distro = ['fedora', 'redhat']

            if distribution in debian_based_distro:
                lib_dir = '/usr/lib/p7zip'

            elif distribution in rpm_based_distro:
                lib_dir = '/usr/libexec/p7zip'

            else:
                raise Exception('Unsupported system: {}'.format(distribution))
        elif mainstream_system == 'freebsd':
            lib_dir = '/usr/local/libexec/p7zip'

        locations = {
            'extractcode.sevenzip.libdir': lib_dir,
            'extractcode.sevenzip.exe': path.join(lib_dir, '7z'),
        }

        return locations
