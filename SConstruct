# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:syntax=python:ts=4:
#
# Top-level SConstruct file for s3g.
#

import os,sys

AddOption('--test', action='store_true', dest='test')
run_test = GetOption('test')

env = Environment(ENV = os.environ)

if 'win32' == sys.platform:
	env.Command('virtualenv', 'setup.bat', 'setup.bat')
else:
	env.Command('virtualenv', 'setup.sh', './setup.sh')

if run_test:
    if 'win32' == sys.platform:
        env.Command('test', 'test.bat', 'test.bat')
    else: 
        env.Command('test', 'test.sh', 'test.sh')

#if run_test:
#    env.Command('test', 'unit_tests.py', 'python unit_tests.py')
