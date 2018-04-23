


# Lazydog

Python module monitoring high-level file system events (Copy, Move, Create, Delete, Modify). Lazydog tries to aggregate low-level events in order to emit a minimum number of high-level events. Lazydog uses python Watchdog module to detect low-level events.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them

```
Give examples
```

### Installing

A step by step series of examples that tell you have to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Test coverage

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

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

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

