# -*- coding: utf-8 -*-
#
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

import logging
from watchdog.utils import BaseThread
from watchdog.utils.delayed_queue import DelayedQueue
from watchdog.observers.inotify_buffer import InotifyBuffer
from revised_watchdog.observers.inotify_c import Inotify 

logger = logging.getLogger(__name__)

#############################################
### watchdog.observers.inotify_buffer     ###
#############################################

class InotifyBuffer(InotifyBuffer):
    """A wrapper for `Inotify` that holds events for `delay` seconds. During
    this time, IN_MOVED_FROM and IN_MOVED_TO events are paired.
    """


    def __init__(self, path, recursive=False):
        BaseThread.__init__(self)
        self._queue = DelayedQueue(self.delay)
        self._inotify = Inotify(path, recursive)
        self.start()
