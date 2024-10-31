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


class LibarchivePaths(LocationProviderPlugin):

    def get_like_distro(self):
        info = platform.freedesktop_os_release()
        ids = [info["ID"]]
        if "ID_LIKE" in info:
            # ids are space separated and ordered by precedence
            ids.extend(info["ID_LIKE"].split())
        return ids

    def get_locations(self):
        """
        Return a mapping of {location key: location} providing the installation
        locations of the libarchive shared library as installed on various Linux
        distros or on FreeBSD.
        """
        lib_archive = environ.get('EXTRACTCODE_LIBARCHIVE_PATH')
        if not lib_archive:
            system_arch = platform.machine()
            mainstream_system = platform.system().lower()

            if mainstream_system == 'linux':
                distribution = self.get_like_distro()
                debian_based_distro = ['ubuntu', 'mint', 'debian']
                rpm_based_distro = ['fedora', 'rhel']

                if any(dist in debian_based_distro for dist in distribution):
                    db_dir = '/usr/lib/file'
                    lib_dir = '/usr/lib' if platform.architecture()[0] == '32bit' else '/usr/lib/'+system_arch+'-linux-gnu'

                elif any(dist in rpm_based_distro for dist in distribution):
                    db_dir = '/usr/share/misc'
                    lib_dir = '/usr/lib' if platform.architecture()[0] == '32bit' else '/usr/lib64'

                else:
                    raise Exception(
                        'Unsupported system: {}'.format(distribution))

                lib_archive = path.join(lib_dir, 'libarchive.so.13')
            elif mainstream_system == 'freebsd':
                lib_archive = ''
                for lib_dir in ('/usr/local/lib', '/usr/lib'):
                    possible_lib_archive = path.join(lib_dir, 'libarchive.so')
                    if path.exists(possible_lib_archive):
                        lib_archive = possible_lib_archive
                        break
            elif mainstream_system == 'darwin':
                # This assumes that libarchive was installed using Homebrew
                lib_dir = '/opt/homebrew/opt/libarchive/lib'
                lib_archive = path.join(lib_dir, 'libarchive.dylib')
        else:
            lib_dir = path.dirname(lib_archive)

        # Check that path exists
        if not path.exists(lib_archive):
            raise Exception(
                'libarchive not found. Please refer to the scancode-toolkit '
                'documentation on how to install libarchive for your system.'
            )

        locations = {
            'extractcode.libarchive.dll': lib_archive,
        }
        return locations
