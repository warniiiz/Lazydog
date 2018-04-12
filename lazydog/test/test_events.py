
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from events import LazydogEvent
from states import LocalState

from watchdog.events import (
    FileCreatedEvent,
    DirCreatedEvent,
    FileMovedEvent,
    DirMovedEvent,
    FileDeletedEvent,
    DirDeletedEvent,
    EVENT_TYPE_MOVED, 
    EVENT_TYPE_CREATED, 
    EVENT_TYPE_MODIFIED,
    EVENT_TYPE_DELETED
    )

from revised_watchdog.events import (
    TrueFileModifiedEvent,
    MetaFileModifiedEvent,
    TrueDirModifiedEvent,
    MetaDirModifiedEvent,
    EVENT_TYPE_C_MODIFIED,
    EVENT_TYPE_M_MODIFIED
    )


TEST_DIR = None
LS = None

def dumb_hash_function(absolute_path:str):
    return 'HASH'

def create_dir(dirname:str):
    if not os.path.exists(TEST_DIR + dirname):
        os.mkdir(TEST_DIR + dirname)

def create_file(filename:str, text:str=''):
    os.mknod(TEST_DIR + filename)
    append_file(filename, text)

def append_file(filename:str, text:str=''):
    if text is not None:
        if len(text) > 0:
            with open(TEST_DIR + filename, "a") as f:
                f.write(text)

def move_file(filename:str, dest_filename:str):
    os.rename(TEST_DIR + filename, TEST_DIR + dest_filename)

def delete_file(filename:str):
    try:
        if os.path.isdir(TEST_DIR + filename):
            os.rmdir(TEST_DIR + filename)
        else:
            os.remove(TEST_DIR + filename)
    except FileNotFoundError:
        pass



def test_LDE_basics_0():
    # LazydogEvent.p1_comes_before_p2
    assert LazydogEvent.p1_comes_before_p2('/', '/dir1')
    assert LazydogEvent.p1_comes_before_p2('/', '/file1.txt')
    assert LazydogEvent.p1_comes_before_p2('/', '/dir1/file1.txt')
    assert LazydogEvent.p1_comes_before_p2('/dir1', '/dir1/file1.txt')
    assert LazydogEvent.p1_comes_before_p2('/dir1/', '/dir1/file1.txt')
    assert not LazydogEvent.p1_comes_before_p2('/dir1/file2.txt', '/dir1/file1.txt')
    assert not LazydogEvent.p1_comes_before_p2('/dir1/dir2', '/dir1/file1.txt')    
    assert not LazydogEvent.p1_comes_before_p2('/dir1', '/')      
    assert not LazydogEvent.p1_comes_before_p2('/dir1', '/dir1')       
    assert not LazydogEvent.p1_comes_before_p2('/', '/')    
    # LazydogEvent.p1_comes_after_p2
    assert not LazydogEvent.p1_comes_after_p2('/', '/dir1')
    assert not LazydogEvent.p1_comes_after_p2('/', '/file1.txt')
    assert not LazydogEvent.p1_comes_after_p2('/', '/dir1/file1.txt')
    assert not LazydogEvent.p1_comes_after_p2('/dir1', '/dir1/file1.txt')
    assert not LazydogEvent.p1_comes_after_p2('/dir1/', '/dir1/file1.txt')
    assert not LazydogEvent.p1_comes_after_p2('/dir1/file2.txt', '/dir1/file1.txt')
    assert not LazydogEvent.p1_comes_after_p2('/dir1/dir2', '/dir1/file1.txt')    
    assert LazydogEvent.p1_comes_after_p2('/dir1', '/')      
    assert LazydogEvent.p1_comes_after_p2('/file1.txt', '/')     
    assert LazydogEvent.p1_comes_after_p2('/dir1/file1.txt', '/dir1')     
    assert not LazydogEvent.p1_comes_after_p2('/dir1', '/dir1')       
    assert not LazydogEvent.p1_comes_after_p2('/', '/')   

def test_LDE_basics_1(tmpdir):
    # Saving TEST_DIR
    global TEST_DIR
    TEST_DIR = str(tmpdir)
    assert os.path.isdir(TEST_DIR)
    # creating LocalState
    global LS
    LS = LocalState(TEST_DIR)
    # LazydogEvent.count_files_in
    assert LazydogEvent.count_files_in(TEST_DIR) == 0
    assert LazydogEvent.count_files_in(TEST_DIR + '/nodir') is None
    assert LazydogEvent.get_file_size(TEST_DIR) is None
    assert LazydogEvent.get_file_size(TEST_DIR + '/nodir') is None

# dir_created_event
def test_LDE_basics_2():
    dir_created_event = DirCreatedEvent(TEST_DIR)
    LE = LazydogEvent(dir_created_event, LS)
    # testing paths
    assert LE.path == '/'
    assert LE.to_path is None
    assert LE.ref_path == LE.path
    assert not LE.has_dest()
    assert LE.parent_rp is None
    assert LE.basename == ''
    assert LE.absolute_ref_path == TEST_DIR + LE.path
    assert LE.is_dir
    assert LE.is_directory()
    # type testing
    assert LE.is_same_type_than(LE)
    assert LE.type == EVENT_TYPE_CREATED
    assert not LE.is_moved_event()
    assert not LE.is_dir_moved_event()
    assert not LE.is_deleted_event()
    assert not LE.is_dir_deleted_event()
    assert LE.is_created_event()
    assert LE.is_dir_created_event()
    assert not LE.is_file_created_event()
    assert not LE.is_copied_event()
    assert not LE.is_modified_event()
    assert not LE.is_meta_modified_event()
    assert not LE.is_data_modified_event()
    assert not LE.is_file_modified_event()
    assert not LE.is_meta_file_modified_event()
    assert not LE.is_data_file_modified_event()
    assert not LE.is_dir_modified_event()
    # misc testing
    assert LE.has_same_mtime_than(LE)
    assert LE.has_same_size_than(LE)
    assert LE.has_same_path_than(LE)
    assert LE.has_same_src_path_than(LE)
    assert LE.file_hash == LS.DEFAULT_DIRECTORY_VALUE
    assert LE.dir_files_qty == 0
    assert LE.file_size is None
    assert LE.is_empty() 


# file_created_event
def test_LDE_basics_3():
    file1name = '/file1.txt'
    create_file(file1name, 'coucou')
    file_created_event = FileCreatedEvent(TEST_DIR + file1name)
    LE = LazydogEvent(file_created_event, LS)
    # testing paths
    assert LE.path == file1name
    assert LE.to_path is None
    assert LE.ref_path == LE.path
    assert not LE.has_dest()
    assert LE.parent_rp == '/'
    assert LE.basename == 'file1.txt'
    assert LE.absolute_ref_path == TEST_DIR + LE.path
    assert not LE.is_dir
    assert not LE.is_directory()
    # type testing
    assert LE.is_same_type_than(LE)
    assert LE.type == EVENT_TYPE_CREATED
    assert not LE.is_moved_event()
    assert not LE.is_dir_moved_event()
    assert not LE.is_deleted_event()
    assert not LE.is_dir_deleted_event()
    assert LE.is_created_event()
    assert not LE.is_dir_created_event()
    assert LE.is_file_created_event()
    assert not LE.is_copied_event()
    assert not LE.is_modified_event()
    assert not LE.is_meta_modified_event()
    assert not LE.is_data_modified_event()
    assert not LE.is_file_modified_event()
    assert not LE.is_meta_file_modified_event()
    assert not LE.is_data_file_modified_event()
    assert not LE.is_dir_modified_event()
    # misc testing
    assert LE.has_same_mtime_than(LE)
    assert LE.has_same_size_than(LE)
    assert LE.has_same_path_than(LE)
    assert LE.has_same_src_path_than(LE)
    assert LE.file_hash == '71e9c373a6282c8ab2db54bff41ac99a0188fd22cfd6f10848ed211d61dbb481'
    assert LE.dir_files_qty is None
    assert LE.file_size == 6
    assert not LE.is_empty() # because not null-size


# file_moved_event
def test_LDE_basics_4():
    file1name = '/file1.txt'
    file2name = '/file2.txt'
    move_file(file1name, file2name)
    file_moved_event = FileMovedEvent(TEST_DIR + file1name, TEST_DIR + file2name)
    LE = LazydogEvent(file_moved_event, LS)
    # testing paths
    assert LE.path == file1name
    assert LE.to_path == file2name
    assert LE.ref_path == LE.to_path
    assert LE.has_dest()
    assert LE.parent_rp == '/'
    assert LE.basename == 'file2.txt'
    assert LE.absolute_ref_path == TEST_DIR + LE.ref_path
    assert not LE.is_dir
    assert not LE.is_directory()
    # type testing
    assert LE.is_same_type_than(LE)
    assert LE.type == EVENT_TYPE_MOVED
    assert LE.is_moved_event()
    assert not LE.is_dir_moved_event()
    assert not LE.is_deleted_event()
    assert not LE.is_dir_deleted_event()
    assert not LE.is_created_event()
    assert not LE.is_dir_created_event()
    assert not LE.is_file_created_event()
    assert not LE.is_copied_event()
    assert not LE.is_modified_event()
    assert not LE.is_meta_modified_event()
    assert not LE.is_data_modified_event()
    assert not LE.is_file_modified_event()
    assert not LE.is_meta_file_modified_event()
    assert not LE.is_data_file_modified_event()
    assert not LE.is_dir_modified_event()
    # misc testing
    assert LE.has_same_mtime_than(LE)
    assert LE.has_same_size_than(LE)
    assert LE.has_same_path_than(LE)
    assert not LE.has_same_src_path_than(LE) # comparing source path of LE against ref_path of LE...
    assert LE.file_hash == '71e9c373a6282c8ab2db54bff41ac99a0188fd22cfd6f10848ed211d61dbb481'
    assert LE.dir_files_qty is None
    assert LE.file_size == 6
    assert not LE.is_empty() # because not null-size

# dir_moved_event
def test_LDE_basics_5():
    assert True

# dir_deleted_event
def test_LDE_basics_6():
    assert True

# file_deleted_event
def test_LDE_basics_7():
    assert True

# file_metadata_modified_event
def test_LDE_basics_8():
    assert True

# file_content_modified_event
def test_LDE_basics_9():
    assert True

# dir_modified_event
def test_LDE_basics_10():
    assert True

# copied_modified_event
def test_LDE_basics_11():
    assert True




# update_main_event
def test_LDE_complex_1():
    # definitions
    file1name = '/file1.txt'
    file2name = '/file2.txt'
    delete_file(file1name)
    delete_file(file2name)
    # create file
    create_file(file1name, 'hello')
    file_created_event = FileCreatedEvent(TEST_DIR + file1name)
    created_LE = LazydogEvent(file_created_event, LS)
    # move the same file
    move_file(file1name, file2name)
    file_moved_event = FileMovedEvent(TEST_DIR + file1name, TEST_DIR + file2name)
    moved_LE = LazydogEvent(file_moved_event, LS)
    # then associate both events: update previous created_event with moved event
    assert created_LE.ref_path == file1name
    moved_LE.update_main_event(created_LE)
    assert created_LE.ref_path == file1name
    # assertions
    assert moved_LE in created_LE.related_events
    assert created_LE.first_event_date <= moved_LE.first_event_date
    assert created_LE.latest_event_date >= moved_LE.latest_event_date
    assert created_LE.latest_event_date > created_LE.first_event_date
    assert created_LE.is_related
    assert moved_LE.is_related
    assert created_LE.latest_reworked_date > created_LE.first_event_date
    assert created_LE.latest_reworked_date > created_LE.latest_event_date


# _get_most_potential_source
def test_LDE_complex_2():
    set_of_paths = set(['/file1.txt', '/file2.txt', '/dir1/file3.txt', '/dir2/file 3.txt'])
    assert LazydogEvent._get_most_potential_source(set_of_paths, '/copy-dir/copy of file3.txt') == '/dir1/file3.txt'
    assert LazydogEvent._get_most_potential_source(set_of_paths, '/copy-dir/copy of file 3.txt') == '/dir2/file 3.txt'
    assert LazydogEvent._get_most_potential_source(set_of_paths, '/file2 copy.txt') == '/file2.txt'
    
# add_source_paths_and_transforms_into_copied_event
def test_LDE_complex_3():
     # definitions
    file1name = '/file1.txt'
    file2name = '/file2.txt'
    delete_file(file1name)
    delete_file(file2name)
    # create file
    create_file(file1name, 'hello')
    create_file(file2name, 'hello')
    file_created_event = FileCreatedEvent(TEST_DIR + file2name)
    created_LE = LazydogEvent(file_created_event, LS)
    # assertions before transformation
    assert created_LE.is_created_event()
    assert created_LE.is_file_created_event()
    assert created_LE.ref_path == file2name
    assert created_LE.path == file2name
    assert not created_LE.has_dest()
    # transformation
    created_LE.add_source_paths_and_transforms_into_copied_event(file1name)
    copied_LE = created_LE
    # assertions after transformation
    assert copied_LE.is_copied_event()
    assert not copied_LE.is_directory()
    assert copied_LE.ref_path == file2name
    assert copied_LE.has_dest()
    assert copied_LE.path == file1name
    assert len(copied_LE.possible_src_paths) == 0

# add_source_paths_and_transforms_into_copied_event
def test_LDE_complex_3_bis():
     # definitions
    file1name = '/dir1/file1.txt'
    file2name = '/dir2/file1.txt'
    delete_file(file1name)
    delete_file(file2name)
    # create file
    create_dir('/dir1')
    create_dir('/dir2')
    create_file(file1name, 'hello')
    create_file(file2name, 'hello')
    file_created_event = FileCreatedEvent(TEST_DIR + file2name)
    created_LE = LazydogEvent(file_created_event, LS)
    # assertions before transformation
    assert created_LE.is_created_event()
    assert created_LE.path == file2name
    # transformation
    created_LE.add_source_paths_and_transforms_into_copied_event(file1name)
    copied_LE = created_LE
    # assertions after transformation
    assert copied_LE.is_copied_event()
    assert copied_LE.ref_path == file2name
    assert copied_LE.path == file1name
    assert len(copied_LE.possible_src_paths) == 1
   

