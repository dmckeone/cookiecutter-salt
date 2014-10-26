#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Start the salt minion
'''

from salt.scripts import salt_minion
from multiprocessing import freeze_support

if __name__ == '__main__':
    freeze_support()
    salt_minion()


