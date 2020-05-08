These are various scancode plugins.
Several of them contain pre-built binaries. 

To re-provision prebuilt binaries, follow these instructions:

- For windows, see msys2.py::

    pip install requests
    python msys2.py --build-all --cache-dir msys-cache
    clamscan *

- For Linux and macOS, see homebrew.py::

    pip install requests
    python homebrew.py --build-all --cache-dir homebrew-cache
    clamscan *

        
In all cases, run clamscan or an up to date antivirus scanner before pushing
a new release.