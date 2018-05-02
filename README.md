

# Lazydog

Python module monitoring user-level file system events like Creation, Modification, Move, Copy, and Deletion of files and folders. Lazydog tries to aggregate low-level events between them in order to emit a minimum number of high-level events (actually one event per user action). Lazydog uses python Watchdog API to detect low-level events.


## Getting Started

### How to install it

The easiest way:

```
$ pip3 install lazydog
```



### How to use it

Where the watchdog module would throw dozen of events after each user event, lazydog only throws one. For example, ask lazidog to watch any existing directory:

```
$ lazydog /the/directory/you/want/to/watch
```

And just move a file in the watched directory (here from `/watched/directory/move_test.txt` to ```/watched/directory/move_test_2.txt```), and wait 2 seconds. You will get something like this in the console:

```
INFO -
INFO - LIST OF THE LAST EVENTS:
INFO - moved: '/move_test.txt' to '/move_test_2.txt' mtime[1512151173.0] size[5] inode[51675246]
INFO -
```

Try to copy the same file, and you will get somthiing like this:

```
INFO -
INFO - LIST OF THE LAST EVENTS:
INFO - copied: '/move_test_2.txt' to '/move_test_2 - Copie.txt' mtime[1512151173.0] size[5] inode[51675199]
INFO -
```

Only one event per user action. You can try it with other type of action (Deletion, Creation, Modification), and also with directories.


### How to use in in third-part apps

Below is an example on how to rapidly initialize the high-level lazydog event handler, 
and log every new event in the console (using logging module). 
The watched directory is the current one (using ```os.getcwd()```). 

Please note that once installed, using the ```$ lazydog``` command in the console
does just the same.

```python 

import logging
import os

from lazydog.handlers import HighlevelEventHandler

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

# INITIALIZE 
# get dir in parameter else current dir
watched_dir = directory if len(directory) > 1 else os.getcwd()
# initializing a new HighlevelEventHandler
highlevel_handler = HighlevelEventHandler.get_instance(watched_dir)
# starting it (since it is a thread)
highlevel_handler.start()
    
# OPERATING
try:
    while True:

        # The following loop check every 1 second if any new event.
        time.sleep(1)
        local_events = highlevel_handler.get_available_events()
        
        # If any, it logs it directly in the console.
        if len(local_events) > 0:
            logging.info('')
            logging.info('LIST OF THE LAST EVENTS: ')
        for e in local_events:
            logging.info(e)
        
        if len(local_events) > 0:
            logging.info('')

    # Keyboard <CTRL+C> interrupts the loop 
    except KeyboardInterrupt:   
        highlevel_handler.stop()

```


### Getting further

Please find full code documentation in an HTML format on ReadTheDocs.org: http://lazydog.readthedocs.io/


### Miscellaneous...

Watchdog uses inotify by default on Linux to monitor directories for changes. It's not uncommon to encounter a system limit on the number of files you can monitor (for example 8192 directories). You can get your current inotify file watch limit by executing:
 
```
$ cat /proc/sys/fs/inotify/max_user_watches
8192
```

When this limit is not enough to monitor all files inside a directory, the limit must be increased for Lazydog to work properly. You can set a new limit temporary with:
 
```
$ sudo sysctl fs.inotify.max_user_watches=524288
$ sudo sysctl -p
```

If you like to make your limit permanent, use:

``` 
$ echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
$ sudo sysctl -p
```



## Get it installed, the contributor way

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. 


### Prerequisites

Main dependency of lazydog, is the python watchdog API. You can install it using the following command:

```
$ pip3 install watchdog
```

Please read the official documentation for any question about this project: https://pypi.org/project/watchdog/


### Installing development environment

Just clone the repository in your local working directory (or fork it).

```
$ git clone https://github.com/warniiiz/Lazydog
```

In order to contribute, you will need pytest for testing purpose (or refer to the [pytest documentation](https://docs.pytest.org/en/latest/getting-started.html) ).

```
$ pip3 install pytest
```

You will also need Sphinx package for documentation purpose (or refer to the [Sphinx documentation](http://www.sphinx-doc.org/en/stable/install.html) ).

```
$ apt-get install python-sphinx
```



## Tests

### Module testing

The different python module are in the ```/lazydog``` directory. Each of them has attached test functions, that are in the ```/lazydog/test``` directory. You can launch tests unitary like this (for example for testing the events module):

```
$ pytest lazydog/test/test_events.py
```

Kind of results:

```
================================= test session starts =================================
platform linux -- Python 3.4.2, pytest-3.5.0, py-1.5.3, pluggy-0.6.0
rootdir: /media/maxtor/media/Python/Lazydog, inifile:
plugins: cov-2.5.1
collected 16 items

lazydog/test/test_events.py ................                                    [100%]

============================== 16 passed in 0.51 seconds ==============================
```

You can also test the whole package (assuming you are in the developpement directory):

```
$ pytest
```


### Test coverage

Check the test coverage:

```
$ py.test --cov lazydog
```

Test coverage is > 90%. The metric is not very relevant about the test quality, but at least you will be reasssured there are some tests ;)

```
========================== test session starts ===========================
platform linux -- Python 3.4.2, pytest-3.5.0, py-1.5.3, pluggy-0.6.0
rootdir: /media/maxtor/media/Python/Lazydog, inifile:
plugins: cov-2.5.1
collected 58 items

lazydog/test/test_events.py ................                        [ 27%]
lazydog/test/test_handlers.py ......................                [ 65%]
lazydog/test/test_queues.py ..                                      [ 68%]
lazydog/test/test_states.py ..................                      [100%]

----------- coverage: platform linux, python 3.4.2-final-0 -----------
Name                                                   Stmts   Miss  Cover
--------------------------------------------------------------------------
lazydog/__init__.py                                        0      0   100%
lazydog/dropbox_content_hasher.py                         66     14    79%
lazydog/events.py                                        249      7    97%
lazydog/handlers.py                                      214     29    86%
lazydog/lazydog.py                                        39     39     0%
lazydog/queues.py                                         18      0   100%
lazydog/revised_watchdog/__init__.py                       0      0   100%
lazydog/revised_watchdog/events.py                        31      1    97%
lazydog/revised_watchdog/observers/__init__.py             0      0   100%
lazydog/revised_watchdog/observers/inotify.py             49      6    88%
lazydog/revised_watchdog/observers/inotify_buffer.py      12      0   100%
lazydog/revised_watchdog/observers/inotify_c.py           72     22    69%
lazydog/states.py                                        109      1    99%
lazydog/test/test_events.py                              261      2    99%
lazydog/test/test_handlers.py                            355      3    99%
lazydog/test/test_queues.py                               31      0   100%
lazydog/test/test_states.py                              172      0   100%
--------------------------------------------------------------------------
TOTAL                                                   1678    124    93%

====================== 58 passed in 30.15 seconds ========================
```


## Documentation

### Full code documentation

Please find full code documentation in an HTML format on ReadTheDocs.org: http://lazydog.readthedocs.io/ 

This documentation is automatically updated each time an update is made no GitHub.


### Maintaining documentation up-to-date

Please document each change. If you want to check the result before publishing, you can run the following after each documentation modification:

```
$ cd docs    # first go in the /docs subdirectory.
$ make html  # recompute the sphinx documentation
```

The resulted documentation is then in the local relative folder ```/docs/_build/html/index.html```.

Note that if you did not modify local file from ```/docs``` subdirectory, the changes will not be taken... you can use the following command to force recomputing all the changes:

```
$ touch autodoc.rst; make html 
```

Last thing. If you modified the main ```README.md```, and you want the changes to appear in the documentation (and not only on github), you have to convert the .md file to a .rst one. You can use the pandoc app to do thiss conversion, using the following command (after installing Pandoc, please refer to [Pandoc documentation](https://pandoc.org/installing.html) for more information):

```
pandoc --from=markdown --to=rst --output=README.rst ../README.md     # Assuming you are in the /docs subdirectory.
```

Then don't forget to run the previous command again to recompute the whole documentation.




## Contributing

For **lazydog** to be a truly great project, third-party code contributions are
important. If you want to enhance lazydog, spot bugs or fix them, or 
just ask for new enhancements, you are so much welcome! Below is a list of things
that might help you in contributing to lazydog.


### Check the current issues 

The list of the current bugs, issues, new enhancement proposals, etc. are all grouped on GitHub Issues' tab:

* [Issue tracker](https://github.com/warniiiz/Lazydog/issues)

For more information about GitHub, please check the followings:

* [General GitHub documentation](http://help.github.com/)
* [GitHub pull request documentation](http://help.github.com/send-pull-requests/)


### Getting Started

To get involved in code enhancement:

* Make sure you have a [GitHub account](https://github.com/signup/free)
* Get the latest version, by either way cloning of forking this repository (depending on what you want to do)
* Install the requirements via pip: `pip install -r requirements.txt`
* Submit an issue directly on GitHub:
   * For bugs, clearly describe the issue including steps to reproduce
   * For enhancement proposals, be sure to indicate if you're willing to work on implementing the enhancement

*If you do not have GitHub account and you just want to notify for a new bug, please report me by e-mail.*

### Making Changes

[comment]: # (`lazydog` uses [git-flow] http://nvie.com/posts/a-successful-git-branching-model/ as the git branching model
              **No commits should be made directly to `master`** 
              [Install git-flow] https://github.com/nvie/gitflow and create a `feature` branch like so: `$ git flow feature start <name of your feature>`)

* `lazydog` does not use any git Workflow until now. This will remains until the volume of changes and contribution needs a clearer workflow.
* Make commits of logical units.
* Check for unnecessary whitespace with `git diff --check` before committing.
* Make sure you have added the necessary tests for your changes. 
* Run `python setup.py test` to make sure your tests pass
* Run `coverage run --source=lazydog setup.py test` if you have the `coverage` package installed to generate coverage data
* Check your coverage by running `coverage report`
* Please correctly document the code you wrote, and ensure it is readable once HTML generated
* Update main documentation files (README.md, etc.) when necessary.

### Submitting Changes

* Push your changes to the feature branch in your fork of the repository.
* Submit a pull request to the main repository



## Versioning and release notes

We use [SemVer](http://semver.org/) for versioning. Please read [RELEASE-NOTES.md](https://github.com/warniiiz/Lazydog/blob/master/RELEASE-NOTES.md) for details about each releases.



## Authors and contributors

* **Clément Warneys** - *Initial work* - [warniiiz](https://github.com/warniiiz)



## License

This project is licensed under the Apache License Version 2.0. Please see the [LICENSE.md](https://github.com/warniiiz/Lazydog/blob/master/LICENSE.md) file for details.



## Special thanks

Thanks to Jeff Knupp for this [general guidelines for open sourcing a python project](https://jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/) (which helped me a lot since it is my first open source project I deliver):



