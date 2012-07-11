from distutils.core import setup

setup(
    name='pys3g',
    version='0.5.0-Beta',
    author='MakerBot Industries',
    author_email='matt.mets@makerbot.com',
    packages=['s3g', 's3g.test'],
    url='http://github.com/makerbot/s3g',
    license='COPYING.txt',
    description='3d printer drivers in python, by MakerBot',
    long_description=open('README.md').read(),
)

