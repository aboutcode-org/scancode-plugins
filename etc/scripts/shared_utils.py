# Copyright (c) 2020 nexB Inc.

import hashlib
import os
import shutil
import subprocess
import tarfile
import zipfile

import requests

REQUEST_TIMEOUT = 60

TRACE = False
TRACE_FETCH = False
TRACE_INSTALL = False


def fetch_file(url, dir_location, file_name=None, force=False, indent=1):
    """
    Fetch the file at `url` and save it in `dir_location`.
    Return the `location` where the file is saved.
    If `force` is False, do not refetch if already fetched.
    """
    if TRACE_FETCH:
        print(indent * ' ' + f'Fetching {url}')

    if not file_name:
        _, _, file_name = url.rpartition('/')

    location = os.path.join(dir_location, file_name)

    if force or not os.path.exists(location):
        with open(location, 'wb') as o:
            o.write(requests.get(url, timeout=REQUEST_TIMEOUT).content)
    return location


def extract_tar(location, target_dir):
    """
    Extract a tar archive at `location` in the `target_dir` directory.
    Return a list of extracted locations (either directories or files)
    """
    temp_extraction = None
    if location.endswith('.tar.zst'):
        # rare and "new" but used in msys
        subprocess.check_call(['unzstd', '-q', '-k', '-f', location])
        temp_extraction, _, _ = location.rpartition('.zst')
        location = temp_extraction
    with open(location, 'rb') as input_tar:
        with tarfile.open(fileobj=input_tar) as tar:
            members = tar.getmembers()
            for tarinfo in members:
                tarinfo.mode = 0o755
            tar.extractall(target_dir, members=members)
    if temp_extraction:
        os.remove(temp_extraction)


def extract_in_place(location):
    """
    Extract a tar archive at `location` in a directory created side-by-side with
    the archive and named after the archive stripped from it's extension.
    Remove this directory if it already exists.

    Return the directory where the files are extracted.
    """
    if '.tar' in location:
        extractor = extract_tar
        # split from tar.gz/xz/lzma/zst/bz2
        target_dir, _, _ = location.rpartition('.tar')

    elif location.endswith('.zip'):
        extractor = extract_zip
        target_dir = location.replace('.zip', '')

    elif location.endswith('.exe'):
        # for 7z self extracting exe
        extractor = extract_7zip
        target_dir = location.replace('.exe', '')

    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

    os.makedirs(target_dir, exist_ok=True)

    extractor(location, target_dir)
    return target_dir


def extract_zip(location, target_dir):
    """
    Extract a zip archive file at location to the `target_dir` directory.
    """
    with zipfile.ZipFile(location) as zipf:
        zipf.extractall(path=target_dir)


def extract_7zip(location, target_dir):
    """
    Extract a 7z archive at `location` to the `target_dir` directory.
    """
    out = subprocess.check_output(['7z', 'x', location], cwd=target_dir)
    if not b'Everything is Ok' in out:
        raise Exception(out)


def verify(fetched_location, expected_sha256=None):
    """
    Verify that the file at `fetched_location` has the `expected_sha256` checksum.
    """
    if not fetched_location or not expected_sha256:
        print(f'Cannot verify download at: {fetched_location} and sha256: {expected_sha256}')
        return

    with open (fetched_location, 'rb') as f:
        fsha256 = hashlib.sha256(f.read()).hexdigest()
        assert fsha256 == expected_sha256, f'Invalid SHA256 for: {fetched_location}'
