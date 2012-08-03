# setup.py for pySerial
#
# Windows installer:
#   "python setup.py bdist_wininst"
#
# Direct install (all systems):
#   "python setup.py install"
#
# For Python 3.x use the corresponding Python executable,
# e.g. "python3 setup.py ..."
import sys

from distutils.core import setup

import re, os
if sys.version_info >= (3, 0):
    try:
        from distutils.command.build_py import build_py_2to3 as build_py
        from distutils.command.build_scripts import build_scripts_2to3 as build_scripts
    except ImportError:
        raise ImportError("build_py_2to3 not found in distutils - it is required for Python 3.x")
    suffix = "-py3k"
else:
    from distutils.command.build_py import build_py
    from distutils.command.build_scripts import build_scripts
    suffix = ""



if sys.version < '2.6':
    # distutils that old can't cope with the "classifiers" or "download_url"
    # keywords and True/False constants and basestring are missing
    raise ValueError("Sorry Python versions older than 2.6 are not "
                     "supported. Sadly we will probably never support them :(")

if sys.version >= '2.6' and sys.version < '3.0':
  import s3g 
  version = s3g.__version__

elif sys.version >= 3.0:
  import re, os
  version = re.search(
        "__version__.*'(.+)'",
        open(os.path.join('s3g', '__init__.py')).read()).group(1)



setup(
    name='s3g' + suffix,
    version=version,
    author= ['Matt Mets','David Sayles (MBI)','Far McKon (MBI)'],
    author_email=['cibomahto@gmail.com','david.sayles@makerbot.com','far@makerbot.com'],
    packages=[
        's3g',
        's3g.Encoder',
        's3g.FileReader',
        's3g.Firmware',
        's3g.Gcode',
        's3g.Preprocessors',
        's3g.Writer'
    ],
    url='http://github.com/makerbot/s3g',
    license='LICENSE.txt',
    description='Python driver to connect to 3D Printers which use the s3g protocol',
    long_description=open('README.md').read(),
	platforms = 'any',
)

