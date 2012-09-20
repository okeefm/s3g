import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest

import makerbot_driver

class TestABPProcessor(unittest.TestCase):

  def setUp(self):
    self.abp = makerbot_driver.GcodeProcessors.AbpProcessor()

  def tearDown(self):
    self.abp = None

  def test_transform_m107(self):
    cases = [
        ['M107\n', ''],
        ['M107', ''],
        ['M106', 'M106'],
        ]
    for case in cases:
      self.assertEqual(case[1], self.abp._transform_m107(case[0]))

  def test_transform_m106(self):
    cases = [
        ['M106\n', ''],
        ['M106', ''],
        ['M107', 'M107'],
        ]
    for case in cases:
      self.assertEqual(case[1], self.abp._transform_m106(case[0]))

if __name__ == "__main__":
  unittest.main()
