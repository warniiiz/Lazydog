#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on 17 janv. 2018
 
@author: Warniiiz
'''

import time
import datetime
import logging
import threading
import os
#from watchdog.observers import Observer
#from watchdog.observers.inotify import InotifyObserver
#from watchdog.events import LoggingEventHandler
#from watchdog.events import FileSystemEventHandler
#from watchdog.events import FileSystemEvent

from hashers.dropbox_content_hasher import DropboxContentHasher


#===============================================================================
# from watchdog_pipoevents import FileSystemEvent
# from watchdog_pipoevents import FileSystemEventHandler
#===============================================================================

from revised_watchdog.events import FileSystemEventHandler, FileSystemEvent
from revised_watchdog.observers.inotify import InotifyObserver



from watchdog.observers.polling import (
    PollingObserver
    )




__version__ = "0.1"


### watchdog.observers.pipoinotify_buffer -> Nothing to change










#===============================================================================
# Listen uses inotify by default on Linux to monitor directories for changes. It's not uncommon to encounter a system limit on the number of files you can monitor. For example, Ubuntu Lucid's (64bit) inotify limit is set to 8192.
# 
# You can get your current inotify file watch limit by executing:
# 
# $ cat /proc/sys/fs/inotify/max_user_watches
# When this limit is not enough to monitor all files inside a directory, the limit must be increased for Listen to work properly.
# 
# You can set a new limit temporary with:
# 
# $ sudo sysctl fs.inotify.max_user_watches=524288
# $ sudo sysctl -p
# If you like to make your limit permanent, use:
# 
# $ echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
# $ sudo sysctl -p
#===============================================================================




#===============================================================================
# SYNC_FOLDER = '/media/maxtor/media/Dropbox/'
# ABSOLUTE_ROOT_FOLDER = '/media/maxtor/media/Dropbox/'
#===============================================================================




class LocalState():
    
    # Method to get the MD5 Hash of the file with the supplied file name.
    @staticmethod
    def _default_hashing_function(absolute_path:str):
        _hash = None
        try:
            # Directory
            if os.path.isdir(absolute_path):
                _hash = 'DIR'
            # File
            else:
                # Open the file and hash it using Dropbox python helpers
                hasher = DropboxContentHasher()
                if os.path.exists(absolute_path):
                    duration = time.perf_counter()
                    with open(absolute_path, 'rb') as f:
                        while True:
                            chunk = f.read(1024)  # or whatever chunk size you want
                            if len(chunk) == 0:
                                break
                            hasher.update(chunk)
                    _hash = hasher.hexdigest()
                    logging.debug("Successfully computed hash of file (%.3f): %s" % (time.perf_counter() - duration, absolute_path))
        except:
            logging.exception("Error while hashing file %s" % absolute_path)
        return _hash
    
    def __init__(self, absolute_root_folder, hash_function=None, custom_intializing_values:dict=None):
        
        # keep absolute root folder
        self.absolute_root_folder = absolute_root_folder
        
        # keep hash function
        self.hash_function = hash_function if hash_function is not None else self._default_hashing_function
        
        # self.hashes is a dictionary with key=file_path, value=file_hash
        self.hashes = {}
        self.hashes.clear()
        
        # self.hash_paths is a dictionary with key=file_hash, values=list(file_path)
        self.hash_paths = {}
        self.hash_paths.clear()
        
        # self.sizetimes is a dictionary with key=path, value=tuple(file_size, file_mtime)
        self.sizetimes = {}
        self.sizetimes.clear()
        
        # self.sizetime_paths is a dictionary with key=file_hash, values=list(file_path)
        self.sizetime_paths = {}
        self.sizetime_paths.clear()
        
        # Initializing values
        if custom_intializing_values is not None:
            # custom_intializing_values should be a dict with:
            # - key=file_path
            # - value=list(file_hash, file_size, file_time)
            for k, v in custom_intializing_values.items():
                if os.path.exists(self.absolute_local_path(k)):
                    self.save(k, v[0], v[1], v[2])
        else:
            # Default initializing
            for root, dirs, files in os.walk(self.absolute_root_folder):  
                for i in dirs + files:
                    relative_path = self.relative_local_path(os.path.join(root, i))
                    self.get_hash(relative_path)
                    self.get_sizetime(relative_path)
        
    

    
    def absolute_local_path(self, relative_path:str) -> str:
        if relative_path.startswith('/'):
            relative_path = relative_path[1:]
        return os.path.join(self.absolute_root_folder, relative_path)
    
    def relative_local_path(self, absolute_path:str) -> str:
        absolute_path = os.path.normpath(absolute_path)
        return '/' + os.path.relpath(absolute_path, self.absolute_root_folder)

    def get_hash(self, key:str, create:bool=True) -> str:
        if key not in self.hashes and create:
            self.hashes[key] = self.hash_function(self.absolute_local_path(key))
            if self.hash_paths.get(self.hashes[key]) is None:
                self.hash_paths[self.hashes[key]] = set()
            self.hash_paths[self.hashes[key]].update([key]) 
        return self.hashes.get(key, None)
        
    def get_files_by_hash_key(self, hash_key:str) -> set:
        return self.hash_paths.get(hash_key, set())

    def get_sizetime(self, key:str, create:bool=True):
        if key not in self.sizetimes and create:
            if os.path.isdir(self.absolute_local_path(key)):
                self.sizetimes[key] = ('DIR', 'DIR')
            else:
                self.sizetimes[key] = (os.path.getsize(self.absolute_local_path(key)), os.path.getmtime(self.absolute_local_path(key)))
            if self.sizetime_paths.get(self.sizetimes[key]) is None:
                self.sizetime_paths[self.sizetimes[key]] = set()
            self.sizetime_paths[self.sizetimes[key]].update([key]) 
        return self.sizetimes.get(key, None)
        
    def get_files_by_sizetime_key(self, sizetime_key) -> set:
        return self.sizetime_paths.get(sizetime_key, set())
    
    def save(self, key:str, file_hash, file_size, file_mtime):
        if os.path.isdir(self.absolute_local_path(key)):
            file_hash = 'DIR'
            file_size = 'DIR'
            file_mtime = 'DIR'
        self.hashes[key] = file_hash
        if self.hash_paths.get(self.hashes[key]) is None:
            self.hash_paths[self.hashes[key]] = set()
        self.hash_paths[self.hashes[key]].update([key]) 
        self.sizetimes[key] = (file_size, file_mtime)
        if self.sizetime_paths.get(self.sizetimes[key]) is None:
            self.sizetime_paths[self.sizetimes[key]] = set()
        self.sizetime_paths[self.sizetimes[key]].update([key])
    
    # Delete key recursively
    def delete(self, delete_key:str):
        dk = delete_key + '/'
        for key in [x for x in self.hashes.copy() if x.startswith(dk)]:
            self._delete_hash(key)
        if delete_key in self.hashes:
            self._delete_hash(delete_key)
        for key in [x for x in self.sizetimes.copy() if x.startswith(dk)]:
            self._delete_sizetime(key)
        if delete_key in self.sizetimes:
            self._delete_sizetime(delete_key)
    
    def _delete_hash(self, key:str):
        if self.hash_paths.get(self.hashes[key]) is not None:
            self.hash_paths[self.hashes[key]].discard(key) 
        self.hashes.pop(key)
        
    def _delete_sizetime(self, key:str):
        if self.sizetime_paths.get(self.sizetimes[key], None) is not None:
            self.sizetime_paths[self.sizetimes[key]].discard(key) 
        self.sizetimes.pop(key) 
        
    # Move key recursively
    def move(self, src_key:str, dst_key:str):
        mk = src_key + '/'
        for key in [x for x in self.hashes.copy() if x.startswith(mk)]:
            self._move_hash(key, key.replace(src_key, dst_key, 1))
        if src_key in self.hashes:
            self._move_hash(src_key, dst_key)
        for key in [x for x in self.sizetimes.copy() if x.startswith(mk)]:
            self._move_sizetime(key, key.replace(src_key, dst_key, 1))
        if src_key in self.sizetimes:
            self._move_sizetime(src_key, dst_key)
        
    def _move_hash(self, src_key:str, dst_key:str):
        if self.hash_paths.get(self.hashes[src_key]) is not None:
            self.hash_paths[self.hashes[src_key]].discard(src_key) 
            self.hash_paths[self.hashes[src_key]].update([dst_key]) 
        self.hashes[dst_key] = self.hashes.pop(src_key)
        
    def _move_sizetime(self, src_key:str, dst_key:str):
        if self.sizetime_paths.get(self.sizetimes[src_key]) is not None:
            self.sizetime_paths[self.sizetimes[src_key]].discard(src_key) 
            self.sizetime_paths[self.sizetimes[src_key]].update([dst_key]) 
        self.sizetimes[dst_key] = self.sizetimes.pop(src_key)
            
    


class SyncDatedlocaleventQueue(FileSystemEventHandler):
    """Accumulate all the captured events, and date them."""

    def __init__(self, local_states:LocalState):
        self.events_list = []
        self.events_list.clear()
        self.local_states = local_states
        super(SyncDatedlocaleventQueue, self).__init__()

    def on_any_event(self, event):
        """Catch-all event handler.

        :param event:
            The event object representing the file system event.
        :type event:
            :class:`FileSystemEvent`
        """
        super(SyncDatedlocaleventQueue, self).on_any_event(event)
        self.events_list.append(PipoEvent(event, self.local_states))

    def next(self):
        return self.events_list.pop(0) if not self.is_empty() else None
            
    def size(self):
        return len(self.events_list)

    def is_empty(self):
        return self.size() == 0
    





class PipoEvent():

    EVENT_TYPE_COPIED = 'copied'
    EVENT_TYPE_CREATED = 'created'
    EVENT_TYPE_DELETED = 'deleted'
    EVENT_TYPE_MOVED = 'moved'
    EVENT_TYPE_C_MODIFIED = 'modified' # content modification
    EVENT_TYPE_M_MODIFIED = 'metadata' # metadata modification
    
                
    # class datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
    COPY_AGGREGATION_TIME_LIMIT = datetime.timedelta(minutes=20)
    CREATE_AGGREGATION_TIME_LIMIT = datetime.timedelta(minutes=20)
    DELETE_AGGREGATION_TIME_LIMIT = datetime.timedelta(minutes=20)
    MODIFY_AGGREGATION_TIME_LIMIT = datetime.timedelta(minutes=20)
    MOVE_AGGREGATION_TIME_LIMIT = datetime.timedelta(minutes=20)
    
    AGGREGATION_TIME_LIMIT = {
        EVENT_TYPE_COPIED: COPY_AGGREGATION_TIME_LIMIT,
        EVENT_TYPE_CREATED: CREATE_AGGREGATION_TIME_LIMIT,
        EVENT_TYPE_DELETED: DELETE_AGGREGATION_TIME_LIMIT,
        EVENT_TYPE_C_MODIFIED: MODIFY_AGGREGATION_TIME_LIMIT,
        EVENT_TYPE_M_MODIFIED: MODIFY_AGGREGATION_TIME_LIMIT,
        EVENT_TYPE_MOVED: MOVE_AGGREGATION_TIME_LIMIT,
        }
    
        
    
    
    def __init__(self, event:FileSystemEvent, local_states:LocalState):
        # Dating now
        self.event_date = datetime.datetime.now()
        
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
        
        #logging.debug('---' + str(self))
        
        
    def __str__(self):
        if self.is_moved_event() or self.is_copied_event():
            return ('logged[' + str(self.event_date) + '] ' +
                    self.type + ": '" + self.path + "' " +
                    "to '" + self.to_path + "' " + 
                    'mtime[' + str(self.file_mtime) + '] ' +
                    'size[' + str(self.file_size) + '] ' +
                    'inode[' + str(self.file_inode) + '] ')
        else:
            return ('logged[' + str(self.event_date) + '] ' +
                    self.type + ": '" + self.path +  "' " + 
                    'mtime[' + str(self.file_mtime) + '] ' +
                    'size[' + str(self.file_size) + '] ' +
                    'inode[' + str(self.file_inode) + '] ')
            
    
    def _correct_path_value(self, value:str) -> str:
        return '/' if value == '/.' else value
    
    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, value:str):
        self._path = self._correct_path_value(value)
        self._reset_ref_paths()
        
    @property
    def to_path(self) -> str:
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
        if self.ref_path == '/':
            return None
        else:
            return os.path.dirname(self.ref_path)
        
    # Filename or dirname
    @property
    def basename(self) -> str:
        return os.path.basename(self.ref_path)
    
    @property
    def absolute_ref_path(self) -> str:
        if self._absolute_ref_path is None:
            self._absolute_ref_path = self.local_states.absolute_local_path(self.ref_path)
        return self._absolute_ref_path
    
    
    def is_directory(self) -> bool:
        return self.is_dir
    
    # Check if same type (only type, without considering Dir)
    def is_same_type_than(self, event) -> bool:
        return self.type == event.type
    
    def is_moved_event(self) -> bool:
        return self.type == PipoEvent.EVENT_TYPE_MOVED
    
    def is_dir_moved_event(self) -> bool:
        return self.is_moved_event() and self.is_directory()
    
    def is_deleted_event(self) -> bool:
        return self.type == PipoEvent.EVENT_TYPE_DELETED
    
    def is_dir_deleted_event(self) -> bool:
        return self.is_deleted_event() and self.is_directory()
    
    def is_created_event(self) -> bool:
        return self.type == PipoEvent.EVENT_TYPE_CREATED
    
    def is_dir_created_event(self) -> bool:
        return self.is_created_event() and self.is_directory()
    
    def is_file_created_event(self) -> bool:
        return self.is_created_event() and not self.is_directory()
    
    def is_copied_event(self) -> bool:
        return self.type == PipoEvent.EVENT_TYPE_COPIED
    
    def is_modified_event(self) -> bool:
        return self.is_meta_modified_event() or self.is_data_modified_event()
    
    def is_meta_modified_event(self) -> bool:
        return self.type == PipoEvent.EVENT_TYPE_M_MODIFIED
    
    def is_data_modified_event(self) -> bool:
        return self.type == PipoEvent.EVENT_TYPE_C_MODIFIED 
    
    def is_file_modified_event(self) -> bool:
        return self.is_modified_event() and not self.is_directory()
    
    def is_meta_file_modified_event(self) -> bool:
        return self.is_meta_modified_event() and not self.is_directory()
    
    def is_data_file_modified_event(self) -> bool:
        return self.is_data_modified_event() and not self.is_directory()
    
    def is_dir_modified_event(self) -> bool:
        return self.is_modified_event() and self.is_directory()
    
    def has_dest(self) -> bool:
        return self.is_moved_event() or self.is_copied_event()
    
    # Check times
    def is_aggregable_with(self, event) -> bool:
        return True
        #return abs(event.latest_event_date - self.latest_event_date) <= PipoEvent.AGGREGATION_TIME_LIMIT[self.type]
    
    def has_same_mtime_than(self, previous_event) -> bool:
        return self.file_mtime == previous_event.file_mtime
    
    # Check size 
    def has_same_size_than(self, event) -> bool:
        return self.file_size == event.file_size
    
    # Check paths
    def has_same_path_than(self, event) -> bool:
        if self.has_dest() and event.has_dest():
            return self.path == event.path and self.to_path == event.to_path
        else:
            return self.ref_path == event.ref_path
    
    def has_same_src_path_than(self, event) -> bool:
        return self.path == event.ref_path
        
    
    
    @staticmethod
    def p1_comes_after_p2(p1:str, p2:str) -> bool:
        if not p1.endswith('/'):
            p1 = p1 + '/'
        if not p2.endswith('/'):
            p2 = p2 + '/'
        return p1.startswith(p2) and p1 != p2
    
    @staticmethod
    def p1_comes_before_p2(p1:str, p2:str) -> bool:
        return PipoEvent.p1_comes_after_p2(p2, p1)
    
    
    def comes_before(self, event) -> bool:
        return event.comes_after(self)
            
    def same_or_comes_before(self, event) -> bool:
        return self.comes_before(event) or self.has_same_path_than(event)
    
    
        
    
    def comes_after(self, event, complete_check:bool=True) -> bool:
        if complete_check and self.has_dest() and event.has_dest():
            return PipoEvent.p1_comes_after_p2(self.path, event.path) and PipoEvent.p1_comes_after_p2(self.to_path, event.to_path)
        else:
            return PipoEvent.p1_comes_after_p2(self.ref_path, event.ref_path)
        
    def same_or_comes_after(self, event) -> bool:
        return self.comes_after(event) or self.has_same_path_than(event)
                
    
    @staticmethod
    def datetime_difference_from_now(dt:datetime.datetime) -> datetime.datetime:
        return datetime.datetime.now() - dt
    
    def idle_time(self) -> datetime.datetime:
        return PipoEvent.datetime_difference_from_now(self.latest_reworked_date)
                                                      
    @property
    def file_hash(self) -> str:
        if self._file_hash is None:
            if self.is_directory():
                self._file_hash = 'DIR'
            else:
                try:
                    self._file_hash = self.local_states.hash_function(self.absolute_ref_path)
                except:
                    self._file_hash = None
        return self._file_hash
    
              
    # Count all files in subfolder, when file size > 0
    @staticmethod
    def count_files_in(absolute_dir_path:str) -> int:
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
    
    # Count only file (not folder), adding them recursively.
    @property
    def dir_files_qty(self) -> int:
        if self._dir_files_qty is None and self.is_directory():
            self._dir_files_qty = PipoEvent.count_files_in(self.absolute_ref_path)
        return self._dir_files_qty
    
    @staticmethod
    def get_file_size(absolute_file_path:str) -> int:
        try:
            return os.path.getsize(absolute_file_path)
        except:
            return None
        
    
    @property
    def file_size(self) -> int:
        if self._file_size is None and not self.is_directory():
            self._file_size = PipoEvent.get_file_size(self.absolute_ref_path)
        return self._file_size
    
    def is_empty(self) -> bool:
        if self.is_directory():
            return self.dir_files_qty == 0
        else:
            return self.file_size == 0
    
    @property
    def file_mtime(self) -> float:
        if self._file_mtime is None:
            try:
                self._file_mtime = os.path.getmtime(self.absolute_ref_path)
            except:
                self._file_mtime = None
        return self._file_mtime
    
    @property
    def file_inode(self) -> int:
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
        # usual aggregations
        for e in self.related_events:
            main_event.related_events.append(e)
        # re-init
        if self.is_modified_event() and not self.is_directory() and not main_event.is_directory():
            if main_event._file_mtime != self._file_mtime or main_event._file_size != self._file_size or main_event._file_mtime != self._file_mtime:
                main_event._file_inode = self._file_inode
                main_event._file_mtime = self._file_mtime
                main_event._file_size = self._file_size
                main_event._file_hash = self._file_hash # which means hash will be recomputed...
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
        # Re-assignment
        #self = main_event
    
    def related_events_includes_inode(self, file_inode:int) -> bool:
        for e in self.related_events:
            if file_inode == e.file_inode:
                return True
        return False
    
    
            
    def add_source_paths_and_transforms_into_copied_event(self, src_paths:set):
        for sp in src_paths:
            if not self.is_copied_event():
                self.type = PipoEvent.EVENT_TYPE_COPIED
                self.to_path = self.path
                self.path = sp
            if os.path.basename(sp) == os.path.basename(self.to_path):
                self.possible_src_paths[sp] = os.path.dirname(sp) if sp != '/' else None
            
            
    def transforms_created_into_moved_event(self, upper_moved_event):
        self.type = PipoEvent.EVENT_TYPE_MOVED
        self.to_path = self.ref_path
        self.path = os.path.join(upper_moved_event.path, self.basename)
        # update for highlevel
        self.update_main_event(upper_moved_event)
        # update timings
        self.latest_reworked_date = datetime.datetime.now()
        
        
        

class HighlevelEventHandler(threading.Thread):
    """Post-treat the low level events to suggest only one high-level ones."""

    POSTTREATMENT_TIME_LIMIT = datetime.timedelta(seconds=2)
    CREATE_EVENT_TIME_LIMIT_FOR_EMPTY_FILES = datetime.timedelta(minutes=15)
    
    #===========================================================================
    # GENERAL_TIME_LIMIT = datetime.timedelta(seconds=60)             # 60 sec
    # DELETE_EVENT_TIME_LIMIT = datetime.timedelta(seconds=2)
    # COPY_EVENT_TIME_LIMIT = datetime.timedelta(seconds=2)    
    # CREATE_EVENT_TIME_LIMIT = datetime.timedelta(seconds=2)
    # CREATE_EVENT_TIME_LIMIT_FOR_EMPTY_FILES = datetime.timedelta(minutes=15)
    # MOVE_EVENT_TIME_LIMIT = datetime.timedelta(seconds=2)
    # MOVE_EVENT_TIME_LIMIT_FOR_EMPTY_FILES = datetime.timedelta(minutes=1)
    # MODIFY_EVENT_TIME_LIMIT = datetime.timedelta(seconds=2)       
    #===========================================================================
    
    @classmethod
    def get_instance(cls, watched_dir:str, hashing_function=None, custom_intializing_values=None):
        local_files = LocalState(watched_dir, hashing_function, custom_intializing_values)
        
        dated_event_queue = SyncDatedlocaleventQueue(local_files)
        observer = InotifyObserver() # generate_full_events=False) # With reviewed Inotify 
        observer.schedule(dated_event_queue, watched_dir, recursive=True)
        observer.name = 'Local Inotify observer'
        observer.start()
        
        return cls(dated_event_queue, local_files)
    
    
    def __init__(self, lowlevel_event_queue:SyncDatedlocaleventQueue, local_states:LocalState):
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
        self._stop_handler.set()
    
    def size(self):
        return len(self.queue)

    def is_empty(self):
        return self.size() == 0
    
    def _update_posttreatment_cursor(self):
        self._latest_highlevel_posttreatment = datetime.datetime.now()

        
    
    # check equality between source and destination for empty folder (= contains only sub-folder or null-size file) 
    @staticmethod
    def _len_list_dir(absolute_path:str) -> int:
        try:
            return len(os.listdir(absolute_path))
        except:
            return None
    
    # check equality between source and destination for empty folder (= contains only sub-folder or null-size file) 
    @staticmethod
    def _check_empty_src_dest_folder(abs_src_path:str, abs_dest_path:str) -> bool:
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
        
        if len(self._copied_dir_list) == 0:
            return
        
        # Cleaning...
        for k, t in self._copied_dir_list.items():
            if datetime.datetime.now() - t > PipoEvent.COPY_AGGREGATION_TIME_LIMIT:
                self._copied_dir_list.pop(k)
        
        to_paths = {}
        
        # General idea is to identify if all the file from a same source folder have 
        # each of them generated copied_events to the same destination folder
         
        # Count parent_to_path and associated parent_src_path
        for e in [x for x in self.events_list if x.is_copied_event() and x.parent_rp in self._copied_dir_list]:
            if not e.parent_rp in to_paths:
                to_paths[e.parent_rp] = {}
            for sp, parent_sp in e.possible_src_paths.items():
                if to_paths[e.parent_rp].get(parent_sp) is None:
                    to_paths[e.parent_rp][parent_sp] = []
                to_paths[e.parent_rp][parent_sp].append(e)
        
        # Then we add potential empty folders that have been copied but not transformed (because no file inside)
        for e in [x for x in self.events_list if x.is_created_event() and x.parent_rp in to_paths]:
            if e.is_empty():
                for parent_sp in to_paths[e.parent_rp]:
                    absolute_source_path = self.local_states.absolute_local_path(os.path.join(parent_sp, e.basename))
                    if e.is_directory() and PipoEvent.count_files_in(absolute_source_path) == 0:
                        if HighlevelEventHandler._check_empty_src_dest_folder(absolute_source_path, e.absolute_ref_path):
                            to_paths[e.parent_rp][parent_sp].append(e)
                    elif not e.is_directory() and PipoEvent.get_file_size(absolute_source_path) == 0:
                        to_paths[e.parent_rp][parent_sp].append(e)
        
        # Then we check if any created folder event corresponds to the parent_to_paths
        recurse = False
        for tp in to_paths:
            dir_created_event = next(iter([x for x in self.events_list if x.is_dir_created_event() and x.ref_path == tp]), None)
            for sp in to_paths[tp]:
                #logging.debug("Posttreating copied folder: %s - %s - %s", len(to_paths[tp][sp]), HighlevelEventHandler._len_list_dir(sp), HighlevelEventHandler._len_list_dir(tp))
                if (len(to_paths[tp][sp]) == HighlevelEventHandler._len_list_dir(self.local_states.absolute_local_path(sp)) and 
                    len(to_paths[tp][sp]) == HighlevelEventHandler._len_list_dir(self.local_states.absolute_local_path(tp))):
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
                                e.add_source_paths_and_transforms_into_copied_event(set([os.path.join(sp, e.basename)]))
                                # update main and remove
                                if e in self.events_list:
                                    e.update_main_event(dir_created_event)
                                    self._update_local_state(e)
                                    self.events_list.remove(e)
                            # remove folder from potentially copied... since it will be effectively transformed
                            self._copied_dir_list.pop(tp)
                            self._update_local_state(dir_created_event)
                        # transform main event
                        dir_created_event.add_source_paths_and_transforms_into_copied_event(set([sp]))
                        self._update_posttreatment_cursor()
                    
        # if any event has been transformed to copied event:
        if recurse:
            self._posttreat_copied_folder()
        
        
                        
    def posttreat_lowlevel_event(self, local_event:PipoEvent):
        
        # posttreat file copy
        copy_event_to_posttreat = None
        
        # created events
        if local_event.is_created_event():
            copy_event_to_posttreat = local_event
                       
        # deleted events arrive backward
        if local_event.is_deleted_event():
            for e in [x for x in reversed(self.events_list) if x.is_deleted_event() and x.is_aggregable_with(local_event)]:
                if local_event.comes_before(e):
                    e.update_main_event(local_event)
                    self.events_list.remove(e)
                    local_event.is_related = False
                    self._update_posttreatment_cursor()
            for e in [x for x in reversed(self.events_list) if x.has_same_path_than(local_event) and x.is_aggregable_with(local_event)]:
                if e.is_created_event() or e.is_copied_event() or e.is_modified_event():
                    self.events_list.remove(e)
                    local_event.is_related = True
                    self._update_posttreatment_cursor()
                if e.is_moved_event():
                    e.update_main_event(local_event)
                    local_event.path = e.path
                    local_event.is_related = False
                    self.events_list.remove(e)
                    self._update_posttreatment_cursor()
                    
        # moving event can also arrive just after newly created or copied or moved event
        if local_event.is_moved_event():
            self._update_local_state(local_event)
            for e in [x for x in self.events_list if (x.is_created_event() or x.is_copied_event() or x.is_moved_event()) and x.is_aggregable_with(local_event)]:
                if local_event.has_same_src_path_than(e):
                    local_event.update_main_event(e)
                    e.ref_path = local_event.to_path
                    if e.is_moved_event():
                        self._posttreat_move_by_deletion_creation(e)
                
        
        # modified event
        if local_event.is_modified_event():
            if local_event.is_directory():
                local_event.is_related = True
            else:
                for e in [x for x in reversed(self.events_list) if x.is_aggregable_with(local_event)]:
                    if e.is_deleted_event() or e.is_moved_event() or e.is_copied_event():
                        if local_event.same_or_comes_after(e):
                            local_event.update_main_event(e)
                    elif e.is_created_event() or e.is_modified_event():
                        if local_event.has_same_path_than(e):
                            local_event.update_main_event(e)
                            if e.is_created_event() and local_event.is_meta_file_modified_event():
                                copy_event_to_posttreat = e
        
        # else...
        if not local_event.is_related:
            self.events_list.append(local_event)
                
        # then posttreat file copied event
        if copy_event_to_posttreat is not None:
            if copy_event_to_posttreat.file_size is not None:
                if copy_event_to_posttreat.file_size > 0:
                    if len(self.local_states.get_files_by_sizetime_key((copy_event_to_posttreat.file_size, copy_event_to_posttreat.file_mtime))) > 0:
                        self._block_releases_while_hashing = True
                        # the following command also transforms the created event into a copied one (if any src paths found)...
                        copy_event_to_posttreat.add_source_paths_and_transforms_into_copied_event(self.local_states.get_files_by_hash_key(copy_event_to_posttreat.file_hash))
                        if copy_event_to_posttreat.is_copied_event():
                            self._copied_dir_list[os.path.dirname(copy_event_to_posttreat.to_path)] = datetime.datetime.now()
                        self._update_local_state(copy_event_to_posttreat)
                        self._update_posttreatment_cursor()
                        self._block_releases_while_hashing = False
            
        # then posttreat dir copied event
        self._posttreat_copied_folder()
        
        self._update_posttreatment_cursor()
            
                        
    def _update_local_state(self, event:PipoEvent):
        if event.is_deleted_event():
            self.local_states.delete(event.ref_path)
        elif event.is_moved_event():
            self.local_states.move(event.path, event.to_path)
        else:
            self.save_locals(event.ref_path, [event.file_hash, event.file_size, event.file_mtime])
        
                           
    def save_locals(self, file_path, file_references):
        self.local_states.save(file_path, file_references[0], file_references[1], file_references[2])
        
    
    def get_available_events(self) -> list:
        ready_events = []
        if not self._block_releases_while_hashing and PipoEvent.datetime_difference_from_now(self._latest_highlevel_posttreatment) > HighlevelEventHandler.POSTTREATMENT_TIME_LIMIT:

            if all(x.idle_time() > HighlevelEventHandler.POSTTREATMENT_TIME_LIMIT for x in self.events_list):
                
                for e in self.events_list.copy():
                    if e.is_file_created_event() and e.is_empty() and e.idle_time() <= HighlevelEventHandler.CREATE_EVENT_TIME_LIMIT_FOR_EMPTY_FILES:
                        continue
                    
                    self.events_list.remove(e)
                    ready_events.append(e)
                    
                # clean erratic modified events
                for e in ready_events.copy():
                    if e.is_modified_event():
                        if ( e.file_hash == self.local_states.get_hash(e.path, create=False) and
                            (e.file_size, e.file_mtime) == self.local_states.get_sizetime(e.path, create=False)):
                            ready_events.remove(e)
                        else:
                            self._update_local_state(e)
                    elif e.is_created_event() or e.is_deleted_event():
                        self._update_local_state(e)
                            
        return ready_events
    
    def run(self):
        
        while not self._stop_handler.is_set():
            
            time.sleep(0.2) # to give some time for hashing from other threads...
            
            while not self.lowlevel_event_queue.is_empty():                

                # Post-treatment of the next lowlevel event
                lowlevel_event = self.lowlevel_event_queue.next()
                
                #logging.debug('+++' + str(lowlevel_event))
                self.posttreat_lowlevel_event(lowlevel_event)
                




def logging_in_console(directory:str=''):
    if directory == None:
        directory = ''
    
    # LOG    
    # create logger 
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(console_handler)
    
    
    # MAIN 
    import os
    watched_dir = os.getcwd()
    watched_dir = '/media/maxtor/media/Dropbox/'
    watched_dir = directory if len(directory) > 1 else watched_dir
    
    highlevel_handler = HighlevelEventHandler.get_instance(watched_dir)
    highlevel_handler.start()
    
    try:
        while True:
            time.sleep(1)
            local_events = highlevel_handler.get_available_events()
            
            if len(local_events) > 0:
                logging.info('')
                logging.info('LISTE DES EVENEMENTS PRETS: ')
            for e in local_events:
                logging.info(e)
            
            if len(local_events) > 0:
                logging.info('')
                
    except KeyboardInterrupt:   
        highlevel_handler.stop()
    




# this function is the one called when calling '$ cerberus' in the console.
def main():
    
    import sys
    print(len(sys.argv))
    print(sys.argv[0])
    directory_to_watch = sys.argv[1] if len(sys.argv) > 1 else None
    logging_in_console(directory_to_watch)
    
    
    
if __name__ == "__main__":
    main()
    