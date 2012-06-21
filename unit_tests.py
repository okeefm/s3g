#!/usr/bin/python

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import warnings

if __name__ == "__main__":
  with warnings.catch_warnings():
    warnings.simplefilter("ignore")  
    all_tests = unittest.TestLoader().discover('tests', pattern='*.py')
    unittest.TextTestRunner().run(all_tests)
