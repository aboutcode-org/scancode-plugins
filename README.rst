ScanCode plugins 
================

https://github.com/nexB/scancode-plugins

These are various scancode plugins, some are builtins and some are extras. 
Several of them contain pre-built binaries. 

Each plugin is under its own license.

The src-* directories contain the source code of pre-built plugins that contain
native binaries.

See also:

 - https://github.com/nexB/scancode-toolkit
 - https://github.com/nexB/scancode-thirdparty-src (source for some plugins being transitioned)


To re-provision pre-built binaries, follow these instructions (only on Linux)::

    ./configure
    etc/scripts/fetch-plugins.sh
    clamscan -v *
        
In all cases, run clamscan or an up to date antivirus scanner before pushing
a new release.


To build the wheels for all the plugins::

    etc/scripts/build-plugins.sh
