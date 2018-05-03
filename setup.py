#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Created on 17 janv. 2018

@author: Clement Warneys <clement.warneys@gmail.com>
'''

from __future__ import print_function
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

import io
import codecs
import os
import sys

import lazydog

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = 'Python module monitoring high-level file system events ' + \
                   'like Creation, Modification, Move, Copy, and Deletion of ' + \
                   'files and folders. Lazydog tries to aggregate low-level ' + \
                   'events between them in order to emit a minimum number of ' + \
                   'high-level events (actualy one event per user action). ' + \
                   'Lazydog uses python Watchdog module to detect low-level events.'

class PyTest(TestCommand):
    
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='lazydog',
    version=lazydog.__version__,
    url='http://github.com/warniiiz/lazydog/',
    license='Apache Software License',
    author='Clément Warneys',
    author_email='clement.warneys@gmail.com',

    python_requires='>=3.5',
    tests_require=['pytest'],
    
    #===========================================================================
    # # How to know current version on your system?
    # import pip
    # for x in pip.get_installed_distributions(): print(x)
    #===========================================================================
    
    install_requires=['watchdog>=0.8.3',
                    ],
    cmdclass={'test': PyTest},
    description='User-level filesystem event observer',

    long_description=long_description,
    keywords='python watchdog inotify monitoring watcher observer file filesystem filesystem-events copy move create delete modify detect',

    project_urls={
        'Documentation': 'http://lazydog.readthedocs.io/',
        'Source': 'https://github.com/warniiiz/lazydog',
    },

    packages=['lazydog', 'lazydog.revised_watchdog', 'lazydog.revised_watchdog.observers'],
    include_package_data=True,
    platforms='any',
    test_suite='lazydog.test',
    classifiers = [
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Filesystems',
        'Topic :: Desktop Environment :: File Managers',
        'Topic :: Security',
        'Topic :: Software Development :: Libraries :: Python Modules'
        ],

    entry_points = {
        'console_scripts': ['lazydog=lazydog.lazydog:main'],
    },
    extras_require={
        'testing': ['pytest'],
    }
)




