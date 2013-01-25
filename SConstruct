# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:syntax=python:ts=4:
#
# Top-level SConstruct file for s3g.
#

import os,sys

AddOption('--test', action='store_true', dest='test')
run_test = GetOption('test')

#not used, added for consistency
AddOption('--debug_build', action='store_true', dest='debug_build')
debug = GetOption('debug_build')

env = Environment(ENV = os.environ)

env.Tool('mb_install', toolpath=[Dir('submodule/mw-scons-tools')])

driver_src = []
src_str = '#/makerbot_driver'

for curpath, dirnames, filenames in os.walk(str(Dir(src_str))):
    driver_src.append(filter(lambda f:
                                 (os.path.exists(str(f)) and
                                  not os.path.isdir(str(f))),
                             env.Glob(os.path.join(curpath, '*.py'))))

if env.MBIsWindows():
    vcmd=env.Command('virtualenv', 'setup.bat', 'setup.bat')
else:
    vcmd=env.Command('virtualenv', 'setup.sh', './setup.sh')

env.Clean(vcmd,'virtualenv')

if run_test:
    if env.MBIsWindows():
        env.Command('test', 'test.bat', 'test.bat')
    else: 
        env.Command('test', 'test.sh', 'test.sh')

path_to_avrdude = os.path.join(
    'makerbot_driver',
    'Firmware',
    'avrdude',
    )

env.Command(path_to_avrdude, vcmd, 'python copy_avrdude.py')

if env.MBIsWindows():
    pycmd = 'virtualenv\\Scripts\\python'
else:
    pycmd = 'virtualenv/bin/python'

s3g_egg = env.Command('dist/makerbot_driver-0.1.1-py2.7.egg',
                      driver_src + [vcmd],
                      pycmd + ' -c "import setuptools; execfile(\'setup.py\')" bdist_egg')

env.MBInstallEgg(s3g_egg)

if env.MBIsWindows():
    env.MBInstallResources('#\makerbot_driver\EEPROM', 's3g')
    env.MBInstallResources('#\makerbot_driver\profiles', 's3g')

env.MBCreateInstallTarget()

#if run_test:
#    env.Command('test', 'unit_tests.py', 'python unit_tests.py')
