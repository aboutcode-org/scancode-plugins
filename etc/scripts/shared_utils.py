
import os
import subprocess
import tarfile

import requests
import shutil
import hashlib

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
    locations = []
    if location.endswith('.tar.zst'):
        # rare and "new" but used in msys
        subprocess.check_call(['unzstd', '-q', '-k', '-f', location])
        location, _, _ = location.rpartition('.zst')
        locations.append(location)
    with open(location, 'rb') as input_tar:
        with tarfile.open(fileobj=input_tar) as tar:
            members = tar.getmembers()
            for tarinfo in members:
                tarinfo.mode = 0o755
            tar.extractall(target_dir, members=members)
    locations.append(target_dir)
    return locations



def extract_in_place(location):
    """
    Extract a tar archive at `location` in a directory created side-by-side with
    the archive and named after the archive stripped from it's extension.
    Remove this directory if it already exists.
    
    Return the directory where the files are extracted, and a list of all
    extracted_locations.
    """
    target_dir = location.replace('.tar.xz', '').replace('.tar.gz', '').replace('.tar.zst', '')
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir, exist_ok=True)
    extracted_locations = extract_tar(location, target_dir)
    return target_dir, extracted_locations



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



