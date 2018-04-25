#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2018 Clément Warneys <clement.warneys@gmail.com>
# Copyright 2011 Yesudeep Mangalapilly <yesudeep@gmail.com>
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
:module: revised_watchdog.observers.inotify_c
:author: yesudeep@google.com (Yesudeep Mangalapilly)
:author: Clément Warneys <clement.warneys@gmail.com>

This module is overloading the original :py:mod:`watchdog.observers.inotify_c` module 
by revising and completing it. Please read original **watchdog** project 
documentation for more information: https://github.com/gorakhargosh/watchdog

Fundamental changes and corrections have been brought to the original :py:class:`Inotify` 
class, whose behaviour was not correct when moving or deleting sub-directories.

"""

import os
import errno

from watchdog.observers.inotify_c import (
    Inotify, 
    InotifyEvent, 
    InotifyConstants,
    DEFAULT_EVENT_BUFFER_SIZE
    )


class Inotify(Inotify):
    """
    Linux inotify(7) API wrapper class. 

    With modified :py:meth:`read_events` method, 
    and added :py:meth:`_remove_watch_bookkeeping` method, 
    thus covering specifics needs of lazydog.

    :param path:
        The directory path for which we want an inotify object.
    :type path:
        bytes
    :param recursive:
        ``True`` if subdirectories should be monitored. ``False`` otherwise.
    :type recursive:
        boolean
    """
    
    def _remove_watch_bookkeeping(self, path):
        wd = self._wd_for_path.pop(path)
        del self._path_for_wd[wd]
        return wd


    def read_events(self, event_buffer_size=DEFAULT_EVENT_BUFFER_SIZE):
        """
        Reads events from inotify and yields them to the Inotify buffer.
        This method has been largely modified from original watchdog module...
        Thus preventing from unwanted behaviour.
        """
        # HACK: We need to traverse the directory path
        # recursively and simulate events for newly
        # created subdirectories/files. This will handle
        # mkdir -p foobar/blah/bar; touch foobar/afile

        def _recursive_simulate(src_path, event_type, cookie=0):
            events = []
            for root, dirnames, filenames in os.walk(src_path):
                for dirname in dirnames:
                    try:
                        full_path = os.path.join(root, dirname)
                        wd_dir = self._add_watch(full_path, self._event_mask)
                        e = InotifyEvent(
                            wd_dir, event_type | InotifyConstants.IN_ISDIR, cookie, dirname, full_path)
                        events.append(e)
                    except OSError:
                        pass
                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    wd_parent_dir = self._wd_for_path[os.path.dirname(full_path)]
                    e = InotifyEvent(
                        wd_parent_dir, event_type, cookie, filename, full_path)
                    events.append(e)
            return events

        event_buffer = None
        while True:
            try:
                event_buffer = os.read(self._inotify_fd, event_buffer_size)
            except OSError as e:
                if e.errno == errno.EINTR:
                    continue
            break

        with self._lock:

            event_list = []
            for wd, mask, cookie, name in Inotify._parse_event_buffer(event_buffer):

                if wd == -1:
                    continue
                wd_path = self._path_for_wd[wd]
                src_path = os.path.join(wd_path, name) if name else wd_path #avoid trailing slash
                inotify_event = InotifyEvent(wd, mask, cookie, name, src_path)
                move_src_path = None
                #print(inotify_event)
                
                if inotify_event.is_moved_from:
                    self.remember_move_from_event(inotify_event)
                elif inotify_event.is_moved_to:
                    move_src_path = self.source_for_move(inotify_event)
                    if move_src_path is not None:
                        # Adjusting existing watcher paths
                        for moved_path in [x for x in self._wd_for_path if x.startswith(move_src_path)]:
                            new_path = moved_path.replace(move_src_path, inotify_event.src_path, 1)
                            moved_wd = self._wd_for_path[moved_path]
                            self._wd_for_path.pop(moved_path)
                            self._wd_for_path[new_path] = moved_wd
                            self._path_for_wd[moved_wd] = new_path
                        
                    #===========================================================
                    # src_path = os.path.join(wd_path, name)
                    # inotify_event = InotifyEvent(wd, mask, cookie, name, src_path)
                    #===========================================================

                if inotify_event.is_ignored:
                    # Clean up book-keeping for deleted watches.
                    self._remove_watch_bookkeeping(src_path)
                    continue

                event_list.append(inotify_event)

                if (self.is_recursive and inotify_event.is_directory): 
                    
                    if inotify_event.is_create:
                        
                        # Putting newly created dir under observation
                        try:
                            self._add_watch(src_path, self._event_mask)
                        except OSError:
                            continue
                        
                        # The following generate elements that would have been created before 
                        # watcher had time to register...
                        event_list.extend(_recursive_simulate(src_path, InotifyConstants.IN_CREATE))
                    
                    
                    elif inotify_event.is_moved_to and move_src_path is None:
                    
                        # When a directory from another part of the
                        # filesystem is moved into a watched directory, this
                        # will not generate events for the directory tree.
                        # We need to coalesce IN_MOVED_TO events and those
                        # IN_MOVED_TO events which don't pair up with
                        # IN_MOVED_FROM events should be marked IN_CREATE
                        # instead relative to this directory.
                        
                        # Putting newly created dir under observation
                        try:
                            self._add_watch(src_path, self._event_mask)
                        except OSError:
                            continue
                        
                        # The following generate elements that would have been created before 
                        # watcher had time to register...
                        event_list.extend(_recursive_simulate(src_path, InotifyConstants.IN_MOVED_TO, -1))
                        
                        

        return event_list

