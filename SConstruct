#
# Top-level SConstruct file for s3g.
#

AddOption('--test', action='store_true', dest='test')
run_test = GetOption('test')

env = Environment()

#disabled until setup.py works
#env.Command('build', 'setup.py', 'python setup.py')

if run_test:
    env.Command('test', 'unit_tests.py', 'python unit_tests.py')
