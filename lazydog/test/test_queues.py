
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from queues import DatedlocaleventQueue
from states import LocalState
from revised_watchdog.observers.inotify import InotifyObserver

TEST_DIR = None
TESTED_QUEUE = None

def create_file(filename:str):
    os.mknod(TEST_DIR + filename)

def test_instanciate_tested_queue(tmpdir):
    # tmpdir creates a temporary test dir
    global TEST_DIR
    TEST_DIR = str(tmpdir)
    # create local state
    local_states = LocalState(str(tmpdir))
    # create tested queue
    global TESTED_QUEUE
    TESTED_QUEUE = DatedlocaleventQueue(local_states)

def test_DatedlocaleventQueue():
    
    # Basics
    assert TESTED_QUEUE.is_empty() 
    assert TESTED_QUEUE.size() == 0
    assert TESTED_QUEUE.next() is None

    # Adding an observer using this queue
    observer = InotifyObserver() # generate_full_events=False) # With reviewed Inotify 
    observer.schedule(TESTED_QUEUE, TEST_DIR, recursive=True)
    observer.name = 'Local Inotify observer'
    observer.start()

    # Generating a created event
    create_file('/test.txt')

    # Checking result - 3 new events during the tests
    time.sleep(0.1)
    time.sleep(0.5)
    assert TESTED_QUEUE.size() > 0
    assert not TESTED_QUEUE.is_empty() 

    # Getting the events
    while not TESTED_QUEUE.is_empty():
        assert TESTED_QUEUE.next().__class__.__name__ == 'LazydogEvent'

    # Checking emptyness of the queue
    assert TESTED_QUEUE.is_empty() 






