#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Start the salt master
'''

from salt.scripts import salt_master
from multiprocessing import freeze_support

if __name__ == '__main__':
    freeze_support()
    salt_master()


