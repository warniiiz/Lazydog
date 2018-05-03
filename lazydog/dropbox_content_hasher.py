#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2018 Clément Warneys <clement.warneys@gmail.com>
# Copyright 2017 Dropbox, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
:module: lazydog.dropbox_content_hasher
:synopsis: Function to get hash of a file, based on dropbox api hasher.
:author: Dropbox, Inc.
:author: Clément Warneys <clement.warneys@gmail.com>

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import hashlib
# import six

import time
import os
import logging


def default_hash_function(absolute_path:str, default_directory_hash:str='DIR'):
    """
    Main function in this module that returns the 
    dropbox-like hash of any local file. If the local path does not exist, 
    ``None`` is returned. If the local path is a directory, the 
    ``default_directory_hash`` parameter is returned, or the default 
    string "DIR". 

    :param absolute_path:
        The absolute local path of the file or directory.
    :type absolute_path:
        str
    :param default_directory_hash:
        *Optional*. The returned value in case the absolute path is a directory.
    :type absolute_path:
        str
    :returns: 
        The hash of the file or directory located in ``absolute_path``. 
        The hash is computed based on the default Dropbox API hasher. 
        ``None`` if absolute local path does not exist.
    :rtype: 
        str

    """

    _hash = None
    try:
        duration = time.perf_counter()
        # Directory
        if os.path.isdir(absolute_path):
            _hash = default_directory_hash
        # File
        elif os.path.exists(absolute_path):
            # Open the file and hash it using Dropbox python helpers
            hasher = DropboxContentHasher()
            with open(absolute_path, 'rb') as f:
                while True:
                    chunk = f.read(1024)  # or whatever chunk size you want
                    if len(chunk) == 0:
                        break
                    hasher.update(chunk)
            _hash = hasher.hexdigest()
        logging.getLogger(__name__).debug("Successfully computed hash of file (%.3f): %s" % (time.perf_counter() - duration, absolute_path))
    except:
        logging.getLogger(__name__).exception("Error while hashing file %s" % absolute_path)
    return _hash
    
    
    
    
class DropboxContentHasher(object):
    """
    Computes a hash using the same algorithm that the Dropbox API uses for the
    the "content_hash" metadata field.

    The digest() method returns a raw binary representation of the hash.  The
    hexdigest() convenience method returns a hexadecimal-encoded version, which
    is what the "content_hash" metadata field uses.

    How to use it:

    .. code-block:: python 

        hasher = DropboxContentHasher()
        with open('some-file', 'rb') as f:
            while True:
                chunk = f.read(1024)  # or whatever chunk size you want
                if len(chunk) == 0:
                    break
                hasher.update(chunk)
        print(hasher.hexdigest())

    """

    BLOCK_SIZE = 4 * 1024 * 1024

    def __init__(self):
        self._overall_hasher = hashlib.sha256()
        self._block_hasher = hashlib.sha256()
        self._block_pos = 0

        self.digest_size = self._overall_hasher.digest_size
        # hashlib classes also define 'block_size', but I don't know how people use that value

    def update(self, new_data):
        if self._overall_hasher is None:
            raise AssertionError(
                "can't use this object anymore; you already called digest()")

        # assert isinstance(new_data, six.binary_type), (
        #     "Expecting a byte string, got {!r}".format(new_data))

        new_data_pos = 0
        while new_data_pos < len(new_data):
            if self._block_pos == self.BLOCK_SIZE:
                self._overall_hasher.update(self._block_hasher.digest())
                self._block_hasher = hashlib.sha256()
                self._block_pos = 0

            space_in_block = self.BLOCK_SIZE - self._block_pos
            part = new_data[new_data_pos:(new_data_pos+space_in_block)]
            self._block_hasher.update(part)

            self._block_pos += len(part)
            new_data_pos += len(part)

    def _finish(self):
        if self._overall_hasher is None:
            raise AssertionError(
                "can't use this object anymore; you already called digest() or hexdigest()")

        if self._block_pos > 0:
            self._overall_hasher.update(self._block_hasher.digest())
            self._block_hasher = None
        h = self._overall_hasher
        self._overall_hasher = None  # Make sure we can't use this object anymore.
        return h

    def digest(self):
        return self._finish().digest()

    def hexdigest(self):
        return self._finish().hexdigest()

    def copy(self):
        c = DropboxContentHasher.__new__(DropboxContentHasher)
        c._overall_hasher = self._overall_hasher.copy()
        c._block_hasher = self._block_hasher.copy()
        c._block_pos = self._block_pos
        return c
    
    
            



