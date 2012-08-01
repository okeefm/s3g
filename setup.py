from distutils.core import setup

import re, os
version = re.search(
        "__version__.*'(.+)'",
        open(os.path.join('s3g', '__init__.py')).read()).group(1)

setup(
    name='pys3g',
    version=version,
    author='MakerBot Industries',
    author_email='matt.mets@makerbot.com',
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
    description='.',
    long_description=open('readme.markdown').read(),
)

