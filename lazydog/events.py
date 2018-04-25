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
:module: lazydog.events
:synopsis: Definitions of the high-level lazydog events, based on the \
low-level watchdog ones, which are now aggregable and also convertible \
to copy or move events.
:author: Clément Warneys <clement.warneys@gmail.com>

Possible type of lazydog events:

* :py:attr:`~LazydogEvent.EVENT_TYPE_CREATED` for the creation of a file or folder
* :py:attr:`~LazydogEvent.EVENT_TYPE_MODIFIED` for the creation of a file or folder \
(whatever the modification concerns: metadata or content)
* :py:attr:`~LazydogEvent.EVENT_TYPE_MOVED` for the move of a file or folder
* :py:attr:`~LazydogEvent.EVENT_TYPE_COPIED` for the copy of a file or folder
* :py:attr:`~LazydogEvent.EVENT_TYPE_DELETED` for the deletion of a file or folder

.. note:: Some kind of events such as Moved and Copied have 2 path attributes:
    :py:attr:`~LazydogEvent.path` for the origin path, and 
    :py:attr:`~LazydogEvent.to_path` for the destination path. Other kinds have only 
    the :py:attr:`~LazydogEvent.path` attribute.

    The :py:attr:`~LazydogEvent.ref_path` attribute always refers 
    to the current location of the file (:py:attr:`~LazydogEvent.to_path` if any, 
    else :py:attr:`~LazydogEvent.path`). All the paths are always relative to the 
    main watched directory.

Lazydog has the ability to aggregate related low-level events. For example, in 
the case of multiple deletion events, each of one under the same parent directory, 
the lazydog handler will emit only one deletion event, with the path of the common 
parent directory.

Lazydog is also able to correlate almost simultaneous deletion and creation events
into a unique moved event, if the low-level events are related. Or mutiple creation events
into a unique copied event, if the new files and folders were already existing 
elsewhere in the main watched folder.

All these correlations are mainly done by the :py:class:`~lazydog.handlers.HighlevelEventHandler`
class, but some helper methods are defined in the :py:class:`~lazydog.events.LazydogEvent`
class such as :py:meth:`~lazydog.events.LazydogEvent.add_source_paths_and_transforms_into_copied_event`
or :py:meth:`~lazydog.events.LazydogEvent.update_main_event`.

"""

import datetime
import os

from lazydog.states import LocalState

from lazydog.revised_watchdog.events import (
    FileSystemEvent,
    EVENT_TYPE_C_MODIFIED,
    EVENT_TYPE_M_MODIFIED 
    )

from watchdog.events import (
    EVENT_TYPE_MOVED, 
    EVENT_TYPE_CREATED, 
    EVENT_TYPE_DELETED
    )

class LazydogEvent():
    """
    Main class of :py:mod:`lazydog.events` module. Initialization with a 
    low-level watchdog event that is then converted into 
    high-level lazydog event.

    .. note:: The local path of the event is referenced as a relative path
        starting from the absolute path of the watched directory. For this 
        mechanism, the Lazydog event needs a reference, which is given 
        at the initialisation with a :class:`LocalState` reference.

    :param event:
        A low-level watchdog event.
    :type event:
        :py:class:`~revised_watchdog.events.FileSystemEvent`
    :param local_states:
        The reference state of the local files in the watched directory.
        Including the absolute path of the watched directory, thus allowing to 
        manage high-level event with relative path.
    :type local_states:
         :py:class:`~lazydog.states.LocalState`
    :returns: 
        A high-level lazydog event (converted from low-level watchdog event).
    :rtype: 
        :py:class:`~lazydog.events.LazydogEvent`

    """


    EVENT_TYPE_CREATED = EVENT_TYPE_CREATED # 'created'
    """Created event type, imported from :py:mod:`watchdog` module"""

    EVENT_TYPE_DELETED = EVENT_TYPE_DELETED # 'deleted'
    """Deleted event type, imported from :py:mod:`watchdog` module"""

    EVENT_TYPE_MOVED = EVENT_TYPE_MOVED # 'moved'
    """Moved event type, imported from :py:mod:`watchdog` module"""

    EVENT_TYPE_C_MODIFIED = EVENT_TYPE_C_MODIFIED # 'modified' # content modification
    """Content modified event type, imported from :py:mod:`lazydog.revised_watchdog` module"""

    EVENT_TYPE_M_MODIFIED = EVENT_TYPE_M_MODIFIED # 'metadata' # metadata modification
    """Metadata modified event type, imported from :py:mod:`lazydog.revised_watchdog` module"""
        
    EVENT_TYPE_COPIED = 'copied'
    """
    New kind of event, that does not exist in watchdog python module.
    Copied event can only be obtained by transforming Created events. 
    The transformation decision is made by the 
    :py:class:`~lazydog.handlers.HighlevelEventHandler` and is based on 
    the existing files or folders in the watched directory.
    """
    
    def __init__(self, event:FileSystemEvent, local_states:LocalState):
        # Dating now
        self.event_date = datetime.datetime.now()
        
        # Saving LocalState Reference
        self.local_states = local_states
        
        # FileSystemEvent definitions
        self.type = event.event_type
        self.is_dir = event.is_directory
        
        # Path and local file handling
        self.path = self.local_states.relative_local_path(event.src_path)
        self.to_path = self.local_states.relative_local_path(event.dest_path) if self.has_dest() else None
        self._reset_ref_paths()
            
        # Local file or folder computations
        self._reset_file_infos()
        
        # Helpers for high-level event identification
        self.possible_src_paths = {}
        self.possible_src_paths.clear()
        self.related_events = []
        self.related_events.clear()
        self.related_events.append(self)
        self.first_event_date = self.event_date
        self.latest_event_date = self.event_date
        self.latest_reworked_date = datetime.datetime.now()
        self.is_related = False
        self.is_irrelevant = False

        
    def __str__(self):
        if self.is_moved_event() or self.is_copied_event():
            return ('logged[' + str(self.event_date) + '] ' +
                    self.type + ": '" + self.path + "' " +
                    "to '" + self.to_path + "' " + 
                    'mtime[' + str(self.file_mtime) + '] ' +
                    'size[' + str(self.file_size) + '] ' +
                    'inode[' + str(self.file_inode) + '] ' +
                    ('irrelevant ' if self.is_irrelevant else ''))
        else:
            return ('logged[' + str(self.event_date) + '] ' +
                    self.type + ": '" + self.path +  "' " + 
                    'mtime[' + str(self.file_mtime) + '] ' +
                    'size[' + str(self.file_size) + '] ' +
                    'inode[' + str(self.file_inode) + '] ' +
                    ('irrelevant ' if self.is_irrelevant else ''))
            
    
    # managing weird phenomenom when approahing the root of the watched dir.
    def _correct_path_value(self, value:str) -> str:
        return '/' if value == '/.' else value
    
    @property
    def path(self) -> str:
        """Origin path of the event."""
        return self._path

    @path.setter
    def path(self, value:str):
        self._path = self._correct_path_value(value)
        self._reset_ref_paths()
        
    @property
    def to_path(self) -> str:
        """Destination path of the event, if any, else ``None``."""
        return self._to_path

    @to_path.setter
    def to_path(self, value:str):
        self._to_path = self._correct_path_value(value)
        self._reset_ref_paths()
    
    
    def _reset_ref_paths(self):
        self._ref_path = None
        self._absolute_ref_path = None
    
    @property
    def ref_path(self) -> str:
        """
        Refers to the current location of the file or the event,
        which is :py:attr:`to_path` if any, else :py:attr:`path`.
        """
        if self._ref_path is None:
            self._ref_path = self.to_path if self.has_dest() else self.path
        return self._ref_path
    
    @ref_path.setter
    def ref_path(self, value:str):
        if self.has_dest():
            self.to_path = value
        else:
            self.path = value
    
    # Parent directory of destination directory
    @property
    def parent_rp(self) -> str:
        """
        Refers to the directory name of the event.
        If the directory name is already the main watched 
        directory, ``None`` is returned.
        """
        if self.ref_path == '/':
            return None
        else:
            return os.path.dirname(self.ref_path)
        
    # Filename or dirname
    @property
    def basename(self) -> str:
        """Returns the filename or directory name of the related file or dir."""
        return os.path.basename(self.ref_path)
    
    @property
    def absolute_ref_path(self) -> str:
        """Returns the absolute path of the current location of the file or dir."""
        if self._absolute_ref_path is None:
            self._absolute_ref_path = self.local_states.absolute_local_path(self.ref_path)
        return self._absolute_ref_path
    
    
    def is_directory(self) -> bool:
        """Returns ``True`` if the event is related to a directory."""
        return self.is_dir
    
    # Check if same type (only type, without considering Dir)
    def is_same_type_than(self, event) -> bool:
        return self.type == event.type
    
    def is_moved_event(self) -> bool:
        """Returns ``True`` if the event is a file or dir move."""
        return self.type == LazydogEvent.EVENT_TYPE_MOVED
    
    def is_dir_moved_event(self) -> bool:
        """Returns ``True`` if the event is a dir move."""
        return self.is_moved_event() and self.is_directory()
    
    def is_deleted_event(self) -> bool:
        """Returns ``True`` if the event is a file or dir deletion."""
        return self.type == LazydogEvent.EVENT_TYPE_DELETED
    
    def is_dir_deleted_event(self) -> bool:
        """Returns ``True`` if the event is a dir deletion."""
        return self.is_deleted_event() and self.is_directory()
    
    def is_created_event(self) -> bool:
        """Returns ``True`` if the event is a file or dir creation."""
        return self.type == LazydogEvent.EVENT_TYPE_CREATED
    
    def is_dir_created_event(self) -> bool:
        """Returns ``True`` if the event is a dir creation."""
        return self.is_created_event() and self.is_directory()
    
    def is_file_created_event(self) -> bool:
        """Returns ``True`` if the event is a file creation."""
        return self.is_created_event() and not self.is_directory()
    
    def is_copied_event(self) -> bool:
        """Returns ``True`` if the event is a file or dir copy."""
        return self.type == LazydogEvent.EVENT_TYPE_COPIED
    
    def is_modified_event(self) -> bool:
        """Returns ``True`` if the event is a file or dir modification."""
        return self.is_meta_modified_event() or self.is_data_modified_event()
    
    def is_meta_modified_event(self) -> bool:
        """Returns ``True`` if the event is a file or dir modification of the metadata only."""
        return self.type == LazydogEvent.EVENT_TYPE_M_MODIFIED
    
    def is_data_modified_event(self) -> bool:
        """Returns ``True`` if the event is a file or dir modification of the content."""
        return self.type == LazydogEvent.EVENT_TYPE_C_MODIFIED 
    
    def is_file_modified_event(self) -> bool:
        """Returns ``True`` if the event is a file modification."""
        return self.is_modified_event() and not self.is_directory()
    
    def is_meta_file_modified_event(self) -> bool:
        """Returns ``True`` if the event is a file modification of the metadata only."""
        return self.is_meta_modified_event() and not self.is_directory()
    
    def is_data_file_modified_event(self) -> bool:
        """Returns ``True`` if the event is a file modification of the content."""
        return self.is_data_modified_event() and not self.is_directory()
    
    def is_dir_modified_event(self) -> bool:
        """Returns ``True`` if the event is a dir modification."""
        return self.is_modified_event() and self.is_directory()
    
    def has_dest(self) -> bool:
        """
        Returns ``True`` if the event has a destination path 
        (i.e. if it's a Moved or Copied event).
        """
        return self.is_moved_event() or self.is_copied_event()
    
    def has_same_mtime_than(self, previous_event) -> bool:
        """Returns ``True`` if the event has the same modification time than the event in parameter."""
        return self.file_mtime == previous_event.file_mtime
    
    # Check size 
    def has_same_size_than(self, event) -> bool:
        """Returns ``True`` if the event has the same size than the event in parameter."""
        return self.file_size == event.file_size
    
    # Check paths
    def has_same_path_than(self, event) -> bool:
        """
        Returns ``True`` if the event has the same :py:attr:`ref_path` 
        than the event in parameter.
        
        If both events have destination path, source paths
        are compared too.
        """
        if self.has_dest() and event.has_dest():
            return self.path == event.path and self.to_path == event.to_path
        else:
            return self.ref_path == event.ref_path
    
    def has_same_src_path_than(self, event) -> bool:
        """
        Returns ``True`` if the :py:attr:`path` of event is the same 
        than the :py:attr:`ref_path` of the event in parameter.
        """
        return self.path == event.ref_path
        
    
    
    @staticmethod
    def p1_comes_after_p2(p1:str, p2:str) -> bool:
        """
        p1 and p2 are both paths (str format). This method is
        a basic comparison method to check if the first parameter p1
        is striclty a parent path of the second parameter p2. 

        Returns ``False`` if both paths are identical.
        """
        if not p1.endswith('/'):
            p1 = p1 + '/'
        if not p2.endswith('/'):
            p2 = p2 + '/'
        return p1.startswith(p2) and p1 != p2
    
    @staticmethod
    def p1_comes_before_p2(p1:str, p2:str) -> bool:
        """Same than :py:meth:`p1_comes_after_p2` method, but opposite result.""" 
        return LazydogEvent.p1_comes_after_p2(p2, p1)
    
    def comes_before(self, event) -> bool:
        """Same than :py:meth:`comes_after` method, but opposite result.""" 
        return event.comes_after(self)
            
    def same_or_comes_before(self, event) -> bool:
        """Same than :py:meth:`comes_before` method, but also ``True`` when both events have identical paths.""" 
        return self.comes_before(event) or self.has_same_path_than(event)
    
    def comes_after(self, event, complete_check:bool=True) -> bool:
        """
        Same result than :py:meth:`p1_comes_after_p2`,
        comparing current event :py:attr:`ref_path` path (as p1), to the 
        :py:attr:`ref_path` path of the event in parameter (as p2).

        If both events have a destination path, source paths
        are compared too.

        Returns ``False`` if both paths are identical.
        """ 
        if complete_check and self.has_dest() and event.has_dest():
            return LazydogEvent.p1_comes_after_p2(self.path, event.path) and LazydogEvent.p1_comes_after_p2(self.to_path, event.to_path)
        else:
            return LazydogEvent.p1_comes_after_p2(self.ref_path, event.ref_path)
        
    def same_or_comes_after(self, event) -> bool:
        """Same than :py:meth:`comes_after` method, but also ``True`` when both events have identical paths.""" 
        return self.comes_after(event) or self.has_same_path_than(event)
                
    
    @staticmethod
    def datetime_difference_from_now(dt:datetime.datetime) -> datetime.datetime:
        """ 
        Returns :py:class:`datetime.datetime` object representing time difference 
        between the datetime in parameter, and now.
        """
        return datetime.datetime.now() - dt
    
    def idle_time(self) -> datetime.datetime:
        """ 
        Returns time difference between last time this event has been updated
        and now. 

        .. note:: Event updates occur when the event is aggregated to another 
            related event, or also when the event is transformed into a copied
            or a moved one...
        """
        return LazydogEvent.datetime_difference_from_now(self.latest_reworked_date)
                                                      
    @property
    def file_hash(self) -> str:
        """
        Returns the file hash of the file related to the event if any, else ``None``.
        File hash value is saved into a private variable, in order to avoid useless
        computation time...
        """
        if self._file_hash is None:
            if self.is_directory():
                self._file_hash = self.local_states.DEFAULT_DIRECTORY_VALUE
            else:
                try:
                    # Here we don't use local_states which is considered as historic value of hash. 
                    # We need to compute new hash value (to be able to compare it to historic one)
                    self._file_hash = self.local_states.hash_function(self.absolute_ref_path)
                except:
                    self._file_hash = None
        return self._file_hash
    
              
    @staticmethod
    def count_files_in(absolute_dir_path:str) -> int:
        """
        Counts all non-empty (file size > 0) files in ``absolute_dir_path`` 
        directory and all its sub-directories. Returns ``None`` if 
        the ``absolute_dir_path`` is not a directory.

        .. note:: Be careful: ``absolute_dir_path`` has to represent 
            absolute path (not a relative one).
        """
        qty = None
        try:
            if os.path.isdir(absolute_dir_path):
                qty = 0  
                for root, dirs, files in os.walk(absolute_dir_path):
                    for f in files:
                        if os.path.getsize(os.path.join(root, f)) > 0:
                            qty = qty + 1
        except:
            pass
        return qty  
    
    @property
    def dir_files_qty(self) -> int:
        """
        Counts all non-empty (file size > 0) files in the related path
        of the event, and all its sub-directories. Returns ``None`` 
        if the event is not related to a directory.
        """
        if self._dir_files_qty is None and self.is_directory():
            self._dir_files_qty = LazydogEvent.count_files_in(self.absolute_ref_path)
        return self._dir_files_qty
    
    @staticmethod
    def get_file_size(absolute_file_path:str) -> int:
        """Returns the size of the file at the specified absolute path if any, else ``None``."""
        try:
            return os.path.getsize(absolute_file_path) if not os.path.isdir(absolute_file_path) else None
        except:
            return None
        
    @property
    def file_size(self) -> int:
        """
        Size of the file related to the event if any, else ``None``.
        File size value is saved in a private variable, in order to avoid useless
        sollicitation of file-system.
        """
        if self._file_size is None and not self.is_directory():
            self._file_size = LazydogEvent.get_file_size(self.absolute_ref_path)
        return self._file_size
    
    def is_empty(self) -> bool:
        """
        Returns ``True`` if the event is related to an empty directory, 
        or if the event is related to an empty file (size = 0).
        """
        if self.is_directory():
            return self.dir_files_qty == 0
        else:
            return self.file_size == 0
    
    @property
    def file_mtime(self) -> float:
        """
        Last modification time of the file related to the event if any, else ``None``.
        File modification time value is saved in a private variable, in order to avoid useless
        sollicitation of file-system.
        """
        if self._file_mtime is None:
            try:
                self._file_mtime = round(os.path.getmtime(self.absolute_ref_path), 3)
            except:
                self._file_mtime = None
        return self._file_mtime
    
    @property
    def file_inode(self) -> int:
        """
        Inode of the file related to the event if any, else ``None``.
        Inode value is saved in a private variable, in order to avoid useless
        sollicitation of file-system.

        .. note:: This property seems now useless, and could be deprecated.
        """
        if self._file_inode is None:
            try:
                self._file_inode = os.stat(self.absolute_ref_path).st_ino
            except:
                self._file_inode = None
        return self._file_inode
        
    
    def _reset_file_infos(self):
        # reset
        self._file_inode = None
        self._file_size = None
        self._file_mtime = None
        self._file_hash = None
        self._dir_files_qty = None
        # compute again
        self.file_mtime
        self.file_size
        self.file_inode
        self.dir_files_qty
        
    
    def update_main_event(self, main_event):    
        """
        High level helper method to facilitate the work of the 
        :py:class:`~lazydog.handlers.HighlevelEventHandler`. 
        When different events are identified as related ones, this method 
        is merging the current event in the main one (in parameter). 

        General idea is to update paramters of the main event, such as 
        :py:attr:`file_inode`, :py:attr:`file_mtime`, :py:attr:`file_size`, 
        :py:attr:`file_hash`, and also the dates of occurence (which are needed
        to manage an aggregation time limit).

        Each related events, including the main event itself, are all listed 
        in :py:attr:`related_events` list, to keep track of them.
        """

        # usual aggregations
        for e in self.related_events:
            main_event.related_events.append(e)
        # re-init
        if self.is_modified_event() and not self.is_directory() and not main_event.is_directory():
            if main_event._file_mtime != self._file_mtime or main_event._file_size != self._file_size:
                main_event._file_inode = self._file_inode
                main_event._file_mtime = self._file_mtime
                main_event._file_size = self._file_size
                main_event._file_hash = self._file_hash
        if main_event.is_directory():
            self._dir_files_qty = None
        # timing    
        if main_event.latest_event_date < self.latest_event_date:
            main_event.latest_event_date = self.latest_event_date
        if main_event.first_event_date > self.first_event_date:
            main_event.first_event_date = self.first_event_date
        main_event.latest_reworked_date = datetime.datetime.now()
        # is now related
        self.is_related = True
        main_event.is_related = True
    
    # looking for the most probable source aamong a list of potential sources, based on the basename of the destination file or folder
    @staticmethod
    def _get_most_potential_source(src_paths:set, dest_path:str) -> str:
        """
        High level private helper method that identifies the best match 
        when there are multiple possibilities to aggregate creations events 
        in a copied one. 

        To be more accurate, when there is a new file creation, it can correspond
        to an existing file by matching its size, its modification date, and eventually 
        its hash. Actually, there could be multiple matches (if you copy the same file 
        multiple times). The idea is to get the more likely source file, based on the
        filename of the different sources, and comparing to the desination filename.

        Usually, if the source filename is something like "foo.txt", the destination 
        filename will be something like "Copy of foo.txt" or "foo-copy.txt" or anything
        approaching, depending on the operating system that did the copy. The goal
        is to catch the "foo.txt" source filename preferentially before any other one.
        """
        most_potential_sources = [x for x in src_paths if os.path.splitext(os.path.basename(x))[0] in os.path.splitext(os.path.basename(dest_path))[0]]
        most_potential_sources.sort(key = lambda x: -len(x))
        return most_potential_sources[0] if most_potential_sources else next(iter(src_paths))

    def add_source_paths_and_transforms_into_copied_event(self, src_paths:set):
        """
        High level helper method to facilitate the work of the 
        :py:class:`~lazydog.handlers.HighlevelEventHandler`. 
        When a creation event is actually identified as a copied one, 
        this method is transforming the current event in a copied one. 
 
        The old :py:attr:`path` attribute is converted into a :py:attr:`to_path`
        one. And the :py:attr:`path` id filled with one of the identified possible 
        source paths (this identification is the job of the 
        :py:class:`~lazydog.handlers.HighlevelEventHandler`).

        To get prepared to potential future aggregation of multiple copied 
        events (for example in the case of a copied directory), we need to keep 
        track of all the possible source paths which are then saved into 
        a :py:attr:`possible_src_paths` attribute.
        """
        if src_paths.__class__.__name__ == str.__name__:
            src_paths = set([src_paths])
        for sp in src_paths:
            if not self.is_copied_event():
                self.type = LazydogEvent.EVENT_TYPE_COPIED
                self.to_path = self.path
                self.path = LazydogEvent._get_most_potential_source(src_paths, self.to_path)
            # save all potential parent source path, for future use
            if os.path.basename(sp) == os.path.basename(self.to_path):
                self.possible_src_paths[sp] = os.path.dirname(sp) if sp != '/' else None
            