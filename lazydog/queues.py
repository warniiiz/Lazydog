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
:module: lazydog.queues
:synopsis: Bufferizes lazydog events pending for a possible \
aggregation with other simultaneous events.
:author: Clément Warneys <clement.warneys@gmail.com>

"""

from lazydog.states import LocalState
from lazydog.events import LazydogEvent
from lazydog.revised_watchdog.events import FileSystemEventHandler


class DatedlocaleventQueue(FileSystemEventHandler):
    """
    Basically accumulates all the events emited by a watchdog oberver.
    It inherits from :py:class:`~revised_watchdog.events.FileSystemEventHandler`, so it 
    is compatible with watchdog oberver. The :py:meth:`on_any_event` catches the 
    low-level event and adds them to the queue, after transorming them 
    to :py:class:`~lazydog.events.LazydogEvent`, which will further allow them
    to be post-treated by a :py:class:`~lazydog.handlers.HighlevelEventHandler`.

    The :py:class:`~lazydog.queues.DatedlocaleventQueue` has to be initialized 
    with a :py:class:`~lazydog.states.LocalState` object.
    """

    def __init__(self, local_states:LocalState):
        self.events_list = []
        self.events_list.clear()
        self.local_states = local_states
        super(DatedlocaleventQueue, self).__init__()

    def on_any_event(self, event):
        """
        Catch-all event handler.

        :param event:
            The event object representing the file system event.
        :type event:
            :py:class:`watchdog.events.FileSystemEvent`
        """
        super(DatedlocaleventQueue, self).on_any_event(event)
        self.events_list.append(LazydogEvent(event, self.local_states))

    def next(self):
        """
        Provides with the oldest event that has been queued, removing it 
        from the queue in the same time.
        """
        return self.events_list.pop(0) if not self.is_empty() else None
            
    def size(self):
        """Returns an integer corresponding to the current size of the queue."""
        return len(self.events_list)

    def is_empty(self):
        """``True`` if the queue size is 0."""
        return self.size() == 0
    

