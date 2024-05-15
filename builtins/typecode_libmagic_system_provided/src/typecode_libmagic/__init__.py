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
from os import path

from plugincode.location_provider import LocationProviderPlugin


class LibmagicPaths(LocationProviderPlugin):
    def get_locations(self):
        """
        Return a mapping of {location key: location} providing the installation
        locations of the libmagic shared library as installed on various Linux
        distros or on FreeBSD.
        """
        mainstream_system = platform.system().lower()
        if mainstream_system == 'linux':
            system_arch = platform.machine()
            distribution = platform.linux_distribution()[0].lower()
            debian_based_distro = ['ubuntu', 'mint', 'debian']
            rpm_based_distro = ['fedora', 'redhat']

            if distribution in debian_based_distro:
                db_dir = '/usr/lib/file'
                lib_dir = '/usr/lib/'+system_arch+'-linux-gnu'
            elif distribution in rpm_based_distro:
                db_dir = '/usr/share/misc'
                lib_dir = '/usr/lib64'
            else:
                raise Exception('Unsupported system: {}'.format(distribution))

            dll_loc = path.join(lib_dir, 'libmagic.so.1')
        elif mainstream_system == 'freebsd':
            dll_loc = ''
            db_dir = ''
            for lib_dir in ('/usr/local/', '/usr'):
                possible_dll_loc = path.join(lib_dir, 'lib/libmagic.so')
                possible_db_loc = path.join(lib_dir, 'share/misc/magic.mgc')
                if path.exists(possible_dll_loc) and path.exists(possible_db_loc):
                    dll_loc = possible_dll_loc
                    db_dir =  path.dirname(possible_db_loc)
                    break
        elif mainstream_system == 'darwin':
            # This assumes that libmagic was installed using Homebrew
            lib_dir = '/opt/homebrew'
            dll_loc = path.join(lib_dir, 'lib/libmagic.dylib')
            db_dir = path.join(lib_dir, 'share/misc')

        magicdb_loc = path.join(db_dir, 'magic.mgc')

        # Check that paths exist
        if not path.exists(dll_loc):
            raise Exception(
                'libmagic not found. Please refer to the scancode-toolkit '
                'documentation on how to install libmagic for your operating system.'
            )

        if not path.exists(magicdb_loc):
            raise Exception(
                'magic.mgc not found. Please refer to the scancode-toolkit '
                'documentation on how to install libmagic for your system.'
            )

        locations = {
            # typecode.libmagic.libdir is not used anymore and deprecated
            # but we are keeping it around for now for backward compatibility
            'typecode.libmagic.libdir': lib_dir,
            'typecode.libmagic.dll': dll_loc,
            'typecode.libmagic.db': magicdb_loc,
            }
        return locations
