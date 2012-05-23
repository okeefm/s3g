from distutils.core import setup

setup(
    name='pys3g',
    version='0.1.0',
    author='MakerBot Industries',
    author_email='matt.mets@makerbot.com',
    packages=['s3g', 's3g.test'],
    url='http://github.com/makerbot/s3g',
    license='LICENSE.txt',
    description='.',
    long_description=open('readme.markdown').read(),
)

