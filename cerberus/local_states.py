
import os




class LocalState():
    
    # Method to get the MD5 Hash of the file with the supplied file name.
    @staticmethod
    def _default_hashing_function(absolute_path:str):
        from dropbox_content_hasher import default_hash_function 
        return default_hash_function(absolute_path)
    
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
            
    
