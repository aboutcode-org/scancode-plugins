#
# Copyright (c) nexB Inc. and others.
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# 
# Redistributions of source code must retain the above copyright notice, this list
# of conditions and the following disclaimer.
# 
# Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import platform
from os import environ
from os import path

from plugincode.location_provider import LocationProviderPlugin


class LibmagicPaths(LocationProviderPlugin):

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
        locations of the libmagic shared library as installed on various Linux
        distros or on FreeBSD.
        """

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
                raise Exception('Unsupported system: {}'.format(distribution))

            dll_loc = path.join(lib_dir, 'libmagic.so')

        elif mainstream_system == 'freebsd':
            if path.isdir('/usr/local/'):
                lib_dir = '/usr/local'
            else:
                lib_dir = '/usr'

            dll_loc = path.join(lib_dir, 'lib/libmagic.so')
            db_dir = path.join(lib_dir,'share/file')

        magicdb_loc = path.join(db_dir, 'magic.mgc')

        locations = {
            # typecode.libmagic.libdir is not used anymore and deprecated
            # but we are keeping it around for now for backward compatibility
            'typecode.libmagic.libdir': lib_dir,
            'typecode.libmagic.dll': dll_loc,
            'typecode.libmagic.db': magicdb_loc,
            }
        return locations
