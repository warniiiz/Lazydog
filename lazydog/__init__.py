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
:package: lazydog
:synopsis: File system user-level events monitoring.
:author: Clément Warneys <clement.warneys@gmail.com>

This is the main package of the **lazydog** library. It relies on another 
sub-package **revised_watchdog** which is a modified version of **watchdog**
package.

As a summary, **watchdog** is a "*python API and shell utilities to monitor file 
system events*". As such, **watchdog** is monitoring and emitting every tiny 
local event on the file system, which often means 5 or more watchdog events per
user event. For example, when a user is creating a new file, you will get 1 creation
event, multiple modification events (some of them for the content modification, others 
for metadata mosification), and 1 or more modification event for the directory of 
the file.

The goal of **lazydog** is to emit only 1 event per user event. This kind of event 
will sometimes be call **high-level event**, compared to **low-level event**
which are emitted by the **watchdog** API. To do so, **lazydog** is waiting a little 
amount of time in order to correlate different **watchdog** events between them, and to 
aggregate them when related. This mechanism results in some delays between the user action
and the event emission. The total delay depends on the **watchdog** observer class. For 
example, if you use an :class:`InotifyObserver` observer, you only need a 2-seconds delay. But if you use
a more basic observer as the :class:`PollingObserver` observer (which is more compatible between different 
system), then you need a greater delay such as 10-seconds.

The **lazydog** package contains the following modules:

* :py:mod:`~lazydog.lazydog` is a sample module that show how to use the package, \
by logging the high-level events in the console. The main function of this module is  \
called when calling ``$ lazidog`` in the console.
* :py:mod:`~lazydog.handlers` is the main module of the library with the aggregation algorithms. 
* :py:mod:`~lazydog.events` defines the high-level lazydog events, based on the \
low-level watchdog ones, which are now aggregable and also convertible \
to copy or move events.
* :py:mod:`~lazydog.queues` bufferizes lazydog events pending for a possible \
aggregation with other simultaneous events.
* :py:mod:`~lazydog.states` keeps track of the current state of the watched local directory. \
The idea is to save computational time, avoiding recomputing file hashes \
or getting size and time of each watched files (depending on the requested \
method), thus facilitating identification of copy events.
* :py:mod:`~lazydog.dropbox_content_hasher` is the default hash function to get a hash of a file. \
Based on the hash function of the Dropbox API.


lazydog.lazydog
===============

.. automodule:: lazydog.lazydog
   :members:

lazydog.handlers
================

.. automodule:: lazydog.handlers
   :members:

lazydog.events
==============

.. automodule:: lazydog.events
   :members:

lazydog.queues
==============

.. automodule:: lazydog.queues
   :members:

lazydog.states
==============

.. automodule:: lazydog.states
   :members:

lazydog.dropbox_content_hasher
==============================

.. automodule:: lazydog.dropbox_content_hasher
   :members:

"""

__version__ = '0.1.1'

