#
# Copyright (c) nexB Inc. and others. All rights reserved.
# ScanCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/aboutcode-org/scancode-toolkit for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#


import platform
from os import environ
from os import path

from plugincode.location_provider import LocationProviderPlugin


class SevenzipPaths(LocationProviderPlugin):

    def get_like_distro(self):
        info = platform.freedesktop_os_release()
        ids = [info['ID']]
        if 'ID_LIKE' in info:
            # ids are space separated and ordered by precedence
            ids.extend(info['ID_LIKE'].split())
        return ids


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
                distribution = self.get_like_distro()
                debian_based_distro = ['ubuntu', 'mint', 'debian']
                rpm_based_distro = ['fedora', 'rhel']

                if any(dist in debian_based_distro for dist in distribution):
                    lib_dir = '/usr/bin'
                    for bin_name in ('7z', '7zz'):
                        lib_7z = path.join(lib_dir, bin_name)
                        if path.exists(lib_7z):
                            break
                elif any(dist in rpm_based_distro for dist in distribution):
                    # 7zip proper is not available on dnf
                    lib_dir = '/usr/libexec/p7zip'
                    lib_7z = path.join(lib_dir, '7za')
                else:
                    raise Exception(
                        'Unsupported system: {}'.format(distribution))
            elif mainstream_system == 'freebsd':
                lib_dir = '/usr/local/bin'
                lib_7z = path.join(lib_dir, '7z')
            elif mainstream_system == 'darwin':
                # This assumes that 7zip was installed using Homebrew
                lib_dir = '/opt/homebrew/bin'
                lib_7z = path.join(lib_dir, '7zz')
        else:
            lib_dir = path.dirname(lib_7z)

        # Check that path exist
        if not path.exists(lib_7z):
            raise Exception(
                '7zip not found. Please refer to the scancode-toolkit '
                'documentation on how to install 7zip for your system.'
            )

        locations = {
            # extractcode.sevenzip.libdir is not used anymore and deprecated
            # but we are keeping it around for now for backward compatibility
            'extractcode.sevenzip.libdir': lib_dir,
            'extractcode.sevenzip.exe': lib_7z,
        }
        return locations
