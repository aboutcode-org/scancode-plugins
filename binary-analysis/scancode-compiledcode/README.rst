CompiledCode is ScanCode scan plugin to get lkm clue, dwarfs, gwt, cpp includes,
code/comments lines and various binary and compiled code info.

--cpp-includes: 
--dwarf: 
--elf: 
--generatedcode:
--gwt:
--javaclass:
--makedepend:
--codecommentlines:

To run tests::

    ./configure --dev
    source bin/activate
    pip install \
        -e plugins/scancode-dwarfdump-manylinux2014_x86_64 \
        -e plugins/scancode-ctags-manylinux2014_x86_64 \
        -e plugins/scancode-readelf-manylinux2014_x86_64 \
        -e plugins/scancode-compiledcode[testing,binary]

    pytest -vvs plugins/scancode-compiledcode/tests

Note that in step3, the path depends on your OS versions, please update according to your real os enviroment.