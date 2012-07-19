#!/usr/bin/python
"""
Runs tests in the form of ./tests/*.py
Defaults to an abbreviated set of tests.  If -l is thrown,
we exectute the additional test of 'test_gcodeFileReading', which
makes sure we can parse skeinforge and MG files w/o errors.
That seems really important, but its actually unnecessary.
"""


try:
    import unittest2 as unittest
except ImportError:
    import unittest
import logging
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-l', dest="long", 
    help="Run The Entirety of the unit tests.", default=False, action="store_true")
args = parser.parse_args()

#Configure logging (This should only be done for testing, nowhere else)
logging.basicConfig()
#Disable logging
logging.disable(100)

if __name__ == "__main__":
  all_tests = unittest.TestLoader().discover('tests', pattern='*.py') 
  if args.long:
    unittest.TextTestRunner().run(all_tests)
  else:
    for test in all_tests:
      if 'gcodeFileReading' not in str(test):
        unittest.TextTestRunner().run(test)
