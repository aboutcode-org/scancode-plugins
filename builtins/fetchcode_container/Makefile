#
# Copyright (c) nexB Inc. and others. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/ for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

clean:
	rm -rf build/ dist/
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

build:
	rm -f src/fetchcode_container/bin/skopeo*
	python setup.py clean --all sdist
	rm -f src/fetchcode_container/bin/skopeo*
	GOOS=linux GOARCH=amd64 python setup.py clean --all bdist_wheel --python-tag py3 --plat-name manylinux1_x86_64
#	rm -f src/fetchcode_container/bin/skopeo*
#	GOOS=darwin GOARCH=amd64 python setup.py clean --all bdist_wheel --python-tag py3 --plat-name macosx_10_14_x86_64
#	rm -f src/fetchcode_container/bin/skopeo*
#	GOOS=windows GOARCH=amd64 python setup.py clean --all bdist_wheel --python-tag py3 --plat-name win_amd64


.PHONY: clean build

