# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:syntax=python:ts=4:
#
# Top-level SConstruct file for s3g.
#

import os,sys

AddOption('--test', action='store_true', dest='test')
run_test = GetOption('test')

env = Environment(ENV = os.environ)

if 'win32' == sys.platform:
	vcmd=env.Command('virtualenv', 'setup.bat', 'setup.bat')
else:
	vcmd=env.Command('virtualenv', 'setup.sh', './setup.sh')

env.Clean(vcmd,'virtualenv')

if run_test:
    if 'win32' == sys.platform:
        env.Command('test', 'test.bat', 'test.bat')
    else: 
        env.Command('test', 'test.sh', 'test.sh')

path_to_avrdude = os.path.join(
    'makerbot_driver',
    'Firmware',
    'avrdude',
    )

env.Command(path_to_avrdude, vcmd, 'python copy_avrdude.py')

#if run_test:
#    env.Command('test', 'unit_tests.py', 'python unit_tests.py')
