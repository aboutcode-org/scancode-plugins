#
# Copyright (c) nexB Inc. and others. All rights reserved.
# ScanCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/scancode-toolkit for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#


import platform
from os import environ
from os import path

from plugincode.location_provider import LocationProviderPlugin


class SevenzipPaths(LocationProviderPlugin):

    def get_locations(self):
        """
        Return a mapping of {location key: location} providing the installation
        locations of the 7zip exe and shared libraries as installed on various
        Linux distros or on FreeBSD.
        """
        lib_dir = None
        lib_7z = environ.get('EXTRACTCODE_7Z_PATH')
        if not lib_7z:
            mainstream_system = platform.system().lower()

            if mainstream_system == 'linux':
                distribution = platform.linux_distribution()[0].lower()
                debian_based_distro = ['ubuntu', 'mint', 'debian']
                rpm_based_distro = ['fedora', 'redhat']

                if distribution in debian_based_distro:
                    lib_dir = '/usr/lib/p7zip'
                    lib_7z = path.join(lib_dir, '7zr')
                elif distribution in rpm_based_distro:
                    lib_dir = '/usr/libexec/p7zip'
                    lib_7z = path.join(lib_dir, '7za')
                else:
                    raise Exception('Unsupported system: {}'.format(distribution))
            elif mainstream_system == 'freebsd':
                lib_dir = '/usr/local/bin'
                lib_7z = path.join(lib_dir, '7z')
            elif mainstream_system == 'darwin':
                # This assumes that p7zip was installed using Homebrew
                lib_dir = '/opt/homebrew/lib/p7zip'
                lib_7z = path.join(lib_dir, '7z')
        else:
            lib_dir = path.dirname(lib_7z)

        # Check that path exist
        if not path.exists(lib_7z):
            raise Exception(
                'p7zip not found. Please refer to the scancode-toolkit '
                'documentation on how to install p7zip for your system.'
            )

        locations = {
            # extractcode.sevenzip.libdir is not used anymore and deprecated
            # but we are keeping it around for now for backward compatibility
            'extractcode.sevenzip.libdir': lib_dir,
            'extractcode.sevenzip.exe': lib_7z,
        }
        return locations
