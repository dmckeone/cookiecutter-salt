#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Directly call a salt command in the modules, does not require a running salt minion to run.
'''

from salt.scripts import salt_call
from multiprocessing import freeze_support

if __name__ == '__main__':
    freeze_support()
    salt_call()


