#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Execute a salt convenience routine
'''

from salt.scripts import salt_run
from multiprocessing import freeze_support

if __name__ == '__main__':
    freeze_support()
    salt_run()


