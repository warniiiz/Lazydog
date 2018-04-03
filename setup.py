'''
Created on 17 janv. 2018

@author: Clément Warneys <clement.warneys@gmail.com>
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

long_description = read('README.txt', 'CHANGES.txt')

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
    tests_require=['pytest'],
    
    #===========================================================================
    # # How to know current version on your system?
    # import pip
    # for x in pip.get_installed_distributions(): print(x)
    #===========================================================================
    install_requires=['watchdog>=0.8.3',
                    ],
    cmdclass={'test': PyTest},
    author_email='clement.warneys@gmail.com',
    description='High-level disk event observer',
    long_description=long_description,
    packages=['lazydog'],
    include_package_data=True,
    platforms='any',
    test_suite='lazydog.test.test_lazydog',
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        ],
    entry_points = {
        'console_scripts': ['lazydog=lazydog.lazydog:main'],
    },
    extras_require={
        'testing': ['pytest'],
    }
)




