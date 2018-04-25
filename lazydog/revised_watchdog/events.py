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
:module: revised_watchdog.events
:synopsis: File system events and event handlers.
:author: yesudeep@google.com (Yesudeep Mangalapilly)
:author: Clément Warneys <clement.warneys@gmail.com>

This module is overloading the original :py:mod:`watchdog.events` module 
by revising and completing it. Please read original **watchdog** project 
documentation for more information: https://github.com/gorakhargosh/watchdog

This module imports some definitions of watchdog.events and keeps them unchanged:

* :py:class:`FileModifiedEvent`
* :py:class:`DirModifiedEvent`
* :py:class:`FileSystemEvent`
* :py:class:`FileSystemEventHandler`
* :py:data:`EVENT_TYPE_MOVED`
* :py:data:`EVENT_TYPE_CREATED`
* :py:data:`EVENT_TYPE_DELETED`

It adds the following definitions, in order to add some granularity in the
:py:class:`watchdog.events.ModifiedEvent` definition, thus differentiating content modification
from only metadata (access date, owner, etc.) modification:

* :py:class:`MetaFileModifiedEvent`
* :py:class:`TrueFileModifiedEvent`
* :py:class:`MetaDirModifiedEvent`
* :py:class:`TrueDirModifiedEvent`
* :py:data:`EVENT_TYPE_C_MODIFIED`
* :py:data:`EVENT_TYPE_M_MODIFIED`

Finally, it overloads the FileSystemEventHandler class, in order 
to manage the new granularity of modified events:

* :py:class:`FileSystemEventHandler`

"""

from watchdog.events import (
    FileModifiedEvent, 
    DirModifiedEvent, 
    FileSystemEvent,
    FileSystemEventHandler, 
    EVENT_TYPE_MOVED, 
    EVENT_TYPE_CREATED, 
    EVENT_TYPE_DELETED
    )

EVENT_TYPE_C_MODIFIED = 'modified' # content-only modification
EVENT_TYPE_M_MODIFIED = 'metadata' # metadata-only modification

class MetaFileModifiedEvent(FileModifiedEvent):
    """File system event representing metadata file modification on the file system."""

    event_type = EVENT_TYPE_M_MODIFIED

    def __init__(self, src_path):
        super(MetaFileModifiedEvent, self).__init__(src_path)

class TrueFileModifiedEvent(FileModifiedEvent):
    """File system event representing true file content modification on the file system."""

    event_type = EVENT_TYPE_C_MODIFIED

    def __init__(self, src_path):
        super(TrueFileModifiedEvent, self).__init__(src_path)

class MetaDirModifiedEvent(DirModifiedEvent):
    """File system event representing metadata directory modification on the file system."""

    event_type = EVENT_TYPE_M_MODIFIED

    def __init__(self, src_path):
        super(MetaDirModifiedEvent, self).__init__(src_path)

class TrueDirModifiedEvent(DirModifiedEvent):
    """File system event representing true directory content modification on the file system."""

    event_type = EVENT_TYPE_C_MODIFIED

    def __init__(self, src_path):
        super(TrueDirModifiedEvent, self).__init__(src_path)

class FileSystemEventHandler(FileSystemEventHandler):
    """
    Base file system event handler that you can override methods from.
    With modified dispatch method, added :py:meth:`on_data_modified` 
    and :py:meth:`on_meta_modified` methods, thus covering specific 
    needs of lazydog.
    """

    def dispatch(self, event):
        """
        Dispatches events to the appropriate methods.

        :param event:
            The event object representing the file system event.
        :type event:
            :py:class:`~watchdog.events.FileSystemEvent`
        """
        self.on_any_event(event)
        _method_map = {
            EVENT_TYPE_M_MODIFIED: self.on_meta_modified,
            EVENT_TYPE_C_MODIFIED: self.on_data_modified,
            EVENT_TYPE_MOVED: self.on_moved,
            EVENT_TYPE_CREATED: self.on_created,
            EVENT_TYPE_DELETED: self.on_deleted,
        }
        event_type = event.event_type
        _method_map[event_type](event)


    def on_data_modified(self, event):
        """Called when a file or directory true content is modified.

        :param event:
            Event representing file or directory modification.
        :type event:
            :py:class:`DirModifiedEvent` or :py:class:`FileModifiedEvent`
        """
        self.on_modified(event)
        
    def on_meta_modified(self, event):
        """Called when a file or directory metadata is modified.

        :param event:
            Event representing file or directory modification.
        :type event:
            :py:class:`DirModifiedEvent` or :py:class:`FileModifiedEvent`
        """
        self.on_modified(event)

