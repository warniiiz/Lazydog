
import datetime
import os

from states import LocalState
from revised_watchdog.events import FileSystemEvent


class LazydogEvent():

    EVENT_TYPE_COPIED = 'copied'
    EVENT_TYPE_CREATED = 'created'
    EVENT_TYPE_DELETED = 'deleted'
    EVENT_TYPE_MOVED = 'moved'
    EVENT_TYPE_C_MODIFIED = 'modified' # content modification
    EVENT_TYPE_M_MODIFIED = 'metadata' # metadata modification
        
    
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
        return self.type == LazydogEvent.EVENT_TYPE_MOVED
    
    def is_dir_moved_event(self) -> bool:
        return self.is_moved_event() and self.is_directory()
    
    def is_deleted_event(self) -> bool:
        return self.type == LazydogEvent.EVENT_TYPE_DELETED
    
    def is_dir_deleted_event(self) -> bool:
        return self.is_deleted_event() and self.is_directory()
    
    def is_created_event(self) -> bool:
        return self.type == LazydogEvent.EVENT_TYPE_CREATED
    
    def is_dir_created_event(self) -> bool:
        return self.is_created_event() and self.is_directory()
    
    def is_file_created_event(self) -> bool:
        return self.is_created_event() and not self.is_directory()
    
    def is_copied_event(self) -> bool:
        return self.type == LazydogEvent.EVENT_TYPE_COPIED
    
    def is_modified_event(self) -> bool:
        return self.is_meta_modified_event() or self.is_data_modified_event()
    
    def is_meta_modified_event(self) -> bool:
        return self.type == LazydogEvent.EVENT_TYPE_M_MODIFIED
    
    def is_data_modified_event(self) -> bool:
        return self.type == LazydogEvent.EVENT_TYPE_C_MODIFIED 
    
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
        return LazydogEvent.p1_comes_after_p2(p2, p1)
    
    def comes_before(self, event) -> bool:
        return event.comes_after(self)
            
    def same_or_comes_before(self, event) -> bool:
        return self.comes_before(event) or self.has_same_path_than(event)
    
    
        
    
    def comes_after(self, event, complete_check:bool=True) -> bool:
        if complete_check and self.has_dest() and event.has_dest():
            return LazydogEvent.p1_comes_after_p2(self.path, event.path) and LazydogEvent.p1_comes_after_p2(self.to_path, event.to_path)
        else:
            return LazydogEvent.p1_comes_after_p2(self.ref_path, event.ref_path)
        
    def same_or_comes_after(self, event) -> bool:
        return self.comes_after(event) or self.has_same_path_than(event)
                
    
    @staticmethod
    def datetime_difference_from_now(dt:datetime.datetime) -> datetime.datetime:
        return datetime.datetime.now() - dt
    
    def idle_time(self) -> datetime.datetime:
        return LazydogEvent.datetime_difference_from_now(self.latest_reworked_date)
                                                      
    @property
    def file_hash(self) -> str:
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
    
              
    # Count all files in subfolder, when file size > 0
    # Returns None if folder does not exist
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
            self._dir_files_qty = LazydogEvent.count_files_in(self.absolute_ref_path)
        return self._dir_files_qty
    
    @staticmethod
    def get_file_size(absolute_file_path:str) -> int:
        try:
            return os.path.getsize(absolute_file_path) if not os.path.isdir(absolute_file_path) else None
        except:
            return None
        
    
    @property
    def file_size(self) -> int:
        if self._file_size is None and not self.is_directory():
            self._file_size = LazydogEvent.get_file_size(self.absolute_ref_path)
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
        # Re-assignment
        #self = main_event
    
    # looking for the most probable source aamong a list of potential sources, based on the basename of the destination file or folder
    @staticmethod
    def _get_most_potential_source(src_paths:set, dest_path:str) -> str:
        most_potential_sources = [x for x in src_paths if os.path.splitext(os.path.basename(x))[0] in os.path.splitext(os.path.basename(dest_path))[0]]
        most_potential_sources.sort(key = lambda x: -len(x))
        return most_potential_sources[0] if most_potential_sources is not None else next(iter(src_paths))

    def add_source_paths_and_transforms_into_copied_event(self, src_paths:set):
        for sp in src_paths:
            if not self.is_copied_event():
                self.type = LazydogEvent.EVENT_TYPE_COPIED
                self.to_path = self.path
                self.path = LazydogEvent._get_most_potential_source(src_paths, self.to_path)
            # save all potential parent source path, for future use
            if os.path.basename(sp) == os.path.basename(self.to_path):
                self.possible_src_paths[sp] = os.path.dirname(sp) if sp != '/' else None
            