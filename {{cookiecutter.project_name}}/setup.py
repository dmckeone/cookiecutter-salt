#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import collections
import os
import re
import shutil
import sys

# Import esky freezer
from esky import bdist_esky

try:
    import salt
    import salt.scripts
except ImportError as e:
    print u"Missing Salt.  Please verify that salt is installed in your Python environment.  Error: {}".format(e)
    exit()

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Common Imports
try:
    import ast
    import difflib
    import distutils
    import numbers
    import json
    import M2Crypto
    import Cookie
    import asyncore
    import fileinput
    import sqlite3
    import email
    import requests
except ImportError as e:
    msg = (
        u"Missing Salt dependency.  Please verify if you are missing a dependency in your Python environment, or "
        u"if a recent version of Salt has new dependencies that are not included in this script.  Error: {error}"
    )
    print msg.format(error=e)
    exit()

try:
    import zmq
    HAS_ZMQ = True
except ImportError:
    zmq = None
    HAS_ZMQ = False

# Platform detection
IS_LINUX = sys.platform.startswith("linux")
IS_MAC = sys.platform.startswith("darwin")
IS_SUNOS = sys.platform.startswith("sunos")
IS_WINDOWS = sys.platform.startswith("win")

# Linux Only Imports
if IS_LINUX:
    try:
        import yum
    except ImportError:
        pass

    try:
        import spwd
    except ImportError as e:
        msg = (
            u"Missing Linux specific Salt dependency.  Please verify if you are missing a dependency in your "
            u"Python environment, or if a recent version of Salt has new dependencies that are not included in "
            u"this script.  Error: {error}"
        )
        print msg.format(error=e)
        exit()

# SunOS Only Imports
if IS_SUNOS:
    try:
        import sodium_grabber
        import ioflo
        import raet
        import libnacl
    except ImportError as e:
        msg = (
            u"Missing SunOS specific Salt dependency.  Please verify if you are missing a dependency in your "
            u"Python environment, or if a recent version of Salt has new dependencies that are not included in "
            u"this script.  Error: {error}"
        )
        print msg.format(error=e)
        exit()

# Windows Only Imports
if IS_WINDOWS:
    try:
        import win32api
        import win32file
        import win32con
        import win32com
        import win32net
        import win32netcon
        import win32gui
        import win32security
        import ntsecuritycon
        import pywintypes
        import pythoncom
        import _winreg
        import wmi
        import site
        import psutil
    except ImportError as e:
        msg = (
            u"Missing Windows specific Salt dependency.  Please verify if you are missing a dependency in your "
            u"Python environment, or if a recent version of Salt has new dependencies that are not included in "
            u"this script.  Error: {error}"
        )
        print msg.format(error=e)
        exit()


# Import script descriptions
from descriptions import MAIN_DESCRIPTION, API_DESCRIPTION, CALL_DESCRIPTION, CLOUD_DESCRIPTION, CP_DESCRIPTION, \
    KEY_DESCRIPTION, MASTER_DESCRIPTION, MINION_DESCRIPTION, RUN_DESCRIPTION, SSH_DESCRIPTION, SYNDIC_DESCRIPTION

SETUP_DIR = os.path.dirname(os.path.abspath(__file__))

class BUILD_TYPES(object):
    """ All valid build types """
    DEFAULT = u"default"
    BOTH = u"both"
    MINION_ONLY = u"minion"
    MASTER_ONLY = u"master"
    ALL = frozenset([DEFAULT, BOTH, MINION_ONLY, MASTER_ONLY])


VENDOR_PREFIX = u"{{ cookiecutter.salt_prefix }}".strip()
VENDOR_BUILD_TYPE = u"{{ cookiecutter.build_type }}".strip().lower()
VENDOR_MINION_NAME_MODIFICATION = bool(u"{{ cookiecutter.modify_minion_name }}".strip())
if VENDOR_BUILD_TYPE not in BUILD_TYPES.ALL:
    error_description = u"Incorrect build type used in CookieCutter generation.  Valid options are: {}"
    valid_build_types = u", ".join(BUILD_TYPES.ALL)
    raise ValueError(error_description.format(valid_build_types))

SCRIPT_TEMPLATE = u"""
#!/usr/bin/env python
\"\"\"
{description}
\"\"\"

from salt.scripts import {salt_script}
from multiprocessing import freeze_support

if __name__ == "__main__":
    freeze_support()
    {salt_script}()
"""

readme = codecs.open(os.path.join(SETUP_DIR, u"README.rst")).read()
requirements = codecs.open(os.path.join(SETUP_DIR, u"requirements.txt")).readlines()


class SaltScript(object):
    """
    Container for SaltScript information
    """
    def __init__(self, salt_script, description=u""):
        self.salt_script = salt_script
        self.description = description


build_type = VENDOR_BUILD_TYPE
if build_type == BUILD_TYPES.DEFAULT:
    if IS_WINDOWS:
        build_type = BUILD_TYPES.MINION_ONLY
    else:
        build_type = BUILD_TYPES.BOTH

# Setup all salt scripts

#   Commons scripts
script_map = {
    u"{{ cookiecutter.salt_prefix }}-cp": SaltScript(salt.scripts.salt_cp.__name__, CP_DESCRIPTION),
}

#   Master build scripts
if build_type in (BUILD_TYPES.BOTH, BUILD_TYPES.MASTER_ONLY):
    script_map.update({
        u"{{ cookiecutter.salt_prefix }}": SaltScript(salt.scripts.salt_main.__name__, MAIN_DESCRIPTION),
        u"{{ cookiecutter.salt_prefix }}-cloud": SaltScript(salt.scripts.salt_cloud.__name__, CLOUD_DESCRIPTION),
        u"{{ cookiecutter.salt_prefix }}-key": SaltScript(salt.scripts.salt_key.__name__, KEY_DESCRIPTION),
        u"{{ cookiecutter.salt_prefix }}-master": SaltScript(salt.scripts.salt_master.__name__, MASTER_DESCRIPTION),
        u"{{ cookiecutter.salt_prefix }}-run": SaltScript(salt.scripts.salt_run.__name__, RUN_DESCRIPTION),
        u"{{ cookiecutter.salt_prefix }}-ssh": SaltScript(salt.scripts.salt_ssh.__name__, SSH_DESCRIPTION),
        u"{{ cookiecutter.salt_prefix }}-syndic": SaltScript(salt.scripts.salt_syndic.__name__, SYNDIC_DESCRIPTION),
    })

#   Minion build scripts
if build_type in (BUILD_TYPES.BOTH, BUILD_TYPES.MINION_ONLY):
    script_map.update({
        u"{{ cookiecutter.salt_prefix }}-call": SaltScript(salt.scripts.salt_call.__name__, CALL_DESCRIPTION),
        u"{{ cookiecutter.salt_prefix }}-minion": SaltScript(salt.scripts.salt_minion.__name__, MINION_DESCRIPTION),
    })

# If requested, modify the name of the salt-minion to be just the name of the product.  This has a better aesthetic
# in any kind of process monitor for the end-user who has no idea what a 'minion' is, but should know the name of the
# vendors product.
if VENDOR_MINION_NAME_MODIFICATION:
    if build_type == BUILD_TYPES.MINION_ONLY:
        # vendor_service-minion -> vendor_service
        script_map[u"{{ cookiecutter.salt_prefix }}"] = script_map[u"{{ cookiecutter.salt_prefix }}-minion"]
        del script_map[u"{{ cookiecutter.salt_prefix }}-minion"]

# Version specific scripts
version_parts = salt.__version__.split('.')
major = version_parts[0]
minor = version_parts[1]

# Added salt-api to the master in version 2014.7
if major > 2014 or (major == 2014 and minor >= 7):
    if build_type in (BUILD_TYPES.BOTH, BUILD_TYPES.MASTER_ONLY):
        script_map[u"{{ cookiecutter.salt_prefix }}-api"] = SaltScript(u"salt_api", API_DESCRIPTION)

# Create sets of all modules/packages that must be explicitly included in the freezing process.
# Note: These are modules/packages, and not strings. (They are converted to strings later)
basic_freezer_includes = {
    salt,

    ast,
    asyncore,
    Cookie,
    difflib,
    distutils,
    distutils,
    email,
    fileinput,
    json,
    M2Crypto,
    numbers,
    requests,
    sqlite3
}

if HAS_ZMQ:
    basic_freezer_includes.add(zmq)

if IS_LINUX:
    basic_freezer_includes.add(spwd)
    # Yum not available on all flavors of Linux  (See conditional import above)
    if globals()['yum']:
        basic_freezer_includes.add(yum)

if IS_SUNOS:
    basic_freezer_includes |= {
        libnacl,
        ioflo,
        raet,
        sodium_grabber
    }

if IS_WINDOWS:
    basic_freezer_includes |= {
        ntsecuritycon,
        psutil,
        pywintypes,
        pythoncom,
        site,
        win32api,
        win32file,
        win32con,
        win32com,
        win32net,
        win32netcon,
        win32gui,
        win32security,
        wmi,
        _winreg
    }

# Split up all freezer includes into lists of packages
package_root_paths = {os.path.abspath(package.__file__): package.__name__ for package in basic_freezer_includes}
prefix = os.path.commonprefix(package_root_paths)
all_freezer_modules = set()
for package_path, package_name in package_root_paths.iteritems():
    all_freezer_modules.add(package_name)
    if re.search('__init__.py.*$', package_path):
        # Looks like a package.  Walk the directory and see if there are more.
        package_modules = set()
        for root, dirs, files in os.walk(os.path.dirname(package_path)):
            if u'__init__.py' in files:
                package_modules.add(root)
                for module in [f for f in files if f != "__init__.py" and f.endswith('.py')]:
                    package_modules.add(os.path.join(root, module))

        common_prefix = os.path.commonprefix(package_modules)
        common_dir = os.path.dirname(common_prefix)
        package_tails = {f[len(common_dir) + len(os.sep):] for f in package_modules}
        package_names = {tail.replace(os.sep, '.') for tail in package_tails}
        all_freezer_modules |= package_names

# Create all specified scripts (removes any previous scripts)
scripts = set()
scripts_dir = os.path.join(SETUP_DIR, u'scripts')
if os.path.exists(scripts_dir):
    raise EnvironmentError(u"Scripts directory should not exist prior to running setup.  Path: {}".format(scripts_dir))

os.mkdir(scripts_dir)
for script_name, script_formula in script_map.iteritems():
    script_path = os.path.join(scripts_dir, u"{}.py".format(script_name))
    print u"Creating Salt script {}".format(script_path)
    with codecs.open(script_path, u"wb+") as f:
        f.write(SCRIPT_TEMPLATE.format(
            salt_script=script_formula.salt_script,
            description=script_formula.description
        ))
    scripts.add(script_path)

# Run the distutils setup
setup(
    name=u"{{ cookiecutter.project_name }}",
    version=salt.__version__,
    description=u"{{ cookiecutter.project_short_description }}",
    long_description=readme + '\n\n',
    author=u"{{ cookiecutter.author_name }}",
    author_email=u"{{ cookiecutter.author_email }}",
    url=u"{{ cookiecutter.project_url }}",
    scripts=scripts,
    include_package_data=True,
    install_requires=requirements,
    license=u"BSD",
    zip_safe=False,
    options={
        u"bdist_esky": {
            u"freezer_options": {
                u"includes": all_freezer_modules
            },
            u"bundle_msvcrt": True,
            u"enable_appdata_dir": True
        }
    },
)

# Cleanup
#   Remove the scripts dir (remove the temptation to edit a dynamically generated folder)
shutil.rmtree(scripts_dir)