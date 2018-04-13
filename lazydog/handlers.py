


import os
import time
import datetime
import threading

from states import LocalState
from events import LazydogEvent
from queues import DatedlocaleventQueue

from revised_watchdog.observers.inotify import InotifyEmitter, InotifyObserver
from watchdog.observers.polling import PollingObserver




class HighlevelEventHandler(threading.Thread):
    """Post-treat the low level events to suggest only one high-level ones."""

    POSTTREATMENT_TIME_LIMIT = datetime.timedelta(seconds=2)
    CREATE_EVENT_TIME_LIMIT_FOR_EMPTY_FILES = datetime.timedelta(minutes=15) # older behaviour...
    CREATE_EVENT_TIME_LIMIT_FOR_EMPTY_FILES = datetime.timedelta(seconds=2)
    
    @classmethod
    def get_instance(cls, watched_dir:str, hashing_function=None, custom_intializing_values=None):
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
        self._stop_handler.set()
    
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
                    dir_created_event.add_source_paths_and_transforms_into_copied_event(potential_sp)
                    self._update_posttreatment_cursor()
                    
        # if any event has been transformed to copied event:
        if recurse:
            self._posttreat_copied_folder()
        
        
    # to protect against get_available_events modifications...              
    def posttreat_lowlevel_event(self, local_event:LazydogEvent):
        
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
        self.local_states.save(file_path, file_references[0], file_references[1], file_references[2])
        
    # to protect against posttreat_lowlevel_event modifications...
    def get_available_events(self) -> list:
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
                    
                # clean erratic modified events
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
        
        while not self._stop_handler.is_set():
            
            time.sleep(0.2) # to give some time for hashing from other threads...
            
            while not self.lowlevel_event_queue.is_empty():                

                # Post-treatment of the next lowlevel event
                lowlevel_event = self.lowlevel_event_queue.next()
                print('+++ INCOMING LOW LEVEL EVENT +++')
                for e in self.events_list:
                    print('+ ' + str(e))
                print(lowlevel_event)
                
                #logging.debug('+++' + str(lowlevel_event))
                self.posttreat_lowlevel_event(lowlevel_event)
                
