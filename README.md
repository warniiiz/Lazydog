

# Lazydog

Python module monitoring high-level file system events like Creation, Modification, Move, Copy, and Deletion of files and folders. Lazydog tries to aggregate low-level events between them in order to emit a minimum number of high-level events (actualy one event per user action). Lazydog uses python Watchdog module to detect low-level events.

## Example


### Sample how to use it

Below is an example on how to initialize the high-level lazydog event handler, and log every new event in the console (using logging module). The watched directory is the current one (using ```os.getcwd()```). If you don't want to type all this, you can just launch ```$ lazydog``` command after installing the python package, which does just the same.


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


### Expected results

Where the watchdog module would throw dozen of events after each user event, lazydog only throws one. For example, after launching the previous code (with ```$ lazydog``` to simplify), just move a file in the watched directory (here from '/move_test.txt' to '/move_test_2.txt'), and wait 2 seconds. You will get something like this in the console:

```
$ lazydog /media/maxtor/media/Dropbox
INFO -
INFO - LIST OF THE LAST EVENTS:
INFO - moved: '/move_test.txt' to '/move_test_2.txt' mtime[1512151173.0] size[5] inode[51675246]
INFO -
```

Try to copy the same file:

```
INFO -
INFO - LIST OF THE LAST EVENTS:
INFO - copied: '/move_test_2.txt' to '/move_test_2 - Copie.txt' mtime[1512151173.0] size[5] inode[51675199]
INFO -
```

Only one event per user action. You can try it with other type of action, and also with directories.


## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.


### Prerequisites

Main dependency of lazydog, is the python watchdog API. You can install it using the following command:

```
$ pip3 install watchdog
```

Please read the official documentation for any question about this project: https://pypi.org/project/watchdog/


### Installing development environment

Just clone the repository in your local working directory.

```
$ git clone https://github.com/warniiiz/Lazydog
```

In order to contribute, you will need pytest for testing purpose (or refer to the related documentation https://docs.pytest.org/en/latest/getting-started.html ).

```
$ pip3 install pytest
```

You will also need Sphinx package for documentation purpose (or refer to the related documentation http://www.sphinx-doc.org/en/stable/install.html ).

```
$ apt-get install python-sphinx
```


## Running the tests

You can run the tests either 

### Module testing

The different python module are in the /lazydog directory. Each of them has attached test functions, that are in the /lazydog/test directory. You can launch tests unitary like this (for example for testing the events module):

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

You can also test the whole package:

```
$ pytest
```


### Test coverage

Check the test coverage:

```
$ py.test --cov lazydog
```

Test covergae is > 90%. The metric is not very relevant about the test quality, but at least you will be reasssured there are some tests ;)

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

Please document each change and run the following after each documentation modification:

```
$ cd docs    # first go in the /docs subdirectory.
$ make html  # recompute the sphinx documentation
```

Note that if you did not modify local file from /docs subdirectory, the changes will not be taken... you can use the following command to force recomputing all the changes:

```
$ touch autodoc.rst; make html 
```

Last thing. If you modified the main 'README.md', and you want the changes to appear in the documentation (and not only on github), you have to convert the .md file to a .rst one. You can use the pandoc app to do thiss conversion, using the following command (after installing pandoc https://pandoc.org/installing.html):

```
pandoc --from=markdown --to=rst --output=../README.rst ../README.md     # Assuming you are in the /docs subdirectory.
```

Then don't forget to run the previous command again to recompute the whole documentation.


## Deployment

Add additional notes about how to deploy this on a live system

## Built With



## Contributing

# How to contribute

For `sandman` to be a truly great project, third-party code contributions are
critical. I (@jeffknupp) can only do so much, and I don't have the benefit of
working on `sandman` in a team, where multiple ideas and points-of-view would be
heard. So if you want to enhance `sandman`, spot and fix a bug, or just
generally want to get involved, I'd love the help! Below is a list of things
that might aid you in contributing to `sandman`.

## Getting Started

* Create a new, Python 2.7+ virtualenv and install the requirements via pip: `pip install -r requirements.txt`
* Make sure you have a [GitHub account](https://github.com/signup/free)
* Either sumbit an issue directly on GitHub or head to `sandman's` [Waffle.io](https://waffle.io/jeffknupp/sandman) page
  * For bugs, clearly describe the issue including steps to reproduce
  * For enhancement proposals, be sure to indicate if you're willing to work on implementing the enhancement
* Fork the repository on GitHub

## Making Changes

* `sandman` uses [git-flow](http://nvie.com/posts/a-successful-git-branching-model/) as the git branching model
    * **No commits should be made directly to `master`** 
    * [Install git-flow](https://github.com/nvie/gitflow) and create a `feature` branch like so: `$ git flow feature start <name of your feature>`
* Make commits of logical units.
* Check for unnecessary whitespace with `git diff --check` before committing.
* Make sure you have added the necessary tests for your changes. 
    * Test coverage is currently at 100% and tracked via [coveralls.io](https://coveralls.io/r/jeffknupp/sandman?branch=develop)
    * Aim for 100% coverage on your code
        * If this is not possible, explain why in your commit message
        * This may be an indication that your code should be refactored
    * If you're creating a totaly new feature, create a new class in `test_sandmand.py` that inherits from `TestSandmanBase`
* Run `python setup.py test` to make sure your tests pass
* Run `coverage run --source=sandman setup.py test` if you have the `coverage` package installed to generate coverage data
* Check your coverage by running `coverage report`

## Submitting Changes

* Push your changes to the feature branch in your fork of the repository.
* Submit a pull request to the main repository



# Additional Resources

* [Issue tracker (Waffle.io)](https://waffle.io/jeffknupp/sandman)
* [General GitHub documentation](http://help.github.com/)
* [GitHub pull request documentation](http://help.github.com/send-pull-requests/)





## Versioning and release notes

We use [SemVer](http://semver.org/) for versioning. Please read [RELEASE-NOTES.md](RELEASE-NOTES.md) for details about each releases.



## Authors and contributors

* **Clément Warneys** - *Initial work* - [warniiiz](https://github.com/warniiiz)


## License

This project is licensed under the Apache License Version 2.0. Please see the [LICENSE.md](LICENSE.md) file for details.







# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change. 

Please note we have a code of conduct, please follow it in all your interactions with the project.

## Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a 
   build.
2. Update the README.md with details of changes to the interface, this includes new environment 
   variables, exposed ports, useful file locations and container parameters.
3. Increase the version numbers in any examples files and the README.md to the new version that this
   Pull Request would represent. The versioning scheme we use is [SemVer](http://semver.org/).
4. You may merge the Pull Request in once you have the sign-off of two other developers, or if you 
   do not have permission to do that, you may request the second reviewer to merge it for you.

## Code of Conduct

### Our Pledge

In the interest of fostering an open and welcoming environment, we as
contributors and maintainers pledge to making participation in our project and
our community a harassment-free experience for everyone, regardless of age, body
size, disability, ethnicity, gender identity and expression, level of experience,
nationality, personal appearance, race, religion, or sexual identity and
orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment
include:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints and experiences
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

Examples of unacceptable behavior by participants include:

* The use of sexualized language or imagery and unwelcome sexual attention or
advances
* Trolling, insulting/derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or electronic
  address, without explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

### Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable
behavior and are expected to take appropriate and fair corrective action in
response to any instances of unacceptable behavior.

Project maintainers have the right and responsibility to remove, edit, or
reject comments, commits, code, wiki edits, issues, and other contributions
that are not aligned to this Code of Conduct, or to ban temporarily or
permanently any contributor for other behaviors that they deem inappropriate,
threatening, offensive, or harmful.

### Scope

This Code of Conduct applies both within project spaces and in public spaces
when an individual is representing the project or its community. Examples of
representing a project or community include using an official project e-mail
address, posting via an official social media account, or acting as an appointed
representative at an online or offline event. Representation of a project may be
further defined and clarified by project maintainers.

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported by contacting the project team at [INSERT EMAIL ADDRESS]. All
complaints will be reviewed and investigated and will result in a response that
is deemed necessary and appropriate to the circumstances. The project team is
obligated to maintain confidentiality with regard to the reporter of an incident.
Further details of specific enforcement policies may be posted separately.

Project maintainers who do not follow or enforce the Code of Conduct in good
faith may face temporary or permanent repercussions as determined by other
members of the project's leadership.

### Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage], version 1.4,
available at [http://contributor-covenant.org/version/1/4][version]




# Lazydog

Python module monitoring high-level file system events like Creation, Modification, Move, Copy, and Deletion of a file or folder. Lazydog tries to aggregate low-level events between them in order to emit a minimum number of high-level events. Lazydog uses python Watchdog module to detect low-level events.



## Test coverage



## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Acknowledgments

* Hat tip to anyone who's code was used
* Inspiration
* etc



When finished, please see http://pandoc.org/ to convert from .md to .rst and include it to setup.py file.
Test


# Configuration of inotify...

Listen uses inotify by default on Linux to monitor directories for changes. It's not uncommon to encounter a system limit on the number of files you can monitor. For example, Ubuntu Lucid's (64bit) inotify limit is set to 8192.
 
You can get your current inotify file watch limit by executing:
 
$ cat /proc/sys/fs/inotify/max_user_watches
When this limit is not enough to monitor all files inside a directory, the limit must be increased for Listen to work properly.
 
You can set a new limit temporary with:
 
$ sudo sysctl fs.inotify.max_user_watches=524288
$ sudo sysctl -p
If you like to make your limit permanent, use:
 
$ echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
$ sudo sysctl -p




# Special thanks

## General guidelines:

Thanks to Jeff Knupp for this general guidelines for open sourcing a python project (which helped me a lot since it is my first open source project I deliver):
https://jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/

REMEMBER: This file should contain the following pieces of information: 
* A description of your project
* Links to the project's ReadTheDocs page
* A TravisCI button showing the state of the build
* "Quickstart" documentation (how to quickly install and use your project)
* A list of non-Python dependencies (if any) and how to install them

