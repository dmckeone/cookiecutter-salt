#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Manage the authentication keys with salt
'''

from salt.scripts import salt_key
from multiprocessing import freeze_support

if __name__ == '__main__':
    freeze_support()
    salt_key()


