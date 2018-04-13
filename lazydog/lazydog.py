#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import logging

from handlers import HighlevelEventHandler

__version__ = "0.1"


# this function shows an example of how to use Lazydog.
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
    




# this function is the one called when calling '$ lazydog' in the console.
def main():
    
    import sys
    directory_to_watch = sys.argv[1] if len(sys.argv) > 1 else None
    logging_in_console(directory_to_watch)
    
    
    
if __name__ == "__main__":
    main()
    