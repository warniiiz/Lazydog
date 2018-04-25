#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2018 Clément Warneys <clement.warneys@gmail.com>
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
:module: lazydog.states
:synopsis: Keeps track of the current state of the watched local directory. \
The idea is to save computational time, avoiding recomputing file hashes \
or getting size and modification time of each watched files (depending on the requested \
method), thus accelerating identification of copy events.
:author: Clément Warneys <clement.warneys@gmail.com>

"""

import os
import logging

from lazydog.dropbox_content_hasher import default_hash_function

class DualAccessMemory():
    """
    Helper class, used by :py:class:`LocalState`. Sort of double-entry dictionary.
    When you save one tuple {key, value}, you can then access it both way:

    * either from the key, using :py:meth:`get`, or using accessor ``object[key]``
    * or from value, using :py:meth:`get_by_value`. In this case, you will get a set \
    of all the corresponding keys that references to this specific value.

    To register a new key, you can either use :py:meth:`save` method, 
    or the accessor ``object[key] = value``.

    Finally you can check if a key is existing using the accessor ``key in object``.

    .. note: This dual-access dictionary has been specifically designed for
        handling `path` key (for example '/dir/file.txt'), and associate it
        to a file value, which can be either file size, file modification time, 
        or file hash...

        Thus the :py:class:`DualAccessMemory` class contains specifics methods
        allowing to :py:meth:`move` and :py:meth:`delete` keys recursively, 
        according to the way file-system paths are recursively moved or deleted.
    """
    
    def __init__(self):
        # self.memories is a dictionary with unique keys and possible same values
        # note that this class has been designed for keys that should be a string containing a path
        self.memories = {}
        self.memories.clear()
        
        # self.dual_memories is a dictionary where the keys are each possible value of self.memories, 
        # and the values are the lists of the associated keys.
        self.dual_memories = {}
        self.dual_memories.clear()

    def get(self, key):
        """
        Returns the value corresponding to the key in parameter, same behaviour as a dictionary. 
        ``None`` if key is unknowned. You can also access it with ``object[key]``.
        """
        return self.memories.get(key, None)
    
    def get_by_value(self, value) -> set:
        """
        Returns a set of key corresponding to the value in parameter. 
        Empty ``set()`` if value is not referenced.
        """
        return self.dual_memories.get(value, set())

    def __getitem__(self, key):
        return self.get(key)
    
    def __setitem__(self, key, value):
        return self.save(key, value)

    def __contains__(self, key):
        return key in self.memories
        
    def _get_children(self, key:str):
        """
        Private inner helper method. Considering the :py:class:`DualAccessMemory` 
        has been designed to handle path key, this method returns a list of every 
        children paths under the key path (including the key path itself).
        """
        complete_key = key if key.endswith('/') else key + '/'
        children = [x for x in self.memories if x.startswith(complete_key)]
        if key in self.memories:
            children = children + [key]
        return children

    def save(self, key:str, value):
        """
        Registers the tuple {key, value} in order it is easily accessible both way.
        If key already exists with another value, the value is first removed, 
        before registering the new one.
        """
        if key in self:
            self.dual_memories[self.memories[key]].discard(key)
        self.memories[key] = value
        if self.dual_memories.get(self.memories[key]) is None:
            self.dual_memories[self.memories[key]] = set()
        self.dual_memories[self.memories[key]].update([key]) 
    
    # Delete key recursively
    def delete(self, delete_key:str):
        """
        Considering the :py:class:`DualAccessMemory` 
        has been designed to handle path key, this method not only deletes the
        ``delete_key`` in parameter, but it also deletes every children keys corresponding to the children paths 
        of the parameter path ``delete_key``.
        """
        for key in self._get_children(delete_key):
            if self.dual_memories.get(self.memories[key]) is not None:
                self.dual_memories[self.memories[key]].discard(key) 
            self.memories.pop(key)
        
    # Move key recursively
    def move(self, src_key:str, dst_key:str):
        """
        Considering the :py:class:`DualAccessMemory` 
        has been designed to handle path key, this method not only moves the
        ``src_key`` in parameter to ``dst_key`` key, but it also moves every 
        children keys corresponding to the children paths 
        of the parameter path ``src_key`` to the related children path under 
        the parameter path ``dst_key``.
        """
        for old_key in self._get_children(src_key):
            new_key = old_key.replace(src_key, dst_key, 1)
            if new_key in self:
                self.dual_memories[self.memories[new_key]].discard(new_key)
            if self.dual_memories.get(self.memories[old_key]) is not None:
                self.dual_memories[self.memories[old_key]].discard(old_key) 
                self.dual_memories[self.memories[old_key]].update([new_key]) 
            self.memories[new_key] = self.memories.pop(old_key)
            
            
    
    
class LocalState():
    """
    Keeps track of the current state of the watched local directory, by listing 
    every sub-files and sub-directories, and associating each of them with their
    size, modification time, and hash values.

    When managing large directory, it can become very long to retrieves this 
    information. But we need it very fast in order to be able to correlate 
    `Created` event into `Copied` ones. Indeed, for this kind of correlation, 
    we need to rapidly find every other file or folder that are having the 
    same characteristics (that will then be eligible to be the source file 
    or folder).

    :py:class:`LocalState` is keeping tracks of files with two 
    :py:class:`DualAccessMemory` objects. The first one keeping tracks of
    couple ``(size, modification time)``, and the second one of single 
    ``hash`` value.

    Hash values are computed depending on a default hashing function. This
    default method is based on the Dropbox hashing algorithm, but you can
    define your own one. You only have to respect the same parameter and return.
    See :py:meth:`_default_hashing_function` method to see the needed parameters 
    names and types and the return type.

    In order to accelerate the initialization of :py:class:`LocalState` when 
    watching large diectory, you can initialize it with pre-computed initializing
    values of your own (that you have to know in the first place, for example by
    keeping track of them in a hard backup file, or if you already have to compute them
    in other place of your application, no need that the hash values have to 
    be computed again... just send them at the initialization). Please looke 
    at the ``custom_intializing_values`` parameter for more information.

    .. note: Once initialized, the :py:class:`LocalState` object needs to 
        be updated by external objects using it. Local state is not 
        automatically updating its own states, but sometimes when it detects 
        that some paths do not exist anymore (then it deletes them, for 
        cleaning purpose).

    :param absolute_root_folder:
        Absolute path of the folder you need to keep track of. Note that
        ever sub-file and sub-folder will then be referenced with
        relative paths.
    :type absolute_root_folder:
        str
    :param custom_hash_function:
        *Optional*. Default value is :py:meth:`_default_hashing_function` is used, 
        which is based on the Dropbox hashing algorithm. But you can also
        provides your own hashing function, as long as your respect the format
        of the default one.
    :type custom_hash_function:
        function
    :param custom_intializing_values:
        *Optional*. If not provided or ``None``, all sub-folders will be browsed
        at initialization, and for each file and folder, the file size, file 
        modification time and file hash will be retrieves and computed (this operation
        can take a long time, depending on the number and size of the files, and on 
        the hashing function). To accelerate this initialization process, you can provide
        __init__ method with pre-computed initializing values under a dictionary format with 
        ``key=file_path`` and ``value=[file_hash, file_size, file_time]``.
        You do not need to know the exact content of the main directory at the initialization, 
        and if you later notice unexpected modifications compared to the initial values you sent, 
        you can still correct each of them using the :py:meth:`save` method.
    :type custom_intializing_values:
        dict

    :returns: 
        An initialized object representing local state of the aimed folder.
    :rtype: 
        :py:class:`LocalState`

    """
    
    DEFAULT_DIRECTORY_VALUE = 'DIR'
    """
    Default hash value for directory (since directory are not hashed, 
    and that we want to reserve ``None`` value to non existing directories).
    """
    
    # Default method to get the Hash of the file with the supplied file name.
    @staticmethod
    def _default_hashing_function(absolute_path:str): 
        """
        Hash values are computed depending on a default hashing function. This
        default method is based on the Dropbox hashing algorithm. For information, 
        if the ``absolute_path`` is a directory, the directory hash will always be 
        the same, here :py:attr:`DEFAULT_DIRECTORY_VALUE`.

        :param absolute_path:
            Absolute path of the file or folder.
        :type absolute_path:
            str
       
        :returns: 
            The hash of the file or folder in parameter
        :rtype: 
            str
        """
        return default_hash_function(absolute_path, LocalState.DEFAULT_DIRECTORY_VALUE)
    
    # Following 3 methods can be used in other classes
    def absolute_local_path(self, relative_path:str) -> str:
        """
        Computes the absolute local path from a relative one.

        .. note: Since the instance of :py:class:`LocalState` contains the reference of 
            the watched directory, this method can be used from any other place where 
            the absolute local path is needed, as a generic helper method.

        :param relative_path:
            Relative local path of the file or folder.
        :type relative_path:
            str
        :returns: 
            Absolute local path of the same file or folder
        :rtype: 
            str
        """
        if relative_path.startswith('/'):
            relative_path = relative_path[1:]
        return os.path.join(self.absolute_root_folder, relative_path)
    
    def relative_local_path(self, absolute_path:str) -> str:
        """
        Same as :py:meth:`absolute_local_path`, but opposite.
        """
        absolute_path = os.path.normpath(absolute_path)
        return '/' + os.path.relpath(absolute_path, self.absolute_root_folder)
    
    def hash_function(self, *args, **kwargs):
        return self._hash_function(*args, **kwargs)
    
    def __init__(self, absolute_root_folder, custom_hash_function=None, custom_intializing_values:dict=None):
        # keep absolute root folder
        self.absolute_root_folder = absolute_root_folder
        
        # keep hash function
        self._hash_function = custom_hash_function if custom_hash_function is not None else LocalState._default_hashing_function
        
        # self.hashes is a dual access dictionary 
        # self.hashes.get(key) with key=file_path returns the value=file_hash
        # self.hashes.get_by_value(value) with value=file_hash returns a set of paths
        self.hashes = DualAccessMemory()
        
        # self.sizetimes is a dual access dictionary 
        # self.sizetimes.get(key) with key=file_path returns the value=tuple(file_size, file_mtime)
        # self.sizetimes.get_by_value(value) with value=tuple(file_size, file_mtime) returns a set of paths
        self.sizetimes = DualAccessMemory()
        
        # Initializing values
        if custom_intializing_values is not None:
            # custom_intializing_values should be a dict with:
            # - key=file_path
            # - value=list(file_hash, file_size, file_time)
            for k, v in custom_intializing_values.items():
                if os.path.exists(self.absolute_local_path(k)):
                    self.save(k, v[0], v[1], v[2])
                    logging.debug('Initial indexing (provided) ' + k + ' - ' + v[0] + ' - ' + str((v[1], v[2])))
        else:
            
            # Default initializing
            for root, dirs, files in os.walk(self.absolute_root_folder):  
                for i in dirs + files:
                    relative_path = self.relative_local_path(os.path.join(root, i))
                    self.get_hash(relative_path)
                    self.get_sizetime(relative_path)
                    logging.debug('Initial indexing (computed) ' + relative_path + ' - ' + self.get_hash(relative_path) + ' - ' + str(self.get_sizetime(relative_path)))
    

    
    def get_hash(self, key:str, compute_if_none:bool=True) -> str:
        """
        Gets the ``file_hash`` value of the file at the ``key`` relative path. If the file is unknown
        (and so the hash value is not yet computed), by default the hash value will
        be computed. This behaviour can be cancelled using ``compute_if_none`` parameter.

        :param key:
            Relative local path of the file or folder.
        :type key:
            str
        :param compute_if_none:
            *Optional*. ``True`` by default, which means that if the file is unknown
            (and so it is for the hash value), the hash value will be computed. Use
            ``False`` if you want to cancel this bahaviour, so the returned value
            will be ``None``.
        :type compute_if_none:
            boolean
        :returns: 
            File or directory hash value, if path exists, else ``None``.
        :rtype: 
            str
        """
        if key not in self.hashes and compute_if_none:
            self.hashes[key] = self.hash_function(self.absolute_local_path(key))
        return self.hashes[key]
        
    def get_files_by_hash_key(self, hash_key:str) -> set:
        """
        Returns a set of every file or directory paths for which the 
        hash value corresponds to the ``hash_key`` parameter.
        """
        file_paths = self.hashes.get_by_value(hash_key)
        return self._check_for_deleted_paths(file_paths)

    def get_sizetime(self, key:str, compute_if_none:bool=True):
        """
        Gets the couple ``(file_size, file_modification_time)`` value of the file 
        at the ``key`` relative path. Same behaviour than :py:meth:`get_hash` method.

        :param key:
            Relative local path of the file or folder.
        :type key:
            str
        :param compute_if_none:
            *Optional*. ``True`` by default, which means that if the file is unknown
            (and so it is for the file size and modification time value), the values 
            will be computed. Use ``False`` if you want to cancel this bahaviour, so the 
            returned value will be ``None``.
        :type compute_if_none:
            boolean
        :returns: 
            File or directory couple (file_size, file_modification_time) value, 
            if path exists, else ``None``.
        :rtype: 
            str
        """
        if key not in self.sizetimes and compute_if_none:
            if os.path.isdir(self.absolute_local_path(key)):
                self.sizetimes[key] = (LocalState.DEFAULT_DIRECTORY_VALUE, 
                                       LocalState.DEFAULT_DIRECTORY_VALUE)
            elif os.path.exists(self.absolute_local_path(key)):
                self.sizetimes[key] = (os.path.getsize(self.absolute_local_path(key)), 
                                       round(os.path.getmtime(self.absolute_local_path(key)), 3))
        return self.sizetimes[key]
        
    def get_files_by_sizetime_key(self, sizetime_key) -> set:
        """
        Returns a set of every file or directory paths for which the 
        couple (file_size, file_modification_time) value corresponds 
        to the ``sizetime_key`` parameter.
        """
        file_paths = self.sizetimes.get_by_value(sizetime_key)
        return self._check_for_deleted_paths(file_paths)
    
    def _check_for_deleted_paths(self, paths:set):
        deleted_paths = [x for x in paths if not os.path.exists(self.absolute_local_path(x))]
        for dp in deleted_paths:
            self.hashes.delete(dp)
            self.sizetimes.delete(dp)
        return paths - set(deleted_paths)
    
    def save(self, key:str, file_hash, file_size, file_mtime):
        """
        Allows an external object to add a new file or folder reference to the local state object, 
        by giving already computed hash, size and modification time values. Note that the values
        will not be neither checked nor recomputed.

        If you prefer that the :py:class:`LocalState` class computes these values itself, and add
        the file or folder reference, you can just call the :py:meth:`get_hash` or 
        :py:meth:`get_sizetime` method. Note that then the :py:class:`LocalState` object just compute
        the needed values: it can compute the hash value without having any reference 
        in its sizetime dictionary. These one will only be computed when calling the 
        related method.

        :param key:
            Relative local path of the file or folder.
        :type key:
            str
        :param file_hash:
            File hash value of the file or folder.
        :type file_hash:
            str
        :param file_size:
            File size value of the file or folder. For information
            the size is computed with :py:meth:`os.path.getsize()`
            method, so the size is the number of bytes of the file.
        :type file_size:
            int
        :param file_mtime:
            File modification time value of the file or folder. For information
            the modification time is computed with :py:meth:`os.path.getmtime()`
            method, rounded to the third decimal, so the time is a number giving 
            the number of seconds since the epoch, precise at the millisecond.
        :type file_mtime:
            int
        :returns: 
            ``None``
        """
        if os.path.isdir(self.absolute_local_path(key)):
            file_hash = LocalState.DEFAULT_DIRECTORY_VALUE
            file_size = LocalState.DEFAULT_DIRECTORY_VALUE
            file_mtime = LocalState.DEFAULT_DIRECTORY_VALUE
        self.hashes[key] = file_hash
        self.sizetimes[key] = (file_size, file_mtime)
    
    def delete(self, delete_key:str):
        """
        Deletes key recursively. This method can be called internally 
        when detecting a file or folder does not exists anymore, or 
        by an external objects, that do not need to keep track of 
        this path anymore.
        """
        self.hashes.delete(delete_key)
        self.sizetimes.delete(delete_key)
    
    def move(self, src_key:str, dst_key:str):
        """
        Moves key recursively. This method can be called by an 
        external object, when you know a file or folder has been moved
        and that you want to keep the already computed values in 
        reference, without recomputing them all.
        """
        self.hashes.move(src_key, dst_key)
        self.sizetimes.move(src_key, dst_key)
            
    
    
    
    
    
    
