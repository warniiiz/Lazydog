
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from states import DualAccessMemory
from states import LocalState

DAM = DualAccessMemory()

def test_DAM_basics_1():
    DAM.save('key1', 'value1')
    assert DAM.get('key0') is None
    assert DAM.get('key1') == 'value1'
    assert DAM.get_by_value('value0') == set()
    assert DAM.get_by_value('value1') == set(['key1'])

def test_DAM_basics_2():
    DAM.save('key2', 'value2')
    assert DAM.get('key0') is None
    assert DAM.get('key1') == 'value1'
    assert DAM.get('key2') == 'value2'
    assert DAM.get_by_value('value0') == set()
    assert DAM.get_by_value('value1') == set(['key1'])
    assert DAM.get_by_value('value2') == set(['key2'])

def test_DAM_basics_3():
    DAM.save('key1bis', 'value1')
    assert DAM.get('key0') is None
    assert DAM.get('key1') == 'value1'
    assert DAM.get('key2') == 'value2'
    assert DAM.get('key1bis') == 'value1'
    assert DAM.get_by_value('value0') == set()
    assert DAM.get_by_value('value1') == set(['key1', 'key1bis'])
    assert DAM.get_by_value('value2') == set(['key2'])

def test_DAM_basics_4():
    DAM.save('key2', 'value1')
    assert DAM.get('key2') == 'value1'
    assert DAM.get_by_value('value1') == set(['key1', 'key1bis', 'key2'])
    assert DAM.get_by_value('value2') == set()
    DAM.save('key2', 'value2')
    DAM.delete('key1bis')

def test_DAM_basics_5():
    assert 'key0' not in DAM
    assert 'key1' in DAM
    assert 'key2' in DAM

def test_DAM_basics_6():
    assert 'key3' not in DAM
    DAM['key3'] = 'value3'
    assert 'key3' in DAM
    assert DAM['key3'] == 'value3'

def test_DAM_complex_1():
    assert 'key2' in DAM
    assert 'key3' in DAM
    DAM.delete('key3')
    assert 'key2' in DAM
    assert 'key3' not in DAM

# recursive deletion
def test_DAM_complex_2():
    assert 'key2' in DAM
    assert 'key2/subkey1' not in DAM
    assert DAM.get_by_value('value2') == set(['key2'])
    DAM['key2/subkey1'] = 'subvalue'
    DAM['key2/subkey2'] = 'subvalue'
    assert 'key2/subkey1' in DAM
    assert DAM.get_by_value('subvalue') == set(['key2/subkey1', 'key2/subkey2'])
    DAM.delete('key2')
    assert DAM.get_by_value('subvalue') == set()
    assert DAM.get_by_value('value2') == set()
    assert 'key2' not in DAM
    assert 'key2/subkey1' not in DAM
    assert 'key2/subkey2' not in DAM
    assert 'key1' in DAM

# recursive move
def test_DAM_complex_3():
    assert 'key1' in DAM
    assert 'key2' not in DAM
    DAM['key2'] = 'value2'
    DAM['key2/subkey1'] = 'subvalue'
    DAM['key2/subkey2'] = 'subvalue'
    assert 'key2' in DAM
    assert 'key2/subkey1' in DAM
    assert DAM.get_by_value('subvalue') == set(['key2/subkey1', 'key2/subkey2'])
    assert DAM.get_by_value('value2') == set(['key2'])
    DAM.move('key2', 'movedkey2')
    assert 'key2' not in DAM
    assert 'key2/subkey2' not in DAM
    assert 'movedkey2' in DAM
    assert 'movedkey2/subkey1' in DAM
    assert DAM.get_by_value('subvalue') == set(['movedkey2/subkey1', 'movedkey2/subkey2'])
    assert DAM.get_by_value('value2') == set(['movedkey2'])
    assert 'key1' in DAM
    DAM.move('movedkey2', 'key2')

# deletion of unexisting key
def test_DAM_complex_4():
    assert 'key1' in DAM
    assert 'key3' not in DAM
    DAM.delete('key3') 
    assert 'key1' in DAM
    assert 'key3' not in DAM

# move of unexisting key
def test_DAM_complex_5():
    assert 'key1' in DAM
    assert 'key3' not in DAM
    assert 'movedkey3' not in DAM
    DAM.move('key3', 'movedkey3') 
    assert 'key1' in DAM
    assert 'key3' not in DAM
    assert 'movedkey3' not in DAM

# move to existing key
def test_DAM_complex_6():
    assert 'key1' in DAM
    assert 'key2' in DAM
    assert DAM.get_by_value('value1') == set(['key1'])
    assert DAM.get_by_value('value2') == set(['key2'])
    DAM.move('key2', 'key1') 
    assert 'key1' in DAM
    assert 'key2' not in DAM
    assert DAM.get_by_value('value1') == set()
    assert DAM.get_by_value('value2') == set(['key1'])
    




LS = None
TEST_DIR = None

def dumb_hash_function(absolute_path:str):
    return 'HASH'

def create_file(filename:str):
    os.system('touch ' + TEST_DIR + filename)

def move_file(filename:str, dest_filename:str):
    os.system('mv ' + TEST_DIR + filename + ' ' + TEST_DIR + dest_filename)

def delete_file(filename:str):
    os.system('rm ' + TEST_DIR + filename)

def test_LS_basics_1(tmpdir):
    # Saving TEST_DIR
    global TEST_DIR
    TEST_DIR = str(tmpdir)
    # Adding a file
    create_file('/test.txt')
    # Initializing LS with dumb hash function
    global LS
    LS = LocalState(TEST_DIR, 
                    custom_hash_function=dumb_hash_function)
    assert LS.get_hash('/') == 'HASH'
    assert LS.get_hash('/test.txt') == 'HASH'


def test_LS_basics_2():
    # Re-Initializing LS
    global LS
    LS = LocalState(TEST_DIR,  
                    custom_hash_function=dumb_hash_function,
                    custom_intializing_values={'/':['H', 1, 1523055888], '/test.txt':['H', 2,  1523055999]})
    assert LS.get_hash('/test.txt') == 'H'
    assert LS.get_hash('/') == LocalState.DEFAULT_DIRECTORY_VALUE
    assert LS.get_sizetime('/test.txt') == (2,  1523055999)
    assert LS.get_sizetime('/') == (LocalState.DEFAULT_DIRECTORY_VALUE, LocalState.DEFAULT_DIRECTORY_VALUE)
    # Adding a file
    create_file('/test2.txt')
    assert LS.get_hash('/test2.txt') == 'HASH'
    assert LS.get_sizetime('/test2.txt') == (0, os.path.getmtime(LS.absolute_local_path('/test2.txt')))
    # Adding a file
    create_file('/test3.txt')
    assert LS.get_hash('/test3.txt', compute_if_none=False) == None
    assert LS.get_sizetime('/test3.txt', compute_if_none=False) == None


def test_LS_basics_3():
    # Re-Initializing LS
    global LS
    LS = LocalState(TEST_DIR)
    # Empty file hash = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
    assert LS.get_files_by_hash_key('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855') == set(['/test.txt', '/test2.txt', '/test3.txt'])
    assert LS.get_files_by_sizetime_key((0, os.path.getmtime(LS.absolute_local_path('/test2.txt')))) == set(['/test2.txt'])
    # Delete a file
    delete_file('/test3.txt')
    assert LS.get_hash('/test3.txt') == 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
    assert LS.get_files_by_hash_key('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855') == set(['/test.txt', '/test2.txt'])


def test_LS_basics_4():
    global LS
    LS.save('/test4.txt', 'H', 1, 2)
    assert LS.get_hash('/test4.txt') == 'H'
    assert LS.get_sizetime('/test4.txt') == (1, 2)
    assert LS.get_files_by_hash_key('H') == set()
    # Adding a file
    create_file('/test4.txt')
    LS.save('/test4.txt', 'H', 1, 2)
    assert LS.get_hash('/test4.txt') == 'H'
    assert LS.get_files_by_hash_key('H') == set(['/test4.txt'])


def test_LS_basics_5():
    global LS
    delete_file('/test4.txt')
    LS.delete('/test4.txt')
    assert LS.get_hash('/test4.txt') == None
    assert LS.get_sizetime('/test4.txt') == None
    assert LS.get_files_by_hash_key('H') == set()
    
def test_LS_basics_6():
    global LS
    create_file('/test4.txt')
    LS.save('/test4.txt', 'H', 1, 2)
    assert LS.get_hash('/test4.txt') == 'H'
    assert LS.get_sizetime('/test4.txt') == (1, 2)
    assert LS.get_files_by_hash_key('H') == set(['/test4.txt'])
    # move file
    move_file('/test4.txt', '/test5.txt')
    LS.move('/test4.txt', '/test5.txt')
    assert LS.get_hash('/test4.txt') == None
    assert LS.get_files_by_hash_key('H') == set(['/test5.txt'])
    assert LS.get_hash('/test4.txt') == None
    assert LS.get_hash('/test5.txt') == 'H'
    


