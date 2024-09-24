# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import os
import hashlib
import json
import time

from ._constants import CACHE_DIR, SECONDS_IN_WEEK

def read_cache(key):
    hkey = _hash_key(key)
    file_path = os.path.join(CACHE_DIR, hkey + ".json")

    if not os.path.isfile(file_path):
        # print(f"Cache miss: {file_path}")
        return None

    with open(file_path, "rt") as fh:
        file_data = json.loads(fh.read())
        if time.time() > file_data["expires"]:
            # print(f"Cache expired: {file_path}")
            return None
        else:
            # print(f"Cache hit: {file_path}")
            return file_data["data"]


def write_cache(key, data, expires_in=2*SECONDS_IN_WEEK):
    os.makedirs(CACHE_DIR, exist_ok=True)

    hkey = _hash_key(key)
    file_path = os.path.join(CACHE_DIR, hkey + ".json")

    with open(file_path, "wt") as fh:
        fh.write(json.dumps({ "expires": time.time() + expires_in, "key_hash": hkey, "key": key, "data": data }, indent=4))


def _hash_key(key):
    return hashlib.md5(json.dumps(key).encode()).hexdigest().lower()
