#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
This script is used to kick off a salt syndic daemon
'''

from salt.scripts import salt_syndic
from multiprocessing import freeze_support

if __name__ == '__main__':
    freeze_support()
    salt_syndic()


