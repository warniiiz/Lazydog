
import sys
import os
import time
import datetime
import shutil
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from events import LazydogEvent
from states import LocalState
from handlers import HighlevelEventHandler



TEST_DIR = None
HANDLER = None
LIST_OF_LOCAL_FILES = []

def dumb_hash_function(absolute_path:str):
    return 'HASH'

def create_dir(dirname:str):
    global LIST_OF_LOCAL_FILES
    if not os.path.exists(TEST_DIR + dirname):
        os.mkdir(TEST_DIR + dirname)
        LIST_OF_LOCAL_FILES.append(dirname)

def create_file(filename:str, text:str=''):
    global LIST_OF_LOCAL_FILES
    os.mknod(TEST_DIR + filename)
    append_file(filename, text)
    LIST_OF_LOCAL_FILES.append(filename)

def append_file(filename:str, text:str=''):
    if text is not None:
        if len(text) > 0:
            with open(TEST_DIR + filename, "a") as f:
                f.write(text)

def move_file(filename:str, dest_filename:str):
    global LIST_OF_LOCAL_FILES
    if os.path.normpath(TEST_DIR + dest_filename).startswith(TEST_DIR):
        LIST_OF_LOCAL_FILES.append(dest_filename)
    if os.path.normpath(TEST_DIR + filename).startswith(TEST_DIR):
        LIST_OF_LOCAL_FILES.remove(filename)
    for root, dirs, files in os.walk(TEST_DIR + filename):
        for d in dirs:
            p = os.path.join(dest_filename, d)
            if os.path.normpath(TEST_DIR + p).startswith(TEST_DIR):
                LIST_OF_LOCAL_FILES.append(p)
            p = os.path.join(filename, d)
            if os.path.normpath(TEST_DIR + p).startswith(TEST_DIR):
                LIST_OF_LOCAL_FILES.remove(p)
        for f in files:
            p = os.path.join(dest_filename, f)
            if os.path.normpath(TEST_DIR + p).startswith(TEST_DIR):
                LIST_OF_LOCAL_FILES.append(p)
            p = os.path.join(filename, f)
            if os.path.normpath(TEST_DIR + p).startswith(TEST_DIR):
                LIST_OF_LOCAL_FILES.remove(p)
    shutil.move(TEST_DIR + filename, TEST_DIR + dest_filename)

def copy_file(filename:str, dest_filename:str):
    global LIST_OF_LOCAL_FILES
    if os.path.isdir(TEST_DIR + filename):
        shutil.copytree(TEST_DIR + filename, TEST_DIR + dest_filename)
        for root, dirs, files in os.walk(TEST_DIR + filename):
            for d in dirs:
                LIST_OF_LOCAL_FILES.append(os.path.join(dest_filename, d))
            for f in files:
                LIST_OF_LOCAL_FILES.append(os.path.join(dest_filename, f))
    else:
        shutil.copy2(TEST_DIR + filename, TEST_DIR + dest_filename)
    LIST_OF_LOCAL_FILES.append(dest_filename)

def delete_file(filename:str):
    global LIST_OF_LOCAL_FILES
    try:
        if os.path.isdir(TEST_DIR + filename):
            for root, dirs, files in os.walk(TEST_DIR + filename):
                for d in dirs:
                    LIST_OF_LOCAL_FILES.remove(os.path.join(filename, d))
                for f in files:
                    LIST_OF_LOCAL_FILES.remove(os.path.join(filename, f))
            shutil.rmtree(TEST_DIR + filename)
        else:
            os.remove(TEST_DIR + filename)
        LIST_OF_LOCAL_FILES.remove(filename)
    except FileNotFoundError:
        pass

def get_events():
    time.sleep(1)
    events = HANDLER.get_available_events()
    print('LISTING READY EVENTS...')
    for e in events:
        print(e)
    return events

def print_filetree(dirname:str=''):
    print('LISTING FILE TREE...')
    startpath = TEST_DIR + dirname
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 3 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 3 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))

def check_local_state() -> bool:
    global LIST_OF_LOCAL_FILES
    print('CHECKING LIST OF LOCAL FILES...')
    print('Saved files:    ' + str(sorted(list(HANDLER.local_states.hashes.memories.keys()))))
    print('Expected files: ' + str(sorted(LIST_OF_LOCAL_FILES)))
    return set(HANDLER.local_states.hashes.memories.keys()) == set(LIST_OF_LOCAL_FILES)



# initialization
def test_H_basics_0(tmpdir):
    # Saving TEST_DIR
    global TEST_DIR
    TEST_DIR = str(tmpdir)
    assert os.path.isdir(TEST_DIR)
    # Saving HANDLER
    global HANDLER
    HANDLER = HighlevelEventHandler.get_instance(TEST_DIR)
    HANDLER.start()
    assert len(HANDLER.get_available_events()) == 0



# create dir
def test_H_basics_1a():
    HighlevelEventHandler.POSTTREATMENT_TIME_LIMIT = datetime.timedelta(seconds=1)
    dir1name = '/dir1'
    create_dir(dir1name)
    time.sleep(0.5)
    assert len(HANDLER.get_available_events()) == 0
    time.sleep(0.5)
    events = get_events()
    assert len(events) == 1
    assert len(HANDLER.get_available_events()) == 0
    e = events[0]
    assert e.is_dir_created_event()
    assert e.path == dir1name
    assert check_local_state()

# create file (not empty file)
def test_H_basics_1b():
    HighlevelEventHandler.POSTTREATMENT_TIME_LIMIT = datetime.timedelta(seconds=0)
    HighlevelEventHandler.CREATE_EVENT_TIME_LIMIT_FOR_EMPTY_FILES = datetime.timedelta(seconds=0)
    file1name = '/file1.txt'
    create_file(file1name, 'not_empty')
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_file_created_event()
    assert e.path == file1name
    assert e.file_size == 9
    assert check_local_state()

# move file 
def test_H_basics_3a():
    file1name = '/file1.txt'
    file1name_moved = '/file1_moved.txt'
    move_file(file1name, file1name_moved)
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_moved_event()
    assert e.path == file1name
    assert e.to_path == file1name_moved
    assert e.file_size == 9
    assert check_local_state()

# move file to external location (=delete)
def test_H_basics_3b():
    file1name_moved = '/file1_moved.txt'
    file1name_extmoved = '/../file1_moved.txt'
    move_file(file1name_moved, file1name_extmoved)
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_deleted_event()
    assert e.path == file1name_moved
    assert not e.has_dest()
    assert check_local_state()

# move file from external localtion (=create)
def test_H_basics_3c():
    file1name_extmoved = '/../file1_moved.txt'
    file1name = '/file1.txt'
    move_file(file1name_extmoved, file1name)
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_file_created_event()
    assert e.path == file1name
    assert not e.has_dest()
    assert e.file_size == 9
    assert check_local_state()

# move dir 
def test_H_basics_3d():
    dir1name = '/dir1'
    create_file(dir1name + '/f1.txt', 'file_content_1')
    create_file(dir1name + '/f2.txt', 'file_content_2')
    time.sleep(1)
    events = HANDLER.get_available_events() # emptying the events list
    moved_dir1name = '/moved_dir1'
    move_file(dir1name, moved_dir1name)
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_moved_event()
    assert e.path == dir1name
    assert e.to_path == moved_dir1name
    assert check_local_state()

# modify file
def test_H_basics_4a():
    file1name = '/file1.txt'
    append_file(file1name, ' edited')
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_file_modified_event()
    assert e.path == file1name
    assert e.file_size == 16
    assert check_local_state()

# copy file
def test_H_basics_5a():
    file1name = '/file1.txt'
    copied_file1name = '/copied_file1.txt'
    copy_file(file1name, copied_file1name)
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_copied_event()
    assert e.path == file1name
    assert e.to_path == copied_file1name
    assert e.file_size == 16
    assert check_local_state()

# copy dir 
def test_H_basics_5b():
    moved_dir1name = '/moved_dir1'
    copied_dir1name = '/dir1'
    copy_file(moved_dir1name, copied_dir1name)
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_copied_event()
    assert e.path == moved_dir1name
    assert e.to_path == copied_dir1name
    assert check_local_state()

# delete file
def test_H_basics_6a():
    copied_file1name = '/copied_file1.txt'
    delete_file(copied_file1name)
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_deleted_event()
    assert e.path == copied_file1name
    assert check_local_state()

# delete dir 
def test_H_basics_6b():
    moved_dir1name = '/moved_dir1'
    delete_file(moved_dir1name)
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_deleted_event()
    assert e.path == moved_dir1name
    assert check_local_state()

# delete moved empty dir 
def test_H_basics_6c():
    dir2name = '/dir2'
    moved_dir2name = '/moved_dir2'
    create_dir(dir2name)
    move_file(dir2name, moved_dir2name)
    delete_file(moved_dir2name)
    print_filetree()
    events = get_events()
    assert len(events) == 0 # since it has been created and instantely deleted
    assert check_local_state()

# delete copied empty dir 
def test_H_basics_6d():
    dir2name = '/dir2'
    copied_dir2name = '/copied_dir2'
    create_dir(dir2name)
    copy_file(dir2name, copied_dir2name)
    delete_file(copied_dir2name)
    print_filetree()
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_created_event()
    assert e.path == dir2name
    assert check_local_state()

# delete copied then moved empty dir 
def test_H_basics_6e():
    dir2name = '/dir2'
    copied_dir2name = '/copied_dir2'
    moved_dir2name = '/moved_dir2'
    copy_file(dir2name, copied_dir2name)
    move_file(copied_dir2name, moved_dir2name)
    delete_file(moved_dir2name)
    delete_file(dir2name)
    print_filetree()
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_deleted_event()
    assert e.path == dir2name
    assert check_local_state()


# create empty file, then move it, and finaly, append content to it
def test_H_complex_1():
    HighlevelEventHandler.CREATE_EVENT_TIME_LIMIT_FOR_EMPTY_FILES = datetime.timedelta(minutes=15)
    # create empty file
    emptyfile = '/emptyfile.txt'
    create_file(emptyfile)
    time.sleep(1)
    assert HANDLER.lowlevel_event_queue.size() == 0
    assert len(HANDLER.get_available_events()) == 0
    assert len(HANDLER.events_list) == 1
    assert HANDLER.events_list[0].is_file_created_event()
    # move file 
    movedemptyfile = '/movedemptyfile.txt'
    move_file(emptyfile, movedemptyfile)
    time.sleep(1)
    assert HANDLER.lowlevel_event_queue.size() == 0
    assert len(HANDLER.get_available_events()) == 0
    assert len(HANDLER.events_list) == 1
    assert HANDLER.events_list[0].is_file_created_event() # and not move because of agregation
    HighlevelEventHandler.CREATE_EVENT_TIME_LIMIT_FOR_EMPTY_FILES = datetime.timedelta(seconds=0)
    # append file
    movedemptyfile = '/movedemptyfile.txt'
    append_file(movedemptyfile, 'content')
    events = get_events()
    assert HANDLER.lowlevel_event_queue.size() == 0
    assert len(events) == 1
    assert len(HANDLER.events_list) == 0
    e = events[0]
    assert e.is_file_created_event()
    assert e.path == movedemptyfile
    assert e.file_size == 7
    assert check_local_state()

# multiple file modification
def test_H_complex_2():
    file1name = '/file1.txt'
    append_file(file1name, '#')
    time.sleep(0.1)
    append_file(file1name, '#')
    time.sleep(0.1)
    append_file(file1name, '#')
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_file_modified_event()
    assert e.path == file1name
    assert e.file_size == 19
    assert check_local_state()

# rapid create and delete file
def test_H_complex_3():
    tmp_filename = '/tmp_file.txt'
    create_file(tmp_filename, '#')
    delete_file(tmp_filename)
    events = get_events()
    assert len(events) == 0
    assert check_local_state()

# copy dir containing empty file and empty folder (among other)
def test_H_complex_4a():
    dir1name = '/dir1'
    emtpy_dirname = '/dir1/empty_dir'
    emtpy_filename = '/dir1/empty_file.txt'
    create_file(emtpy_filename)
    create_dir(emtpy_dirname)
    time.sleep(1)
    events = HANDLER.get_available_events()
    copied_dir1name = '/copied_dir1'
    copy_file(dir1name, copied_dir1name)
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_copied_event()
    assert e.path == dir1name
    assert e.to_path == copied_dir1name
    assert check_local_state()

# move dir containing empty file and empty folder (among other)
def test_H_complex_4b():
    copied_dir1name = '/copied_dir1'
    moved_dir1name = '/moved_dir1'
    move_file(copied_dir1name, moved_dir1name)
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_moved_event()
    assert e.path == copied_dir1name
    assert e.to_path == moved_dir1name
    assert check_local_state()

# delete dir containing empty file and empty folder (among other)
def test_H_complex_4c():
    moved_dir1name = '/moved_dir1'
    print_filetree()
    delete_file(moved_dir1name)
    print_filetree()
    events = get_events()
    assert len(events) == 1
    e = events[0]
    assert e.is_deleted_event()
    assert e.path == moved_dir1name
    assert check_local_state()



def test_H_basics_99():
    HANDLER.stop()
    assert HANDLER._stop_handler.is_set()









    # POSTTREATMENT_TIME_LIMIT
    # def get_instance(cls, watched_dir:str, hashing_function=None, custom_intializing_values=None):
    # def __init__(self, lowlevel_event_queue:DatedlocaleventQueue, local_states:LocalState):
    # def stop(self):
    # def _update_posttreatment_cursor(self):
    # def _len_list_dir(absolute_path:str) -> int:
    # def _check_empty_src_dest_folder(abs_src_path:str, abs_dest_path:str) -> bool:
    # def _posttreat_copied_folder(self):
    # def posttreat_lowlevel_event(self, local_event:LazydogEvent):
    # def _update_local_state(self, event:LazydogEvent):
    # def save_locals(self, file_path, file_references):
    # def get_available_events(self) -> list:
    # def run(self):





# # dir_created_event
# def test_LDE_basics_2():
#     dir_created_event = DirCreatedEvent(TEST_DIR)
#     LE = LazydogEvent(dir_created_event, LS)
#     # testing paths
#     assert LE.path == '/'
#     assert LE.to_path is None
#     assert LE.ref_path == LE.path
#     assert not LE.has_dest()
#     assert LE.parent_rp is None
#     assert LE.basename == ''
#     assert LE.absolute_ref_path == TEST_DIR + LE.path
#     assert LE.is_dir
#     assert LE.is_directory()
  


# # xxxxx
# def test_LDE_complex_1():
#     assert True

