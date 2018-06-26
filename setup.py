#!/usr/bin/env python

from setuptools import setup

setup(name='aw-watcher-terminal',
      version='0.1.0',
      description='Terminal watcher for ActivityWatch',
      long_description=('Terminal watcher for ActivityWatch. '
                        'Used in conjunction with shell-specific watchers.'),
      author='A_A',
      author_email='lindrope@hotmail.com',
      url='https://github.com/Otto-AA/aw-watcher-terminal/',
      packages=['aw_watcher_terminal'],
      install_requires=[
          'aw-client(>=0.2.0)',
          'aw-core(>=0.4.1)'
      ],
      classifiers=[
          'Programming Language :: Python :: 3'
      ]
      )
