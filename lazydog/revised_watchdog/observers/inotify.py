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
:module: revised_watchdog.observers.inotify
:synopsis: ``inotify(7)`` based emitter implementation, enhanced implementation of original watchdog one.
:author: Sebastien Martini <seb@dbzteam.org>
:author: Luke McCarthy <luke@iogopro.co.uk>
:author: yesudeep@google.com (Yesudeep Mangalapilly)
:author: Tim Cuthbertson <tim+github@gfxmonk.net>
:author: Clément Warneys <clement.warneys@gmail.com>
:platforms: Linux 2.6.13+.

This module is overloading the original :py:mod:`watchdog.observers.inotify` module 
by revising and completing it. Please read original **watchdog** project 
documentation for more information: https://github.com/gorakhargosh/watchdog

The main changes concern some methods in the :py:class:`InotifyEmitter` class:

* :py:meth:`~InotifyEmitter.on_thread_start` This method now uses revised \
:py:class:`~lazydog.revised_watchdog.observers.inotify_buffer.InotifyBuffer`.
* :py:meth:`~InotifyEmitter.queue_events` This method has been simplified in order to reduce \
the number of emitted low-level events, in comparison with \
original watchdog module. 


"""

from watchdog.observers.inotify import (
    InotifyEmitter, 
    InotifyObserver
    )

from watchdog.observers.api import (
    BaseObserver,
    DEFAULT_OBSERVER_TIMEOUT
)

from watchdog.utils import unicode_paths

from watchdog.events import (
    FileMovedEvent,
    DirMovedEvent,
    FileCreatedEvent,
    DirCreatedEvent,
    FileDeletedEvent,
    DirDeletedEvent,
    )


from lazydog.revised_watchdog.observers.inotify_buffer import InotifyBuffer

from lazydog.revised_watchdog.events import (
    TrueFileModifiedEvent,
    MetaFileModifiedEvent,
    TrueDirModifiedEvent,
    MetaDirModifiedEvent
    )

class InotifyEmitter(InotifyEmitter):
    """
    inotify(7)-based event emitter. Revised package mainly 
    concerns :py:meth:`queue_events` method, thus covering 
    specific needs of lazydog package.

    :param event_queue:
        The event queue to fill with events.
    :type event_queue:
        :py:class:`watchdog.events.EventQueue`
    :param watch:
        A watch object representing the directory to monitor.
    :type watch:
        :py:class:`watchdog.observers.api.ObservedWatch`
    :param timeout:
        Read events blocking timeout (in seconds).
    :type timeout:
        float
    """

    def on_thread_start(self):
        path = unicode_paths.encode(self.watch.path)
        self._inotify = InotifyBuffer(path, self.watch.is_recursive)


    def queue_events(self, timeout, full_events=False):
        """
        This method is classifying the events received from Inotify into
        watchdog events type (defined in :py:mod:`watchdog.events` module).

        :param timeout:
            Unused param (from watchdog original package).
        :type timeout:
            float
        :param full_events:
            If ``True``, then the method will report unmatched move 
            events as separate events. This means that if 
            ``True``, a file move event from outside the watched directory
            will result in a :py:class:`watchdog.events.FileMovedEvent` event, with no origin. Else 
            (if ``False``), it will result in a :py:class:`watchdog.events.FileCreatedEvent` event.
            This behavior is by default only called by a :py:class:`InotifyFullEmitter`.
        :type full_events:
            boolean
        """
        with self._lock:

            event = self._inotify.read_event()
            if event is None:
                return
            if isinstance(event, tuple):
                move_from, move_to = event
                src_path = self._decode_path(move_from.src_path)
                dest_path = self._decode_path(move_to.src_path)
                cls = DirMovedEvent if move_from.is_directory else FileMovedEvent
                self.queue_event(cls(src_path, dest_path))
                #===============================================================
                # self.queue_event(MetaDirModifiedEvent(os.path.dirname(src_path)))
                # self.queue_event(MetaDirModifiedEvent(os.path.dirname(dest_path)))
                #===============================================================
                #===============================================================
                # if move_from.is_directory and self.watch.is_recursive:
                #     for sub_event in generate_sub_moved_events(src_path, dest_path):
                #         self.queue_event(sub_event)
                #===============================================================
                return

            src_path = self._decode_path(event.src_path)
            if event.is_moved_to:
                if (full_events):
                    cls = DirMovedEvent if event.is_directory else FileMovedEvent
                    self.queue_event(cls(None, src_path))
                else:
                    cls = DirCreatedEvent if event.is_directory else FileCreatedEvent
                    self.queue_event(cls(src_path))
                #===============================================================
                # self.queue_event(DirModifiedEvent(os.path.dirname(src_path)))
                #===============================================================
                #===============================================================
                # if event.is_directory and self.watch.is_recursive:
                #     for sub_event in generate_sub_created_events(src_path):
                #         self.queue_event(sub_event)
                #===============================================================
            elif event.is_attrib:
                cls = MetaDirModifiedEvent if event.is_directory else MetaFileModifiedEvent
                self.queue_event(cls(src_path))
            elif event.is_modify:
                cls = TrueDirModifiedEvent if event.is_directory else TrueFileModifiedEvent
                self.queue_event(cls(src_path))
            elif event.is_delete or (event.is_moved_from and not full_events):
                cls = DirDeletedEvent if event.is_directory else FileDeletedEvent
                self.queue_event(cls(src_path))
                #===============================================================
                # self.queue_event(DirModifiedEvent(os.path.dirname(src_path)))
                #===============================================================
            elif event.is_moved_from and full_events:
                cls = DirMovedEvent if event.is_directory else FileMovedEvent
                self.queue_event(cls(src_path, None))
                #===============================================================
                # self.queue_event(DirModifiedEvent(os.path.dirname(src_path)))
                #===============================================================
            elif event.is_create:
                cls = DirCreatedEvent if event.is_directory else FileCreatedEvent
                self.queue_event(cls(src_path))
                #===============================================================
                # self.queue_event(DirModifiedEvent(os.path.dirname(src_path)))
                #===============================================================


class InotifyObserver(InotifyObserver):
    """
    Observer thread that schedules watching directories and dispatches
    calls to event handlers. 

    Please note that his class remains unmodified 
    in revised_watchdog package. Only the :py:meth:`__init__` method is overided 
    in order it uses the new definition of :py:class:`InotifyEmitter` class.
    """

    def __init__(self, timeout=DEFAULT_OBSERVER_TIMEOUT, generate_full_events=False):
        if (generate_full_events):
            BaseObserver.__init__(self, emitter_class=InotifyFullEmitter, timeout=timeout)
        else:
            BaseObserver.__init__(self, emitter_class=InotifyEmitter, timeout=timeout)
