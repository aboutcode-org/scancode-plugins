# -*- coding: utf-8 -*-
#
# Copyright (c) nexB Inc. and others. All rights reserved.
# ScanCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/scancode-plugins for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

import json
import os

from commoncode.testcase import FileBasedTesting

from dwarf import dwarfng
from unittest.case import expectedFailure


class TestDwarfNg(FileBasedTesting):
    test_data_dir = os.path.join(os.path.dirname(__file__), 'data')

    def test_dwarfng_with_error_misc_elfs_cpp_test_o(self):
        self.check_dwarfng('misc_elfs/cpp-test.o', 'misc_elfs/cpp-test.o.dwarfng.expected.json')

    def test_dwarfng_error_misc_elfs_cpp_test_o(self):
        test_file = 'misc_elfs/cpp-test.o'
        test_loc = self.get_test_loc(test_file)
        emsg1 = 'File format is ambiguous'
        try:
            list(dwarfng.get_dwarf_cu_and_die_paths(test_loc))
        except Exception as e:
            assert emsg1 in str(e)

    def test_dwarfng_with_error_ssdeep_x86_64(self):
        self.check_dwarfng('dwarf/ssdeep.x86_64', 'dwarf/ssdeep.x86_64.dwarfng.expected.json')

    def test_dwarfng_error_ssdeep_x86_64(self):
        test_file = 'dwarf/ssdeep.x86_64'
        test_loc = self.get_test_loc(test_file)
        emsg1 = 'File format is ambiguous'
        try:
            list(dwarfng.get_dwarf_cu_and_die_paths(test_loc))
        except Exception as e:
            assert emsg1 in str(e)

    def test_dwarfng_with_error_amd64_exec(self):
        self.check_dwarfng('dwarf/amd64_exec', 'dwarf/amd64_exec.dwarfng.expected.json')

    def test_dwarfng_error_amd64_exec(self):
        test_file = 'dwarf/amd64_exec'
        test_loc = self.get_test_loc(test_file)
        emsg1 = 'File format is ambiguous'
        try:
            list(dwarfng.get_dwarf_cu_and_die_paths(test_loc))
        except Exception as e:
            assert emsg1 in str(e)

    def test_dwarfng_with_error_shash_x86_64(self):
        self.check_dwarfng('dwarf/shash.x86_64', 'dwarf/shash.x86_64.dwarfng.expected.json')

    def test_dwarfng_error_shash_x86_64(self):
        test_file = 'dwarf/shash.x86_64'
        test_loc = self.get_test_loc(test_file)
        emsg1 = 'File format is ambiguous'
        try:
            list(dwarfng.get_dwarf_cu_and_die_paths(test_loc))
        except Exception as e:
            assert emsg1 in str(e)

    def check_dwarfng(self, test_file, expected_file, regen=False):
        test_loc = self.get_test_loc(test_file)
        result = [list(r) for r in dwarfng.get_dwarf_cu_and_die_paths(test_loc)]

        expected_loc = self.get_test_loc(expected_file, must_exist=False)

        if regen:
            with open(expected_loc, 'w') as exc:
                json.dump(result, exc, indent=2)

        with open(expected_loc) as exc:
            expected = json.load(exc)

        assert result == expected

    def test_dwarfng_corrupted_malformed_stringtable(self):
        test_file = 'elf-corrupted/malformed_stringtable'
        expected_file = 'elf-corrupted/malformed_stringtable.dwarfng.expected.json'
        self.check_dwarfng(test_file, expected_file)

    def test_dwarfng_empty_on_non_existing_file(self):
        test_file = 'dwarf/32.fsize.chgg_DOES_NOT_EXIST'
        assert list(dwarfng.get_dwarf_cu_and_die_paths(test_file)) == []

    def test_dwarfng_misc_elfs_null_elf(self):
        self.check_dwarfng('misc_elfs/null_elf', 'misc_elfs/null_elf.dwarfng.expected.json')

    def test_dwarfng_misc_elfs_mips32_exec(self):
        self.check_dwarfng('misc_elfs/mips32_exec', 'misc_elfs/mips32_exec.dwarfng.expected.json')

    def test_dwarfng_misc_elfs_mips64_exec(self):
        self.check_dwarfng('misc_elfs/mips64_exec', 'misc_elfs/mips64_exec.dwarfng.expected.json')

    def test_dwarfng_corrupted_corrupt_o(self):
        self.check_dwarfng('elf-corrupted/corrupt.o', 'elf-corrupted/corrupt.o.dwarfng.expected.json')

    def test_dwarfng_analyze_so_debug(self):
        self.check_dwarfng('dwarf2/analyze.so.debug', 'dwarf2/analyze.so.debug.dwarfng.expected.json')

    def test_dwarfng_autotalent_so_debug(self):
        self.check_dwarfng('dwarf2/autotalent.so.debug', 'dwarf2/autotalent.so.debug.dwarfng.expected.json')

    def test_dwarfng_arm_exec_nosect(self):
        self.check_dwarfng('dwarf/arm_exec_nosect', 'dwarf/arm_exec_nosect.dwarfng.expected.json')

    def test_dwarfng_file_darwin_i386(self):
        self.check_dwarfng('dwarf/file.darwin.i386', 'dwarf/file.darwin.i386.dwarfng.expected.json')

    def test_dwarfng_file_linux_i686(self):
        self.check_dwarfng('dwarf/file.linux.i686', 'dwarf/file.linux.i686.dwarfng.expected.json')

    def test_dwarfng_file_linux_x86_64(self):
        self.check_dwarfng('dwarf/file.linux.x86_64', 'dwarf/file.linux.x86_64.dwarfng.expected.json')

    def test_dwarfng_file_stripped(self):
        self.check_dwarfng('dwarf/file_stripped', 'dwarf/file_stripped.dwarfng.expected.json')

    def test_dwarfng_ia64_exec(self):
        self.check_dwarfng('dwarf/ia64_exec', 'dwarf/file_stripped.dwarfng.expected.json')

    def test_dwarfng_labrea_debug(self):
        self.check_dwarfng('dwarf2/labrea.debug', 'dwarf2/labrea.debug.dwarfng.expected.json')

    def test_dwarfng_latex2emf_debug(self):
        self.check_dwarfng('dwarf2/latex2emf.debug', 'dwarf2/latex2emf.debug.dwarfng.expected.json')

    def test_dwarfng_libgnutls_so_26_22_4(self):
        self.check_dwarfng('dwarf2/libgnutls.so.26.22.4', 'dwarf2/libgnutls.so.26.22.4.dwarfng.expected.json')

    def test_dwarfng_libgnutls_extra_so_26_22_4(self):
        self.check_dwarfng('dwarf2/libgnutls-extra.so.26.22.4', 'dwarf2/libgnutls-extra.so.26.22.4.dwarfng.expected.json')

    def test_dwarfng_libgnutls_openssl_so_27_0_0(self):
        self.check_dwarfng('dwarf2/libgnutls-openssl.so.27.0.0', 'dwarf2/libgnutls-openssl.so.27.0.0.dwarfng.expected.json')

    def test_dwarfng_libgnutlsxx_so_27_0_0(self):
        self.check_dwarfng('dwarf2/libgnutlsxx.so.27.0.0', 'dwarf2/libgnutlsxx.so.27.0.0.dwarfng.expected.json')

    @expectedFailure
    def test_dwarfng_pam_vbox_so_debug(self):
        self.check_dwarfng('dwarf2/pam_vbox.so.debug', 'dwarf2/pam_vbox.so.debug.dwarfng.expected.json')

    def test_dwarfng_arm_exec(self):
        self.check_dwarfng('dwarf/arm_exec', 'dwarf/arm_exec.dwarfng.expected.json')

    def test_dwarfng_arm_gentoo_elf(self):
        self.check_dwarfng('dwarf/arm_gentoo_elf', 'dwarf/arm_gentoo_elf.dwarfng.expected.json')

    def test_dwarfng_arm_object(self):
        self.check_dwarfng('dwarf/arm_object', 'dwarf/arm_object.dwarfng.expected.json')

    def test_dwarfng_arm_scatter_load(self):
        self.check_dwarfng('dwarf/arm_scatter_load', 'dwarf/arm_scatter_load.dwarfng.expected.json')

    def test_dwarfng_ia32_exec(self):
        self.check_dwarfng('dwarf/ia32_exec', 'dwarf/ia32_exec.dwarfng.expected.json')

    def test_dwarfng_libelf_begin_o(self):
        self.check_dwarfng('dwarf/libelf-begin.o', 'dwarf/libelf-begin.o.dwarfng.expected.json')

    def test_dwarfng_shash_i686(self):
        self.check_dwarfng('dwarf/shash.i686', 'dwarf/shash.i686.dwarfng.expected.json')

    def test_dwarfng_ssdeep_i686(self):
        self.check_dwarfng('dwarf/ssdeep.i686', 'dwarf/ssdeep.i686.dwarfng.expected.json')

    def test_dwarfng_amd64_exec(self):
        self.check_dwarfng('dwarf/amd64_exec', 'dwarf/amd64_exec.dwarfng.expected.json')

