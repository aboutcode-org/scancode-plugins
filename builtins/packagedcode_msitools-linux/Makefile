#
# Copyright (c) nexB Inc. and others. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/aboutcode-org/ for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

ARCH := $(shell uname -m)
ifeq ($(ARCH),aarch64)
	PLAT_NAME := "manylinux2014_aarch64"
else
	PLAT_NAME := "manylinux1_x86_64"
endif

clean:
	rm -rf build/ dist/
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

build:
	rm -f src/packagedcode_msitools/bin/msi*
	python setup.py clean --all sdist
	rm -f src/packagedcode_msitools/bin/msi*
	python setup.py clean --all bdist_wheel --python-tag py3 --plat-name $(PLAT_NAME)

.PHONY: clean build
