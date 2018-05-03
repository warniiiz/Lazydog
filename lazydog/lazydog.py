#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2018 Clément Warneys <clement.warneys@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
:module: lazydog.lazidog
:synopsis: An sample module that show how to use the package, \
by logging the high-level lazydog events in the console. \
The main function of this module is executed by calling \
``$ lazidog`` in the system console.
:author: Clément Warneys <clement.warneys@gmail.com>

Please read the source code for more information. Below is an example on 
how to initialize the high-level lazydog event handler, and log every 
new event in the console (using logging module). The watched directory 
is the current one (using ``os.getcwd()``).

.. code-block:: python 
   :linenos:

    import logging
    import os

    from lazydog.handlers import HighlevelEventHandler

    # LOG    
    # create logger 
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # create console handler with a higher log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(console_handler)

    # INITIALIZE 
    # get dir in parameter else current dir
    watched_dir = directory if len(directory) > 1 else os.getcwd()
    # initializing a new HighlevelEventHandler
    highlevel_handler = HighlevelEventHandler.get_instance(watched_dir)
    # starting it (since it is a thread)
    highlevel_handler.start()
    # log first message
    logging.info('LISTENING EVENTS IN DIR: \'%s\'' % watched_dir)
        
    # OPERATING
    try:
        while True:

            # The following loop check every 1 second if any new event.
            time.sleep(1)
            local_events = highlevel_handler.get_available_events()
            
            # If any, it logs it directly in the console.
            for e in local_events:
                logging.info(e)

        # Keyboard <CTRL+C> interrupts the loop 
        except KeyboardInterrupt:   
            highlevel_handler.stop()


"""

import time
import logging
import os

from lazydog.handlers import HighlevelEventHandler



# this function shows an example of how to use Lazydog.
def logging_in_console(directory:str=''):
    if directory == None:
        directory = ''
    
    # LOG    
    # create logger 
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # create console handler with a higher log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(console_handler)
    
    # INITIALIZE 
    # get dir in parameter else current dir
    watched_dir = directory if len(directory) > 1 else os.getcwd()
    # initializing a new HighlevelEventHandler
    highlevel_handler = HighlevelEventHandler.get_instance(watched_dir)
    # starting it (since it is a thread)
    highlevel_handler.start()
    # log first message
    logging.info('LISTENING EVENTS IN DIR: \'%s\'' % watched_dir)

    try:
        while True:

            # The following loop check every 1 second if any new event.
            time.sleep(1)
            local_events = highlevel_handler.get_available_events()

            # If any, it logs it directly in the console.
            for e in local_events:
                logging.info(e)
                
    # Keyboard <CTRL+C> interrupts the loop 
    except KeyboardInterrupt:   
        highlevel_handler.stop()
    




# this function is the one executed when calling '$ lazydog' in the system console.
def main():
    
    import sys
    directory_to_watch = sys.argv[1] if len(sys.argv) > 1 else None
    logging_in_console(directory_to_watch)
    
    
    
if __name__ == "__main__":
    main()
    