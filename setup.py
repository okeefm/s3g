#Setup.py based on pyserial/pyserial/setup.py

import sys

from distutils.core import setup


if sys.version_info < (2,6):
	raise ValueError("Sorry, python versions older than 2.6"	
					" are not supported")
elif sys.version_info >= (3, 0):
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

import re, os
version = re.search(
        "__version__.*'(.+)'",
        open(os.path.join('s3g', '__init__.py')).read()).group(1)


setup(
    name='pys3g' + suffix, 
    version=version,
    author='MakerBot Industries',
    author_email='matt.mets@makerbot.com',
    packages=['s3g', 's3g.tests'],
    url='http://github.com/makerbot/s3g',
    license='COPYING.txt',
    description='3d printer drivers in python, by MakerBot',
    long_description=open('README.md').read(),
	#classifiers = []
	platforms = 'any',
	#cmdclass = { ? : ? }
	#scripts = ['/scripts/file']
)

