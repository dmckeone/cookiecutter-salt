#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import shutil
import sys

from esky import bdist_esky
bdist_esky = bdist_esky  # Silence linter
from frosty import build_includes
from textwrap import dedent

try:
    import salt
    import salt.scripts
except ImportError as e:
    print u"Missing salt package.  Please verify that salt is installed in your Python environment."
    raise

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# ----------------------------------------------------------------------------------------------------------
# Build-Time Constants
# ----------------------------------------------------------------------------------------------------------
# Platform detection (supported platforms taken from salt's setup.py -- v2014.7)
IS_LINUX = sys.platform.startswith("linux")
IS_MAC = sys.platform.startswith("darwin")
IS_SUNOS = sys.platform.startswith("sunos")
IS_WINDOWS = sys.platform.startswith("win")

# Import script descriptions
from descriptions import MAIN_DESCRIPTION, API_DESCRIPTION, CALL_DESCRIPTION, CLOUD_DESCRIPTION, CP_DESCRIPTION, \
    KEY_DESCRIPTION, MASTER_DESCRIPTION, MINION_DESCRIPTION, RUN_DESCRIPTION, SSH_DESCRIPTION, SYNDIC_DESCRIPTION


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

SETUP_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------------------------------------------
# Setup tools project description and requirements
# ----------------------------------------------------------------------------------------------------------
readme = codecs.open(os.path.join(SETUP_DIR, u"README.rst")).read()
requirements = codecs.open(os.path.join(SETUP_DIR, u"requirements.txt")).readlines()

# ----------------------------------------------------------------------------------------------------------
# Script generation groundwork
# ----------------------------------------------------------------------------------------------------------
SCRIPT_TEMPLATE = dedent(u"""\
    #!/usr/bin/env python
    \"\"\"
    {description_section}
    \"\"\"

    from multiprocessing import freeze_support
    {import_section}

    if __name__ == \"__main__\":
        freeze_support()
        {script_section}\
""")


class ScriptFormula(object):
    """
    Container for script template contant
    """

    def __init__(self, import_=None, script=None, description=u""):
        self.import_ = import_
        self.script = script
        self.description = description

# Setup constants for the name of packages (with hard-links for better linting support)
SCRIPTS_NAME = salt.scripts.__name__


class SaltScript(ScriptFormula):
    """
    Container for simple salt scripts that just import the script and execute it.
    """

    def __init__(self, name, script=None, description=None):
        self.name = name
        super(SaltScript, self).__init__(script=script, description=description)

    @property
    def import_(self):
        """
        Returns an import from salt's built-in scripts
        :return:
        """
        return u"from {} import {}".format(SCRIPTS_NAME, self.name)

    @import_.setter
    def import_(self, _):
        """
        Ignore setting the import.
        """

    @property
    def script(self):
        """
        Returns the script as a basic function call
        :return:
        """
        if not self._script:
            return u"{}()".format(self.name)
        else:
            return self._script

    @script.setter
    def script(self, new_script):
        self._script = new_script

# ----------------------------------------------------------------------------------------------------------
# Declare all dynamic salt scripts
# ----------------------------------------------------------------------------------------------------------
# Commons scripts
script_map = {
    u"{{ cookiecutter.salt_prefix }}-cp": SaltScript(
        salt.scripts.salt_cp.__name__,
        description=CP_DESCRIPTION
    )
}

# Determine cookiecutter specified build type
build_type = VENDOR_BUILD_TYPE
if build_type == BUILD_TYPES.DEFAULT:
    if IS_WINDOWS:
        build_type = BUILD_TYPES.MINION_ONLY
    else:
        build_type = BUILD_TYPES.BOTH

# Master specific build scripts
if build_type in (BUILD_TYPES.BOTH, BUILD_TYPES.MASTER_ONLY):
    script_map.update({
        u"{{ cookiecutter.salt_prefix }}": SaltScript(
            salt.scripts.salt_main.__name__,
            description=MAIN_DESCRIPTION
        ),
        u"{{ cookiecutter.salt_prefix }}-cloud": SaltScript(
            salt.scripts.salt_cloud.__name__,
            description=CLOUD_DESCRIPTION
        ),
        u"{{ cookiecutter.salt_prefix }}-key": SaltScript(
            salt.scripts.salt_key.__name__,
            description=KEY_DESCRIPTION
        ),
        u"{{ cookiecutter.salt_prefix }}-master": SaltScript(
            salt.scripts.salt_master.__name__,
            description=MASTER_DESCRIPTION
        ),
        u"{{ cookiecutter.salt_prefix }}-run": SaltScript(
            salt.scripts.salt_run.__name__,
            description=RUN_DESCRIPTION
        ),
        u"{{ cookiecutter.salt_prefix }}-ssh": SaltScript(
            salt.scripts.salt_ssh.__name__,
            description=SSH_DESCRIPTION
        ),
        u"{{ cookiecutter.salt_prefix }}-syndic": SaltScript(
            salt.scripts.salt_syndic.__name__,
            description=SYNDIC_DESCRIPTION
        ),
    })

# Minion specific build scripts
if build_type in (BUILD_TYPES.BOTH, BUILD_TYPES.MINION_ONLY):
    script_map.update({
        u"{{ cookiecutter.salt_prefix }}-call": SaltScript(
            salt.scripts.salt_call.__name__,
            description=CALL_DESCRIPTION
        ),
        u"{{ cookiecutter.salt_prefix }}-minion": SaltScript(
            salt.scripts.salt_minion.__name__,
            description=MINION_DESCRIPTION
        ),
    })

# If requested in the cookiecutter, modify the name of the salt-minion to be just the name of the product.  This has a
# better aesthetic in any kind of process monitor that an end-user (who may have no idea what a 'minion' is) might use.
# The assumption is that the end-user may have a better idea what the vendor's product name is.
if VENDOR_MINION_NAME_MODIFICATION:
    if build_type == BUILD_TYPES.MINION_ONLY:
        # vendor_service-minion -> vendor_service
        script_map[u"{{ cookiecutter.salt_prefix }}"] = script_map[u"{{ cookiecutter.salt_prefix }}-minion"]
        del script_map[u"{{ cookiecutter.salt_prefix }}-minion"]

# Version specific salt scripts
version_parts = salt.__version__.split('.')
salt_major = int(version_parts[0])
salt_minor = int(version_parts[1])

# Added in 2014.7
# ----------------------------------------------------------------------------------------------------------
# Added salt-api to the master
if salt_major > 2014 or (salt_major == 2014 and salt_minor >= 7):
    if build_type in (BUILD_TYPES.BOTH, BUILD_TYPES.MASTER_ONLY):
        script_map[u"{{ cookiecutter.salt_prefix }}-api"] = SaltScript(
            salt.scripts.salt_api.__name__,
            description=API_DESCRIPTION
        )

# ----------------------------------------------------------------------------------------------------------
# Setup all explicitly included packages
# (packages that fail in some way if they are not included with all all of their subpackages/submodules)
# ----------------------------------------------------------------------------------------------------------
required_includes = {
    u"salt",

    u"ast",
    u"asyncore",
    u"Cookie",
    u"difflib",
    u"distutils",
    u"email",
    u"fileinput",
    u"json",
    u"M2Crypto",
    u"numbers",
    u"requests",
    u"sqlite3"
}

optional_includes = {
    u"zmq"
}

if IS_LINUX:
    required_includes |= {
        u"spwd"
    }

    optional_includes |= {
        u"yum"
    }

if IS_SUNOS:
    required_includes |= {
        u"libnacl",
        u"ioflo",
        u"raet",
        u"sodium_grabber"
    }

if IS_WINDOWS:
    required_includes |= {
        u"ntsecuritycon",
        u"psutil",
        u"pywintypes",
        u"pythoncom",
        u"site",
        u"win32api",
        u"win32file",
        u"win32con",
        u"win32com",
        u"win32net",
        u"win32netcon",
        u"win32gui",
        u"win32security",
        u"wmi",
        u"_winreg"
    }

# ----------------------------------------------------------------------------------------------------------
# Create all dynamic scripts
# ----------------------------------------------------------------------------------------------------------
scripts = set()
scripts_dir = os.path.join(SETUP_DIR, u'scripts')
if os.path.exists(scripts_dir):
    raise EnvironmentError(u"Scripts directory should not exist prior to running setup.  Path: {}".format(scripts_dir))

os.mkdir(scripts_dir)
try:
    # Write the actual script content.
    # For nicer debugging, the creation is sorted by script name and the full content of the script is printed.
    for script_name, script_formula in sorted(script_map.iteritems()):
        script_path = os.path.join(scripts_dir, u"{}.py".format(script_name))
        with codecs.open(script_path, u"wb+") as f:
            content = SCRIPT_TEMPLATE.format(import_section=script_formula.import_,
                                             script_section=script_formula.script,
                                             description_section=script_formula.description)
            f.write(content)
            print u"Write Salt script \"{}\":\n{}\n".format(script_path, content)
        scripts.add(script_path)

    # ----------------------------------------------------------------------------------------------------------
    # Run the distutils setup
    # ----------------------------------------------------------------------------------------------------------
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
                    u"includes": build_includes(required_includes, optional=optional_includes)
                },
                u"bundle_msvcrt": True,
                u"enable_appdata_dir": True
            }
        },
    )
finally:
    # Cleanup
    #   Remove the scripts dir (remove the temptation to edit a dynamically generated folder)
    shutil.rmtree(scripts_dir)