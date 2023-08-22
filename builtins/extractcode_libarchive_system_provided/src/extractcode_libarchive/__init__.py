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
                    lib_dir = '/usr/lib/'+system_arch+'-linux-gnu'

                elif any(dist in rpm_based_distro for dist in distribution):
                    db_dir = '/usr/share/misc'
                    lib_dir = '/usr/lib64'

                else:
                    raise Exception('Unsupported system: {}'.format(distribution))

            elif mainstream_system == 'freebsd':
                if path.isdir('/usr/local/'):
                    lib_dir = '/usr/local/lib'
                else:
                    lib_dir = '/usr/lib'
            lib_archive = path.join(lib_dir, 'libarchive.so')
        else:
            lib_dir = path.dirname(lib_archive)

        locations = {
            'extractcode.libarchive.dll': lib_archive,
        }
        return locations
