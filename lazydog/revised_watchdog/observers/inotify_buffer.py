#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2018 Clément Warneys <clement.warneys@gmail.com>
# Copyright 2014 Thomas Amland <thomas.amland@gmail.com>
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
:author: Thomas Amland <thomas.amland@gmail.com>
:author: Clément Warneys <clement.warneys@gmail.com>

This module is overloading the original :py:mod:`watchdog.observers.inotify_buffer` module 
by revising and completing it. Please read original **watchdog** project 
documentation for more information: https://github.com/gorakhargosh/watchdog

The main change is in the :py:class:`InotifyBuffer` class, whose :py:meth:`InotifyBuffer.__init__`
method now uses revised watchdog :py:class:`~lazydog.revised_watchdog.observers.inotify_c.Inotify` class.

"""

import logging
from watchdog.utils import BaseThread
from watchdog.utils.delayed_queue import DelayedQueue
from watchdog.observers.inotify_buffer import InotifyBuffer
from lazydog.revised_watchdog.observers.inotify_c import Inotify 

logger = logging.getLogger(__name__)

class InotifyBuffer(InotifyBuffer):
    """
    A wrapper for `Inotify` that holds events for `delay` seconds. During
    this time, ``IN_MOVED_FROM`` and ``IN_MOVED_TO`` events are paired.

    Please note that his class remains unmodified 
    in revised_watchdog package. Only the :py:meth:`__init__` method is overrided 
    in order it uses the new definition of :py:class:`~lazydog.revised_watchdog.observers.inotify_c.Inotify` class.
    """


    def __init__(self, path, recursive=False):
        BaseThread.__init__(self)
        self._queue = DelayedQueue(self.delay)
        self._inotify = Inotify(path, recursive)
        self.start()
