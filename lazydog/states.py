


import os
from dropbox_content_hasher import default_hash_function



class DualAccessMemory():
    
    def __init__(self):

        # self.memories is a dictionary with unique keys and possible same values
        # note that this class has been designed for keys that should be a string containing a path
        self.memories = {}
        self.memories.clear()
        
        # self.dual_memories is a dictionary where the keys are each possible value of self.memories, 
        # and the values are the lists of the associated keys.
        self.dual_memories = {}
        self.dual_memories.clear()

    def get(self, key):
        return self.memories.get(key, None)
    
    def get_by_value(self, value) -> set:
        return self.dual_memories.get(value, set())

    def __getitem__(self, key):
        return self.get(key)
    
    def __setitem__(self, key, value):
        return self.save(key, value)

    def __contains__(self, key):
        return key in self.memories
        
    def _get_children(self, key:str):
        complete_key = key if key.endswith('/') else key + '/'
        children = [x for x in self.memories if x.startswith(complete_key)]
        if key in self.memories:
            children = children + [key]
        return children

    def save(self, key:str, value):
        if key in self:
            self.dual_memories[self.memories[key]].discard(key)
        self.memories[key] = value
        if self.dual_memories.get(self.memories[key]) is None:
            self.dual_memories[self.memories[key]] = set()
        self.dual_memories[self.memories[key]].update([key]) 
    
    # Delete key recursively
    def delete(self, delete_key:str):
        for key in self._get_children(delete_key):
            if self.dual_memories.get(self.memories[key]) is not None:
                self.dual_memories[self.memories[key]].discard(key) 
            self.memories.pop(key)
        
    # Move key recursively
    def move(self, src_key:str, dst_key:str):
        for old_key in self._get_children(src_key):
            new_key = old_key.replace(src_key, dst_key, 1)
            if new_key in self:
                self.dual_memories[self.memories[new_key]].discard(new_key)
            if self.dual_memories.get(self.memories[old_key]) is not None:
                self.dual_memories[self.memories[old_key]].discard(old_key) 
                self.dual_memories[self.memories[old_key]].update([new_key]) 
            self.memories[new_key] = self.memories.pop(old_key)
            
            
    
    


class LocalState():
    
    DEFAULT_DIRECTORY_VALUE = 'DIR'
    
    # Default method to get the Hash of the file with the supplied file name.
    @staticmethod
    def _default_hashing_function(absolute_path:str): 
        return default_hash_function(absolute_path, LocalState.DEFAULT_DIRECTORY_VALUE)
    
    # Following 3 methods can be used in other classes
    def absolute_local_path(self, relative_path:str) -> str:
        if relative_path.startswith('/'):
            relative_path = relative_path[1:]
        return os.path.join(self.absolute_root_folder, relative_path)
    
    def relative_local_path(self, absolute_path:str) -> str:
        absolute_path = os.path.normpath(absolute_path)
        return '/' + os.path.relpath(absolute_path, self.absolute_root_folder)
    
    def hash_function(self, *args, **kwargs):
        return self._hash_function(*args, **kwargs)
    
    def __init__(self, absolute_root_folder, custom_hash_function=None, custom_intializing_values:dict=None):
        
        # keep absolute root folder
        self.absolute_root_folder = absolute_root_folder
        
        # keep hash function
        self._hash_function = custom_hash_function if custom_hash_function is not None else LocalState._default_hashing_function
        
        # self.hashes is a dual access dictionary 
        # self.hashes.get(key) with key=file_path returns the value=file_hash
        # self.hashes.get_by_value(value) with value=file_hash returns a set of paths
        self.hashes = DualAccessMemory()
        
        # self.sizetimes is a dual access dictionary 
        # self.sizetimes.get(key) with key=file_path returns the value=tuple(file_size, file_mtime)
        # self.sizetimes.get_by_value(value) with value=tuple(file_size, file_mtime) returns a set of paths
        self.sizetimes = DualAccessMemory()
        
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
    

    
    def get_hash(self, key:str, compute_if_none:bool=True) -> str:
        if key not in self.hashes and compute_if_none:
            self.hashes[key] = self.hash_function(self.absolute_local_path(key))
        return self.hashes[key]
        
    def get_files_by_hash_key(self, hash_key:str) -> set:
        file_paths = self.hashes.get_by_value(hash_key)
        return self._check_for_deleted_paths(file_paths)

    def get_sizetime(self, key:str, compute_if_none:bool=True):
        if key not in self.sizetimes and compute_if_none:
            if os.path.isdir(self.absolute_local_path(key)):
                self.sizetimes[key] = (LocalState.DEFAULT_DIRECTORY_VALUE, 
                                       LocalState.DEFAULT_DIRECTORY_VALUE)
            elif os.path.exists(self.absolute_local_path(key)):
                self.sizetimes[key] = (os.path.getsize(self.absolute_local_path(key)), 
                                       os.path.getmtime(self.absolute_local_path(key)))
        return self.sizetimes[key]
        
    def get_files_by_sizetime_key(self, sizetime_key) -> set:
        file_paths = self.sizetimes.get_by_value(sizetime_key)
        return self._check_for_deleted_paths(file_paths)
    
    def _check_for_deleted_paths(self, paths:set):
        deleted_paths = [x for x in paths if not os.path.exists(self.absolute_local_path(x))]
        for dp in deleted_paths:
            self.hashes.delete(dp)
            self.sizetimes.delete(dp)
        return paths - set(deleted_paths)
    
    def save(self, key:str, file_hash, file_size, file_mtime):
        if os.path.isdir(self.absolute_local_path(key)):
            file_hash = LocalState.DEFAULT_DIRECTORY_VALUE
            file_size = LocalState.DEFAULT_DIRECTORY_VALUE
            file_mtime = LocalState.DEFAULT_DIRECTORY_VALUE
        self.hashes[key] = file_hash
        self.sizetimes[key] = (file_size, file_mtime)
    
    # Delete key recursively
    def delete(self, delete_key:str):
        self.hashes.delete(delete_key)
        self.sizetimes.delete(delete_key)
    
    # Move key recursively
    def move(self, src_key:str, dst_key:str):
        self.hashes.move(src_key, dst_key)
        self.sizetimes.move(src_key, dst_key)
            
    
    
    
    
    
    
