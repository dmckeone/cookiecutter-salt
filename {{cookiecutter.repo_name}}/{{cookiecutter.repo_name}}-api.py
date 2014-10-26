#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Publish commands to the salt api system from the command line on the master.
'''
try:
    from salt.scripts import salt_api
except ImportError:
    #  Pre-2014.7 did not have the direct salt_api call.
    print "{{ cookiecutter.repo_name }}_api is unavailable in this version of {{ cookiecutter.repo_name }}."
    exit()

from multiprocessing import freeze_support

if __name__ == '__main__':
    freeze_support()
    salt_api()


