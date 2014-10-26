#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Publish commands to the salt system from the command line on the master.
'''

from salt.scripts import salt_cp
from multiprocessing import freeze_support

if __name__ == '__main__':
    freeze_support()
    salt_cp()


