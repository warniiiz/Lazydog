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
:module: lazydog.handlers
:synopsis: Main module of lazydog including the aggregation logics.
:author: Clément Warneys <clement.warneys@gmail.com>

"""


import os
import time
import datetime
import threading

from lazydog.states import LocalState
from lazydog.events import LazydogEvent
from lazydog.queues import DatedlocaleventQueue

from lazydog.revised_watchdog.observers.inotify import InotifyEmitter, InotifyObserver
from watchdog.observers.polling import PollingObserver




class HighlevelEventHandler(threading.Thread):
    """
    Post-treats the low level events to suggest only high-level ones. 

    To do so, a high-level handler needs a :py:class:`~lazydog.queues.DatedlocaleventQueue`
    (an event queue containing the last lazydog events and inherited from 
    :py:class:`~revised_watchdog.events.FileSystemEventHandler` so it is compatible
    with watchdog observers), that is already populated by a low-level watchdog observer, 
    for example :py:class:`~revised_watchdog.observers.inotify.InotifyObserver`, that retrieves 
    the low-level file-system events.

    The simplest way to instanciate :py:class:`~lazydog.handlers.HighlevelEventHandler`
    is to use the :py:meth:`get_instance` method. In this case, you only need to specify the 
    directory to watch ``watched_dir``. Two other optional parameters ``hashing_function``
    and ``custom_intializing_values`` respectively allow to use custom hashing function 
    (which will be use to compute the hashs of each file, in order to correlate copy events)
    and to accelerate the initialization phase (by providing already computed hash values of the 
    current files in the watched directory, thus avoiding to compute them at the start). Please see 
    the related methods documentation for more information.

    This class inherits from :py:class:`threading.Thread` so it works autonomously. It can be started 
    :py:meth:`start` method (from `Thread` module, and a stopping order can be send with :py:meth:`stop` 
    inner method.


    :param lowlevel_event_queue:
        An event queue containing the last lazydog events. Note that the provided queue
        shall be already associated with a low-level watchdog observer that retrieves
        the low-level file-system events (in order to fill the queue).
    :type lowlevel_event_queue:
        :py:class:`~lazydog.queues.DatedlocaleventQueue`
    :param local_states:
        The reference state of the local files in the watched directory. This state will be 
        dynamically updated by the handler, depending on the low-level events. This state 
        contains also the path of the watched directory.
    :type local_states:
        :py:class:`~lazydog.states.LocalState`
    :returns: 
        A non-running high-level lazydog events handler.
    :rtype: 
        :py:class:`~lazydog.handlers.HighlevelEventHandler`
    """

    POSTTREATMENT_TIME_LIMIT = datetime.timedelta(seconds=2)
    """
    If neither new low-level events nor high-level post-treatments appends
    during this 2-seconds delay, the current events in the queue are ready to be
    emitted the listener, when using :py:meth:`get_available_events` method.
    """

    CREATE_EVENT_TIME_LIMIT_FOR_EMPTY_FILES = datetime.timedelta(minutes=15) # older behaviour...
    CREATE_EVENT_TIME_LIMIT_FOR_EMPTY_FILES = datetime.timedelta(seconds=2)
    """
    *Deprecated*. At the beginning of the project, empty file creation was more delayed before 
    the handler emits them. Because empty file are often created and then 
    rapidly renamed and modified... The idea was to limit the number of high-level
    events that were being sent. But this specific behaviour could generate unwanted 
    problems for the third-application using this library.
    """
    
    @classmethod
    def get_instance(cls, watched_dir:str, hashing_function=None, custom_intializing_values=None):
        """
        This method provides you with the  simplest way to instanciate 
        :py:class:`~lazydog.handlers.HighlevelEventHandler`. You only need to specify the 
        directory to watch ``watched_dir``. Two other optional parameters ``hashing_function``
        and ``custom_intializing_values`` respectively allow to use custom hashing function 
        (which will be use to compute the hashs of each file, in order to correlate copy events)
        and to accelerate the initialization phase (by providing already computed hash values of the 
        current files in the watched directory, thus avoiding to compute them at the start). 

        :param watched_dir:
            The path you want to watch.
        :type watched_dir:
            str
        :param hashing_function:
            Custom hashing function that will be use to compute the hashs of each file, 
            in order the handler is able to correlate copy events. The function shall be defined  
            with the same parameters and retrun format than 
            :py:func:`~lazydog.dropbox_content_hasher.default_hash_function`.
        :type hashing_function:
            function
        :param custom_intializing_values:
            Providing custom intializing values accelerate the initialization phase 
            by providing already computed hash values of all the files currently in 
            the watched directory. The provided dictionary shall cover all the local
            files and directory because hash values will not be computed for 
            missing files. If some reference were missing in the provided dictionary, 
            they can be completed later using :py:meth:`save_locals` 
            method. For more information about the structure of this parameter, 
            please see the documentation of :py:class:`~lazydog.states.LocalState`.
        :type custom_intializing_values:
            :py:class:`~lazydog.states.LocalState`
        :returns: 
            An already running high-level lazydog events handler.
        :rtype: 
            :py:class:`~lazydog.handlers.HighlevelEventHandler`
        """
        local_files = LocalState(watched_dir, hashing_function, custom_intializing_values)
        
        dated_event_queue = DatedlocaleventQueue(local_files)
        observer = InotifyObserver() # generate_full_events=False) # With reviewed Inotify 
        observer.schedule(dated_event_queue, watched_dir, recursive=True)
        observer.name = 'Local Inotify observer'
        observer.start()
        
        return cls(dated_event_queue, local_files)
    
    
    def __init__(self, lowlevel_event_queue:DatedlocaleventQueue, local_states:LocalState):
        self.events_list = []
        self.events_list.clear()
        self.lowlevel_event_queue = lowlevel_event_queue
        self.local_states = local_states
        super(HighlevelEventHandler, self).__init__()
        self._update_posttreatment_cursor()
        self._copied_dir_list = {}
        self._copied_dir_list.clear()
        
        self._block_releases_while_hashing = False
        self._stop_handler = threading.Event()
        self.name = 'Highlevel local event handler'


    def stop(self):
        """
        Set the :py:class:`threading.Event` so that the handler thread
        knows that it has to stop running. Call this method when you want 
        to preperly stop the handler. The handler will then stop a few seconds 
        afterwards.
        """
        self._stop_handler.set()
    
    def _update_posttreatment_cursor(self):
        """
        Private method updating the last time a post-treatment occurs for
        the watched directory. This last time cursor, combined with the 
        :py:attr:`POSTTREATMENT_TIME_LIMIT` class attribute, defines whether
        current queued events are ready to be emitted by the handler or not.
        """
        self._latest_highlevel_posttreatment = datetime.datetime.now()

    @staticmethod
    def _len_list_dir(absolute_path:str) -> int:
        """
        Private method counting the number of files and directories contained
        under the ``absolute_path`` path. Returns ``None`` if path does not exist.
        """
        try:
            return len(os.listdir(absolute_path))
        except:
            return None
    
    @staticmethod
    def _check_empty_src_dest_folder(abs_src_path:str, abs_dest_path:str) -> bool:
        """
        Private method checking that ``abs_src_path`` and ``abs_dest_path`` 
        paths contains the same files and the same directories (recursively). 
        The relative paths (including the file or dir basename) have to be 
        the same.
        """
        for root, dirs, files in os.walk(abs_src_path):  
            for i in dirs:
                abs_dest_path_i = os.path.join(abs_dest_path, i)
                if not os.path.exists(abs_dest_path_i):
                    return False
            for i in files:
                abs_dest_path_i = os.path.join(abs_dest_path, i)
                if not os.path.exists(abs_dest_path_i):
                    return False
        for root, dirs, files in os.walk(abs_dest_path):  
            for i in dirs:
                abs_src_path_i = os.path.join(abs_src_path, i)
                if not os.path.exists(abs_src_path_i):
                    return False
            for i in files:
                abs_src_path_i = os.path.join(abs_src_path, i)
                if not os.path.exists(abs_src_path_i):
                    return False
        return True
                
    
    def _posttreat_copied_folder(self):
        """
        Private helper method identifying possible matches between a list of copied events
        (from ``self.events_list``)`and the already-existing folders in the watched directory.
        If one of the already-existing folder contains a list of file and folder, each of them 
        corresponding to a related copied event, this helper removes every corresponding 
        copied events from the queue, and then creates a new copied event 
        :py:attr:`~lazydog.events.LazydogEvent.EVENT_TYPE_COPIED` related to their 
        common parent folder. As for a simple file copied event, multiple sources can be
        append to the new copied event, in order to remind all the potential source
        folder (this is sometimes useful if we need to recursively do the same post-treatment with
        the parent folder).
        """
        if len(self._copied_dir_list) == 0:
            return
        
        # Cleaning...
        for k, t in self._copied_dir_list.items():
            if datetime.datetime.now() - t > datetime.timedelta(minutes=20):
                self._copied_dir_list.pop(k)
        
        to_paths = {}
        
        # General idea is to identify if all the file from a same source folder have 
        # each of them generated copied_events to the same destination folder
         
        # For each parent_to_path, get the possible parent_src_paths
        for e in [x for x in self.events_list if x.is_copied_event() and x.parent_rp in self._copied_dir_list]:
            if not e.parent_rp in to_paths:
                to_paths[e.parent_rp] = {}
            for sp, parent_sp in e.possible_src_paths.items():
                if to_paths[e.parent_rp].get(parent_sp) is None:
                    to_paths[e.parent_rp][parent_sp] = []
                to_paths[e.parent_rp][parent_sp].append(e)
        
        # Then, we add potential empty folders that have been copied but not transformed into copied event (because no file inside)
        for e in [x for x in self.events_list if x.is_created_event() and x.parent_rp in to_paths]:
            if e.is_empty():
                for parent_sp in to_paths[e.parent_rp]:
                    absolute_source_path = self.local_states.absolute_local_path(os.path.join(parent_sp, e.basename))
                    # if directory does not exist, count_files_in returns None
                    if e.is_directory() and LazydogEvent.count_files_in(absolute_source_path) == 0:
                        if HighlevelEventHandler._check_empty_src_dest_folder(absolute_source_path, e.absolute_ref_path):
                            to_paths[e.parent_rp][parent_sp].append(e)
                    # if file does not exist, get_file_size returns None
                    elif not e.is_directory() and LazydogEvent.get_file_size(absolute_source_path) == 0:
                        to_paths[e.parent_rp][parent_sp].append(e)
        
        # Then, we check if any created folder event corresponds to the parent_to_paths
        recurse = False
        for tp in to_paths:
            dir_created_event = next(iter([x for x in self.events_list if x.is_dir_created_event() and x.ref_path == tp]), None)
            #for sp in to_paths[tp]:
            potential_sp = [x for x in to_paths[tp] 
                 if (len(to_paths[tp][x]) == HighlevelEventHandler._len_list_dir(self.local_states.absolute_local_path(x)) and 
                     len(to_paths[tp][x]) == HighlevelEventHandler._len_list_dir(self.local_states.absolute_local_path(tp)))]
            # TODO : possibility to simplify again because this loop seems not needed...
            for sp in potential_sp:
                #logging.debug("Posttreating copied folder: %s - %s - %s", len(to_paths[tp][sp]), HighlevelEventHandler._len_list_dir(sp), HighlevelEventHandler._len_list_dir(tp))
                #if (len(to_paths[tp][sp]) == HighlevelEventHandler._len_list_dir(self.local_states.absolute_local_path(sp)) and 
                #    len(to_paths[tp][sp]) == HighlevelEventHandler._len_list_dir(self.local_states.absolute_local_path(tp))):
                    # merging the copied files under a copied folder
                    # only the first iteration will remain a created_event, following one will have been transformed into copied event
                if dir_created_event is not None:
                    # once transformed into copied event, the following will not be applied
                    if dir_created_event.is_created_event():
                        # at the end we will posttreat the parent folder
                        recurse = True
                        self._copied_dir_list[os.path.dirname(tp)] = datetime.datetime.now()
                        # for now remove any related event
                        for e in to_paths[tp][sp]:
                            # if still not transformed : means it is empty file or folder
                            if e.is_created_event():
                                # for all empty subfolders and files, update e, then remove them:
                                for ee in [x for x in self.events_list if x.is_created_event() and x.comes_after(e) and x.is_empty()]:
                                    ee.update_main_event(e)
                                    self._update_local_state(ee)
                                    self.events_list.remove(ee)
                            # add source (and transforms) 
                            e.add_source_paths_and_transforms_into_copied_event(os.path.join(sp, e.basename))
                            # update main and remove
                            if e in self.events_list:
                                e.update_main_event(dir_created_event)
                                self._update_local_state(e)
                                self.events_list.remove(e)
                        # remove folder from potentially copied... since it will be effectively transformed
                        self._copied_dir_list.pop(tp)
                        self._update_local_state(dir_created_event)
                    # transform main event
                    # TODO : the following seems not well... we are using potential_sp (instead of sp) inside a loop above potential_sp....
                    dir_created_event.add_source_paths_and_transforms_into_copied_event(potential_sp)
                    self._update_posttreatment_cursor()
                    
        # if any event has been transformed to copied event:
        if recurse:
            self._posttreat_copied_folder()
        
        
    # IMPORTANT TODO : to be protected against simultaneous get_available_events modifications...              
    def posttreat_lowlevel_event(self, local_event:LazydogEvent):
        """
        Executes the main logics of the High-level Handler. These are all the aggregation 
        rules, depending on the order of arrival of the low-level event, how to identify 
        the relation between them and when to decide to aggregate them, or to transform 
        them into a high-level `Copied` or a `Moved` event.

        Please read directly the commented code for more information about these rules. Here is 
        a summary of the execution:

        * Aggregation rules:

            * Using an :py:class:`~revised_watchdog.observers.inotify.InotifyObserver`,  \
            `Deleted` events arrive backward, which means that if you delete a directory \
            with some files inside, you will get first a `Deleted` event for the inside  \
            files then another one for their parent directory. So if we find a `Deleted` \
            event for a directory, we remove every children `Deleted` events previously  \
            queued. Note that if a `Deleted` event arrives after a `Modified` event or   \
            anything else for the same file or folder, then we just remove (or adapt)    \
            the previous related events.
            * Using an :py:class:`~revised_watchdog.observers.inotify.InotifyObserver`,  \
            `Moved` events are the most simple to post-treat: if you move a folder with  \
            sub-files, you only get one low-level event. So nothing to aggregate here... \
            The only thing is when a `Moved` event is rapidly succeding a `Created` event \
            (or anything else), then you have to adapt the original event in the queue.
            * `Modified` events are easy to aggregate to other ones. They are often      \
            meaningless, since a low-level `Whatever` event often comes with one or more \
            `Modified` events, so we often just ignore these `Modified` events... Note   \
            that when you copy or create a large file, you will get multiple low-level   \
            `Modified` events per seconds that you will have to ignore (since you want   \
            to do a high-level lazy observer).

        * If the new event is not related to any other already-listed events, thent it is \
        added to the queue as a new high-level event.
        * Transformation of `Created` events into `Copied` ones, if one or more potentiel \
        sources have been found for the `Created` event. The identification of the sources \
        is based on the :py:attr:`~lazydog.events.LazydogEvent.file_size`, the             \
        :py:attr:`~lazydog.events.LazydogEvent.file_mtime` and the                         \
        :py:attr:`~lazydog.events.LazydogEvent.file_hash` attributes. The first step concerns \
        only the files. Then at the end, if any event has been transformed into a `Copied` \
        one, the :py:meth:`_posttreat_copied_folder` helper method is called.

        """
        
        # posttreat file copy is done at the end of this method
        copy_event_to_posttreat = None
        
        # created events
        if local_event.is_created_event():
            copy_event_to_posttreat = local_event
                       
        # deleted events arrive backward
        if local_event.is_deleted_event():
            for e in [x for x in reversed(self.events_list) if x.is_deleted_event()]:
                if local_event.comes_before(e):
                    e.update_main_event(local_event)
                    self.events_list.remove(e)
                    local_event.is_related = False
                    self._update_posttreatment_cursor()
                elif local_event.has_same_path_than(e):
                    local_event.update_main_event(e)
                    self._update_posttreatment_cursor()
            for e in [x for x in reversed(self.events_list) if x.has_same_path_than(local_event)]:
                if e.is_created_event() or e.is_copied_event() or e.is_modified_event():
                    e.update_main_event(local_event)
                    self.events_list.remove(e)
                    local_event.is_related = False
                    local_event.is_irrelevant = True
                    self._update_posttreatment_cursor()
                elif e.is_moved_event():
                    e.update_main_event(local_event)
                    local_event.path = e.path
                    local_event.is_related = False
                    self.events_list.remove(e)
                    self._update_posttreatment_cursor()
                    
        # moving event can also arrive just after newly created or copied or moved event
        if local_event.is_moved_event():
            self._update_local_state(local_event)
            for e in [x for x in self.events_list if (x.is_created_event() or x.is_copied_event() or x.is_moved_event())]:
                if local_event.has_same_src_path_than(e):
                    local_event.update_main_event(e)
                    e.ref_path = local_event.to_path
                elif local_event.comes_after(e) and e.is_moved_event():
                    local_event.update_main_event(e)
                
        
        # modified event
        if local_event.is_modified_event():
            # we do not need notification for modified folder
            if local_event.is_directory():
                local_event.is_related = True
            else:
                for e in [x for x in reversed(self.events_list)]:
                    # modified file event related to deleted, moved or copied event
                    if e.is_deleted_event() or e.is_moved_event() or e.is_copied_event():
                        if local_event.same_or_comes_after(e):
                            local_event.update_main_event(e)
                    # modified file event related to creted or modified event
                    elif e.is_created_event() or e.is_modified_event():
                        if local_event.has_same_path_than(e):
                            local_event.update_main_event(e)
                            # in case of lastly created event, we re-check for potential copied event
                            if e.is_created_event() and local_event.is_meta_file_modified_event():
                                copy_event_to_posttreat = e
        
        # else... if event has no relation with previous ones, we add it in the list of potential high level event
        if not local_event.is_related:
            self.events_list.append(local_event)
                
        # then posttreat file copied event
        if copy_event_to_posttreat is not None:
            if copy_event_to_posttreat.file_size is not None:
                if copy_event_to_posttreat.file_size > 0:
                    if len(self.local_states.get_files_by_sizetime_key((copy_event_to_posttreat.file_size, copy_event_to_posttreat.file_mtime))) > 0:
                        self._block_releases_while_hashing = True
                        # the following command also transforms the created event into a copied one (if any src paths found)...
                        # File Hash is computed.
                        copy_event_to_posttreat.add_source_paths_and_transforms_into_copied_event(self.local_states.get_files_by_hash_key(copy_event_to_posttreat.file_hash))
                        if copy_event_to_posttreat.is_copied_event():
                            self._copied_dir_list[os.path.dirname(copy_event_to_posttreat.to_path)] = datetime.datetime.now()
                        self._update_local_state(copy_event_to_posttreat)
                        self._update_posttreatment_cursor()
                        self._block_releases_while_hashing = False
            
        # then posttreat dir copied event
        self._posttreat_copied_folder()
        
        # posttreatment cursor temporizes the delivrances of high level event to observers
        self._update_posttreatment_cursor()
            
                        
    def _update_local_state(self, event:LazydogEvent):
        if event.is_deleted_event():
            self.local_states.delete(event.ref_path)
        elif event.is_moved_event():
            self.local_states.move(event.path, event.to_path)
        else:
            # File Hash is computed if needed
            self.save_locals(event.ref_path, [event.file_hash, event.file_size, event.file_mtime])
        
                           
    def save_locals(self, file_path, file_references):
        """
        Directly modifies the local state dictionary associated to the handler, by providing 
        new reference for a file or folder. This method should be use in combination of 
        the optional parameter ``custom_intializing_values`` when calling :py:meth:`get_instance`. 
        In the case you rapidly initialize the handler with some files values, and then 
        you see that some of these values are not good or that some files are missing, 
        you can adjust by passing new values or new files with this method. The data structure 
        is the almost the same. 

        :param file_path:
            The relative path of the file or folder you want to add.
        :type file_path:
            str
        :param file_references:
            A list of 3 values in the following order: ``file_hash``, ``file_size``, ``file_mtime``
        :type file_references:
            list
        :returns: 
            ``None``
        """
        self.local_states.save(file_path, file_references[0], file_references[1], file_references[2])
        
    # IMPORTANT TODO : to be protected against simultaneous posttreat_lowlevel_event modifications... 
    def get_available_events(self) -> list:
        """
        Returns a list of high-level post-treated and ready events. Ready in the sense
        that the :py:attr:`POSTTREATMENT_TIME_LIMIT` has been reached without any new
        low-level events coming... 
        
        .. note: If you instanciated a new Handler using the :py:meth:`get_instance`
            method, then you got an already-running handler. No need to call the 
            :py:meth:`start` method again.

        """
        ready_events = []
        if not self._block_releases_while_hashing and LazydogEvent.datetime_difference_from_now(self._latest_highlevel_posttreatment) > HighlevelEventHandler.POSTTREATMENT_TIME_LIMIT:

            if all(x.idle_time() > HighlevelEventHandler.POSTTREATMENT_TIME_LIMIT for x in self.events_list):
                
                for e in self.events_list.copy():
                    if e.is_file_created_event() and e.is_empty() and e.idle_time() <= HighlevelEventHandler.CREATE_EVENT_TIME_LIMIT_FOR_EMPTY_FILES:
                        continue
                    
                    if e.is_irrelevant:
                        self.events_list.remove(e)
                        continue

                    self.events_list.remove(e)
                    ready_events.append(e)
                    
                # clean erratic modified events (when receiving a `Modified` event
                # but there is no real modification...). We can not check this kind 
                # of problem in the posttreat_lowlevel_event method, because it needs 
                # to compute the file hash (and we could receive alot of `Modified` 
                # event in the first place, that will be merged, so treating this 
                # here allow to compute the hash only once).
                for e in ready_events.copy():
                    if e.is_modified_event():
                        # File Hash is computed.
                        if ( e.file_hash == self.local_states.get_hash(e.path, compute_if_none=False) and
                            (e.file_size, e.file_mtime) == self.local_states.get_sizetime(e.path, compute_if_none=False)):
                            ready_events.remove(e)
                        else:
                            self._update_local_state(e)
                    elif e.is_created_event() or e.is_deleted_event():
                        self._update_local_state(e)
                            
        return ready_events
    
    def run(self):
        """
        Threading module method, that is executed when calling :py:meth:`start` method.
        The thread is running in a loop until you call the :py:meth:`stop` method. Until 
        then, it just check regularly if there is any new queued events emitted by the watchdog 
        oberver. If any, it post-treats it calling the  
        :py:meth:`posttreat_lowlevel_event` method.
        
        .. note: If you instanciated a new Handler using the :py:meth:`get_instance`
            method, then you got an already-running handler. No need to call the 
            :py:meth:`start` method again.

        """
        while not self._stop_handler.is_set():
            
            time.sleep(0.2) # to give some time for hashing from other threads...
            
            while not self.lowlevel_event_queue.is_empty():                

                # Post-treatment of the next lowlevel event
                lowlevel_event = self.lowlevel_event_queue.next()
                # print('+++ INCOMING LOW LEVEL EVENT +++')
                # for e in self.events_list:
                #     print('+ ' + str(e))
                # print(lowlevel_event)
                
                #logging.debug('+++' + str(lowlevel_event))
                self.posttreat_lowlevel_event(lowlevel_event)
                
