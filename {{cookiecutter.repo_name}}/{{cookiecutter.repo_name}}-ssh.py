#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Execute the salt ssh system
'''

from salt.scripts import salt_ssh
from multiprocessing import freeze_support

if __name__ == '__main__':
    freeze_support()
    salt_ssh()


