A ScanCode Toolkit plugin to use pre-installed libmagic library and data file
=============================================================================

the path of libmagic is either determined by distro data or explicitly
taken from ``TYPECODE_LIBMAGIC_PATH`` environment variable. additionally
the path to ``magic.mgc`` file can be explicitly set by using
``TYPECODE_LIBMAGIC_DB_PATH`` environment variable, otherwise it is
calculated from distro data
